import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from main import generate_random_stoplights
from traversal import (
    GridMap,
    Point,
    Stoplight,
    a_star,
    bfs,
    build_algorithm_run_row,
    build_run_path_node_rows,
    dijkstra,
    evaluate_path_cost,
    find_path,
    greedy_best_first,
    list_algorithms,
    run_all_algorithms,
    run_algorithm,
    run_algorithms,
    run_pathfinding_request,
    weighted_astar,
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

    def test_bfs_finds_a_path_on_simple_grid(self) -> None:
        result = bfs(self.simple_grid, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertEqual(result.metadata["supports_weights"], False)
        self.assertEqual(
            result.metadata["optimality"], "optimal_for_unweighted_moves_only"
        )

    def test_greedy_best_first_finds_a_path(self) -> None:
        result = greedy_best_first(self.simple_grid, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertEqual(result.metadata["heuristic"], "manhattan")
        self.assertEqual(result.metadata["optimality"], "not_guaranteed")

    def test_weighted_astar_finds_a_path(self) -> None:
        result = weighted_astar(self.simple_grid, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertEqual(result.metadata["heuristic_weight"], 1.5)

    def test_a_star_stoplight_delay_increases_total_cost(self) -> None:
        grid_map = GridMap(
            [[1, 1, 1]],
            stoplights=[Stoplight(row=0, col=1, average_wait_seconds=15)],
        )

        result = a_star(grid_map, Point(0, 0), Point(0, 2))

        self.assertTrue(result.path_found)
        self.assertEqual(result.path_cost, 17.0)
        self.assertEqual(result.cumulative_costs, [0.0, 16.0, 17.0])
        self.assertEqual(result.metadata["stoplight_delay_total"], 15.0)
        self.assertEqual(result.metadata["stoplights_crossed"], 1)
        self.assertTrue(result.metadata["uses_stoplights"])

    def test_dijkstra_stoplight_delay_increases_total_cost(self) -> None:
        grid_map = GridMap(
            [[1, 1, 1]],
            stoplights=[Stoplight(row=0, col=1, average_wait_seconds=8)],
        )

        result = dijkstra(grid_map, Point(0, 0), Point(0, 2))

        self.assertTrue(result.path_found)
        self.assertEqual(result.path_cost, 10.0)
        self.assertEqual(result.cumulative_costs, [0.0, 9.0, 10.0])
        self.assertTrue(result.metadata["uses_stoplights"])

    def test_bfs_path_is_evaluated_with_weighted_costs_after_search(self) -> None:
        traffic = GridMap._neutral_traffic(1, 3)
        traffic["east"][0][0] = 4.0
        grid_map = GridMap(
            [[1, 1, 1]],
            traffic=traffic,
            stoplights=[Stoplight(row=0, col=1, average_wait_seconds=6)],
        )

        result = bfs(grid_map, Point(0, 0), Point(0, 2))

        self.assertTrue(result.path_found)
        self.assertEqual(result.moves, 2)
        self.assertEqual(result.path_cost, 11.0)
        self.assertEqual(result.cumulative_costs, [0.0, 10.0, 11.0])

    def test_all_algorithms_return_cumulative_costs(self) -> None:
        results = run_all_algorithms(self.simple_grid, self.start, self.goal)

        for result in results:
            self.assertTrue(result.path_found)
            self.assertEqual(len(result.cumulative_costs), len(result.path))
            self.assertEqual(result.cumulative_costs[0], 0.0)

    def test_a_star_and_dijkstra_match_shortest_path_length(self) -> None:
        a_star_result = a_star(self.simple_grid, self.start, self.goal)
        dijkstra_result = dijkstra(self.simple_grid, self.start, self.goal)

        self.assertEqual(a_star_result.moves, dijkstra_result.moves)
        self.assertEqual(a_star_result.path_cost, dijkstra_result.path_cost)

    def test_a_star_and_dijkstra_match_shortest_cost_route_with_stoplight_weights(self) -> None:
        stoplights = [Stoplight(row=0, col=1, average_wait_seconds=10)]
        grid_map = GridMap(
            [
                [1, 1, 1],
                [1, 1, 1],
            ],
            stoplights=stoplights,
        )

        expected_path = [
            Point(0, 0),
            Point(1, 0),
            Point(1, 1),
            Point(1, 2),
            Point(0, 2),
        ]

        a_star_result = a_star(grid_map, Point(0, 0), Point(0, 2))
        dijkstra_result = dijkstra(grid_map, Point(0, 0), Point(0, 2))

        self.assertEqual(a_star_result.path, expected_path)
        self.assertEqual(dijkstra_result.path, expected_path)
        self.assertEqual(a_star_result.path_cost, dijkstra_result.path_cost)

    def test_bfs_can_have_higher_weighted_cost_than_dijkstra_and_astar(self) -> None:
        grid_map = GridMap(
            [
                [1, 1, 1],
                [1, 1, 1],
            ],
            stoplights=[Stoplight(row=0, col=1, average_wait_seconds=10)],
        )

        bfs_result = bfs(grid_map, Point(0, 0), Point(0, 2))
        dijkstra_result = dijkstra(grid_map, Point(0, 0), Point(0, 2))
        a_star_result = a_star(grid_map, Point(0, 0), Point(0, 2))

        self.assertGreater(bfs_result.path_cost, dijkstra_result.path_cost)
        self.assertEqual(dijkstra_result.path_cost, a_star_result.path_cost)

    def test_weighted_astar_and_dijkstra_still_find_same_low_cost_route_on_simple_case(self) -> None:
        traffic = GridMap._neutral_traffic(2, 3)
        traffic["east"][0][0] = 6.0
        grid_map = GridMap(
            [
                [1, 1, 1],
                [1, 1, 1],
            ],
            traffic=traffic,
        )

        weighted_result = weighted_astar(grid_map, Point(0, 0), Point(0, 2))
        dijkstra_result = dijkstra(grid_map, Point(0, 0), Point(0, 2))

        self.assertEqual(weighted_result.path_cost, dijkstra_result.path_cost)
        self.assertEqual(weighted_result.path[-1], Point(0, 2))

    def test_directional_traffic_changes_path_cost_without_breaking_path(self) -> None:
        traffic = GridMap._neutral_traffic(3, 3)
        traffic["east"][0][0] = 3.5
        grid_map = GridMap(
            [
                [1, 1, 1],
                [0, 0, 1],
                [1, 1, 1],
            ],
            traffic=traffic,
        )

        result = dijkstra(grid_map, self.start, self.goal)

        self.assertTrue(result.path_found)
        self.assertEqual(result.path[0], self.start)
        self.assertEqual(result.path[-1], self.goal)
        self.assertGreater(result.path_cost, result.moves)
        self.assertGreater(result.metadata["traffic_cost_total"], 0)

    def test_evaluate_path_cost_returns_cost_breakdown(self) -> None:
        grid_map = GridMap(
            [[1, 1, 1]],
            stoplights=[Stoplight(row=0, col=1, average_wait_seconds=4)],
        )
        path = [Point(0, 0), Point(0, 1), Point(0, 2)]

        evaluation = evaluate_path_cost(grid_map, path)

        self.assertEqual(evaluation["total_cost"], 6.0)
        self.assertEqual(evaluation["cumulative_costs"], [0.0, 5.0, 6.0])
        self.assertEqual(evaluation["base_movement_cost_total"], 2.0)
        self.assertEqual(evaluation["traffic_cost_total"], 0.0)
        self.assertEqual(evaluation["stoplight_delay_total"], 4.0)
        self.assertEqual(evaluation["stoplights_crossed"], 1)

    def test_invalid_stoplight_coordinates_raise_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Stoplight at"):
            GridMap(
                [[1, 1], [1, 1]],
                stoplights=[Stoplight(row=5, col=0, average_wait_seconds=5)],
            )

    def test_result_metadata_includes_graph_complexity(self) -> None:
        result = a_star(self.simple_grid, self.start, self.goal)

        self.assertEqual(result.metadata["time_complexity"], "O((V + E) log V)")
        self.assertEqual(result.metadata["space_complexity"], "O(V)")
        self.assertGreaterEqual(result.metadata["node_count"], 1)
        self.assertGreaterEqual(result.metadata["edge_count"], 1)

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

        result = weighted_astar(grid_map, Point(0, 0), Point(2, 2))

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
            ["bfs", "astar", "dijkstra", "greedy_best_first", "weighted_astar"],
            self.simple_grid,
            self.start,
            self.goal,
        )

        self.assertEqual(
            [result.algorithm_name for result in results],
            ["bfs", "astar", "dijkstra", "greedy_best_first", "weighted_astar"],
        )

    def test_run_all_algorithms_runs_every_registered_algorithm(self) -> None:
        results = run_all_algorithms(self.simple_grid, self.start, self.goal)

        self.assertEqual(len(results), len(list_algorithms()))
        self.assertEqual(
            [result.algorithm_name for result in results],
            list_algorithms(),
        )
        self.assertEqual(
            list_algorithms(),
            ["bfs", "dijkstra", "astar", "greedy_best_first", "weighted_astar"],
        )

    def test_invalid_algorithm_name_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported algorithm 'unknown'"):
            run_algorithm("unknown", self.simple_grid, self.start, self.goal)

    def test_result_objects_include_runtime_ms_stats_and_cumulative_costs(self) -> None:
        result = run_algorithm("weighted_astar", self.simple_grid, self.start, self.goal)
        result_dict = result.to_dict()

        self.assertIn("runtime_ms", result_dict)
        self.assertIn("visited_count", result_dict)
        self.assertIn("expanded_count", result_dict)
        self.assertIn("frontier_pushes", result_dict)
        self.assertIn("cumulative_costs", result_dict)

    def test_run_pathfinding_request_returns_serializable_payload_with_comparison_metrics(self) -> None:
        payload = run_pathfinding_request(
            self.simple_grid,
            self.start,
            self.goal,
            ["bfs", "astar", "dijkstra"],
        )

        self.assertEqual(payload["start"], {"row": 0, "col": 0})
        self.assertEqual(payload["goal"], {"row": 2, "col": 2})
        self.assertEqual(payload["selected_algorithms"], ["bfs", "astar", "dijkstra"])
        self.assertEqual(len(payload["results"]), 3)
        self.assertIn("best_path_cost", payload)
        self.assertIn("fastest_runtime_ms", payload)
        self.assertIn("comparison_label", payload["results"][0])

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
            experiment_id="experiment-123",
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

        self.assertEqual(run_row["experiment_id"], "experiment-123")
        self.assertEqual(run_row["map_id"], "map-123")
        self.assertEqual(run_row["algorithm"], "astar")
        self.assertEqual(run_row["start_node_id"], "node-start")
        self.assertEqual(run_row["end_node_id"], "node-goal")
        self.assertEqual(path_rows[0]["node_id"], "node-start")
        self.assertEqual(path_rows[-1]["node_id"], "node-goal")
        self.assertTrue(path_rows[-1]["reached"])

    def test_serialization_helpers_use_weighted_cumulative_costs(self) -> None:
        result = a_star(
            GridMap(
                [[1, 1, 1]],
                stoplights=[Stoplight(row=0, col=1, average_wait_seconds=4)],
            ),
            Point(0, 0),
            Point(0, 2),
        )

        rows = build_run_path_node_rows(
            result,
            run_id="run-456",
            point_to_node_id={
                (0, 0): "node-start",
                (0, 1): "node-middle",
                (0, 2): "node-goal",
            },
        )

        self.assertEqual(
            [row["cumulative_cost"] for row in rows],
            [0.0, 5.0, 6.0],
        )

    def test_random_stoplight_generation_only_uses_four_way_intersections(self) -> None:
        random.seed(7)
        grid_map = GridMap(
            [
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1],
                [1, 1, 1, 1],
            ]
        )
        start = Point(0, 0)
        goal = Point(3, 3)

        stoplights = generate_random_stoplights(
            grid_map,
            start=start,
            goal=goal,
            density=1.0,
        )

        self.assertGreater(len(stoplights), 0)
        for stoplight in stoplights:
            point = Point(stoplight.row, stoplight.col)
            self.assertTrue(grid_map.is_four_way_intersection(point))
            self.assertNotEqual(point, start)
            self.assertNotEqual(point, goal)


if __name__ == "__main__":
    unittest.main()
