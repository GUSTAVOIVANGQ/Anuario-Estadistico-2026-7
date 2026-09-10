import unittest
from pathlib import Path

from anuario2026.registry import load_figures, load_project_config, reference_page


ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_complete_inventory(self):
        figures = load_figures(ROOT, load_project_config(ROOT))
        self.assertEqual(105, len(figures))
        self.assertEqual("A.1", figures[0].figure_id)
        self.assertEqual("H.14", figures[-1].figure_id)

    def test_reference_pages(self):
        self.assertEqual(11, reference_page("A.1"))
        self.assertEqual(48, reference_page("C.3"))
        self.assertEqual(48, reference_page("C.4"))
        self.assertEqual(85, reference_page("F.1.4"))
        self.assertEqual(115, reference_page("H.14"))

    def test_manual_figures(self):
        figures = load_figures(ROOT, load_project_config(ROOT))
        manual = {item.figure_id for item in figures if item.manual_input}
        self.assertEqual({"A.5", "B.22"}, manual)


if __name__ == "__main__":
    unittest.main()
