from __future__ import annotations

from typing import Any

from traversal.grid import Point
from traversal.models import PathfindingResult, point_to_dict


def _resolve_node_id(
    point: Point,
    point_to_node_id: dict[Point | tuple[int, int], str],
) -> str:
    if point in point_to_node_id:
        return point_to_node_id[point]

    point_key = (point.row, point.col)
    if point_key in point_to_node_id:
        return point_to_node_id[point_key]

    raise ValueError(
        "Missing node id mapping for point "
        f"({point.row}, {point.col}). Database nodes do not match the grid "
        "coordinates for this map."
    )


def build_algorithm_run_row(
    result: PathfindingResult,
    *,
    map_id: str,
    start: Point,
    goal: Point,
    point_to_node_id: dict[Point | tuple[int, int], str],
    experiment_id: str | None = None,
    total_distance_meters: float | None = None,
    total_duration_seconds: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result_metadata = {
        **result.metadata,
        "path_found": result.path_found,
        "path_length_nodes": result.path_length_nodes,
        "moves": result.moves,
        "expanded_count": result.expanded_count,
        "frontier_pushes": result.frontier_pushes,
        "path": [point_to_dict(point) for point in result.path],
        "cumulative_costs": result.cumulative_costs,
    }
    if metadata:
        result_metadata.update(metadata)

    return {
        "experiment_id": experiment_id,
        "map_id": map_id,
        "algorithm": result.algorithm_name,
        "start_node_id": _resolve_node_id(start, point_to_node_id),
        "end_node_id": _resolve_node_id(goal, point_to_node_id),
        "status": "completed" if result.path_found else "no_path",
        "total_cost": result.path_cost,
        "total_distance_meters": total_distance_meters,
        "total_duration_seconds": total_duration_seconds,
        "visited_count": result.visited_count,
        "runtime_ms": result.runtime_ms,
        "metadata": result_metadata,
    }


def build_run_path_node_rows(
    result: PathfindingResult,
    *,
    run_id: str | None = None,
    point_to_node_id: dict[Point | tuple[int, int], str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cumulative_costs = result.cumulative_costs or []
    if result.path and len(cumulative_costs) != len(result.path):
        raise ValueError("PathfindingResult cumulative costs must match the path length.")

    for step_index, point in enumerate(result.path):
        row = {
            "node_id": _resolve_node_id(point, point_to_node_id),
            "step_index": step_index,
            "cumulative_cost": float(cumulative_costs[step_index]),
            "reached": result.path_found and step_index == len(result.path) - 1,
        }
        if run_id is not None:
            row["run_id"] = run_id
        rows.append(row)

    return rows
