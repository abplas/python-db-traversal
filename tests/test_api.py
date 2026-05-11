import sys
import unittest
from pathlib import Path

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
    health,
    run_pathfinding,
)
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

    def _build_request(self, algorithms_value: str | list[str]) -> PathfindingRequest:
        return PathfindingRequest(**{**self.request_body, "algorithms": algorithms_value})

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

    def test_run_pathfinding_with_all_algorithms(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": "all"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(self._build_request("all"))

        self.assertEqual(payload["selected_algorithms"], list_algorithms())
        self.assertEqual(len(payload["results"]), len(list_algorithms()))

    def test_run_pathfinding_with_selected_algorithms(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={
                    **self.request_body,
                    "algorithms": [
                        "bfs",
                        "astar",
                        "dijkstra",
                        "greedy_best_first",
                        "weighted_astar",
                    ],
                },
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(
                self._build_request(
                    ["bfs", "astar", "dijkstra", "greedy_best_first", "weighted_astar"]
                )
            )

        self.assertEqual(
            payload["selected_algorithms"],
            ["bfs", "astar", "dijkstra", "greedy_best_first", "weighted_astar"],
        )
        self.assertEqual(len(payload["results"]), 5)
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

    def test_run_pathfinding_with_invalid_algorithm_name(self) -> None:
        if self.client is not None:
            response = self.client.post(
                "/run-pathfinding",
                json={**self.request_body, "algorithms": ["unknown"]},
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("Unsupported algorithm", response.json()["detail"])
            return

        with self.assertRaises(HTTPException) as context:
            run_pathfinding(self._build_request(["unknown"]))
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
