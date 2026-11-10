import base64
import json
import math
import os
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from ..services.centering import calculate_centering
from ..services.gemini_contract import (
    DEFECT_TYPES,
    GEMINI_PROMPT,
    gemini_response_schema,
)

router = APIRouter(prefix="/api")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
MAX_PROVIDER_ERROR_BODY_BYTES = 4000


def _format_provider_error_body(body: bytes, api_key: str) -> str:
    truncated = len(body) > MAX_PROVIDER_ERROR_BODY_BYTES
    text = body[:MAX_PROVIDER_ERROR_BODY_BYTES].decode("utf-8", errors="replace")
    text = "".join(character for character in text if character.isprintable() or character in "\n\t")
    if api_key:
        text = text.replace(api_key, "[redacted]")
    if truncated:
        text += "\n… (response body truncated)"
    return text or "Gemini did not include an error response body."


def _read_points(value: str, label: str) -> tuple[tuple[float, float], ...]:
    try:
        points = json.loads(value)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=422, detail=f"{label} must be valid JSON.") from error
    if not isinstance(points, list) or len(points) != 4:
        raise HTTPException(status_code=422, detail=f"{label} must contain four corners.")
    valid_points = all(
        isinstance(point, list)
        and len(point) == 2
        and all(
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
            for value in point
        )
        for point in points
    )
    if not valid_points:
        raise HTTPException(
            status_code=422, detail=f"{label} corners must each contain finite numeric x and y coordinates."
        )
    return tuple((float(point[0]), float(point[1])) for point in points)


def _quality_gate(image: Image.Image) -> list[str]:
    reasons = []
    if image.width < 300 or image.height < 400:
        reasons.append("Use a higher-resolution photo (at least 300 × 400 pixels).")

    grayscale = image.convert("L")
    mean_luminance = ImageStat.Stat(grayscale).mean[0]
    if mean_luminance < 12:
        reasons.append("The photo is too dark; use brighter, even lighting.")
    elif mean_luminance > 245:
        reasons.append("The photo is overexposed; reduce glare and use softer lighting.")

    edge_deviation = ImageStat.Stat(grayscale.filter(ImageFilter.FIND_EDGES)).stddev[0]
    if edge_deviation < 5:
        reasons.append("The photo appears out of focus; retake it with the card in focus.")
    return reasons


def _analyze_with_gemini(image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI analysis was requested, but GEMINI_API_KEY is not configured.",
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": GEMINI_PROMPT},
                    {"inlineData": {"mimeType": mime_type, "data": encoded_image}},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": gemini_response_schema(),
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=int(os.getenv("API_TIMEOUT_SECONDS", "45"))
        ) as response:
            response_body = json.loads(response.read())
    except urllib.error.HTTPError as error:
        error_body = _format_provider_error_body(error.read(MAX_PROVIDER_ERROR_BODY_BYTES + 1), api_key)
        raise HTTPException(
            status_code=502,
            detail={
                "message": f"Gemini returned HTTP {error.code}.",
                "provider_response_body": error_body,
            },
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise HTTPException(status_code=502, detail="Vision provider request failed or timed out.") from error
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=502, detail="Vision provider returned invalid JSON.") from error

    try:
        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        defects = result["defects"]
        if not isinstance(defects, dict) or set(defects) != set(DEFECT_TYPES):
            raise ValueError("Unexpected defect categories.")
        for item in defects.values():
            if (
                not isinstance(item["present"], bool)
                or isinstance(item["confidence"], bool)
                or not isinstance(item["confidence"], (int, float))
                or not math.isfinite(item["confidence"])
                or not 0 <= item["confidence"] <= 1
                or not isinstance(item["evidence"], str)
            ):
                raise ValueError("Invalid defect result.")
        return result
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="Vision provider returned an unsupported analysis format."
        ) from error


@router.post("/analyze")
async def analyze_card(
    image_file: Annotated[UploadFile, File()],
    card_corners: Annotated[str, Form()],
    inner_corners: Annotated[str, Form()],
    include_ai: Annotated[bool, Form()] = False,
) -> dict[str, Any]:
    image_bytes = await image_file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413, detail=f"Image exceeds the {MAX_UPLOAD_MB} MB upload limit."
        )
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image_format = source.format
            if source.width * source.height > 30_000_000:
                raise HTTPException(
                    status_code=413,
                    detail="Image resolution exceeds the 30-megapixel limit.",
                )
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG, PNG, or WebP image.") from error
    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG, PNG, or WebP image.")

    retake_reasons = _quality_gate(image)
    if retake_reasons:
        raise HTTPException(
            status_code=422,
            detail={"message": "Photo did not pass the basic quality check.", "retake_reasons": retake_reasons},
        )

    corners = _read_points(card_corners, "Card corners")
    if any(x < 0 or y < 0 or x > image.width or y > image.height for x, y in corners):
        raise HTTPException(status_code=422, detail="Selected corners must be inside the uploaded image.")
    inner = _read_points(inner_corners, "Inner printed border")
    if any(x < 0 or y < 0 or x > image.width or y > image.height for x, y in inner):
        raise HTTPException(status_code=422, detail="Selected inner-border corners must be inside the uploaded image.")
    try:
        centering = calculate_centering(corners, inner)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    vision = (
        await run_in_threadpool(
            _analyze_with_gemini, image_bytes, ALLOWED_FORMATS[image_format]
        )
        if include_ai
        else None
    )
    result: dict[str, Any] = {
        "photo": {"width": image.width, "height": image.height, "quality": "passed_basic_checks"},
        "card_corners": corners,
        "inner_corners": inner,
        "centering": centering,
        "vision": vision,
        "review_basis": [
            {
                "factor": "Photo quality",
                "explanation": (
                    "The app checked minimum image dimensions, average brightness, "
                    "and an edge-detail focus proxy before accepting the photo."
                ),
                "result": (
                    f"Passed basic checks at {image.width} × {image.height} pixels."
                ),
            },
            {
                "factor": "Card outline",
                "explanation": (
                    "You marked the four outside card corners, which define the "
                    "card plane used to correct perspective in the centering calculation."
                ),
                "result": "Four outside card corners marked.",
            },
            {
                "factor": "Centering estimate",
                "explanation": (
                    "The app maps the selected inner printed-border corners into a "
                    "front-on unit square using a projective transform, then compares "
                    "the opposing border widths. Accuracy depends on landmark placement."
                ),
                "result": (
                    f"Left:right {centering['left_right_ratio']} · "
                    f"Top:bottom {centering['top_bottom_ratio']}."
                ),
            },
            {
                "factor": "Visible condition",
                "explanation": (
                    "When enabled, Gemini reviews this photo for possible visible "
                    "wear and reports evidence with model-reported confidence. "
                    "This confidence is not calibrated."
                    if vision
                    else "AI analysis was not requested. No surface, corner, or edge condition assessment was performed."
                ),
                "result": (
                    f"{sum(item['present'] for item in vision['defects'].values())} possible "
                    "visible issue categories noted; see findings above."
                    if vision
                    else "Not assessed."
                ),
            },
        ],
        "grade_note": (
            "No numerical grade is assigned. This MVP has no calibrated grading "
            "model or validated thresholds to turn a single photo into a reliable "
            "professional grade. Centering ratios are manual photo measurements, "
            "not a professional grade or an assessment of other card condition. "
            "The photo checks, centering estimate, and optional visible-condition "
            "observations above are the evidence available for this review."
        ),
        "limitations": [
            "This is a preliminary photo-based aid, not an official grade or authentication.",
            "Only visible areas in this photo can be assessed; hidden or angle-dependent defects may be missed.",
            "Centering is estimated from manually selected corners; inaccurate landmarks, glare, perspective, or an unclear printed border can affect the result.",
        ],
    }
    return result
