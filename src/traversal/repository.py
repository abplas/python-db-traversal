from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
import math
from typing import Any
from uuid import UUID

from traversal.grid import GridMap, Point, Stoplight
from traversal.supabase_client import get_supabase_client

EDGE_SELECT_COLUMNS = (
    "id,map_id,from_node_id,to_node_id,distance_meters,"
    "travel_time_seconds,weight,is_one_way,road_name,metadata"
)
EDGE_SELECT_COLUMNS_WITHOUT_METADATA = (
    "id,map_id,from_node_id,to_node_id,distance_meters,"
    "travel_time_seconds,weight,is_one_way,road_name"
)


def _response_data(response: Any) -> Any:
    return getattr(response, "data", response)


def _require_single_row(data: Any, *, context: str) -> dict[str, Any]:
    if isinstance(data, list):
        if not data:
            raise RuntimeError(f"No rows were returned while {context}.")
        row = data[0]
    else:
        row = data

    if not isinstance(row, dict):
        raise RuntimeError(f"Unexpected response shape while {context}.")
    return row


def _normalize_stoplights(
    stoplights: list[Stoplight | dict[str, Any]] | None,
) -> list[Stoplight]:
    normalized: list[Stoplight] = []
    for stoplight in stoplights or []:
        if isinstance(stoplight, Stoplight):
            normalized.append(
                Stoplight(
                    row=int(
                        sanitize_number(
                            stoplight.row,
                            default=0,
                            minimum=0,
                            integer=True,
                        )
                    ),
                    col=int(
                        sanitize_number(
                            stoplight.col,
                            default=0,
                            minimum=0,
                            integer=True,
                        )
                    ),
                    average_wait_seconds=float(
                        sanitize_number(
                            stoplight.average_wait_seconds,
                            default=0.0,
                            minimum=0.0,
                        )
                    ),
                    light_cycle_seconds=sanitize_number(
                        stoplight.light_cycle_seconds,
                        default=None,
                        minimum=1.0,
                        allow_none=True,
                    ),
                    has_stoplight=bool(stoplight.has_stoplight),
                    metadata=dict(_json_safe_value(stoplight.metadata or {})),
                )
            )
            continue
        normalized.append(
            Stoplight(
                row=int(
                    sanitize_number(
                        stoplight["row"],
                        default=0,
                        minimum=0,
                        integer=True,
                    )
                ),
                col=int(
                    sanitize_number(
                        stoplight["col"],
                        default=0,
                        minimum=0,
                        integer=True,
                    )
                ),
                average_wait_seconds=float(
                    sanitize_number(
                        stoplight["average_wait_seconds"],
                        default=0.0,
                        minimum=0.0,
                    )
                ),
                light_cycle_seconds=sanitize_number(
                    stoplight.get("light_cycle_seconds"),
                    default=None,
                    minimum=1.0,
                    allow_none=True,
                ),
                has_stoplight=bool(stoplight.get("has_stoplight", True)),
                metadata=dict(_json_safe_value(stoplight.get("metadata") or {})),
            )
        )
    return normalized


def _sanitize_traffic_map(
    traffic: dict[str, list[list[float]]] | None,
) -> dict[str, list[list[float]]] | None:
    if traffic is None:
        return None

    sanitized: dict[str, list[list[float]]] = {}
    for direction, rows in traffic.items():
        sanitized[direction] = [
            [
                float(sanitize_number(value, default=1.0, minimum=1.0))
                for value in row
            ]
            for row in rows
        ]
    return sanitized


def sanitize_number(
    value: Any,
    default: float | int | None = 1.0,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    allow_none: bool = False,
    integer: bool = False,
) -> float | int | None:
    if value is None:
        return None if allow_none else default

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None if allow_none else default

    if not math.isfinite(number):
        return None if allow_none else default

    if minimum is not None and number < minimum:
        number = minimum
    if maximum is not None and number > maximum:
        number = maximum

    if integer:
        return int(number)
    return float(number)


def _json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Point):
        return {"row": value.row, "col": value.col}
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        as_float = float(value)
        return as_float if math.isfinite(as_float) else None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, set):
        return [_json_safe_value(item) for item in sorted(value, key=str)]
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    return str(value)


def _json_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _json_safe_value(value) for key, value in row.items()}


def _json_safe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_json_safe_row(row) for row in rows]


def _json_safe_metadata_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    sanitized: dict[str, Any] = {}
    for key, item in value.items():
        safe_value = _json_safe_value(item)
        if isinstance(item, float) and not math.isfinite(item):
            continue
        if safe_value is None and item is not None:
            continue
        sanitized[str(key)] = safe_value
    return sanitized


def _mapping_pairs(point_to_node_id: dict[Point, str]) -> list[dict[str, object]]:
    return [
        {"row": point.row, "col": point.col, "node_id": node_id}
        for point, node_id in sorted(
            point_to_node_id.items(),
            key=lambda item: (item[0].row, item[0].col),
        )
    ]


def _load_map_row(map_id: str) -> dict[str, Any]:
    try:
        client = get_supabase_client()
        response = (
            client.table("maps")
            .select("id,name,slug,description,created_at")
            .eq("id", map_id)
            .limit(1)
            .execute()
        )
        row = _require_single_row(_response_data(response), context="loading map")
        return _json_safe_row(row)
    except Exception as exc:
        raise RuntimeError(f"Failed to load map row for map '{map_id}': {exc}") from exc


def sanitize_edge_row(
    edge: dict[str, Any],
    *,
    include_metadata: bool = True,
) -> dict[str, Any]:
    sanitized = {
        "id": str(edge["id"]) if edge.get("id") is not None else None,
        "map_id": str(edge["map_id"]) if edge.get("map_id") is not None else None,
        "from_node_id": (
            str(edge["from_node_id"]) if edge.get("from_node_id") is not None else None
        ),
        "to_node_id": (
            str(edge["to_node_id"]) if edge.get("to_node_id") is not None else None
        ),
        "distance_meters": sanitize_number(
            edge.get("distance_meters"),
            default=1.0,
            minimum=0.000001,
        ),
        "travel_time_seconds": sanitize_number(
            edge.get("travel_time_seconds"),
            default=None,
            minimum=0.0,
            allow_none=True,
        ),
        "weight": sanitize_number(
            edge.get("weight"),
            default=1.0,
            minimum=0.0,
        ),
        "is_one_way": bool(edge.get("is_one_way", True)),
        "road_name": (
            str(edge.get("road_name")) if edge.get("road_name") is not None else None
        ),
        "metadata": (
            _json_safe_metadata_dict(edge.get("metadata")) if include_metadata else {}
        ),
    }
    return _json_safe_row(sanitized)


def _fetch_edge_page(
    *,
    map_id: str,
    columns: str,
    start: int,
    end: int,
) -> list[dict[str, Any]]:
    try:
        client = get_supabase_client()
        response = (
            client.table("edges")
            .select(columns)
            .eq("map_id", map_id)
            .range(start, end)
            .execute()
        )
        data = _response_data(response) or []
        if not isinstance(data, list):
            raise RuntimeError("Expected edge query to return a list of rows.")
        return [row for row in data if isinstance(row, dict)]
    except Exception as exc:
        raise RuntimeError(
            "Failed to load edges for map "
            f"'{map_id}' using columns '{columns}' and range {start}-{end}: {exc}"
        ) from exc


def _fetch_all_edges_for_map_with_columns(
    map_id: str,
    *,
    columns: str,
    page_size: int,
    include_metadata: bool,
) -> list[dict[str, Any]]:
    if page_size <= 0:
        raise ValueError("page_size must be greater than 0.")

    edges: list[dict[str, Any]] = []
    start = 0

    while True:
        end = start + page_size - 1
        rows = _fetch_edge_page(map_id=map_id, columns=columns, start=start, end=end)
        edges.extend(
            sanitize_edge_row(row, include_metadata=include_metadata) for row in rows
        )
        if len(rows) < page_size:
            break
        start += page_size

    return edges


def fetch_all_edges_for_map(map_id: str, page_size: int = 1000) -> list[dict[str, Any]]:
    try:
        return _fetch_all_edges_for_map_with_columns(
            map_id,
            columns=EDGE_SELECT_COLUMNS,
            page_size=page_size,
            include_metadata=True,
        )
    except Exception as metadata_error:
        try:
            return _fetch_all_edges_for_map_with_columns(
                map_id,
                columns=EDGE_SELECT_COLUMNS_WITHOUT_METADATA,
                page_size=page_size,
                include_metadata=False,
            )
        except Exception as fallback_error:
            raise RuntimeError(
                "Failed to load edges for the requested map graph. "
                f"Primary query with metadata failed: {metadata_error}. "
                f"Fallback without metadata failed: {fallback_error}"
            ) from fallback_error


def _load_traffic_signals_for_map(map_id: str) -> list[dict[str, Any]]:
    try:
        client = get_supabase_client()
        response = (
            client.table("traffic_signals")
            .select("id,map_id,node_id,average_wait_seconds,light_cycle_seconds,signal_type,metadata,created_at")
            .eq("map_id", map_id)
            .execute()
        )
        data = _response_data(response) or []
        if not isinstance(data, list):
            raise RuntimeError("Expected traffic signal query to return a list of rows.")
        return _json_safe_rows([row for row in data if isinstance(row, dict)])
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load traffic_signals for map '{map_id}': {exc}"
        ) from exc


def check_database_connection() -> dict[str, object]:
    client = get_supabase_client()
    response = client.table("maps").select("*").limit(3).execute()
    return {
        "status": "ok",
        "sample_maps": _json_safe_value(_response_data(response) or []),
    }


def list_maps() -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("maps")
        .select("id,name,slug,description,created_at")
        .order("created_at", desc=True)
        .execute()
    )
    data = _response_data(response) or []
    if not isinstance(data, list):
        raise RuntimeError("Expected maps query to return a list of rows.")
    return _json_safe_rows([row for row in data if isinstance(row, dict)])


def create_map(
    *,
    name: str,
    slug: str,
    description: str | None = None,
) -> dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "name": name,
        "slug": slug,
        "description": description,
    }
    try:
        response = client.table("maps").insert(payload).execute()
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()
        if "slug" in lowered and ("duplicate" in lowered or "unique" in lowered):
            raise ValueError(
                f"A map with slug '{slug}' already exists. Choose a unique slug."
            ) from exc
        raise RuntimeError(f"Failed to create map: {message}") from exc

    row = _require_single_row(_response_data(response), context="creating map")
    return _json_safe_row(row)


def load_nodes_for_map(map_id: str) -> list[dict[str, Any]]:
    try:
        client = get_supabase_client()
        response = (
            client.table("nodes")
            .select("id,row,col,label,lat,lng")
            .eq("map_id", map_id)
            .execute()
        )
        data = _response_data(response) or []
        if not isinstance(data, list):
            raise RuntimeError("Expected node query to return a list of rows.")
        return _json_safe_rows([row for row in data if isinstance(row, dict)])
    except Exception as exc:
        raise RuntimeError(f"Failed to load nodes for map '{map_id}': {exc}") from exc


def build_point_to_node_id(map_id: str) -> dict[Point, str]:
    mapping: dict[Point, str] = {}
    for node in load_nodes_for_map(map_id):
        row = node.get("row")
        col = node.get("col")
        node_id = node.get("id")
        if row is None or col is None or not node_id:
            continue
        safe_row = sanitize_number(row, default=None, minimum=0, allow_none=True, integer=True)
        safe_col = sanitize_number(col, default=None, minimum=0, allow_none=True, integer=True)
        if safe_row is None or safe_col is None:
            continue
        mapping[Point(int(safe_row), int(safe_col))] = str(node_id)
    return mapping


def save_generated_map(
    *,
    name: str,
    slug: str,
    description: str | None,
    grid: list[list[int]],
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight | dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_stoplights = _normalize_stoplights(stoplights)
    sanitized_traffic = _sanitize_traffic_map(traffic)
    grid_map = GridMap(grid, traffic=sanitized_traffic, stoplights=normalized_stoplights)
    created_map = create_map(name=name, slug=slug, description=description)
    map_id = str(created_map["id"])
    client = get_supabase_client()

    node_rows: list[dict[str, Any]] = []
    for row in range(grid_map.rows):
        for col in range(grid_map.cols):
            point = Point(row, col)
            if not grid_map.is_road(point):
                continue
            node_rows.append(
                {
                    "map_id": map_id,
                    "row": int(
                        sanitize_number(row, default=0, minimum=0, integer=True)
                    ),
                    "col": int(
                        sanitize_number(col, default=0, minimum=0, integer=True)
                    ),
                    "label": f"{row},{col}",
                    "lat": float(sanitize_number(row, default=0.0, minimum=0.0)),
                    "lng": float(sanitize_number(col, default=0.0, minimum=0.0)),
                }
            )

    if node_rows:
        client.table("nodes").insert(node_rows).execute()

    point_to_node_id = build_point_to_node_id(map_id)

    edge_rows: list[dict[str, Any]] = []
    for point, from_node_id in sorted(
        point_to_node_id.items(), key=lambda item: (item[0].row, item[0].col)
    ):
        for neighbor in grid_map.neighbors(point):
            to_node_id = point_to_node_id.get(neighbor)
            if to_node_id is None:
                raise ValueError(
                    "The generated map contains a traversable neighbor that was not "
                    "saved as a node. Check the grid-to-node mapping."
                )
            edge_weight = float(
                sanitize_number(
                    grid_map.traffic_cost(point, neighbor),
                    default=1.0,
                    minimum=0.0,
                )
            )
            edge_rows.append(
                {
                    "map_id": map_id,
                    "from_node_id": from_node_id,
                    "to_node_id": to_node_id,
                    "distance_meters": float(
                        sanitize_number(1.0, default=1.0, minimum=0.000001)
                    ),
                    "weight": edge_weight,
                    "travel_time_seconds": edge_weight,
                    "is_one_way": True,
                    "metadata": _json_safe_value(
                        {
                        "generated_from_grid": True,
                        "base_movement_cost": 1.0,
                        "directional_traffic_enabled": sanitized_traffic is not None,
                        "source": "generated_map_save",
                        **dict(metadata or {}),
                        }
                    ),
                }
            )

    if edge_rows:
        client.table("edges").insert(edge_rows).execute()

    traffic_signal_rows: list[dict[str, Any]] = []
    for stoplight in normalized_stoplights:
        point = Point(stoplight.row, stoplight.col)
        node_id = point_to_node_id.get(point)
        if node_id is None:
            raise ValueError(
                "Stoplight coordinates do not match a traversable saved node at "
                f"({point.row}, {point.col})."
            )
        traffic_signal_rows.append(
            {
                "map_id": map_id,
                "node_id": node_id,
                "average_wait_seconds": float(
                    sanitize_number(
                        stoplight.average_wait_seconds,
                        default=0.0,
                        minimum=0.0,
                    )
                ),
                "light_cycle_seconds": sanitize_number(
                    stoplight.light_cycle_seconds,
                    default=None,
                    minimum=1.0,
                    allow_none=True,
                ),
                "signal_type": "stoplight",
                "metadata": _json_safe_value(dict(stoplight.metadata or {})),
            }
        )

    if traffic_signal_rows:
        client.table("traffic_signals").insert(traffic_signal_rows).execute()

    return {
        "map": _json_safe_value(
            {
                "id": map_id,
                "name": created_map.get("name", name),
                "slug": created_map.get("slug", slug),
                "description": created_map.get("description", description),
                "created_at": created_map.get("created_at"),
            }
        ),
        "map_id": map_id,
        "node_count": len(point_to_node_id),
        "edge_count": len(edge_rows),
        "stoplight_count": len(traffic_signal_rows),
        "point_node_pairs": _json_safe_value(_mapping_pairs(point_to_node_id)),
        "metadata": _json_safe_value(
            {
                "grid_rows": grid_map.rows,
                "grid_cols": grid_map.cols,
                "traffic_enabled": sanitized_traffic is not None,
                "stoplights_enabled": bool(normalized_stoplights),
                **dict(metadata or {}),
            }
        ),
    }


def load_map_graph(map_id: str) -> dict[str, Any]:
    map_row = _load_map_row(map_id)
    nodes = load_nodes_for_map(map_id)
    edges = fetch_all_edges_for_map(map_id)
    traffic_signals = _load_traffic_signals_for_map(map_id)

    safe_points = [
        (
            sanitize_number(node.get("row"), default=None, minimum=0, allow_none=True, integer=True),
            sanitize_number(node.get("col"), default=None, minimum=0, allow_none=True, integer=True),
        )
        for node in nodes
    ]
    valid_points = [
        (int(row), int(col))
        for row, col in safe_points
        if row is not None and col is not None
    ]

    if valid_points:
        max_row = max(row for row, _col in valid_points)
        max_col = max(col for _row, col in valid_points)
        grid = [[0 for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    else:
        grid = []

    node_id_to_point: dict[str, Point] = {}
    point_to_node_id: dict[Point, str] = {}
    for node in nodes:
        row = node.get("row")
        col = node.get("col")
        node_id = node.get("id")
        if row is None or col is None or not node_id:
            continue
        safe_row = sanitize_number(row, default=None, minimum=0, allow_none=True, integer=True)
        safe_col = sanitize_number(col, default=None, minimum=0, allow_none=True, integer=True)
        if safe_row is None or safe_col is None:
            continue
        point = Point(int(safe_row), int(safe_col))
        if grid:
            grid[point.row][point.col] = 1
        node_id_to_point[str(node_id)] = point
        point_to_node_id[point] = str(node_id)

    if grid:
        traffic = GridMap._neutral_traffic(len(grid), len(grid[0]))
    else:
        traffic = None

    for edge in edges:
        from_node_id = edge.get("from_node_id")
        to_node_id = edge.get("to_node_id")
        if not from_node_id or not to_node_id:
            continue
        from_point = node_id_to_point.get(str(from_node_id))
        to_point = node_id_to_point.get(str(to_node_id))
        if from_point is None or to_point is None:
            continue
        try:
            direction = GridMap.direction_between(from_point, to_point)
        except ValueError:
            continue
        if traffic is not None:
            weight = edge.get("travel_time_seconds")
            if weight is None:
                weight = edge.get("weight")
            traffic[direction][from_point.row][from_point.col] = float(
                sanitize_number(weight, default=1.0, minimum=0.0)
            )

    signal_rows: list[dict[str, Any]] = []
    for signal in traffic_signals:
        node_id = signal.get("node_id")
        point = node_id_to_point.get(str(node_id)) if node_id else None
        signal_row = dict(signal)
        if point is not None:
            signal_row["row"] = point.row
            signal_row["col"] = point.col
            signal_row["label"] = f"{point.row},{point.col}"
        signal_row["average_wait_seconds"] = sanitize_number(
            signal_row.get("average_wait_seconds"),
            default=0.0,
            minimum=0.0,
        )
        signal_row["light_cycle_seconds"] = sanitize_number(
            signal_row.get("light_cycle_seconds"),
            default=None,
            minimum=1.0,
            allow_none=True,
        )
        signal_rows.append(signal_row)

    return {
        "map": _json_safe_row(map_row),
        "grid": grid,
        "nodes": _json_safe_rows(nodes),
        "edges": _json_safe_rows(edges),
        "traffic_signals": _json_safe_rows(signal_rows),
        "traffic": _json_safe_value(traffic),
        "point_node_pairs": _json_safe_value(_mapping_pairs(point_to_node_id)),
    }


def list_experiments_for_map(map_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("route_experiments")
        .select("id,start_node_id,end_node_id,traffic_enabled,stoplights_enabled,metadata,created_at")
        .eq("map_id", map_id)
        .order("created_at", desc=True)
        .execute()
    )
    data = _response_data(response) or []
    if not isinstance(data, list):
        raise RuntimeError("Expected experiments query to return a list of rows.")
    return _json_safe_rows([row for row in data if isinstance(row, dict)])


def create_route_experiment(
    *,
    map_id: str,
    start_node_id: str,
    end_node_id: str,
    traffic_enabled: bool,
    stoplights_enabled: bool,
    metadata: dict[str, Any] | None = None,
) -> str:
    client = get_supabase_client()
    payload = {
        "map_id": map_id,
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
        "traffic_enabled": traffic_enabled,
        "stoplights_enabled": stoplights_enabled,
        "metadata": metadata or {},
    }
    response = client.table("route_experiments").insert(payload).execute()
    row = _require_single_row(_response_data(response), context="creating route_experiment")
    experiment_id = row.get("id")
    if not experiment_id:
        raise RuntimeError("Supabase did not return an experiment id.")
    return str(experiment_id)


def save_algorithm_run_with_path(
    *,
    experiment_id: str,
    map_id: str,
    algorithm: str,
    start_node_id: str,
    end_node_id: str,
    status: str,
    total_cost: float | None,
    total_distance_meters: float | None,
    total_duration_seconds: float | None,
    visited_count: int,
    runtime_ms: int,
    metadata: dict[str, Any],
    path_nodes: list[dict[str, Any]],
) -> str:
    client = get_supabase_client()
    params = {
        "p_experiment_id": experiment_id,
        "p_map_id": map_id,
        "p_algorithm": algorithm,
        "p_start_node_id": start_node_id,
        "p_end_node_id": end_node_id,
        "p_status": status,
        "p_total_cost": total_cost,
        "p_total_distance_meters": total_distance_meters,
        "p_total_duration_seconds": total_duration_seconds,
        "p_visited_count": visited_count,
        "p_runtime_ms": runtime_ms,
        "p_metadata": metadata,
        "p_path_nodes": path_nodes,
    }
    response = client.rpc("save_algorithm_run_with_path", params).execute()
    run_id = _response_data(response)
    if not run_id:
        raise RuntimeError("Supabase did not return a run id from save_algorithm_run_with_path.")
    return str(run_id)


def get_algorithm_comparison_summary(experiment_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("algorithm_comparison_summary")
        .select("*")
        .eq("experiment_id", experiment_id)
        .order("cost_rank")
        .order("speed_rank")
        .execute()
    )
    data = _response_data(response) or []
    if not isinstance(data, list):
        raise RuntimeError("Expected comparison summary query to return a list of rows.")
    return _json_safe_rows([row for row in data if isinstance(row, dict)])


def get_experiment_results(experiment_id: str) -> list[dict[str, Any]]:
    return get_algorithm_comparison_summary(experiment_id)


def get_algorithm_performance_summary(
    map_id: str | None = None,
) -> list[dict[str, Any]]:
    client = get_supabase_client()
    query = client.table("algorithm_performance_summary").select("*")
    if map_id is not None:
        query = query.eq("map_id", map_id)
    response = query.execute()
    data = _response_data(response) or []
    if not isinstance(data, list):
        raise RuntimeError("Expected performance summary query to return a list of rows.")
    return _json_safe_rows([row for row in data if isinstance(row, dict)])


def get_run_path(run_id: str) -> list[dict[str, Any]]:
    client = get_supabase_client()
    response = (
        client.table("run_path_nodes")
        .select("step_index,node_id,cumulative_cost,reached,nodes!inner(row,col,label)")
        .eq("run_id", run_id)
        .order("step_index")
        .execute()
    )
    data = _response_data(response) or []
    if not isinstance(data, list):
        raise RuntimeError("Expected run path query to return a list of rows.")

    rows: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        node_data = row.get("nodes") or {}
        rows.append(
            {
                "step_index": row.get("step_index"),
                "node_id": row.get("node_id"),
                "row": node_data.get("row"),
                "col": node_data.get("col"),
                "label": node_data.get("label"),
                "cumulative_cost": row.get("cumulative_cost"),
                "reached": row.get("reached"),
            }
        )
    return _json_safe_rows(rows)
