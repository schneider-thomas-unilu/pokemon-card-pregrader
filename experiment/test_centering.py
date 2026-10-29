import unittest

from experiment.centering import calculate_centering


class CenteringCalculationTests(unittest.TestCase):
    def test_calculates_axis_aligned_border_margins_and_ratios(self):
        result = calculate_centering(
            ((0, 0), (100, 0), (100, 200), (0, 200)),
            ((10, 20), (88, 20), (88, 174), (10, 174)),
        )
        self.assertEqual(result["left_margin_percent"], 10.0)
        self.assertEqual(result["right_margin_percent"], 12.0)
        self.assertEqual(result["top_margin_percent"], 10.0)
        self.assertEqual(result["bottom_margin_percent"], 13.0)
        self.assertEqual(result["left_right_ratio"], "45.5:54.5")
        self.assertEqual(result["top_bottom_ratio"], "43.5:56.5")

    def test_rectifies_a_perspective_photograph(self):
        def project(x, y):
            denominator = 0.1 * x + 0.05 * y + 1
            return (
                (200 * x + 20 * y + 20) / denominator,
                (30 * x + 390 * y + 10) / denominator,
            )

        outer = tuple(project(x, y) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1)))
        inner = tuple(
            project(x, y) for x, y in ((0.1, 0.1), (0.8, 0.1), (0.8, 0.85), (0.1, 0.85))
        )
        result = calculate_centering(outer, inner)
        self.assertAlmostEqual(result["left_margin_percent"], 10.0, places=1)
        self.assertAlmostEqual(result["right_margin_percent"], 20.0, places=1)
        self.assertAlmostEqual(result["top_margin_percent"], 10.0, places=1)
        self.assertAlmostEqual(result["bottom_margin_percent"], 15.0, places=1)

    def test_rejects_misordered_outer_corners(self):
        with self.assertRaisesRegex(ValueError, "perimeter order"):
            calculate_centering(
                ((0, 0), (100, 0), (0, 100), (100, 100)),
                ((10, 10), (90, 10), (90, 90), (10, 90)),
            )

    def test_rejects_inner_border_outside_card(self):
        with self.assertRaisesRegex(ValueError, "inside"):
            calculate_centering(
                ((0, 0), (100, 0), (100, 100), (0, 100)),
                ((-10, 10), (90, 10), (90, 90), (-10, 90)),
            )
