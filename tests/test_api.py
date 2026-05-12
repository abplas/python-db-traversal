import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import HTTPException

try:
    from fastapi.testclient import TestClient
except (ImportError, RuntimeError):
    TestClient = None

from traversal.api import (
    PathfindingRequest,
    algorithm_metadata,
    algorithms,
    app,
    db_health,
    experiment_results,
    experiment_comparison,
    health,
    load_map,
    map_experiments,
    maps,
    map_nodes,
    map_performance,
    run_path,
    run_pathfinding,
    save_map,
)
from traversal.grid import Point
from traversal.runner import list_algorithm_metadata, list_algorithms


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app) if TestClient is not None else None
        self.request_body = {
            "grid": [
                [1, 1, 1, 1],
                [1, 0, 0, 1],
                [1, 1, 1, 1],
            ],
            "start": {"row": 0, "col": 0},
            "goal": {"row": 2, "col": 3},
        }

    def _build_request(self, **overrides: object) -> PathfindingRequest:
        return PathfindingRequest(**{**self.request_body, **overrides})

    def test_health_endpoint(self) -> None:
        if self.client is not None:
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})
            return

        self.assertEqual(health(), {"status": "ok"})

    def test_algorithms_endpoint(self) -> None:
        if self.client is not None:
            response = self.client.get("/algorithms")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"algorithms": list_algorithms()})
            return

        self.assertEqual(algorithms(), {"algorithms": list_algorithms()})

    def test_algorithm_metadata_endpoint(self) -> None:
        if self.client is not None:
            response = self.client.get("/algorithm-metadata")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = algorithm_metadata()

        self.assertEqual(payload, {"algorithms": list_algorithm_metadata()})

    def test_db_health_endpoint_handles_success(self) -> None:
        mocked_payload = {"status": "ok", "sample_maps": [{"id": "map-1"}]}
        with patch("traversal.api.check_database_connection", return_value=mocked_payload):
            if self.client is not None:
                response = self.client.get("/db-health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), mocked_payload)
                return

            self.assertEqual(db_health(), mocked_payload)

    def test_db_health_endpoint_handles_failure(self) -> None:
        with patch(
            "traversal.api.check_database_connection",
            side_effect=RuntimeError("Missing SUPABASE_URL"),
        ):
            if self.client is not None:
                response = self.client.get("/db-health")
                self.assertEqual(response.status_code, 500)
                self.assertIn("Missing SUPABASE_URL", response.json()["detail"])
                return

            with self.assertRaises(HTTPException) as context:
                db_health()
            self.assertEqual(context.exception.status_code, 500)
            self.assertIn("Missing SUPABASE_URL", context.exception.detail)

    def test_map_nodes_endpoint_returns_mocked_rows(self) -> None:
        mocked_nodes = [{"id": "node-1", "row": 0, "col": 0, "label": "A"}]
        with patch("traversal.api.load_nodes_for_map", return_value=mocked_nodes):
            if self.client is not None:
                response = self.client.get("/maps/map-123/nodes")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"nodes": mocked_nodes})
                return

            self.assertEqual(map_nodes("map-123"), {"nodes": mocked_nodes})

    def test_maps_endpoint_returns_mocked_rows(self) -> None:
        mocked_maps = [{"id": "map-1", "name": "Saved map", "slug": "saved-map"}]
        with patch("traversal.api.list_maps", return_value=mocked_maps):
            if self.client is not None:
                response = self.client.get("/maps")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"maps": mocked_maps})
                return

            self.assertEqual(maps(), {"maps": mocked_maps})

    def test_post_maps_returns_created_map_summary(self) -> None:
        mocked_summary = {
            "map": {"id": "map-1", "name": "Saved map", "slug": "saved-map"},
            "map_id": "map-1",
            "node_count": 3,
            "edge_count": 4,
            "stoplight_count": 1,
            "point_node_pairs": [{"row": 0, "col": 0, "node_id": "node-1"}],
        }
        request_body = {
            "name": "Saved map",
            "slug": "saved-map",
            "description": "Demo",
            "grid": [[1, 1], [1, 0]],
            "stoplights": [{"row": 0, "col": 1, "average_wait_seconds": 5}],
        }
        with patch("traversal.api.save_generated_map", return_value=mocked_summary):
            if self.client is not None:
                response = self.client.post("/maps", json=request_body)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), mocked_summary)
                return

            from traversal.api import MapSaveRequest

            self.assertEqual(save_map(MapSaveRequest(**request_body)), mocked_summary)

    def test_load_map_endpoint_returns_mocked_graph(self) -> None:
        mocked_graph = {
            "map": {"id": "map-1", "name": "Saved map"},
            "grid": [[1, 1]],
            "nodes": [],
            "edges": [],
            "traffic_signals": [],
            "traffic": None,
            "point_node_pairs": [],
        }
        with patch("traversal.api.load_map_graph", return_value=mocked_graph):
            if self.client is not None:
                response = self.client.get("/maps/map-1")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), mocked_graph)
                return

            self.assertEqual(load_map("map-1"), mocked_graph)

    def test_load_map_endpoint_returns_json_safe_response(self) -> None:
        mocked_graph = {
            "map": {"id": "map-1", "name": "Saved map", "slug": "saved-map"},
            "grid": [[1, 1]],
            "nodes": [{"id": "node-1", "row": 0, "col": 0, "lat": 0.0, "lng": 0.0}],
            "edges": [
                {
                    "id": "edge-1",
                    "from_node_id": "node-1",
                    "to_node_id": "node-2",
                    "weight": 1.0,
                    "travel_time_seconds": 1.0,
                    "distance_meters": 1.0,
                }
            ],
            "traffic_signals": [
                {
                    "id": "signal-1",
                    "row": 0,
                    "col": 1,
                    "average_wait_seconds": 5.0,
                    "light_cycle_seconds": 60.0,
                }
            ],
            "traffic": {
                "north": [[1.0, 1.0]],
                "south": [[1.0, 1.0]],
                "east": [[1.0, 1.0]],
                "west": [[1.0, 1.0]],
            },
            "point_node_pairs": [{"row": 0, "col": 0, "node_id": "node-1"}],
        }
        with patch("traversal.api.load_map_graph", return_value=mocked_graph):
            if self.client is not None:
                response = self.client.get("/maps/map-1")
                self.assertEqual(response.status_code, 200)
                json.dumps(response.json())
                self.assertEqual(response.json()["point_node_pairs"][0]["node_id"], "node-1")
                return

            payload = load_map("map-1")
            json.dumps(payload)
            self.assertEqual(payload["point_node_pairs"][0]["node_id"], "node-1")

    def test_map_experiments_endpoint_returns_mocked_rows(self) -> None:
        mocked_rows = [{"id": "exp-1", "traffic_enabled": True}]
        with patch("traversal.api.list_experiments_for_map", return_value=mocked_rows):
            if self.client is not None:
                response = self.client.get("/maps/map-1/experiments")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"experiments": mocked_rows})
                return

            self.assertEqual(map_experiments("map-1"), {"experiments": mocked_rows})

    def test_experiment_comparison_endpoint_returns_mocked_rows(self) -> None:
        mocked_rows = [{"experiment_id": "exp-1", "algorithm": "astar", "cost_rank": 1}]
        with patch(
            "traversal.api.get_algorithm_comparison_summary", return_value=mocked_rows
        ):
            if self.client is not None:
                response = self.client.get("/experiments/exp-1/comparison")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"comparison": mocked_rows})
                return

            self.assertEqual(
                experiment_comparison("exp-1"),
                {"comparison": mocked_rows},
            )

    def test_experiment_results_endpoint_returns_mocked_rows(self) -> None:
        mocked_rows = [{"experiment_id": "exp-1", "algorithm": "astar", "cost_rank": 1}]
        with patch("traversal.api.get_experiment_results", return_value=mocked_rows):
            if self.client is not None:
                response = self.client.get("/experiments/exp-1/results")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"results": mocked_rows})
                return

            self.assertEqual(experiment_results("exp-1"), {"results": mocked_rows})

    def test_run_path_endpoint_returns_mocked_rows(self) -> None:
        mocked_rows = [{"step_index": 0, "row": 0, "col": 0, "cumulative_cost": 0.0}]
        with patch("traversal.api.get_run_path", return_value=mocked_rows):
            if self.client is not None:
                response = self.client.get("/runs/run-1/path")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"path": mocked_rows})
                return

            self.assertEqual(run_path("run-1"), {"path": mocked_rows})

    def test_map_performance_endpoint_returns_mocked_rows(self) -> None:
        mocked_rows = [{"map_id": "map-1", "algorithm": "astar", "avg_runtime_ms": 2.5}]
        with patch(
            "traversal.api.get_algorithm_performance_summary", return_value=mocked_rows
        ):
            if self.client is not None:
                response = self.client.get("/maps/map-1/performance")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"performance": mocked_rows})
                return

            self.assertEqual(map_performance("map-1"), {"performance": mocked_rows})

    def test_run_pathfinding_with_all_algorithms(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": "all"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(self._build_request(algorithms="all"))

        self.assertEqual(payload["selected_algorithms"], list_algorithms())
        self.assertEqual(len(payload["results"]), len(list_algorithms()))

    def test_run_pathfinding_with_selected_algorithms(self) -> None:
        selected = [
            "bfs",
            "dfs",
            "astar",
            "dijkstra",
            "greedy_best_first",
            "weighted_astar",
        ]
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": selected},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(self._build_request(algorithms=selected))

        self.assertEqual(payload["selected_algorithms"], selected)
        self.assertEqual(len(payload["results"]), len(selected))
        self.assertEqual(payload["results"][0]["algorithm_name"], "bfs")
        self.assertEqual(payload["results"][-1]["algorithm_name"], "weighted_astar")
        self.assertIn("best_path_cost", payload)
        self.assertIn("comparison_label", payload["results"][0])

    def test_run_pathfinding_accepts_stoplight_data(self) -> None:
        request_body = {
            "grid": [[1, 1, 1]],
            "start": {"row": 0, "col": 0},
            "goal": {"row": 0, "col": 2},
            "algorithms": ["astar", "dijkstra"],
            "stoplights": [
                {
                    "row": 0,
                    "col": 1,
                    "average_wait_seconds": 7,
                }
            ],
        }

        if self.client is not None:
            response = self.client.post("/run-pathfinding", json=request_body)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(PathfindingRequest(**request_body))

        self.assertTrue(payload["results"][0]["metadata"]["uses_stoplights"])
        self.assertGreater(payload["results"][0]["path_cost"], payload["results"][0]["moves"])

    def test_run_pathfinding_without_save_keeps_existing_behavior(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": ["astar"], "save": False},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(self._build_request(algorithms=["astar"], save=False))

        self.assertNotIn("experiment_id", payload)
        self.assertNotIn("saved_run_ids", payload)
        self.assertEqual(payload["selected_algorithms"], ["astar"])

    def test_run_pathfinding_save_true_requires_ids(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": ["astar"], "save": True},
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("map_id", response.json()["detail"])
            return

        with self.assertRaises(HTTPException) as context:
            run_pathfinding(self._build_request(algorithms=["astar"], save=True))
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("map_id", context.exception.detail)

    def test_run_pathfinding_save_true_returns_saved_ids(self) -> None:
        point_map = {
            Point(0, 0): "node-start",
            Point(0, 1): "node-01",
            Point(0, 2): "node-02",
            Point(0, 3): "node-03",
            Point(1, 0): "node-10",
            Point(1, 3): "node-13",
            Point(2, 0): "node-20",
            Point(2, 1): "node-21",
            Point(2, 2): "node-22",
            Point(2, 3): "node-goal",
        }
        request_body = {
            **self.request_body,
            "algorithms": ["astar"],
            "save": True,
            "map_id": "map-123",
            "start_node_id": "node-start",
            "end_node_id": "node-goal",
        }

        with patch("traversal.api.build_point_to_node_id", return_value=point_map), patch(
            "traversal.api.create_route_experiment", return_value="exp-123"
        ), patch(
            "traversal.api.save_algorithm_run_with_path", return_value="run-456"
        ):
            if self.client is not None:
                response = self.client.post("/run-pathfinding", json=request_body)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
            else:
                payload = run_pathfinding(PathfindingRequest(**request_body))

        self.assertEqual(payload["experiment_id"], "exp-123")
        self.assertEqual(payload["saved_run_ids"], {"astar": "run-456"})

    def test_run_pathfinding_save_true_with_invalid_algorithm_name(self) -> None:
        request_body = {
            **self.request_body,
            "algorithms": ["unknown"],
            "save": True,
            "map_id": "map-123",
            "start_node_id": "node-start",
            "end_node_id": "node-goal",
        }
        if self.client is not None:
            response = self.client.post("/run-pathfinding", json=request_body)
            self.assertEqual(response.status_code, 400)
            self.assertIn("Unsupported algorithm", response.json()["detail"])
            return

        with self.assertRaises(HTTPException) as context:
            run_pathfinding(PathfindingRequest(**request_body))
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Unsupported algorithm", context.exception.detail)

    def test_run_pathfinding_with_invalid_stoplight_coordinates_returns_400(self) -> None:
        request_body = {
            **self.request_body,
            "algorithms": ["astar"],
            "stoplights": [
                {
                    "row": 99,
                    "col": 99,
                    "average_wait_seconds": 5,
                }
            ],
        }

        if self.client is not None:
            response = self.client.post("/run-pathfinding", json=request_body)
            self.assertEqual(response.status_code, 400)
            self.assertIn("Stoplight", response.json()["detail"])
            return

        with self.assertRaises(HTTPException) as context:
            run_pathfinding(PathfindingRequest(**request_body))
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Stoplight", context.exception.detail)

    def test_run_pathfinding_preflight_options_is_allowed(self) -> None:
        if self.client is None:
            self.skipTest("Preflight test requires FastAPI TestClient.")

        response = self.client.options(
            "/run-pathfinding",
            headers={
                "Origin": "http://127.0.0.1:8080",
                "Access-Control-Request-Method": "POST",
            },
        )

        self.assertNotEqual(response.status_code, 405)
        self.assertIn(response.status_code, {200, 204})
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://127.0.0.1:8080",
        )


if __name__ == "__main__":
    unittest.main()
