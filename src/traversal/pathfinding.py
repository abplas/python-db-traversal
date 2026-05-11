from __future__ import annotations

from collections.abc import Callable
from heapq import heappop, heappush
from time import perf_counter_ns

from traversal.grid import GridMap, Point
from traversal.models import PathfindingResult


def manhattan_distance(a: Point, b: Point) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def reconstruct_path(came_from: dict[Point, Point], current: Point) -> list[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _validate_endpoints(grid_map: GridMap, start: Point, goal: Point) -> None:
    if not grid_map.is_road(start):
        raise ValueError("Start point must be on a traversable road cell.")
    if not grid_map.is_road(goal):
        raise ValueError("Goal point must be on a traversable road cell.")


def _complexity_metadata(grid_map: GridMap) -> dict[str, object]:
    node_count = grid_map.traversable_count()
    edge_count = grid_map.directed_edge_count()
    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "time_complexity": "O((V + E) log V)",
        "space_complexity": "O(V)",
        "complexity_variables": {"V": node_count, "E": edge_count},
    }


def _build_result(
    *,
    grid_map: GridMap,
    algorithm_name: str,
    path: list[Point],
    path_cost: float | None,
    runtime_ms: int,
    visited_count: int,
    expanded_count: int,
    frontier_pushes: int,
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    path_found = bool(path)
    path_length_nodes = len(path)
    moves = max(path_length_nodes - 1, 0) if path_found else 0
    result_metadata = {**_complexity_metadata(grid_map), **dict(metadata or {})}
    return PathfindingResult(
        algorithm_name=algorithm_name,
        path=path,
        path_found=path_found,
        path_cost=path_cost,
        path_length_nodes=path_length_nodes,
        moves=moves,
        runtime_ms=runtime_ms,
        visited_count=visited_count,
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=result_metadata,
    )


def _run_priority_search(
    grid_map: GridMap,
    start: Point,
    goal: Point,
    *,
    algorithm_name: str,
    heuristic: Callable[[Point, Point], float],
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    _validate_endpoints(grid_map, start, goal)

    start_time_ns = perf_counter_ns()
    frontier: list[tuple[float, Point]] = []
    heappush(frontier, (0, start))

    came_from: dict[Point, Point] = {}
    cost_so_far: dict[Point, float] = {start: 0.0}
    frontier_pushes = 1
    expanded_count = 0

    while frontier:
        _, current = heappop(frontier)
        expanded_count += 1

        if current == goal:
            runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
            return _build_result(
                grid_map=grid_map,
                algorithm_name=algorithm_name,
                path=reconstruct_path(came_from, current),
                path_cost=cost_so_far[current],
                runtime_ms=runtime_ms,
                visited_count=len(cost_so_far),
                expanded_count=expanded_count,
                frontier_pushes=frontier_pushes,
                metadata=metadata,
            )

        for neighbor in grid_map.neighbors(current):
            new_cost = cost_so_far[current] + grid_map.movement_cost(current, neighbor)
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(neighbor, goal)
                heappush(frontier, (priority, neighbor))
                frontier_pushes += 1
                came_from[neighbor] = current

    runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
    return _build_result(
        grid_map=grid_map,
        algorithm_name=algorithm_name,
        path=[],
        path_cost=None,
        runtime_ms=runtime_ms,
        visited_count=len(cost_so_far),
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=metadata,
    )


def a_star(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a non-diagonal path using A* with Manhattan distance."""
    return _run_priority_search(
        grid_map,
        start,
        goal,
        algorithm_name="astar",
        heuristic=manhattan_distance,
        metadata={"heuristic": "manhattan", "uses_directional_traffic": True},
    )


def dijkstra(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a non-diagonal path using Dijkstra's algorithm."""
    return _run_priority_search(
        grid_map,
        start,
        goal,
        algorithm_name="dijkstra",
        heuristic=lambda _point, _goal: 0,
        metadata={"heuristic": None, "uses_directional_traffic": True},
    )


def bellman_ford(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    raise NotImplementedError(
        "Bellman-Ford is not registered yet. Add explicit weighted-edge support or "
        "a graph abstraction first if you want Bellman-Ford to be a first-class option."
    )


def find_path(grid_map: GridMap, start: Point, goal: Point) -> list[Point]:
    """Backwards-compatible wrapper that returns only the path."""
    return a_star(grid_map, start, goal).path
