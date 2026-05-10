import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traversal import (
    GridMap,
    Point,
    a_star,
    dijkstra,
    find_path,
    list_algorithms,
    build_algorithm_run_row,
    build_run_path_node_rows,
    run_all_algorithms,
    run_algorithm,
    run_algorithms,
    run_pathfinding_request,
)


class PathfindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.simple_grid = GridMap(
            [
                [1, 1, 1],
                [0, 0, 1],
                [1, 1, 1],
            ]
        )
        self.start = Point(0, 0)
        self.goal = Point(2, 2)

    def test_find_path_returns_valid_route(self) -> None:
        path = find_path(self.simple_grid, self.start, self.goal)

        self.assertEqual(path[0], self.start)
        self.assertEqual(path[-1], self.goal)
        self.assertEqual(len(path), 5)

    def test_a_star_returns_result_with_stats(self) -> None:
        result = a_star(self.simple_grid, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertEqual(result.moves, 4)
        self.assertEqual(result.path_cost, 4)
        self.assertIn("runtime_ms", result.to_dict())
        self.assertGreaterEqual(result.visited_count, 1)
        self.assertGreaterEqual(result.expanded_count, 1)
        self.assertGreaterEqual(result.frontier_pushes, 1)

    def test_dijkstra_returns_valid_route(self) -> None:
        result = dijkstra(self.simple_grid, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertEqual(result.moves, 4)

    def test_a_star_and_dijkstra_match_shortest_path_length(self) -> None:
        a_star_result = a_star(self.simple_grid, self.start, self.goal)
        dijkstra_result = dijkstra(self.simple_grid, self.start, self.goal)

        self.assertEqual(a_star_result.moves, dijkstra_result.moves)
        self.assertEqual(a_star_result.path_cost, dijkstra_result.path_cost)

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

    def test_unreachable_destination_returns_result_without_path(self) -> None:
        grid_map = GridMap(
            [
                [1, 0, 1],
                [0, 0, 0],
                [1, 0, 1],
            ]
        )

        result = dijkstra(grid_map, Point(0, 0), Point(2, 2))

        self.assertFalse(result.path_found)
        self.assertEqual(result.path, [])
        self.assertIsNone(result.path_cost)

    def test_diagonal_only_route_is_not_allowed(self) -> None:
        grid_map = GridMap(
            [
                [1, 0],
                [0, 1],
            ]
        )

        path = find_path(grid_map, Point(0, 0), Point(1, 1))

        self.assertEqual(path, [])

    def test_start_equals_goal_returns_single_node_path(self) -> None:
        point = Point(0, 0)
        result = a_star(GridMap([[1, 1], [1, 1]]), point, point)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path, [point])
        self.assertEqual(result.moves, 0)
        self.assertEqual(result.path_cost, 0)

    def test_run_algorithm_runs_one_selected_algorithm(self) -> None:
        result = run_algorithm("astar", self.simple_grid, self.start, self.goal)

        self.assertEqual(result.algorithm_name, "astar")
        self.assertTrue(result.path_found)

    def test_run_algorithms_runs_one_selected_algorithm(self) -> None:
        results = run_algorithms("astar", self.simple_grid, self.start, self.goal)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].algorithm_name, "astar")

    def test_run_algorithms_runs_multiple_selected_algorithms(self) -> None:
        results = run_algorithms(
            ["astar", "dijkstra"], self.simple_grid, self.start, self.goal
        )

        self.assertEqual(
            [result.algorithm_name for result in results], ["astar", "dijkstra"]
        )

    def test_run_all_algorithms_runs_every_registered_algorithm(self) -> None:
        results = run_all_algorithms(self.simple_grid, self.start, self.goal)

        self.assertEqual(len(results), len(list_algorithms()))
        self.assertEqual(
            [result.algorithm_name for result in results],
            list_algorithms(),
        )

    def test_invalid_algorithm_name_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported algorithm 'unknown'"):
            run_algorithm("unknown", self.simple_grid, self.start, self.goal)

    def test_result_objects_include_runtime_ms_and_stats(self) -> None:
        result = run_algorithm("dijkstra", self.simple_grid, self.start, self.goal)
        result_dict = result.to_dict()

        self.assertIn("runtime_ms", result_dict)
        self.assertIn("visited_count", result_dict)
        self.assertIn("expanded_count", result_dict)
        self.assertIn("frontier_pushes", result_dict)

    def test_run_pathfinding_request_returns_serializable_payload(self) -> None:
        payload = run_pathfinding_request(
            self.simple_grid, self.start, self.goal, ["astar", "dijkstra"]
        )

        self.assertEqual(payload["start"], {"row": 0, "col": 0})
        self.assertEqual(payload["goal"], {"row": 2, "col": 2})
        self.assertEqual(payload["selected_algorithms"], ["astar", "dijkstra"])
        self.assertEqual(len(payload["results"]), 2)

    def test_serialization_helpers_prepare_database_rows(self) -> None:
        result = a_star(self.simple_grid, self.start, self.goal)
        point_to_node_id = {
            (0, 0): "node-start",
            (0, 1): "node-01",
            (0, 2): "node-02",
            (1, 2): "node-12",
            (2, 2): "node-goal",
        }

        run_row = build_algorithm_run_row(
            result,
            map_id="map-123",
            start=self.start,
            goal=self.goal,
            point_to_node_id=point_to_node_id,
        )
        path_rows = build_run_path_node_rows(
            result,
            run_id="run-123",
            point_to_node_id=point_to_node_id,
        )

        self.assertEqual(run_row["map_id"], "map-123")
        self.assertEqual(run_row["algorithm"], "astar")
        self.assertEqual(run_row["start_node_id"], "node-start")
        self.assertEqual(run_row["end_node_id"], "node-goal")
        self.assertEqual(path_rows[0]["node_id"], "node-start")
        self.assertEqual(path_rows[-1]["node_id"], "node-goal")
        self.assertTrue(path_rows[-1]["reached"])


if __name__ == "__main__":
    unittest.main()
