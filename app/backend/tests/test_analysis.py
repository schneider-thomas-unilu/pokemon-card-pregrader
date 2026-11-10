import asyncio
import json
import os
from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi import UploadFile
from PIL import Image, ImageDraw

from app.backend.api.routes import (
    MAX_PROVIDER_ERROR_BODY_BYTES,
    _analyze_with_gemini,
    _format_provider_error_body,
    _quality_gate,
    _read_points,
    analyze_card,
)
from app.backend.services.gemini_contract import (
    DEFECT_TYPES,
    GEMINI_PROMPT,
    gemini_response_schema,
)


class AnalysisHelpersTests(unittest.TestCase):
    def test_provider_error_body_is_bounded_and_redacts_api_key(self):
        body = b'{"error":"bad request","key":"test-secret"}'
        formatted = _format_provider_error_body(body, "test-secret")
        self.assertIn("[redacted]", formatted)
        self.assertNotIn("test-secret", formatted)

        large_body = b"x" * (MAX_PROVIDER_ERROR_BODY_BYTES + 1)
        truncated = _format_provider_error_body(large_body, "")
        self.assertLessEqual(len(truncated.split("\n", maxsplit=1)[0]), MAX_PROVIDER_ERROR_BODY_BYTES)
        self.assertIn("response body truncated", truncated)

    def test_gemini_request_and_result_match_the_app_contract(self):
        defects = {
            defect: {
                "present": defect == "corner_wear",
                "confidence": 0.75,
                "evidence": "visible evidence",
            }
            for defect in DEFECT_TYPES
        }
        provider_response = {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps({"defects": defects})}]}}
            ]
        }
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch("app.backend.api.routes.urllib.request.urlopen") as urlopen:
                urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
                    provider_response
                ).encode()
                result = _analyze_with_gemini(b"card image", "image/jpeg")

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["contents"][0]["role"], "user")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], GEMINI_PROMPT)
        self.assertEqual(payload["contents"][0]["parts"][1]["inlineData"]["mimeType"], "image/jpeg")
        self.assertEqual(payload["generationConfig"]["temperature"], 0)
        self.assertEqual(payload["generationConfig"]["responseSchema"], gemini_response_schema())
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        self.assertEqual(result, {"defects": defects})

    def test_reads_four_numeric_landmarks(self):
        points = _read_points("[[0,0],[100,0],[100,200],[0,200]]", "Corners")
        self.assertEqual(points[2], (100.0, 200.0))

    def test_rejects_boolean_landmark_coordinates(self):
        with self.assertRaises(HTTPException):
            _read_points("[[true,0],[100,0],[100,200],[0,200]]", "Corners")

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

    def test_analyze_endpoint_explains_review_basis_without_assigning_grade(self):
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
                card_corners="[[25,30],[375,30],[375,570],[25,570]]",
                inner_corners="[[55,60],[345,60],[345,540],[55,540]]",
                include_ai=False,
            )
        )
        self.assertEqual(len(result["card_corners"]), 4)
        self.assertEqual(result["centering"]["left_right_ratio"], "50.0:50.0")
        self.assertEqual(result["centering"]["top_bottom_ratio"], "50.0:50.0")
        self.assertIsNone(result["vision"])
        self.assertEqual(
            [item["factor"] for item in result["review_basis"]],
            ["Photo quality", "Card outline", "Centering estimate", "Visible condition"],
        )
        self.assertIn("Left:right 50.0:50.0", result["review_basis"][2]["result"])
        self.assertIn("No numerical grade is assigned", result["grade_note"])
        self.assertIn("manual photo measurements", result["grade_note"])

    def test_analyze_endpoint_rejects_inner_border_outside_card(self):
        image = Image.new("RGB", (400, 600), "#8ac080")
        draw = ImageDraw.Draw(image)
        draw.rectangle((25, 30, 375, 570), fill="#faf8e9", outline="#222222", width=8)
        for y in range(100, 500, 35):
            draw.line((75, y, 325, y + 10), fill="#777777", width=3)
        image_bytes = BytesIO()
        image.save(image_bytes, format="JPEG")

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(
                analyze_card(
                    image_file=UploadFile(
                        filename="card.jpg", file=BytesIO(image_bytes.getvalue())
                    ),
                    card_corners="[[25,30],[375,30],[375,570],[25,570]]",
                    inner_corners="[[0,0],[345,60],[345,540],[55,540]]",
                    include_ai=False,
                )
            )
        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("inside", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
