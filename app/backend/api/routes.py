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

from experiment.centering import calculate_centering


router = APIRouter(prefix="/api")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
DEFECT_TYPES = (
    "corner_wear",
    "edge_wear",
    "surface_scratch",
    "bend_or_crease",
    "other_visible_issue",
)


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


def _validate_assumptions(
    raw_sale: float,
    grade_7: float,
    grade_8: float,
    grading_fee: float,
    shipping: float,
    selling_cost: float,
) -> dict[str, Any]:
    values = (raw_sale, grade_7, grade_8, grading_fee, shipping, selling_cost)
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise HTTPException(
            status_code=422,
            detail="Price and cost assumptions must be finite and non-negative.",
        )
    raw_net = raw_sale - selling_cost
    graded_nets = {
        "7": grade_7 - grading_fee - shipping - selling_cost,
        "8": grade_8 - grading_fee - shipping - selling_cost,
    }
    best_grade = max(graded_nets, key=graded_nets.get)
    best_graded_net = graded_nets[best_grade]
    return {
        "currency": "EUR",
        "assumptions": {
            "raw_sale": raw_sale,
            "grade_7_sale": grade_7,
            "grade_8_sale": grade_8,
            "grading_fee": grading_fee,
            "shipping": shipping,
            "selling_cost": selling_cost,
        },
        "raw_net": round(raw_net, 2),
        "graded_net_by_grade": {grade: round(net, 2) for grade, net in graded_nets.items()},
        "recommendation": (
            f"Submit for grading (assuming grade {best_grade})"
            if best_graded_net > raw_net
            else "Sell raw"
        ),
        "disclaimer": "Illustrative comparison from your inputs; prices, grade, and outcome are uncertain.",
    }


def _analyze_with_gemini(image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI analysis was requested, but GEMINI_API_KEY is not configured.",
        )

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    prompt = (
        "Inspect this single Pokémon card photo for visible condition issues only. "
        "Do not infer hidden damage, authenticity, a professional grade, or market value. "
        "Return JSON with a defects array containing exactly one item for each of "
        f"{', '.join(DEFECT_TYPES)}. Each item has type, observed (boolean), evidence "
        "(short string), and confidence (low, medium, or high). Treat reflections and "
        "ordinary card design cautiously. A straight-on photo cannot rule out bends."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": encoded_image}},
            ]
        }],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + urllib.parse.quote(model, safe="")
        + ":generateContent?key="
        + urllib.parse.quote(api_key, safe="")
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=int(os.getenv("API_TIMEOUT_SECONDS", "45"))
        ) as response:
            response_body = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise HTTPException(
            status_code=502, detail=f"Vision provider returned HTTP {error.code}."
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise HTTPException(status_code=502, detail="Vision provider request failed or timed out.") from error
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=502, detail="Vision provider returned invalid JSON.") from error

    try:
        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        defects = result["defects"]
        by_type = {item["type"]: item for item in defects}
        if set(by_type) != set(DEFECT_TYPES) or len(defects) != len(DEFECT_TYPES):
            raise ValueError("Unexpected defect categories.")
        for item in by_type.values():
            if (
                not isinstance(item["observed"], bool)
                or item["confidence"] not in {"low", "medium", "high"}
                or not isinstance(item["evidence"], str)
            ):
                raise ValueError("Invalid defect result.")
        result["defects"] = [by_type[defect_type] for defect_type in DEFECT_TYPES]
        result["confidence_note"] = "Model-reported confidence is not a calibrated probability."
        return result
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="Vision provider returned an unsupported analysis format."
        ) from error


@router.post("/analyze")
async def analyze_card(
    image_file: Annotated[UploadFile, File()],
    outer_corners: Annotated[str, Form()],
    inner_corners: Annotated[str, Form()],
    raw_sale: Annotated[float, Form()] = 0,
    grade_7_sale: Annotated[float, Form()] = 0,
    grade_8_sale: Annotated[float, Form()] = 0,
    grading_fee: Annotated[float, Form()] = 0,
    shipping: Annotated[float, Form()] = 0,
    selling_cost: Annotated[float, Form()] = 0,
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

    outer = _read_points(outer_corners, "Outer card corners")
    inner = _read_points(inner_corners, "Inner border corners")
    if any(x < 0 or y < 0 or x > image.width or y > image.height for x, y in outer + inner):
        raise HTTPException(status_code=422, detail="Selected corners must be inside the uploaded image.")
    try:
        centering = calculate_centering(outer, inner)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    result: dict[str, Any] = {
        "photo": {"width": image.width, "height": image.height, "quality": "passed_basic_checks"},
        "centering": centering,
        "vision": (
            await run_in_threadpool(
                _analyze_with_gemini, image_bytes, ALLOWED_FORMATS[image_format]
            )
            if include_ai
            else None
        ),
        "profit_comparison": _validate_assumptions(
            raw_sale, grade_7_sale, grade_8_sale, grading_fee, shipping, selling_cost
        ),
        "limitations": [
            "This is a preliminary photo-based aid, not an official grade or authentication.",
            "Only visible areas in this photo can be assessed; hidden or angle-dependent defects may be missed.",
            "Centering is based on manually selected landmarks and may be inaccurate if they are misplaced.",
        ],
    }
    return result
