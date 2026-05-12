from __future__ import annotations

from collections import deque
from collections.abc import Callable
from heapq import heappop, heappush
from time import perf_counter_ns
from typing import Any

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


def evaluate_path_cost(grid_map: GridMap, path: list[Point]) -> dict[str, Any]:
    if not path:
        return {
            "total_cost": None,
            "cumulative_costs": [],
            "base_movement_cost_total": 0.0,
            "traffic_cost_total": 0.0,
            "stoplight_delay_total": 0.0,
            "stoplights_crossed": 0,
            "moves": 0,
        }

    cumulative_costs = [0.0]
    base_movement_cost_total = 0.0
    traffic_cost_total = 0.0
    stoplight_delay_total = 0.0
    stoplights_crossed = 0

    for current, neighbor in zip(path, path[1:]):
        components = grid_map.movement_cost_components(current, neighbor)
        base_movement_cost_total += float(components["base_movement_cost"])
        traffic_cost_total += float(components["traffic_delay_cost"])
        stoplight_delay_total += float(components["stoplight_delay"])
        if float(components["stoplight_delay"]) > 0:
            stoplights_crossed += 1
        cumulative_costs.append(cumulative_costs[-1] + float(components["total_cost"]))

    return {
        "total_cost": cumulative_costs[-1],
        "cumulative_costs": cumulative_costs,
        "base_movement_cost_total": base_movement_cost_total,
        "traffic_cost_total": traffic_cost_total,
        "stoplight_delay_total": stoplight_delay_total,
        "stoplights_crossed": stoplights_crossed,
        "moves": max(len(path) - 1, 0),
    }


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
        "stoplight_count": grid_map.stoplight_count(),
        "complexity_variables": {"V": node_count, "E": edge_count},
    }


def _build_result(
    *,
    grid_map: GridMap,
    algorithm_name: str,
    path: list[Point],
    runtime_ms: int,
    visited_count: int,
    expanded_count: int,
    frontier_pushes: int,
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    path_found = bool(path)
    evaluation = evaluate_path_cost(grid_map, path)
    path_length_nodes = len(path)
    result_metadata = {
        **_complexity_metadata(grid_map),
        "uses_directional_traffic": grid_map.has_directional_traffic(),
        "uses_stoplights": grid_map.has_stoplights(),
        "cost_model": "base movement + directional traffic delay + stoplight delay at destination node",
        "base_movement_cost_total": evaluation["base_movement_cost_total"],
        "traffic_cost_total": evaluation["traffic_cost_total"],
        "stoplight_delay_total": evaluation["stoplight_delay_total"],
        "stoplights_crossed": evaluation["stoplights_crossed"],
        **dict(metadata or {}),
    }
    return PathfindingResult(
        algorithm_name=algorithm_name,
        path=path,
        cumulative_costs=evaluation["cumulative_costs"],
        path_found=path_found,
        path_cost=evaluation["total_cost"],
        path_length_nodes=path_length_nodes,
        moves=max(path_length_nodes - 1, 0) if path_found else 0,
        runtime_ms=runtime_ms,
        visited_count=visited_count,
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=result_metadata,
    )


def _run_weighted_priority_search(
    grid_map: GridMap,
    start: Point,
    goal: Point,
    *,
    algorithm_name: str,
    heuristic: Callable[[Point, Point], float],
    heuristic_weight: float = 1.0,
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    _validate_endpoints(grid_map, start, goal)

    start_time_ns = perf_counter_ns()
    frontier: list[tuple[float, Point]] = []
    heappush(frontier, (0.0, start))

    came_from: dict[Point, Point] = {}
    cost_so_far: dict[Point, float] = {start: 0.0}
    frontier_pushes = 1
    expanded_count = 0

    while frontier:
        _, current = heappop(frontier)
        expanded_count += 1

        if current == goal:
            runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
            path = reconstruct_path(came_from, current)
            return _build_result(
                grid_map=grid_map,
                algorithm_name=algorithm_name,
                path=path,
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
                priority = new_cost + heuristic_weight * heuristic(neighbor, goal)
                heappush(frontier, (priority, neighbor))
                frontier_pushes += 1
                came_from[neighbor] = current

    runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
    return _build_result(
        grid_map=grid_map,
        algorithm_name=algorithm_name,
        path=[],
        runtime_ms=runtime_ms,
        visited_count=len(cost_so_far),
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=metadata,
    )


def _run_greedy_best_first(
    grid_map: GridMap,
    start: Point,
    goal: Point,
    *,
    algorithm_name: str,
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    _validate_endpoints(grid_map, start, goal)

    start_time_ns = perf_counter_ns()
    frontier: list[tuple[float, Point]] = []
    heappush(frontier, (float(manhattan_distance(start, goal)), start))
    seen = {start}
    came_from: dict[Point, Point] = {}
    frontier_pushes = 1
    expanded_count = 0

    while frontier:
        _, current = heappop(frontier)
        expanded_count += 1

        if current == goal:
            runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
            path = reconstruct_path(came_from, current)
            return _build_result(
                grid_map=grid_map,
                algorithm_name=algorithm_name,
                path=path,
                runtime_ms=runtime_ms,
                visited_count=len(seen),
                expanded_count=expanded_count,
                frontier_pushes=frontier_pushes,
                metadata=metadata,
            )

        for neighbor in grid_map.neighbors(current):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            came_from[neighbor] = current
            heappush(frontier, (float(manhattan_distance(neighbor, goal)), neighbor))
            frontier_pushes += 1

    runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
    return _build_result(
        grid_map=grid_map,
        algorithm_name=algorithm_name,
        path=[],
        runtime_ms=runtime_ms,
        visited_count=len(seen),
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=metadata,
    )


def _run_breadth_first_search(
    grid_map: GridMap,
    start: Point,
    goal: Point,
    *,
    algorithm_name: str,
    metadata: dict[str, object] | None = None,
) -> PathfindingResult:
    _validate_endpoints(grid_map, start, goal)

    start_time_ns = perf_counter_ns()
    frontier = deque([start])
    visited = {start}
    came_from: dict[Point, Point] = {}
    frontier_pushes = 1
    expanded_count = 0

    while frontier:
        current = frontier.popleft()
        expanded_count += 1

        if current == goal:
            runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
            path = reconstruct_path(came_from, current)
            return _build_result(
                grid_map=grid_map,
                algorithm_name=algorithm_name,
                path=path,
                runtime_ms=runtime_ms,
                visited_count=len(visited),
                expanded_count=expanded_count,
                frontier_pushes=frontier_pushes,
                metadata=metadata,
            )

        for neighbor in grid_map.neighbors(current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            frontier.append(neighbor)
            frontier_pushes += 1

    runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
    return _build_result(
        grid_map=grid_map,
        algorithm_name=algorithm_name,
        path=[],
        runtime_ms=runtime_ms,
        visited_count=len(visited),
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata=metadata,
    )


def bfs(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a route by minimizing moves only, ignoring weights during search."""
    return _run_breadth_first_search(
        grid_map,
        start,
        goal,
        algorithm_name="bfs",
        metadata={
            "display_name": "BFS",
            "heuristic": None,
            "supports_weights": False,
            "search_model": "unweighted_fewest_moves",
            "optimality": "optimal_for_unweighted_moves_only",
            "reliability_category": "baseline",
            "tradeoff": "fast/simple but may be poor when traffic or stoplights matter",
            "time_complexity": "O(V + E)",
            "space_complexity": "O(V)",
        },
    )


def dfs(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a route using depth-first search for reachability exploration."""
    _validate_endpoints(grid_map, start, goal)

    start_time_ns = perf_counter_ns()
    frontier = [start]
    visited = {start}
    came_from: dict[Point, Point] = {}
    frontier_pushes = 1
    expanded_count = 0

    while frontier:
        current = frontier.pop()
        expanded_count += 1

        if current == goal:
            runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
            path = reconstruct_path(came_from, current)
            return _build_result(
                grid_map=grid_map,
                algorithm_name="dfs",
                path=path,
                runtime_ms=runtime_ms,
                visited_count=len(visited),
                expanded_count=expanded_count,
                frontier_pushes=frontier_pushes,
                metadata={
                    "display_name": "DFS",
                    "heuristic": None,
                    "supports_weights": False,
                    "search_model": "depth_first_reachability",
                    "optimality": "not_guaranteed",
                    "reliability_category": "exploratory",
                    "tradeoff": "useful for reachability but does not guarantee the shortest or lowest-cost route",
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V)",
                },
            )

        for neighbor in reversed(grid_map.neighbors(current)):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            frontier.append(neighbor)
            frontier_pushes += 1

    runtime_ms = (perf_counter_ns() - start_time_ns) // 1_000_000
    return _build_result(
        grid_map=grid_map,
        algorithm_name="dfs",
        path=[],
        runtime_ms=runtime_ms,
        visited_count=len(visited),
        expanded_count=expanded_count,
        frontier_pushes=frontier_pushes,
        metadata={
            "display_name": "DFS",
            "heuristic": None,
            "supports_weights": False,
            "search_model": "depth_first_reachability",
            "optimality": "not_guaranteed",
            "reliability_category": "exploratory",
            "tradeoff": "useful for reachability but does not guarantee the shortest or lowest-cost route",
            "time_complexity": "O(V + E)",
            "space_complexity": "O(V)",
        },
    )


def greedy_best_first(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a route using only the heuristic to decide what to explore next."""
    return _run_greedy_best_first(
        grid_map,
        start,
        goal,
        algorithm_name="greedy_best_first",
        metadata={
            "display_name": "Greedy Best-First",
            "heuristic": "manhattan",
            "supports_weights": "partially",
            "search_model": "heuristic_only",
            "optimality": "not_guaranteed",
            "reliability_category": "fast_but_less_reliable",
            "tradeoff": "can be fast but may choose a worse path",
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V)",
        },
    )


def a_star(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a non-diagonal path using weighted A* with a standard heuristic weight of 1."""
    return _run_weighted_priority_search(
        grid_map,
        start,
        goal,
        algorithm_name="astar",
        heuristic=manhattan_distance,
        heuristic_weight=1.0,
        metadata={
            "display_name": "A*",
            "heuristic": "manhattan",
            "heuristic_weight": 1.0,
            "supports_weights": True,
            "search_model": "astar",
            "optimality": "optimal_with_admissible_heuristic",
            "reliability_category": "balanced",
            "tradeoff": "balanced speed and route quality",
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V)",
        },
    )


def weighted_astar(
    grid_map: GridMap,
    start: Point,
    goal: Point,
    heuristic_weight: float = 1.5,
) -> PathfindingResult:
    """Find a weighted route using a heuristic weight greater than 1."""
    return _run_weighted_priority_search(
        grid_map,
        start,
        goal,
        algorithm_name="weighted_astar",
        heuristic=manhattan_distance,
        heuristic_weight=heuristic_weight,
        metadata={
            "display_name": "Weighted A*",
            "heuristic": "manhattan",
            "heuristic_weight": heuristic_weight,
            "supports_weights": True,
            "search_model": "weighted_astar",
            "optimality": "not_guaranteed_when_weight_greater_than_1",
            "reliability_category": "speed_quality_tradeoff",
            "tradeoff": "often faster but may sacrifice route quality",
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V)",
        },
    )


def dijkstra(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    """Find a non-diagonal path using Dijkstra's algorithm."""
    return _run_weighted_priority_search(
        grid_map,
        start,
        goal,
        algorithm_name="dijkstra",
        heuristic=lambda _point, _goal: 0.0,
        heuristic_weight=0.0,
        metadata={
            "display_name": "Dijkstra",
            "heuristic": None,
            "heuristic_weight": 0.0,
            "supports_weights": True,
            "search_model": "uniform_cost",
            "optimality": "optimal_for_nonnegative_weights",
            "reliability_category": "reliable",
            "tradeoff": "reliable but can explore more nodes",
            "time_complexity": "O((V + E) log V)",
            "space_complexity": "O(V)",
        },
    )


def bellman_ford(grid_map: GridMap, start: Point, goal: Point) -> PathfindingResult:
    raise NotImplementedError(
        "Bellman-Ford is not registered yet. Add explicit weighted-edge support or "
        "a graph abstraction first if you want Bellman-Ford to be a first-class option."
    )


def find_path(grid_map: GridMap, start: Point, goal: Point) -> list[Point]:
    """Backwards-compatible wrapper that returns only the path."""
    return a_star(grid_map, start, goal).path
