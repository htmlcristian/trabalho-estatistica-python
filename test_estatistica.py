import math
import tempfile
import unittest
from pathlib import Path

import estatistica


class EntradaTests(unittest.TestCase):
    def test_parse_values_accepts_separators_and_rejects_invalid_numbers(self):
        self.assertEqual(estatistica.parse_values("1, 2; 3\n4"), [1.0, 2.0, 3.0, 4.0])
        with self.assertRaises(ValueError):
            estatistica.parse_values("1, texto")
        with self.assertRaises(ValueError):
            estatistica.parse_values("   ")

    def test_load_csv_with_header_and_semicolon(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dados.csv"
            path.write_text("valor;grupo\n1;10\n2;20\n", encoding="utf-8")
            self.assertEqual(estatistica.load_csv(path), [1.0, 10.0, 2.0, 20.0])

    def test_load_csv_rejects_text_after_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dados.csv"
            path.write_text("valor\n1\nruim\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                estatistica.load_csv(path)

    def test_load_csv_rejects_mixed_text_and_number_in_header_row(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dados.csv"
            path.write_text("valor,10\n1,2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                estatistica.load_csv(path)


class AnaliseTests(unittest.TestCase):
    def test_ungrouped_uses_expected_measures(self):
        self.assertEqual(estatistica.ungrouped_summary([1, 2, 2, 8]),
                         {"mode": 2, "mean": 3.25, "median": 2.0})

    def test_discrete_table_and_weighted_measures(self):
        result = estatistica.discrete_summary([1, 1, 2, 3, 3, 3])
        self.assertEqual(result["rows"], [(1, 2, 2), (2, 1, 3), (3, 3, 6)])
        self.assertEqual(result["modes"], [3])
        self.assertEqual(result["mean"], 13 / 6)
        self.assertEqual(result["median"], 2.5)

    def test_classes_cover_every_observation_and_cumulative_frequency(self):
        rows = estatistica.build_classes([1, 2, 3, 4, 5])
        self.assertEqual(rows[-1][3], 5)
        self.assertEqual(sum(row[2] for row in rows), 5)
        self.assertAlmostEqual(rows[0][0], 1)
        self.assertAlmostEqual(rows[-1][1], 5)

    def test_constant_sample_has_defined_grouped_results(self):
        result = estatistica.continuous_summary([7, 7, 7])
        self.assertEqual(result["rows"], [(7, 7, 3, 3)])
        for measure in ("mean", "median", "mode"):
            self.assertEqual(result[measure], 7)
        self.assertTrue(all(value == 7 for value in result["positions"].values()))

    def test_grouped_interpolation_and_separatrices(self):
        # Três classes de largura 2 e frequências 2, 4 e 2.
        rows = [(0, 2, 2, 2), (2, 4, 4, 6), (4, 6, 2, 8)]
        self.assertAlmostEqual(estatistica._interpolated_position(rows, 8, 0.5), 3)
        self.assertAlmostEqual(estatistica._interpolated_position(rows, 8, 0.25), 2)
        result = estatistica.continuous_summary([0, 1, 2, 2, 2, 3, 4, 5])
        self.assertEqual(set(result["positions"]), {"Q1", "Q3", "D2", "D7", "P15", "P22", "P63", "P70"})
        self.assertTrue(all(math.isfinite(value) for value in result["positions"].values()))

    def test_continuous_summary_matches_grouped_formulas(self):
        # Sturges gera 5 classes de largura 1, com frequências 2, 2, 3, 1, 2.
        values = [0, 0.5, 1.5, 1.5, 2.5, 2.5, 2.5, 3.5, 4.5, 5]
        result = estatistica.continuous_summary(values)
        self.assertEqual(result["rows"], [
            (0, 1, 2, 2), (1, 2, 2, 4), (2, 3, 3, 7), (3, 4, 1, 8), (4, 5, 2, 10)
        ])
        self.assertAlmostEqual(result["mean"], 2.4)
        self.assertAlmostEqual(result["median"], 7 / 3)
        self.assertAlmostEqual(result["mode"], 7 / 3)
        expected = {"Q1": 1.25, "Q3": 3.5, "D2": 1, "D7": 3,
                    "P15": 0.75, "P22": 1.1, "P63": 2 + 2.3 / 3, "P70": 3}
        for name, value in expected.items():
            self.assertAlmostEqual(result["positions"][name], value)


if __name__ == "__main__":
    unittest.main()
