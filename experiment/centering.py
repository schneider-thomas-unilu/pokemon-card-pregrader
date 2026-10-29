"""Perspective-correct centering calculations from manually selected landmarks."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


MEASUREMENT_COLUMNS = (
    "image_id",
    "outer_corners",
    "inner_corners",
    "left_margin_percent",
    "right_margin_percent",
    "top_margin_percent",
    "bottom_margin_percent",
    "left_right_ratio",
    "top_bottom_ratio",
    "method",
)


def _validate_quadrilateral(
    points: tuple[tuple[float, float], ...], label: str
) -> None:
    if len(points) != 4:
        raise ValueError(f"{label} must contain four corners.")
    if any(len(point) != 2 for point in points):
        raise ValueError(f"{label} corners must each have an x and y coordinate.")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for point in points
        for value in point
    ):
        raise ValueError(f"{label} contains a non-finite or non-numeric coordinate.")

    cross_products = []
    for index in range(4):
        first = points[index]
        second = points[(index + 1) % 4]
        third = points[(index + 2) % 4]
        cross = (second[0] - first[0]) * (third[1] - second[1]) - (
            second[1] - first[1]
        ) * (third[0] - second[0])
        if abs(cross) < 1e-8:
            raise ValueError(f"{label} corners must form a non-degenerate quadrilateral.")
        cross_products.append(cross)
    if not (all(value > 0 for value in cross_products) or all(value < 0 for value in cross_products)):
        raise ValueError(f"{label} corners must be selected in perimeter order.")


def _solve_linear_system(
    matrix: list[list[float]], values: list[float]
) -> list[float]:
    """Solve a small square system with pivoted Gaussian elimination."""
    size = len(values)
    augmented = [row[:] + [value] for row, value in zip(matrix, values)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Selected card corners cannot be perspective-rectified.")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [augmented[row][-1] for row in range(size)]


def _card_to_unit_square(
    outer: tuple[tuple[float, float], ...],
    point: tuple[float, float],
) -> tuple[float, float]:
    """Map a point through the projective transform defined by the card corners."""
    destinations = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    matrix = []
    values = []
    for (x, y), (u, v) in zip(outer, destinations):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        values.append(u)
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        values.append(v)
    a, b, c, d, e, f, g, h = _solve_linear_system(matrix, values)
    x, y = point
    denominator = g * x + h * y + 1
    if abs(denominator) < 1e-12:
        raise ValueError("A selected inner-border corner cannot be rectified.")
    return (
        (a * x + b * y + c) / denominator,
        (d * x + e * y + f) / denominator,
    )


def _ratio_text(first: float, second: float) -> str:
    total = first + second
    if total <= 0:
        raise ValueError("Measured opposing borders must have positive total width.")
    first_share = first / total * 100
    return f"{first_share:.1f}:{100 - first_share:.1f}"


def calculate_centering(
    outer_corners: tuple[tuple[float, float], ...],
    inner_corners: tuple[tuple[float, float], ...],
) -> dict[str, Any]:
    """Calculate border percentages after rectifying the photographed card plane."""
    _validate_quadrilateral(outer_corners, "Outer card")
    _validate_quadrilateral(inner_corners, "Inner border")
    transformed = tuple(
        _card_to_unit_square(outer_corners, point) for point in inner_corners
    )
    tolerance = 0.02
    if any(
        coordinate < -tolerance or coordinate > 1 + tolerance
        for point in transformed
        for coordinate in point
    ):
        raise ValueError("Inner-border corners must lie inside the selected card corners.")
    left = sum(point[0] for point in (transformed[0], transformed[3])) / 2
    right = 1 - sum(point[0] for point in (transformed[1], transformed[2])) / 2
    top = sum(point[1] for point in (transformed[0], transformed[1])) / 2
    bottom = 1 - sum(point[1] for point in (transformed[2], transformed[3])) / 2
    if min(left, right, top, bottom) <= 0:
        raise ValueError("The selected inner border must leave measurable margins on all sides.")

    return {
        "left_margin_percent": round(left * 100, 2),
        "right_margin_percent": round(right * 100, 2),
        "top_margin_percent": round(top * 100, 2),
        "bottom_margin_percent": round(bottom * 100, 2),
        "left_right_ratio": _ratio_text(left, right),
        "top_bottom_ratio": _ratio_text(top, bottom),
        "method": "manual_landmarks_perspective_rectified",
    }


def read_centering_measurements(
    path: Path, case_ids: set[str]
) -> dict[str, dict[str, Any]]:
    """Recalculate saved manual landmark pairs and require one row per image."""
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or not set(MEASUREMENT_COLUMNS).issubset(
            reader.fieldnames
        ):
            raise ValueError("Centering CSV is missing required measurement columns.")
        measurements = {}
        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            if image_id not in case_ids:
                raise ValueError(f"Centering CSV refers to an unknown image: {image_id}")
            if image_id in measurements:
                raise ValueError(f"Duplicate centering measurement for image: {image_id}")
            try:
                outer = tuple(tuple(point) for point in json.loads(row["outer_corners"]))
                inner = tuple(tuple(point) for point in json.loads(row["inner_corners"]))
                measurements[image_id] = calculate_centering(outer, inner)
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                raise ValueError(
                    f"Invalid saved centering landmarks for image {image_id}."
                ) from error
    if set(measurements) != case_ids:
        missing = sorted(case_ids - set(measurements))
        raise ValueError(
            "Centering measurements must cover every manifest image; missing: "
            + ", ".join(missing)
        )
    return measurements
