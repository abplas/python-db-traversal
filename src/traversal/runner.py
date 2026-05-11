from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, TypeAlias

from traversal.grid import GridMap, Point, Stoplight
from traversal.models import PathfindingResult, point_to_dict
from traversal.pathfinding import (
    a_star,
    bfs,
    dijkstra,
    greedy_best_first,
    weighted_astar,
)


AlgorithmFunction: TypeAlias = Callable[[GridMap, Point, Point], PathfindingResult]


@dataclass(frozen=True, slots=True)
class AlgorithmSpec:
    key: str
    display_name: str
    function: AlgorithmFunction
    supports_weights: bool | str
    optimality: str
    category: str
    tradeoff: str

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "supports_weights": self.supports_weights,
            "optimality": self.optimality,
            "category": self.category,
            "tradeoff": self.tradeoff,
        }


ALGORITHM_REGISTRY: dict[str, AlgorithmSpec] = {
    "bfs": AlgorithmSpec(
        key="bfs",
        display_name="BFS",
        function=bfs,
        supports_weights=False,
        optimality="optimal_for_unweighted_moves_only",
        category="baseline",
        tradeoff="fast/simple but may be poor when traffic or stoplights matter",
    ),
    "dijkstra": AlgorithmSpec(
        key="dijkstra",
        display_name="Dijkstra",
        function=dijkstra,
        supports_weights=True,
        optimality="optimal_for_nonnegative_weights",
        category="reliable",
        tradeoff="reliable but can explore more nodes",
    ),
    "astar": AlgorithmSpec(
        key="astar",
        display_name="A*",
        function=a_star,
        supports_weights=True,
        optimality="optimal_with_admissible_heuristic",
        category="balanced",
        tradeoff="balanced speed and route quality",
    ),
    "greedy_best_first": AlgorithmSpec(
        key="greedy_best_first",
        display_name="Greedy Best-First",
        function=greedy_best_first,
        supports_weights="partially",
        optimality="not_guaranteed",
        category="fast_but_less_reliable",
        tradeoff="can be fast but may choose a worse path",
    ),
    "weighted_astar": AlgorithmSpec(
        key="weighted_astar",
        display_name="Weighted A*",
        function=weighted_astar,
        supports_weights=True,
        optimality="not_guaranteed_when_weight_greater_than_1",
        category="speed_quality_tradeoff",
        tradeoff="often faster but may sacrifice route quality",
    ),
}


def list_algorithms() -> list[str]:
    return list(ALGORITHM_REGISTRY.keys())


def list_algorithm_metadata() -> list[dict[str, object]]:
    return [spec.to_dict() for spec in ALGORITHM_REGISTRY.values()]


def get_algorithm_spec(name: str) -> AlgorithmSpec:
    normalized_name = name.strip().lower()
    try:
        return ALGORITHM_REGISTRY[normalized_name]
    except KeyError as exc:
        available = ", ".join(list_algorithms())
        raise ValueError(
            f"Unsupported algorithm '{name}'. Available algorithms: {available}."
        ) from exc


def get_algorithm(name: str) -> AlgorithmFunction:
    return get_algorithm_spec(name).function


def _ensure_grid_map(
    grid: GridMap | list[list[int]],
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight] | None = None,
) -> GridMap:
    if isinstance(grid, GridMap):
        return grid
    return GridMap(grid, traffic=traffic, stoplights=stoplights)


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


def _enrich_result(result: PathfindingResult, spec: AlgorithmSpec) -> PathfindingResult:
    result.metadata.setdefault("display_name", spec.display_name)
    result.metadata.setdefault("supports_weights", spec.supports_weights)
    result.metadata.setdefault("optimality", spec.optimality)
    result.metadata.setdefault("reliability_category", spec.category)
    result.metadata.setdefault("tradeoff", spec.tradeoff)
    result.metadata.setdefault("algorithm_key", spec.key)
    return result


def _comparison_label(
    *,
    result_payload: dict[str, Any],
    cost_ratio_to_best: float | None,
    speed_ratio_to_fastest: float | None,
) -> str:
    if not result_payload["path_found"]:
        return "no route found"

    optimality = str(result_payload.get("metadata", {}).get("optimality", ""))
    reliability = str(
        result_payload.get("metadata", {}).get("reliability_category", "")
    )

    if cost_ratio_to_best is not None and cost_ratio_to_best <= 1.05:
        if speed_ratio_to_fastest is not None and speed_ratio_to_fastest <= 1.15:
            return "balanced"
        if "optimal" in optimality:
            return "optimal or near optimal"
        return "near optimal"

    if reliability in {"fast_but_less_reliable", "baseline"}:
        return "fast but less reliable"

    if reliability in {"reliable", "balanced"}:
        return "reliable but slower"

    return "balanced"


def _attach_comparison_metrics(
    results: list[PathfindingResult],
) -> tuple[list[dict[str, Any]], float | None, int | None]:
    successful_results = [
        result for result in results if result.path_found and result.path_cost is not None
    ]
    best_path_cost = (
        min(float(result.path_cost) for result in successful_results)
        if successful_results
        else None
    )
    fastest_runtime_ms = (
        min(result.runtime_ms for result in successful_results)
        if successful_results
        else None
    )

    payload_results: list[dict[str, Any]] = []
    for result in results:
        result_payload = result.to_dict()
        cost_ratio_to_best = None
        if (
            result.path_found
            and result.path_cost is not None
            and best_path_cost is not None
            and best_path_cost > 0
        ):
            cost_ratio_to_best = round(float(result.path_cost) / best_path_cost, 4)
        elif result.path_found and result.path_cost == 0 and best_path_cost == 0:
            cost_ratio_to_best = 1.0

        speed_ratio_to_fastest = None
        if fastest_runtime_ms is not None:
            if fastest_runtime_ms == 0:
                if result.runtime_ms == 0:
                    speed_ratio_to_fastest = 1.0
            else:
                speed_ratio_to_fastest = round(
                    float(result.runtime_ms) / float(fastest_runtime_ms), 4
                )

        result_payload["cost_ratio_to_best"] = cost_ratio_to_best
        result_payload["speed_ratio_to_fastest"] = speed_ratio_to_fastest
        result_payload["comparison_label"] = _comparison_label(
            result_payload=result_payload,
            cost_ratio_to_best=cost_ratio_to_best,
            speed_ratio_to_fastest=speed_ratio_to_fastest,
        )
        payload_results.append(result_payload)

    return payload_results, best_path_cost, fastest_runtime_ms


def run_algorithm(
    name: str,
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight] | None = None,
) -> PathfindingResult:
    spec = get_algorithm_spec(name)
    result = spec.function(_ensure_grid_map(grid, traffic, stoplights), start, goal)
    return _enrich_result(result, spec)


def run_algorithms(
    names: str | Iterable[str],
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight] | None = None,
) -> list[PathfindingResult]:
    grid_map = _ensure_grid_map(grid, traffic, stoplights)
    normalized_names = _normalize_algorithm_names(names)
    results: list[PathfindingResult] = []
    for name in normalized_names:
        spec = get_algorithm_spec(name)
        results.append(_enrich_result(spec.function(grid_map, start, goal), spec))
    return results


def run_all_algorithms(
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight] | None = None,
) -> list[PathfindingResult]:
    return run_algorithms("all", grid, start, goal, traffic=traffic, stoplights=stoplights)


def run_pathfinding_request(
    grid: GridMap | list[list[int]],
    start: Point,
    goal: Point,
    algorithms: str | Iterable[str],
    traffic: dict[str, list[list[float]]] | None = None,
    stoplights: list[Stoplight] | None = None,
) -> dict[str, object]:
    normalized_names = _normalize_algorithm_names(algorithms)
    results = run_algorithms(
        normalized_names,
        grid,
        start,
        goal,
        traffic=traffic,
        stoplights=stoplights,
    )
    payload_results, best_path_cost, fastest_runtime_ms = _attach_comparison_metrics(
        results
    )
    return {
        "start": point_to_dict(start),
        "goal": point_to_dict(goal),
        "selected_algorithms": normalized_names,
        "best_path_cost": best_path_cost,
        "fastest_runtime_ms": fastest_runtime_ms,
        "results": payload_results,
    }
