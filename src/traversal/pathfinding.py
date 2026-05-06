from __future__ import annotations

from heapq import heappop, heappush

from traversal.grid import GridMap, Point


def manhattan_distance(a: Point, b: Point) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def reconstruct_path(came_from: dict[Point, Point], current: Point) -> list[Point]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def find_path(grid_map: GridMap, start: Point, goal: Point) -> list[Point]:
    """Find a non-diagonal path using A* with Manhattan distance."""
    if not grid_map.is_road(start):
        raise ValueError("Start point must be on a traversable road cell.")
    if not grid_map.is_road(goal):
        raise ValueError("Goal point must be on a traversable road cell.")

    frontier: list[tuple[int, Point]] = []
    heappush(frontier, (0, start))

    came_from: dict[Point, Point] = {}
    cost_so_far: dict[Point, int] = {start: 0}

    while frontier:
        _, current = heappop(frontier)

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in grid_map.neighbors(current):
            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + manhattan_distance(neighbor, goal)
                heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    return []
