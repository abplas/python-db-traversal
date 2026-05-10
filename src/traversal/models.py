from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from traversal.grid import Point


def point_to_dict(point: Point) -> dict[str, int]:
    return {"row": point.row, "col": point.col}


@dataclass(slots=True)
class PathfindingResult:
    algorithm_name: str
    path: list[Point]
    path_found: bool
    path_cost: int | None
    path_length_nodes: int
    moves: int
    runtime_ms: int
    visited_count: int
    expanded_count: int
    frontier_pushes: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_name": self.algorithm_name,
            "path": [point_to_dict(point) for point in self.path],
            "path_found": self.path_found,
            "path_cost": self.path_cost,
            "path_length_nodes": self.path_length_nodes,
            "moves": self.moves,
            "runtime_ms": self.runtime_ms,
            "visited_count": self.visited_count,
            "expanded_count": self.expanded_count,
            "frontier_pushes": self.frontier_pushes,
            "metadata": self.metadata,
        }
