import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiment.run_experiment import (
    DEFECT_TYPES,
    REPOSITORY_ROOT,
    calculate_metrics,
    load_api_key,
    make_prediction_row,
    parse_response,
    recommend_card,
    read_cases,
    read_predictions,
    read_references,
    write_csv,
    prediction_columns,
)


class ExperimentMetricTests(unittest.TestCase):
    """Check input validation, metric policy, and model-response parsing."""

    def test_api_key_prefers_process_environment_without_reading_env_file(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "from-environment"}):
            self.assertEqual(load_api_key(), "from-environment")

    def test_api_key_loads_quoted_api_key_from_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text('API_KEY="local-test-key"\n', encoding="utf-8")
            with patch("experiment.run_experiment.REPOSITORY_ROOT", root):
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(load_api_key(), "local-test-key")

    def test_counts_true_and_false_detections_per_defect(self):
        case_ids = {f"card_{number:02}" for number in range(1, 11)}
        references = {
            ("card_01", "corner_wear"),
            ("card_01", "surface_scratch"),
            ("card_02", "edge_wear"),
        }
        predictions = {
            ("card_01", "corner_wear"),
            ("card_01", "edge_wear"),
            ("card_02", "edge_wear"),
            ("card_03", "surface_scratch"),
        }

        rows = calculate_metrics(case_ids, references, predictions)
        by_defect = {row["defect"]: row for row in rows}

        self.assertEqual(
            (
                by_defect["edge_wear"]["true_positives"],
                by_defect["edge_wear"]["false_positives"],
                by_defect["edge_wear"]["false_negatives"],
            ),
            (1, 1, 0),
        )
        self.assertEqual(by_defect["edge_wear"]["precision"], 0.5)
        self.assertEqual(by_defect["ALL"]["true_positives"], 2)
        self.assertEqual(by_defect["ALL"]["false_positives"], 2)
        self.assertEqual(by_defect["ALL"]["false_negatives"], 1)

    def test_defect_weights_and_recommendation_thresholds(self):
        examples = (
            ({"corner_wear"}, 9.5, "SUBMIT FOR GRADING"),
            ({"edge_wear"}, 9.3, "SUBMIT FOR GRADING"),
            ({"surface_scratch"}, 8.5, "SELL RAW"),
            ({"card_bending"}, 6.5, "SELL RAW"),
            ({"other_visible_issue"}, 7.5, "SELL RAW"),
            ({"corner_wear", "card_bending"}, 6.0, "SELL RAW"),
            ({"edge_wear", "card_bending"}, 5.8, "DO NOT BUY"),
            (set(), 10.0, "SUBMIT FOR GRADING"),
        )
        for defects, expected_score, expected_recommendation in examples:
            with self.subTest(defects=defects):
                score, recommendation = recommend_card(defects)
                self.assertEqual(score, expected_score)
                self.assertEqual(recommendation, expected_recommendation)

    def test_all_detected_defects_produce_low_weighted_score(self):
        score, recommendation = recommend_card(
            {"corner_wear", "edge_wear", "surface_scratch", "card_bending", "other_visible_issue"}
        )
        self.assertEqual(score, 1.3)
        self.assertEqual(recommendation, "DO NOT BUY")

    def test_response_requires_all_defect_categories_and_valid_confidence(self):
        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"defects":{'
                                    '"corner_wear":{"present":true,"confidence":0.8,"evidence":"worn"},'
                                    '"edge_wear":{"present":false,"confidence":0.9,"evidence":"none"},'
                                    '"surface_scratch":{"present":false,"confidence":0.7,"evidence":"none"},'
                                    '"card_bending":{"present":true,"confidence":0.6,"evidence":"visible crease"},'
                                    '"other_visible_issue":{"present":false,"confidence":0.8,"evidence":"none"}'
                                    "}}"
                                )
                            }
                        ]
                    }
                }
            ]
        }
        parsed = parse_response(response)
        self.assertTrue(parsed["corner_wear"]["present"])
        self.assertFalse(parsed["edge_wear"]["present"])
        self.assertTrue(parsed["card_bending"]["present"])

    def test_billed_output_tokens_include_thinking_tokens(self):
        response = {
            "usageMetadata": {
                "promptTokenCount": 2000,
                "candidatesTokenCount": 25,
                "thoughtsTokenCount": 4,
            },
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"defects":{'
                                    '"corner_wear":{"present":false,"confidence":0.8,"evidence":"none"},'
                                    '"edge_wear":{"present":false,"confidence":0.9,"evidence":"none"},'
                                    '"surface_scratch":{"present":false,"confidence":0.7,"evidence":"none"},'
                                    '"card_bending":{"present":false,"confidence":0.7,"evidence":"not visible"},'
                                    '"other_visible_issue":{"present":false,"confidence":0.7,"evidence":"none"}'
                                    "}}"
                                )
                            }
                        ]
                    }
                }
            ],
        }

        row = make_prediction_row("card_01", "gemini-3.8-flash", response, 1.25)
        self.assertEqual(row["input_tokens"], 2000)
        self.assertEqual(row["output_tokens"], 29)
        self.assertEqual(row["thinking_tokens"], 4)
        self.assertEqual(row["heuristic_condition_score"], 10.0)
        self.assertEqual(row["recommendation"], "SUBMIT FOR GRADING")

    def test_csv_inputs_and_predictions_work_for_ten_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases_path = root / "cases.csv"
            references_path = root / "references.csv"
            predictions_path = root / "predictions.csv"
            with cases_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(("image_id", "image_path"))
                for number in range(1, 11):
                    image_id = f"card_{number:02}"
                    image_path = root / f"{image_id}.jpg"
                    image_path.write_bytes(b"test fixture")
                    writer.writerow((image_id, image_path.name))
            references_path.write_text(
                "image_id,defect,present\n"
                # Every pair is explicit so an absent label is a reviewed negative.
                + "".join(
                    f"card_{number:02},"
                    f"{defect},"
                    f"{str(number == 1 and defect == 'corner_wear').lower()}\n"
                    for number in range(1, 11)
                    for defect in DEFECT_TYPES
                ),
                encoding="utf-8",
            )
            rows = []
            for number in range(1, 11):
                row = {
                    "image_id": f"card_{number:02}",
                    "model": "fixture",
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "thinking_tokens": 0,
                    "latency_seconds": 0.1,
                }
                for defect in DEFECT_TYPES:
                    row[f"{defect}_detected"] = (
                        "true" if number == 1 and defect == "corner_wear" else "false"
                    )
                    row[f"{defect}_confidence"] = 0.8
                    row[f"{defect}_evidence"] = "fixture"
                rows.append(row)
            write_csv(predictions_path, rows, prediction_columns())

            cases = read_cases(cases_path)
            case_ids = {case.image_id for case in cases}
            references, uncertain = read_references(references_path, case_ids)
            predictions = read_predictions(predictions_path, case_ids)
            metrics = calculate_metrics(case_ids, references, predictions, uncertain)

            corner = next(row for row in metrics if row["defect"] == "corner_wear")
            self.assertEqual(len(cases), 10)
            self.assertEqual(corner["true_positives"], 1)
            self.assertEqual(corner["false_positives"], 0)
            self.assertEqual(corner["false_negatives"], 0)
            self.assertEqual(corner["evaluated_pairs"], 10)

    def test_reference_labels_must_cover_every_image_and_defect(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "references.csv"
            path.write_text(
                "image_id,defect,present\n1,corner_wear,false\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "explicitly cover all 5"):
                read_references(path, {"1"})

    def test_uncertain_reference_is_excluded_from_metrics(self):
        case_ids = {"card_01", "card_02"}
        references = {("card_01", "surface_scratch")}
        predictions = {
            ("card_01", "surface_scratch"),
            ("card_02", "surface_scratch"),
        }
        metrics = calculate_metrics(
            case_ids,
            references,
            predictions,
            {("card_02", "surface_scratch")},
        )
        surface = next(row for row in metrics if row["defect"] == "surface_scratch")
        self.assertEqual(surface["true_positives"], 1)
        self.assertEqual(surface["false_positives"], 0)
        self.assertEqual(surface["uncertain_pairs"], 1)

    def test_card_bending_is_scored_as_its_own_category(self):
        metrics = calculate_metrics(
            {"card_01", "card_02"},
            {("card_01", "card_bending")},
            {("card_01", "card_bending"), ("card_02", "card_bending")},
        )
        bending = next(row for row in metrics if row["defect"] == "card_bending")
        self.assertEqual(bending["true_positives"], 1)
        self.assertEqual(bending["false_positives"], 1)
        self.assertEqual(bending["false_negatives"], 0)

    def test_reviewed_labels_cover_all_categories_for_ten_photos(self):
        cases = read_cases(Path("experiment/cases.csv"))
        case_ids = {case.image_id for case in cases}
        read_references(
            Path("experiment/reference_defects.csv"),
            case_ids,
        )
        with Path("experiment/reference_defects.csv").open(
            newline="", encoding="utf-8"
        ) as file:
            rows = list(csv.DictReader(file))
        for defect in DEFECT_TYPES:
            with self.subTest(defect=defect):
                self.assertEqual(
                    sum(row["defect"] == defect for row in rows),
                    len(case_ids),
                )

    def test_reference_reader_preserves_uncertain_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "references.csv"
            path.write_text(
                "image_id,defect,present\n"
                "1,corner_wear,false\n"
                "1,edge_wear,uncertain\n"
                "1,surface_scratch,true\n"
                "1,card_bending,uncertain\n"
                "1,other_visible_issue,false\n",
                encoding="utf-8",
            )
            references, uncertain = read_references(path, {"1"})
            self.assertEqual(references, {("1", "surface_scratch")})
            self.assertEqual(
                uncertain,
                {("1", "edge_wear"), ("1", "card_bending")},
            )


if __name__ == "__main__":
    unittest.main()
