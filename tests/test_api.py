import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import HTTPException

try:
    from fastapi.testclient import TestClient
except (ImportError, RuntimeError):
    TestClient = None

from traversal.api import PathfindingRequest, algorithms, app, health, run_pathfinding
from traversal.runner import list_algorithms


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
                json={**self.request_body, "algorithms": ["astar", "dijkstra"]},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
        else:
            payload = run_pathfinding(self._build_request(["astar", "dijkstra"]))

        self.assertEqual(payload["selected_algorithms"], ["astar", "dijkstra"])
        self.assertEqual(len(payload["results"]), 2)
        self.assertEqual(payload["results"][0]["algorithm_name"], "astar")
        self.assertEqual(payload["results"][1]["algorithm_name"], "dijkstra")

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
