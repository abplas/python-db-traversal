import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traversal import GridMap, Point, find_path


class PathfindingTests(unittest.TestCase):
    def test_find_path_returns_valid_route(self) -> None:
        grid_map = GridMap(
            [
                [1, 1, 1],
                [0, 0, 1],
                [1, 1, 1],
            ]
        )

        path = find_path(grid_map, Point(0, 0), Point(2, 2))

        self.assertEqual(path[0], Point(0, 0))
        self.assertEqual(path[-1], Point(2, 2))
        self.assertEqual(len(path), 5)

    def test_find_path_returns_empty_when_unreachable(self) -> None:
        grid_map = GridMap(
            [
                [1, 0, 1],
                [0, 0, 0],
                [1, 0, 1],
            ]
        )

        path = find_path(grid_map, Point(0, 0), Point(2, 2))

        self.assertEqual(path, [])

    def test_diagonal_only_route_is_not_allowed(self) -> None:
        grid_map = GridMap(
            [
                [1, 0],
                [0, 1],
            ]
        )

        path = find_path(grid_map, Point(0, 0), Point(1, 1))

        self.assertEqual(path, [])


if __name__ == "__main__":
    unittest.main()
