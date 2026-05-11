import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traversal.grid import Point
from traversal.ui import build_demo_html


class UiTests(unittest.TestCase):
    def test_generated_html_includes_backend_comparison_controls(self) -> None:
        html = build_demo_html(
            [
                [1, 1, 1],
                [1, 0, 1],
                [1, 1, 1],
            ],
            Point(0, 0),
            Point(2, 2),
        )

        self.assertIn("/run-pathfinding", html)
        self.assertIn("astar", html)
        self.assertIn("dijkstra", html)
        self.assertIn("Algorithm comparison", html)
        self.assertIn("Runtime ms", html)
        self.assertIn('max="30"', html)
        self.assertIn('max="40"', html)
        self.assertIn("Directional traffic", html)
        self.assertIn("Time Complexity", html)


if __name__ == "__main__":
    unittest.main()
