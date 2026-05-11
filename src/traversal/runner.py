from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeAlias

from traversal.grid import GridMap, Point
from traversal.models import PathfindingResult, point_to_dict
from traversal.pathfinding import a_star, dijkstra


AlgorithmFunction: TypeAlias = Callable[[GridMap, Point, Point], PathfindingResult]

ALGORITHM_REGISTRY: dict[str, AlgorithmFunction] = {
    "astar": a_star,
    "dijkstra": dijkstra,
}


def list_algorithms() -> list[str]:
    return list(ALGORITHM_REGISTRY.keys())


def get_algorithm(name: str) -> AlgorithmFunction:
    normalized_name = name.strip().lower()
    try:
        return ALGORITHM_REGISTRY[normalized_name]
    except KeyError as exc:
        available = ", ".join(list_algorithms())
        raise ValueError(
            f"Unsupported algorithm '{name}'. Available algorithms: {available}."
        ) from exc


def _ensure_grid_map(
    grid: GridMap | list[list[int]],
    traffic: dict[str, list[list[float]]] | None = None,
) -> GridMap:
    if isinstance(grid, GridMap):
        return grid
    return GridMap(grid, traffic=traffic)


def _normalize_algorithm_names(names: str | Iterable[str]) -> list[str]:
    if isinstance(names, str):
        normalized_name = names.strip().lower()
        if normalized_name == "all":
            return list_algorithms()
        get_algorithm(normalized_name)
        return [normalized_name]

    normalized_names: list[str] = []
    for name in names:
        normalized_name = name.strip().lower()
        get_algorithm(normalized_name)
        normalized_names.append(normalized_name)
    return normalized_names


def run_algorithm(
    name: str,
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
) -> PathfindingResult:
    algorithm = get_algorithm(name)
    return algorithm(_ensure_grid_map(grid, traffic), start, goal)


def run_algorithms(
    names: str | Iterable[str],
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
) -> list[PathfindingResult]:
    grid_map = _ensure_grid_map(grid, traffic)
    normalized_names = _normalize_algorithm_names(names)
    return [get_algorithm(name)(grid_map, start, goal) for name in normalized_names]


def run_all_algorithms(
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
) -> list[PathfindingResult]:
    return run_algorithms("all", grid, start, goal, traffic=traffic)


def run_pathfinding_request(
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    algorithms: str | Iterable[str],
    traffic: dict[str, list[list[float]]] | None = None,
) -> dict[str, object]:
    normalized_names = _normalize_algorithm_names(algorithms)
    results = run_algorithms(normalized_names, grid, start, goal, traffic=traffic)
    return {
        "start": point_to_dict(start),
        "goal": point_to_dict(goal),
        "selected_algorithms": normalized_names,
        "results": [result.to_dict() for result in results],
    }
