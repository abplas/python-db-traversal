from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Point:
    row: int
    col: int


TrafficMap = dict[str, list[list[float]]]


class GridMap:
    """A grid where 0 is blocked and 1 is traversable road.

    Traffic is optional and direction-based. A movement can be slower when
    traveling north than when traveling east, even from the same cell.
    """

    def __init__(self, grid: list[list[int]], traffic: TrafficMap | None = None) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must contain at least one row and one column.")

        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("Grid must be rectangular.")
        if traffic is not None:
            self._validate_traffic(traffic, len(grid), width)

        self.grid = grid
        self.traffic = traffic or self._neutral_traffic(len(grid), width)
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

    def movement_cost(self, current: Point, neighbor: Point) -> float:
        direction = self.direction_between(current, neighbor)
        return float(self.traffic[direction][current.row][current.col])

    def traversable_count(self) -> int:
        return sum(cell == 1 for row in self.grid for cell in row)

    def directed_edge_count(self) -> int:
        return sum(
            len(self.neighbors(Point(row, col)))
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == 1
        )

    @staticmethod
    def direction_between(current: Point, neighbor: Point) -> str:
        row_delta = neighbor.row - current.row
        col_delta = neighbor.col - current.col

        if row_delta == -1 and col_delta == 0:
            return "north"
        if row_delta == 1 and col_delta == 0:
            return "south"
        if row_delta == 0 and col_delta == 1:
            return "east"
        if row_delta == 0 and col_delta == -1:
            return "west"

        raise ValueError("Traffic cost only supports non-diagonal neighboring points.")

    @staticmethod
    def _neutral_traffic(rows: int, cols: int) -> TrafficMap:
        return {
            direction: [[1.0 for _col in range(cols)] for _row in range(rows)]
            for direction in ("north", "south", "east", "west")
        }

    @staticmethod
    def _validate_traffic(traffic: TrafficMap, rows: int, cols: int) -> None:
        required_directions = {"north", "south", "east", "west"}
        missing = required_directions - set(traffic)
        if missing:
            raise ValueError(f"Traffic data is missing directions: {', '.join(sorted(missing))}.")

        for direction in required_directions:
            direction_grid = traffic[direction]
            if len(direction_grid) != rows or any(len(row) != cols for row in direction_grid):
                raise ValueError("Traffic grids must match the road grid dimensions.")
            if any(value < 1 for row in direction_grid for value in row):
                raise ValueError("Traffic multipliers must be greater than or equal to 1.")

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
