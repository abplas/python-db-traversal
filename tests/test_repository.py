import sys
import unittest
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from traversal.grid import Point, Stoplight
from traversal.repository import (
    EDGE_SELECT_COLUMNS,
    EDGE_SELECT_COLUMNS_WITHOUT_METADATA,
    build_point_to_node_id,
    fetch_all_edges_for_map,
    get_run_path,
    list_maps,
    load_map_graph,
    save_algorithm_run_with_path,
    save_generated_map,
)


class FakeRpcCall:
    def __init__(self, client: "FakeClient", name: str, params: dict[str, object]) -> None:
        self.client = client
        self.name = name
        self.params = params

    def execute(self) -> SimpleNamespace:
        self.client.rpc_name = self.name
        self.client.rpc_params = self.params
        return SimpleNamespace(data="run-789")


class FakeQuery:
    def __init__(self, client: "FakeClient", table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.filters: list[tuple[str, object]] = []

    def select(self, _fields: str) -> "FakeQuery":
        return self

    def order(self, _field: str, desc: bool = False) -> "FakeQuery":
        self.client.orders.append((self.table_name, _field, desc))
        return self

    def eq(self, field: str, value: object) -> "FakeQuery":
        self.filters.append((field, value))
        return self

    def execute(self) -> SimpleNamespace:
        if self.table_name == "maps":
            return SimpleNamespace(
                data=[
                    {
                        "id": "map-2",
                        "name": "Newer map",
                        "slug": "newer-map",
                        "description": "Second",
                        "created_at": "2026-05-11T12:00:00Z",
                    }
                ]
            )
        if self.table_name == "run_path_nodes":
            return SimpleNamespace(
                data=[
                    {
                        "step_index": 0,
                        "node_id": "node-1",
                        "cumulative_cost": 0.0,
                        "reached": False,
                        "nodes": {"row": 0, "col": 0, "label": "0,0"},
                    },
                    {
                        "step_index": 1,
                        "node_id": "node-2",
                        "cumulative_cost": 2.5,
                        "reached": True,
                        "nodes": {"row": 0, "col": 1, "label": "0,1"},
                    },
                ]
            )
        return SimpleNamespace(data=[])


class FakeInsertQuery:
    def __init__(self, client: "FakeInsertClient", table_name: str, payload: object) -> None:
        self.client = client
        self.table_name = table_name
        self.payload = payload

    def execute(self) -> SimpleNamespace:
        self.client.inserts.append((self.table_name, self.payload))
        return SimpleNamespace(data=[])


class FakeInsertTable:
    def __init__(self, client: "FakeInsertClient", table_name: str) -> None:
        self.client = client
        self.table_name = table_name

    def insert(self, payload: object) -> FakeInsertQuery:
        return FakeInsertQuery(self.client, self.table_name, payload)


class FakeClient:
    def __init__(self) -> None:
        self.rpc_name: str | None = None
        self.rpc_params: dict[str, object] | None = None
        self.orders: list[tuple[str, str, bool]] = []

    def rpc(self, name: str, params: dict[str, object]) -> FakeRpcCall:
        return FakeRpcCall(self, name, params)

    def table(self, table_name: str) -> FakeQuery:
        return FakeQuery(self, table_name)


class FakeInsertClient:
    def __init__(self) -> None:
        self.inserts: list[tuple[str, object]] = []

    def table(self, table_name: str) -> FakeInsertTable:
        return FakeInsertTable(self, table_name)


class FakePagedEdgeQuery:
    def __init__(self, client: "FakePagedEdgeClient", table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.fields: str | None = None
        self.filters: list[tuple[str, object]] = []
        self.page_range: tuple[int, int] = (0, 999)

    def select(self, fields: str) -> "FakePagedEdgeQuery":
        self.fields = fields
        self.client.selects.append(fields)
        return self

    def eq(self, field: str, value: object) -> "FakePagedEdgeQuery":
        self.filters.append((field, value))
        return self

    def range(self, start: int, end: int) -> "FakePagedEdgeQuery":
        self.page_range = (start, end)
        self.client.ranges.append((start, end))
        return self

    def execute(self) -> SimpleNamespace:
        self.client.requests.append(
            {
                "table": self.table_name,
                "fields": self.fields,
                "filters": list(self.filters),
                "range": self.page_range,
            }
        )
        if self.table_name != "edges":
            return SimpleNamespace(data=[])

        if self.client.fail_metadata and self.fields == EDGE_SELECT_COLUMNS:
            raise RuntimeError("JSON could not be generated")

        start, end = self.page_range
        rows = self.client.edge_rows[start : end + 1]
        if self.fields == EDGE_SELECT_COLUMNS_WITHOUT_METADATA:
            rows = [{key: value for key, value in row.items() if key != "metadata"} for row in rows]
        return SimpleNamespace(data=rows)


class FakePagedEdgeClient:
    def __init__(self, edge_rows: list[dict[str, object]], *, fail_metadata: bool = False) -> None:
        self.edge_rows = edge_rows
        self.fail_metadata = fail_metadata
        self.selects: list[str] = []
        self.ranges: list[tuple[int, int]] = []
        self.requests: list[dict[str, object]] = []

    def table(self, table_name: str) -> FakePagedEdgeQuery:
        return FakePagedEdgeQuery(self, table_name)


class RepositoryTests(unittest.TestCase):
    def test_list_maps_repository_behavior_with_mocked_supabase(self) -> None:
        fake_client = FakeClient()
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            rows = list_maps()

        self.assertEqual(rows[0]["id"], "map-2")
        self.assertIn(("maps", "created_at", True), fake_client.orders)

    def test_build_point_to_node_id_skips_nodes_with_null_row_or_col(self) -> None:
        with patch(
            "traversal.repository.load_nodes_for_map",
            return_value=[
                {"id": "node-1", "row": 0, "col": 0, "label": "A"},
                {"id": "node-2", "row": None, "col": 1, "label": "skip-row"},
                {"id": "node-3", "row": 1, "col": None, "label": "skip-col"},
            ],
        ):
            mapping = build_point_to_node_id("map-123")

        self.assertEqual(mapping, {Point(0, 0): "node-1"})

    def test_save_generated_map_creates_expected_nodes_edges_and_stoplights(self) -> None:
        fake_client = FakeInsertClient()
        point_map = {
            Point(0, 0): "node-00",
            Point(0, 1): "node-01",
            Point(1, 0): "node-10",
            Point(1, 1): "node-11",
        }
        traffic = {
            "north": [[1.0, 1.0], [1.0, 1.0]],
            "south": [[1.0, 1.0], [1.0, 1.0]],
            "east": [[1.5, 2.0], [1.0, 1.0]],
            "west": [[1.0, 1.0], [1.0, 1.0]],
        }
        with patch("traversal.repository.get_supabase_client", return_value=fake_client), patch(
            "traversal.repository.create_map",
            return_value={"id": "map-123", "name": "Saved map", "slug": "saved-map"},
        ), patch(
            "traversal.repository.build_point_to_node_id",
            return_value=point_map,
        ):
            summary = save_generated_map(
                name="Saved map",
                slug="saved-map",
                description="Demo",
                grid=[[1, 1], [1, 1]],
                traffic=traffic,
                stoplights=[Stoplight(row=0, col=1, average_wait_seconds=7)],
                metadata={"source": "test"},
            )

        self.assertEqual(summary["map_id"], "map-123")
        self.assertEqual(summary["node_count"], 4)
        self.assertEqual(summary["stoplight_count"], 1)
        inserted_tables = [table_name for table_name, _payload in fake_client.inserts]
        self.assertEqual(inserted_tables, ["nodes", "edges", "traffic_signals"])
        node_payload = fake_client.inserts[0][1]
        edge_payload = fake_client.inserts[1][1]
        signal_payload = fake_client.inserts[2][1]
        self.assertEqual(len(node_payload), 4)
        self.assertEqual(len(edge_payload), 8)
        self.assertEqual(signal_payload[0]["node_id"], "node-01")
        self.assertEqual(edge_payload[0]["is_one_way"], True)
        self.assertEqual(edge_payload[0]["map_id"], "map-123")
        self.assertEqual(edge_payload[0]["distance_meters"], 1.0)
        self.assertEqual(edge_payload[0]["from_node_id"], "node-00")
        self.assertEqual(edge_payload[0]["to_node_id"], "node-10")
        self.assertIsNotNone(edge_payload[0]["travel_time_seconds"])
        self.assertIsNotNone(edge_payload[0]["weight"])

    def test_save_generated_map_sanitizes_non_finite_numbers(self) -> None:
        fake_client = FakeInsertClient()
        point_map = {
            Point(0, 0): "node-00",
            Point(0, 1): "node-01",
            Point(1, 0): "node-10",
            Point(1, 1): "node-11",
        }
        traffic = {
            "north": [[1.0, 1.0], [1.0, 1.0]],
            "south": [[float("inf"), 1.0], [1.0, 1.0]],
            "east": [[float("nan"), float("-inf")], [1.0, 1.0]],
            "west": [[1.0, 1.0], [1.0, 1.0]],
        }
        with patch("traversal.repository.get_supabase_client", return_value=fake_client), patch(
            "traversal.repository.create_map",
            return_value={"id": "map-123", "name": "Saved map", "slug": "saved-map"},
        ), patch(
            "traversal.repository.build_point_to_node_id",
            return_value=point_map,
        ):
            save_generated_map(
                name="Saved map",
                slug="saved-map",
                description="Demo",
                grid=[[1, 1], [1, 1]],
                traffic=traffic,
                stoplights=[
                    Stoplight(
                        row=0,
                        col=1,
                        average_wait_seconds=float("inf"),
                        light_cycle_seconds=float("nan"),
                    )
                ],
                metadata={"source": "test"},
            )

        node_payload = fake_client.inserts[0][1]
        edge_payload = fake_client.inserts[1][1]
        signal_payload = fake_client.inserts[2][1]

        self.assertTrue(all(math.isfinite(row["lat"]) for row in node_payload))
        self.assertTrue(all(math.isfinite(row["lng"]) for row in node_payload))
        self.assertTrue(all(row["map_id"] == "map-123" for row in edge_payload))
        self.assertTrue(all(row["distance_meters"] > 0 for row in edge_payload))
        self.assertTrue(all(math.isfinite(row["distance_meters"]) for row in edge_payload))
        self.assertTrue(all(math.isfinite(row["weight"]) for row in edge_payload))
        self.assertTrue(all(math.isfinite(row["travel_time_seconds"]) for row in edge_payload))
        self.assertEqual(signal_payload[0]["average_wait_seconds"], 0.0)
        self.assertIsNone(signal_payload[0]["light_cycle_seconds"])

    def test_load_map_graph_returns_expected_shape(self) -> None:
        with patch(
            "traversal.repository._load_map_row",
            return_value={"id": "map-123", "name": "Saved", "slug": "saved"},
        ), patch(
            "traversal.repository.load_nodes_for_map",
            return_value=[
                {"id": "node-00", "row": 0, "col": 0, "label": "0,0"},
                {"id": "node-01", "row": 0, "col": 1, "label": "0,1"},
            ],
        ), patch(
            "traversal.repository.fetch_all_edges_for_map",
            return_value=[
                {
                    "id": "edge-1",
                    "map_id": "map-123",
                    "from_node_id": "node-00",
                    "to_node_id": "node-01",
                    "distance_meters": 1.0,
                    "weight": 2.5,
                    "travel_time_seconds": 2.5,
                    "is_one_way": True,
                    "road_name": None,
                    "metadata": {},
                }
            ],
        ), patch(
            "traversal.repository._load_traffic_signals_for_map",
            return_value=[
                {
                    "id": "signal-1",
                    "map_id": "map-123",
                    "node_id": "node-01",
                    "average_wait_seconds": 9,
                    "light_cycle_seconds": 60,
                    "signal_type": "stoplight",
                    "metadata": {},
                }
            ],
        ):
            graph = load_map_graph("map-123")

        self.assertEqual(graph["map"]["id"], "map-123")
        self.assertEqual(graph["grid"], [[1, 1]])
        self.assertEqual(graph["traffic"]["east"][0][0], 2.5)
        self.assertEqual(graph["traffic_signals"][0]["row"], 0)
        self.assertEqual(graph["point_node_pairs"][0]["node_id"], "node-00")

    def test_load_map_graph_returns_json_safe_data(self) -> None:
        map_id = uuid4()
        node_00 = uuid4()
        node_01 = uuid4()
        signal_id = uuid4()
        edge_id = uuid4()

        with patch(
            "traversal.repository._load_map_row",
            return_value={"id": map_id, "name": "Saved", "slug": "saved"},
        ), patch(
            "traversal.repository.load_nodes_for_map",
            return_value=[
                {"id": node_00, "row": 0, "col": 0, "label": "0,0"},
                {"id": node_01, "row": 0, "col": 1, "label": "0,1"},
            ],
        ), patch(
            "traversal.repository.fetch_all_edges_for_map",
            return_value=[
                {
                    "id": edge_id,
                    "map_id": map_id,
                    "from_node_id": node_00,
                    "to_node_id": node_01,
                    "distance_meters": 1.0,
                    "weight": 1.5,
                    "travel_time_seconds": 1.5,
                    "is_one_way": True,
                    "road_name": None,
                    "metadata": {},
                }
            ],
        ), patch(
            "traversal.repository._load_traffic_signals_for_map",
            return_value=[
                {
                    "id": signal_id,
                    "map_id": map_id,
                    "node_id": node_01,
                    "average_wait_seconds": 9,
                    "light_cycle_seconds": 60,
                    "signal_type": "stoplight",
                    "metadata": {},
                }
            ],
        ):
            graph = load_map_graph(str(map_id))

        json.dumps(graph)
        self.assertIsInstance(graph["map"]["id"], str)
        self.assertIsInstance(graph["edges"][0]["id"], str)
        self.assertIsInstance(graph["traffic_signals"][0]["id"], str)
        self.assertEqual(
            graph["point_node_pairs"],
            [
                {"row": 0, "col": 0, "node_id": str(node_00)},
                {"row": 0, "col": 1, "node_id": str(node_01)},
            ],
        )
        self.assertTrue(
            all(isinstance(key, str) for key in graph["traffic"].keys())
        )
        self.assertTrue(
            all(
                value is None or math.isfinite(value)
                for rows in graph["traffic"].values()
                for row in rows
                for value in row
            )
        )

    def test_load_map_graph_sanitizes_non_finite_edge_and_signal_values(self) -> None:
        with patch(
            "traversal.repository._load_map_row",
            return_value={"id": "map-123", "name": "Saved", "slug": "saved"},
        ), patch(
            "traversal.repository.load_nodes_for_map",
            return_value=[
                {"id": "node-00", "row": 0, "col": 0, "label": "0,0"},
                {"id": "node-01", "row": 0, "col": 1, "label": "0,1"},
            ],
        ), patch(
            "traversal.repository.fetch_all_edges_for_map",
            return_value=[
                {
                    "id": "edge-1",
                    "map_id": "map-123",
                    "from_node_id": "node-00",
                    "to_node_id": "node-01",
                    "distance_meters": 1.0,
                    "weight": float("nan"),
                    "travel_time_seconds": float("inf"),
                    "is_one_way": True,
                    "road_name": None,
                    "metadata": {},
                }
            ],
        ), patch(
            "traversal.repository._load_traffic_signals_for_map",
            return_value=[
                {
                    "id": "signal-1",
                    "map_id": "map-123",
                    "node_id": "node-01",
                    "average_wait_seconds": float("inf"),
                    "light_cycle_seconds": float("nan"),
                    "signal_type": "stoplight",
                    "metadata": {},
                }
            ],
        ):
            graph = load_map_graph("map-123")

        self.assertEqual(graph["traffic"]["east"][0][0], 1.0)
        self.assertIsNone(graph["edges"][0]["weight"])
        self.assertIsNone(graph["edges"][0]["travel_time_seconds"])
        self.assertEqual(graph["traffic_signals"][0]["average_wait_seconds"], 0.0)
        self.assertIsNone(graph["traffic_signals"][0]["light_cycle_seconds"])
        json.dumps(graph)

    def test_fetch_all_edges_for_map_uses_explicit_columns_and_paginates(self) -> None:
        fake_client = FakePagedEdgeClient(
            [
                {
                    "id": "edge-1",
                    "map_id": "map-123",
                    "from_node_id": "node-1",
                    "to_node_id": "node-2",
                    "distance_meters": 1.0,
                    "travel_time_seconds": 1.0,
                    "weight": 1.0,
                    "is_one_way": True,
                    "road_name": "Main",
                    "metadata": {},
                },
                {
                    "id": "edge-2",
                    "map_id": "map-123",
                    "from_node_id": "node-2",
                    "to_node_id": "node-3",
                    "distance_meters": 1.0,
                    "travel_time_seconds": 1.0,
                    "weight": 1.1,
                    "is_one_way": True,
                    "road_name": "Main",
                    "metadata": {},
                },
                {
                    "id": "edge-3",
                    "map_id": "map-123",
                    "from_node_id": "node-3",
                    "to_node_id": "node-4",
                    "distance_meters": 1.0,
                    "travel_time_seconds": 1.0,
                    "weight": 1.2,
                    "is_one_way": True,
                    "road_name": "Second",
                    "metadata": {},
                },
            ]
        )
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            edges = fetch_all_edges_for_map("map-123", page_size=2)

        self.assertEqual(len(edges), 3)
        self.assertEqual(fake_client.selects, [EDGE_SELECT_COLUMNS, EDGE_SELECT_COLUMNS])
        self.assertEqual(fake_client.ranges, [(0, 1), (2, 3)])
        self.assertEqual(
            fake_client.requests[0]["filters"],
            [("map_id", "map-123")],
        )

    def test_fetch_all_edges_for_map_handles_more_than_one_thousand_edges(self) -> None:
        edge_rows = [
            {
                "id": f"edge-{index}",
                "map_id": "map-123",
                "from_node_id": f"node-{index}",
                "to_node_id": f"node-{index + 1}",
                "distance_meters": 1.0,
                "travel_time_seconds": 1.0,
                "weight": 1.0,
                "is_one_way": True,
                "road_name": None,
                "metadata": {},
            }
            for index in range(1001)
        ]
        fake_client = FakePagedEdgeClient(edge_rows)
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            edges = fetch_all_edges_for_map("map-123")

        self.assertEqual(len(edges), 1001)
        self.assertEqual(fake_client.ranges, [(0, 999), (1000, 1999)])

    def test_fetch_all_edges_for_map_retries_without_metadata(self) -> None:
        fake_client = FakePagedEdgeClient(
            [
                {
                    "id": "edge-1",
                    "map_id": "map-123",
                    "from_node_id": "node-1",
                    "to_node_id": "node-2",
                    "distance_meters": 1.0,
                    "travel_time_seconds": 1.0,
                    "weight": 1.0,
                    "is_one_way": True,
                    "road_name": "Main",
                    "metadata": {"source": "db"},
                }
            ],
            fail_metadata=True,
        )
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            edges = fetch_all_edges_for_map("map-123", page_size=1000)

        self.assertEqual(edges[0]["metadata"], {})
        self.assertEqual(
            fake_client.selects,
            [EDGE_SELECT_COLUMNS, EDGE_SELECT_COLUMNS_WITHOUT_METADATA],
        )

    def test_get_run_path_flattens_joined_node_data(self) -> None:
        fake_client = FakeClient()
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            path_rows = get_run_path("run-123")

        self.assertEqual(path_rows[0]["row"], 0)
        self.assertEqual(path_rows[-1]["cumulative_cost"], 2.5)
        self.assertEqual(path_rows[-1]["label"], "0,1")

    def test_save_algorithm_run_with_path_uses_expected_rpc_parameter_names(self) -> None:
        fake_client = FakeClient()
        with patch("traversal.repository.get_supabase_client", return_value=fake_client):
            run_id = save_algorithm_run_with_path(
                experiment_id="exp-123",
                map_id="map-123",
                algorithm="astar",
                start_node_id="node-start",
                end_node_id="node-goal",
                status="completed",
                total_cost=9.5,
                total_distance_meters=None,
                total_duration_seconds=None,
                visited_count=12,
                runtime_ms=3,
                metadata={"path_found": True},
                path_nodes=[
                    {
                        "node_id": "node-start",
                        "step_index": 0,
                        "cumulative_cost": 0.0,
                        "reached": False,
                    }
                ],
            )

        self.assertEqual(run_id, "run-789")
        self.assertEqual(fake_client.rpc_name, "save_algorithm_run_with_path")
        self.assertEqual(
            set(fake_client.rpc_params or {}),
            {
                "p_experiment_id",
                "p_map_id",
                "p_algorithm",
                "p_start_node_id",
                "p_end_node_id",
                "p_status",
                "p_total_cost",
                "p_total_distance_meters",
                "p_total_duration_seconds",
                "p_visited_count",
                "p_runtime_ms",
                "p_metadata",
                "p_path_nodes",
            },
        )


if __name__ == "__main__":
    unittest.main()
