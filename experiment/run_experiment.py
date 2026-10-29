"""Run a reproducible Gemini vision evaluation on 10-20 labeled card photos."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import mimetypes
import os
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if __package__ == "experiment":
    from .centering import read_centering_measurements
else:
    from centering import read_centering_measurements


DEFECT_TYPES = (
    "corner_wear",
    "edge_wear",
    "surface_scratch",
    "card_bending",
    "other_visible_issue",
)
# These prototype penalties are not official grading deductions or learned coefficients.
DEFECT_SCORE_PENALTIES = {
    "corner_wear": 0.5,
    "edge_wear": 0.75,
    "surface_scratch": 1.5,
    "card_bending": 3.5,
    "other_visible_issue": 2.5,
}
GRADING_RECOMMENDATION_THRESHOLD = 9.0
DO_NOT_BUY_THRESHOLD = 6.0
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ImageCase:
    image_id: str
    image_path: Path


def load_api_key() -> str | None:
    """Prefer process secrets, then fall back to the ignored repository .env."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY")
    if api_key:
        return api_key

    env_path = REPOSITORY_ROOT / ".env"
    if not env_path.is_file():
        return None

    values = {}
    for line_number, raw_line in enumerate(
        env_path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in {"GEMINI_API_KEY", "API_KEY"}:
            raise ValueError(
                f"Invalid .env entry on line {line_number}; "
                "use GEMINI_API_KEY=value or API_KEY=value."
            )
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not value:
            raise ValueError(f".env entry on line {line_number} has an empty API key.")
        values[key] = value
    return values.get("GEMINI_API_KEY") or values.get("API_KEY")


def read_cases(path: Path) -> list[ImageCase]:
    """Load image cases and fail early on missing, duplicate, or unsupported inputs."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not {"image_id", "image_path"}.issubset(
            reader.fieldnames
        ):
            raise ValueError("Manifest must have image_id and image_path columns.")
        cases = []
        seen_ids = set()
        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            image_path_text = (row.get("image_path") or "").strip()
            if not image_id or not image_path_text:
                raise ValueError("Every manifest row needs an image_id and image_path.")
            if image_id in seen_ids:
                raise ValueError(f"Duplicate image_id in manifest: {image_id}")
            seen_ids.add(image_id)
            image_path = Path(image_path_text)
            if not image_path.is_absolute():
                image_path = path.parent / image_path
            image_path = image_path.resolve()
            if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported image type for {image_id}: {image_path}")
            if not image_path.is_file():
                raise FileNotFoundError(f"Image for {image_id} was not found: {image_path}")
            cases.append(ImageCase(image_id, image_path))

    if not 10 <= len(cases) <= 20:
        raise ValueError(f"Use 10-20 image cases; manifest currently has {len(cases)}.")
    return cases


def read_references(
    path: Path, case_ids: set[str]
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Return positive and uncertain labels after requiring a complete label grid."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not {
            "image_id",
            "defect",
            "present",
        }.issubset(reader.fieldnames):
            raise ValueError(
                "Reference CSV must have image_id, defect, and present columns."
            )
        references = set()
        uncertain = set()
        reviewed = set()
        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            defect = (row.get("defect") or "").strip()
            present = (row.get("present") or "").strip().lower()
            if not image_id or not defect or present not in {
                "true",
                "false",
                "uncertain",
            }:
                raise ValueError(
                    "Every reference row needs an image_id, defect, and "
                    "present value of true, false, or uncertain."
                )
            if image_id not in case_ids:
                raise ValueError(f"Reference refers to an image not in the manifest: {image_id}")
            if defect not in DEFECT_TYPES:
                raise ValueError(
                    f"Unsupported defect {defect!r}; use: {', '.join(DEFECT_TYPES)}"
                )
            key = (image_id, defect)
            if key in reviewed:
                raise ValueError(f"Duplicate reference label: {image_id}, {defect}")
            reviewed.add(key)
            if present == "true":
                references.add(key)
            elif present == "uncertain":
                uncertain.add(key)
    # Explicit negatives are required; otherwise an unlabeled pair could look like a false positive.
    expected = {(image_id, defect) for image_id in case_ids for defect in DEFECT_TYPES}
    if reviewed != expected:
        missing = sorted(expected - reviewed)
        examples = ", ".join(f"{image_id}/{defect}" for image_id, defect in missing[:5])
        raise ValueError(
            f"Reference labels must explicitly cover all {len(expected)} "
            f"image/defect pairs; missing {len(missing)} (for example: {examples})."
        )
    return references, uncertain


def prediction_columns() -> list[str]:
    columns = [
        "image_id",
        "model",
        "input_tokens",
        "output_tokens",
        "thinking_tokens",
        "latency_seconds",
        "heuristic_condition_score",
        "recommendation",
        "centering_left_margin_percent",
        "centering_right_margin_percent",
        "centering_top_margin_percent",
        "centering_bottom_margin_percent",
        "centering_left_right_ratio",
        "centering_top_bottom_ratio",
        "centering_method",
    ]
    for defect in DEFECT_TYPES:
        columns.extend(
            (f"{defect}_detected", f"{defect}_confidence", f"{defect}_evidence")
        )
    return columns


def recommend_card(detected_defects: set[str]) -> tuple[float, str]:
    """Apply the prototype score and map it to buy, raw-sale, or grading guidance."""
    unknown_defects = detected_defects - set(DEFECT_SCORE_PENALTIES)
    if unknown_defects:
        raise ValueError(f"Unknown defects cannot be scored: {', '.join(sorted(unknown_defects))}")

    penalty = sum(DEFECT_SCORE_PENALTIES[defect] for defect in detected_defects)
    unrounded_score = max(1.0, 10.0 - penalty)
    score = float(
        Decimal(str(unrounded_score)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    )
    if score < DO_NOT_BUY_THRESHOLD:
        recommendation = "DO NOT BUY"
    elif score >= GRADING_RECOMMENDATION_THRESHOLD:
        recommendation = "SUBMIT FOR GRADING"
    else:
        recommendation = "SELL RAW"
    return score, recommendation


def detected_defects_from_row(row: dict[str, Any]) -> set[str]:
    """Read positive defect flags from a validated predictions row."""
    return {
        defect
        for defect in DEFECT_TYPES
        if (row.get(f"{defect}_detected") or "").strip().lower() == "true"
    }


def print_recommendation(image_id: str, score: float, recommendation: str) -> None:
    """Show the per-card rule result without presenting it as an official grade."""
    print(
        f"Card {image_id}: heuristic condition score {score:.1f}/10 "
        f"-> {recommendation}",
        flush=True,
    )


def read_predictions(path: Path, case_ids: set[str]) -> set[tuple[str, str]]:
    """Validate a complete predictions file and return the model's positive labels."""
    rows = read_prediction_rows(path, case_ids)
    return {
        (row["image_id"], defect)
        for row in rows
        for defect in DEFECT_TYPES
        if row[f"{defect}_detected"].strip().lower() == "true"
    }


def read_prediction_rows(path: Path, case_ids: set[str]) -> list[dict[str, str]]:
    """Validate and return prediction rows for scoring and per-card summaries."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"image_id", *(f"{defect}_detected" for defect in DEFECT_TYPES)}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("Prediction CSV is missing required columns.")
        seen_ids = set()
        rows = []
        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            if image_id not in case_ids:
                raise ValueError(f"Prediction refers to an unknown image: {image_id}")
            if image_id in seen_ids:
                raise ValueError(f"Duplicate prediction for image: {image_id}")
            seen_ids.add(image_id)
            for defect in DEFECT_TYPES:
                value = (row.get(f"{defect}_detected") or "").strip().lower()
                if value not in {"true", "false"}:
                    raise ValueError(f"Invalid {defect} prediction for {image_id}: {value!r}")
                row[f"{defect}_detected"] = value
            row["image_id"] = image_id
            rows.append(row)
    if seen_ids != case_ids:
        missing = sorted(case_ids - seen_ids)
        raise ValueError(f"Predictions are incomplete; missing: {', '.join(missing)}")
    return rows


def calculate_metrics(
    case_ids: set[str],
    references: set[tuple[str, str]],
    predictions: set[tuple[str, str]],
    uncertain: set[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Score each defect category, excluding uncertain references from its denominator."""
    rows = []
    totals = {"tp": 0, "fp": 0, "fn": 0}
    uncertain = uncertain or set()
    for defect in DEFECT_TYPES:
        # If reviewers could not judge one category for a photo, omit only that pair.
        evaluated_cases = case_ids - {
            image_id for image_id, uncertain_defect in uncertain if uncertain_defect == defect
        }
        expected = {(image_id, defect) for image_id in case_ids} & references
        found = {(image_id, defect) for image_id in case_ids} & predictions
        evaluated = {(image_id, defect) for image_id in evaluated_cases}
        expected &= evaluated
        found &= evaluated
        tp = len(expected & found)
        fp = len(found - expected)
        fn = len(expected - found)
        totals["tp"] += tp
        totals["fp"] += fp
        totals["fn"] += fn
        rows.append(
            metric_row(
                defect,
                len(case_ids),
                len(evaluated_cases),
                len(evaluated),
                len(uncertain & {(image_id, defect) for image_id in case_ids}),
                tp,
                fp,
                fn,
            )
        )
    evaluated_pairs = {
        (image_id, defect)
        for image_id in case_ids
        for defect in DEFECT_TYPES
        if (image_id, defect) not in uncertain
    }
    rows.append(
        # ALL is a micro-average: counts are pooled across every evaluated photo/category pair.
        metric_row(
            "ALL",
            len(case_ids),
            len(case_ids),
            len(evaluated_pairs),
            len(uncertain),
            totals["tp"],
            totals["fp"],
            totals["fn"],
        )
    )
    return rows


def metric_row(
    defect: str,
    cases: int,
    evaluated_cases: int,
    evaluated_pairs: int,
    uncertain_pairs: int,
    tp: int,
    fp: int,
    fn: int,
) -> dict[str, Any]:
    """Build one metric row; undefined precision or recall is represented as None."""
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "defect": defect,
        "cases": cases,
        "evaluated_cases": evaluated_cases,
        "evaluated_pairs": evaluated_pairs,
        "uncertain_pairs": uncertain_pairs,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
    }


def request_model(
    case: ImageCase, model: str, api_key: str, timeout: int
) -> tuple[dict[str, Any], float]:
    """Send one image to Gemini and retry only transient service/network failures."""
    mime_type, _ = mimetypes.guess_type(case.image_path.name)
    if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise ValueError(f"Could not determine a supported image format: {case.image_path}")
    encoded_image = base64.b64encode(case.image_path.read_bytes()).decode("ascii")
    properties = {
        defect: {
            "type": "OBJECT",
            "properties": {
                "present": {"type": "BOOLEAN"},
                "confidence": {"type": "NUMBER"},
                "evidence": {"type": "STRING"},
            },
            "required": ["present", "confidence", "evidence"],
        }
        for defect in DEFECT_TYPES
    }
    request_body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Inspect this Pokémon card photo for visible corner wear, "
                            "edge wear, surface scratches, and card bending. For card_bending, "
                            "report only visible creases, folds, or warping; do not infer a "
                            "bend from perspective, a hand holding the card, or reflections. "
                            "A single front photo cannot rule out hidden bends, so state that "
                            "limitation in the evidence when relevant. Also report "
                            "other_visible_issue only for visible discoloration, stains, dents, "
                            "print defects, or similar issues not covered by the four named "
                            "categories. Do not count ordinary card design or holographic "
                            "patterns as defects. Do not assess centering; "
                            "it will be measured separately with image geometry. Mark a defect "
                            "present only when visible evidence supports it. Reflections alone "
                            "are not proof of scratches. Return a short evidence note and a "
                            "self-assessed confidence from 0 to 1 for each category. This is "
                            "not an official grade."
                        )
                    },
                    # Send the original photo inline; the runner does not upload it elsewhere.
                    {"inlineData": {"mimeType": mime_type, "data": encoded_image}},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "defects": {
                        "type": "OBJECT",
                        "properties": properties,
                        "required": list(DEFECT_TYPES),
                    }
                },
                "required": ["defects"],
            },
        },
    }
    request = Request(
        f"{API_ROOT}/{model}:generateContent",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        method="POST",
    )
    started = time.perf_counter()
    # Keep retries bounded so a temporary outage cannot stall a batch indefinitely.
    for attempt in range(4):
        print(
            f"Sending image {case.image_id} to {model} "
            f"(attempt {attempt + 1}/4; timeout {timeout}s)...",
            flush=True,
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            latency = time.perf_counter() - started
            print(
                f"Received response for image {case.image_id} "
                f"after {latency:.1f}s.",
                flush=True,
            )
            return result, latency
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            if error.code not in RETRYABLE_STATUS_CODES or attempt == 3:
                raise RuntimeError(
                    f"Gemini API returned HTTP {error.code}: {details[:1000]}"
                ) from error
            retry_after = error.headers.get("Retry-After")
            try:
                delay = min(max(float(retry_after), 1.0), 30.0)
            except (TypeError, ValueError):
                delay = 2**attempt
        except (TimeoutError, URLError) as error:
            if attempt == 3:
                raise RuntimeError(
                    f"Gemini API request failed after {attempt + 1} attempts: {error}"
                ) from error
            delay = 2**attempt
        print(
            f"Transient Gemini error for image {case.image_id}; "
            f"retrying in {delay:g}s.",
            flush=True,
        )
        time.sleep(delay)
    raise RuntimeError("Gemini request retry loop ended without a response.")


def parse_response(response: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate the structured model output before it enters the prediction CSV."""
    candidates = response.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidate; check safety blocks and API response.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    decoded = json.loads(text)
    defects = decoded.get("defects")
    if not isinstance(defects, dict):
        raise ValueError("Gemini response is missing the defects object.")
    validated = {}
    for defect in DEFECT_TYPES:
        result = defects.get(defect)
        if not isinstance(result, dict) or not isinstance(result.get("present"), bool):
            raise ValueError(f"Gemini response has an invalid {defect} result.")
        confidence = result.get("confidence")
        evidence = result.get("evidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError(f"Gemini response has invalid confidence for {defect}.")
        if not isinstance(evidence, str):
            raise ValueError(f"Gemini response has invalid evidence for {defect}.")
        validated[defect] = {
            "present": result["present"],
            "confidence": confidence,
            "evidence": evidence,
        }
    return validated


def make_prediction_row(
    image_id: str,
    model: str,
    response: dict[str, Any],
    latency: float,
    centering: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert one API response into a flat row, including billable thinking tokens."""
    defects = parse_response(response)
    usage = response.get("usageMetadata", {})
    input_tokens = usage.get("promptTokenCount")
    response_tokens = usage.get("candidatesTokenCount")
    thinking_tokens = usage.get("thoughtsTokenCount", 0)
    if not isinstance(input_tokens, int) or not isinstance(response_tokens, int):
        raise ValueError("Gemini response omitted token usage; cannot record experiment cost.")
    if not isinstance(thinking_tokens, int):
        raise ValueError("Gemini response returned invalid thinking-token usage.")
    row: dict[str, Any] = {
        "image_id": image_id,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": response_tokens + thinking_tokens,
        "thinking_tokens": thinking_tokens,
        "latency_seconds": round(latency, 3),
    }
    centering = centering or {}
    for field in (
        "left_margin_percent",
        "right_margin_percent",
        "top_margin_percent",
        "bottom_margin_percent",
        "left_right_ratio",
        "top_bottom_ratio",
        "method",
    ):
        row[f"centering_{field}"] = centering.get(field, "")
    for defect, result in defects.items():
        row[f"{defect}_detected"] = str(result["present"]).lower()
        row[f"{defect}_confidence"] = result["confidence"]
        row[f"{defect}_evidence"] = result["evidence"]
    score, recommendation = recommend_card(
        {defect for defect, result in defects.items() if result["present"]}
    )
    row["heuristic_condition_score"] = score
    row["recommendation"] = recommendation
    return row


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write a CSV, creating its parent directory when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metrics(path: Path, rows: list[dict[str, Any]]) -> None:
    """Persist per-category and pooled evaluation metrics."""
    write_csv(
        path,
        rows,
        [
            "defect",
            "cases",
            "evaluated_cases",
            "evaluated_pairs",
            "uncertain_pairs",
            "true_positives",
            "false_positives",
            "false_negatives",
            "precision",
            "recall",
        ],
    )


def print_metrics(rows: list[dict[str, Any]]) -> None:
    """Print a compact summary for interactive runs."""
    print("Defect          TP  FP  FN  Precision  Recall")
    for row in rows:
        precision = "N/A" if row["precision"] is None else f'{row["precision"]:.1%}'
        recall = "N/A" if row["recall"] is None else f'{row["recall"]:.1%}'
        print(
            f'{row["defect"]:<15} {row["true_positives"]:>2}  '
            f'{row["false_positives"]:>2}  {row["false_negatives"]:>2}  '
            f"{precision:>9}  {recall:>6}"
        )


def print_centering(image_id: str, row: dict[str, Any]) -> None:
    """Print manual border ratios when measurements were attached to a prediction."""
    left_right = row.get("centering_left_right_ratio")
    top_bottom = row.get("centering_top_bottom_ratio")
    if left_right and top_bottom:
        print(
            f"Centering for {image_id}: left:right {left_right}, "
            f"top:bottom {top_bottom} (manual, perspective-rectified).",
            flush=True,
        )


def main() -> None:
    """Validate inputs, run or evaluate the batch, then write and print metrics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("experiment/gemini_predictions.csv"))
    parser.add_argument("--model", default=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"))
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument(
        "--centering-measurements",
        type=Path,
        help="Optional output from measure_centering.py to attach manual border ratios.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    print(f"Loading image manifest: {args.manifest}", flush=True)
    cases = read_cases(args.manifest)
    if args.timeout <= 0:
        raise ValueError("--timeout must be a positive number of seconds.")
    case_ids = {case.image_id for case in cases}
    print(f"Validated {len(cases)} image cases.", flush=True)
    print(f"Loading reference labels: {args.references}", flush=True)
    references, uncertain = read_references(args.references, case_ids)
    print(
        f"Validated {len(DEFECT_TYPES)} categories; "
        f"{len(references)} positive labels and {len(uncertain)} uncertain labels.",
        flush=True,
    )
    centering_measurements = (
        read_centering_measurements(args.centering_measurements, case_ids)
        if args.centering_measurements
        else {}
    )
    if centering_measurements:
        print(
            f"Loaded manual centering measurements for "
            f"{len(centering_measurements)} cards.",
            flush=True,
        )
    if args.evaluate_only:
        print(f"Reading existing predictions from {args.output} (no API calls).", flush=True)
        prediction_rows = read_prediction_rows(args.output, case_ids)
        predictions = {
            (row["image_id"], defect)
            for row in prediction_rows
            for defect in DEFECT_TYPES
            if row[f"{defect}_detected"] == "true"
        }
        for row in prediction_rows:
            score, recommendation = recommend_card(detected_defects_from_row(row))
            print_recommendation(row["image_id"], score, recommendation)
            row.update(
                {
                    f"centering_{field}": value
                    for field, value in centering_measurements.get(
                        row["image_id"], {}
                    ).items()
                }
            )
            print_centering(row["image_id"], row)
    else:
        api_key = load_api_key()
        if not api_key:
            raise RuntimeError(
                "Set GEMINI_API_KEY in the environment or add it to the repository .env file."
            )
        print(f"Loaded API key from environment or .env (value hidden). Model: {args.model}.", flush=True)
        if args.output.exists() and not args.overwrite:
            raise FileExistsError(
                f"{args.output} already exists; choose another --output or pass --overwrite."
            )
        results: list[dict[str, Any]] = []
        write_csv(args.output, results, prediction_columns())
        print(
            f"Starting {len(cases)} image requests. Progress is saved to {args.output}.",
            flush=True,
        )
        for index, case in enumerate(cases, start=1):
            try:
                response, latency = request_model(case, args.model, api_key, args.timeout)
                results.append(
                    make_prediction_row(
                        case.image_id,
                        args.model,
                        response,
                        latency,
                        centering_measurements.get(case.image_id),
                    )
                )
                prediction = results[-1]
                # Persist each success so an interrupted batch can retain completed cases.
                write_csv(args.output, results, prediction_columns())
            except Exception as error:
                print(
                    f"Stopped on image {case.image_id} ({index}/{len(cases)}): "
                    f"{type(error).__name__}: {error}",
                    flush=True,
                )
                raise
            print(
                f"Saved image {case.image_id} ({index}/{len(cases)}).",
                flush=True,
            )
            print_recommendation(
                case.image_id,
                prediction["heuristic_condition_score"],
                prediction["recommendation"],
            )
            print_centering(case.image_id, prediction)
        predictions = read_predictions(args.output, case_ids)

    print("Calculating per-category metrics...", flush=True)
    metrics = calculate_metrics(case_ids, references, predictions, uncertain)
    metrics_path = args.output.with_name(f"{args.output.stem}_metrics.csv")
    write_metrics(metrics_path, metrics)
    print_metrics(metrics)
    print(f"Metrics saved to {metrics_path}", flush=True)


if __name__ == "__main__":
    main()
