from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Point:
    row: int
    col: int


class GridMap:
    """A grid where 0 is blocked and 1 is traversable road."""

    def __init__(self, grid: list[list[int]]) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must contain at least one row and one column.")

        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("Grid must be rectangular.")

        self.grid = grid
        self.rows = len(grid)
        self.cols = width

    def in_bounds(self, point: Point) -> bool:
        return 0 <= point.row < self.rows and 0 <= point.col < self.cols

    def is_road(self, point: Point) -> bool:
        return self.in_bounds(point) and self.grid[point.row][point.col] == 1

    def neighbors(self, point: Point) -> list[Point]:
        candidates = [
            Point(point.row - 1, point.col),
            Point(point.row + 1, point.col),
            Point(point.row, point.col - 1),
            Point(point.row, point.col + 1),
        ]
        return [candidate for candidate in candidates if self.is_road(candidate)]

    def render(
        self,
        path: list[Point] | None = None,
        start: Point | None = None,
        goal: Point | None = None,
    ) -> str:
        path_points = set(path or [])
        lines: list[str] = []

        for row in range(self.rows):
            symbols: list[str] = []
            for col in range(self.cols):
                point = Point(row, col)
                if point == start:
                    symbols.append("A")
                elif point == goal:
                    symbols.append("B")
                elif point in path_points:
                    symbols.append("*")
                elif self.grid[row][col] == 1:
                    symbols.append(".")
                else:
                    symbols.append("#")
            lines.append(" ".join(symbols))

        return "\n".join(lines)
