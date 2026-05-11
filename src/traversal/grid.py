from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, order=True)
class Point:
    row: int
    col: int


TrafficMap = dict[str, list[list[float]]]
StoplightMap = dict[tuple[int, int], "Stoplight"]


@dataclass(slots=True)
class Stoplight:
    row: int
    col: int
    average_wait_seconds: float
    light_cycle_seconds: float | None = None
    has_stoplight: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class GridMap:
    """A grid where 0 is blocked and 1 is traversable road.

    Traffic is optional and direction-based. A movement can be slower when
    traveling north than when traveling east, even from the same cell.
    Stoplights are optional and add delay when entering an intersection.
    """

    def __init__(
        self,
        grid: list[list[int]],
        traffic: TrafficMap | None = None,
        stoplights: list[Stoplight] | None = None,
    ) -> None:
        if not grid or not grid[0]:
            raise ValueError("Grid must contain at least one row and one column.")

        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("Grid must be rectangular.")
        if traffic is not None:
            self._validate_traffic(traffic, len(grid), width)

        self.grid = grid
        self.traffic = traffic or self._neutral_traffic(len(grid), width)
        self.stoplights = self._normalize_stoplights(stoplights or [], len(grid), width)
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

    def traffic_cost(self, current: Point, neighbor: Point) -> float:
        direction = self.direction_between(current, neighbor)
        return float(self.traffic[direction][current.row][current.col])

    def movement_cost_components(self, current: Point, neighbor: Point) -> dict[str, float]:
        traffic_cost = self.traffic_cost(current, neighbor)
        stoplight_delay = self.stoplight_delay(neighbor)
        return {
            "base_movement_cost": 1.0,
            "traffic_cost": traffic_cost,
            "traffic_delay_cost": max(traffic_cost - 1.0, 0.0),
            "stoplight_delay": stoplight_delay,
            "total_cost": traffic_cost + stoplight_delay,
        }

    def movement_cost(self, current: Point, neighbor: Point) -> float:
        return self.movement_cost_components(current, neighbor)["total_cost"]

    def stoplight_at(self, point: Point) -> Stoplight | None:
        return self.stoplights.get((point.row, point.col))

    def stoplight_delay(self, point: Point) -> float:
        stoplight = self.stoplight_at(point)
        if stoplight is None or not stoplight.has_stoplight:
            return 0.0
        return float(stoplight.average_wait_seconds)

    def traversable_count(self) -> int:
        return sum(cell == 1 for row in self.grid for cell in row)

    def directed_edge_count(self) -> int:
        return sum(
            len(self.neighbors(Point(row, col)))
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == 1
        )

    def stoplight_count(self) -> int:
        return sum(1 for stoplight in self.stoplights.values() if stoplight.has_stoplight)

    def has_stoplights(self) -> bool:
        return self.stoplight_count() > 0

    def is_four_way_intersection(self, point: Point) -> bool:
        return self.is_road(point) and len(self.neighbors(point)) == 4

    def find_four_way_intersections(
        self,
        *,
        exclude: set[Point] | None = None,
    ) -> list[Point]:
        excluded = exclude or set()
        intersections: list[Point] = []
        for row in range(self.rows):
            for col in range(self.cols):
                point = Point(row, col)
                if point in excluded:
                    continue
                if self.is_four_way_intersection(point):
                    intersections.append(point)
        return intersections

    def has_directional_traffic(self) -> bool:
        return any(
            value != 1.0
            for direction in ("north", "south", "east", "west")
            for row in self.traffic[direction]
            for value in row
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
    def _normalize_stoplights(
        stoplights: list[Stoplight], rows: int, cols: int
    ) -> StoplightMap:
        normalized: StoplightMap = {}
        for stoplight in stoplights:
            point = Point(stoplight.row, stoplight.col)
            if not (0 <= point.row < rows and 0 <= point.col < cols):
                raise ValueError(
                    f"Stoplight at ({point.row}, {point.col}) must be within grid bounds."
                )
            if stoplight.average_wait_seconds < 0:
                raise ValueError("Stoplight average wait must be greater than or equal to 0.")
            if (
                stoplight.light_cycle_seconds is not None
                and stoplight.light_cycle_seconds <= 0
            ):
                raise ValueError("Stoplight cycle seconds must be greater than 0.")
            normalized[(point.row, point.col)] = stoplight
        return normalized

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
