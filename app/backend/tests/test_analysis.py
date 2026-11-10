import asyncio
from io import BytesIO
import unittest

from fastapi import HTTPException
from fastapi import UploadFile
from PIL import Image, ImageDraw

from app.backend.api.routes import (
    _quality_gate,
    _read_points,
    _validate_assumptions,
    analyze_card,
)


class AnalysisHelpersTests(unittest.TestCase):
    def test_reads_four_numeric_landmarks(self):
        points = _read_points("[[0,0],[100,0],[100,200],[0,200]]", "Corners")
        self.assertEqual(points[2], (100.0, 200.0))

    def test_rejects_boolean_landmark_coordinates(self):
        with self.assertRaises(HTTPException):
            _read_points("[[true,0],[100,0],[100,200],[0,200]]", "Corners")

    def test_computes_raw_and_graded_net_values(self):
        result = _validate_assumptions(30, 45, 70, 20, 8, 3)
        self.assertEqual(result["raw_net"], 27)
        self.assertEqual(result["graded_net_by_grade"], {"7": 14, "8": 39})
        self.assertEqual(
            result["recommendation"], "Submit for grading (assuming grade 8)"
        )

    def test_rejects_non_finite_or_negative_price_inputs(self):
        for value in (-1, float("nan")):
            with self.subTest(value=value), self.assertRaises(HTTPException):
                _validate_assumptions(value, 0, 0, 0, 0, 0)

    def test_quality_gate_flags_low_resolution(self):
        image = Image.new("RGB", (200, 200), "white")
        reasons = _quality_gate(image)
        self.assertTrue(any("higher-resolution" in reason for reason in reasons))

    def test_quality_gate_accepts_a_clear_evenly_lit_photo(self):
        image = Image.new("RGB", (400, 600), "#8ac080")
        draw = ImageDraw.Draw(image)
        draw.rectangle((25, 30, 375, 570), fill="#faf8e9", outline="#222222", width=8)
        draw.rectangle((55, 60, 345, 540), outline="#444444", width=5)
        for y in range(100, 500, 35):
            draw.line((75, y, 325, y + 10), fill="#777777", width=3)
        self.assertEqual(_quality_gate(image), [])

    def test_analyze_endpoint_returns_centering_and_user_input_comparison(self):
        image = Image.new("RGB", (400, 600), "#8ac080")
        draw = ImageDraw.Draw(image)
        draw.rectangle((25, 30, 375, 570), fill="#faf8e9", outline="#222222", width=8)
        draw.rectangle((55, 60, 345, 540), outline="#444444", width=5)
        for y in range(100, 500, 35):
            draw.line((75, y, 325, y + 10), fill="#777777", width=3)
        image_bytes = BytesIO()
        image.save(image_bytes, format="JPEG")

        result = asyncio.run(
            analyze_card(
                image_file=UploadFile(
                    filename="card.jpg", file=BytesIO(image_bytes.getvalue())
                ),
                outer_corners="[[25,30],[375,30],[375,570],[25,570]]",
                inner_corners="[[55,60],[345,60],[345,540],[55,540]]",
                raw_sale=30,
                grade_7_sale=45,
                grade_8_sale=70,
                grading_fee=20,
                shipping=8,
                selling_cost=3,
                include_ai=False,
            )
        )
        self.assertEqual(result["centering"]["left_right_ratio"], "50.0:50.0")
        self.assertEqual(result["profit_comparison"]["raw_net"], 27)
        self.assertIsNone(result["vision"])


if __name__ == "__main__":
    unittest.main()
