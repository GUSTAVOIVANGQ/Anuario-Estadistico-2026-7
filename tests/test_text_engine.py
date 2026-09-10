import unittest

from anuario2026.text_engine import extreme_record, percent_variation


class TextEngineTests(unittest.TestCase):
    def test_percent_variation(self):
        self.assertEqual(25.0, percent_variation(80, 100))
        self.assertIsNone(percent_variation(0, 100))

    def test_superlatives(self):
        rows = [
            {"entidad": "A", "valor": 10},
            {"entidad": "B", "valor": 30},
            {"entidad": "C", "valor": 20},
        ]
        self.assertEqual(
            {"etiqueta": "B", "valor": 30.0},
            extreme_record(rows, "valor", "entidad", "max"),
        )
        self.assertEqual(
            {"etiqueta": "A", "valor": 10.0},
            extreme_record(rows, "valor", "entidad", "min"),
        )


if __name__ == "__main__":
    unittest.main()

