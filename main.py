from pathlib import Path
import argparse
import random
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from traversal import (
    GridMap,
    Point,
    find_path,
    list_algorithms,
    run_algorithms,
)
from traversal.ui import launch_demo_ui


def _path_exists(grid_map: GridMap, start: Point, goal: Point) -> bool:
    queue = [start]
    visited = {start}

    while queue:
        current = queue.pop(0)
        if current == goal:
            return True

        for neighbor in grid_map.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False


def build_demo_layout(
    rows: int = 30,
    cols: int = 40,
    density: float = 0.3,
    attempts: int = 80,
) -> tuple[list[list[int]], Point, Point]:
    for _attempt in range(attempts):
        grid = [
            [0 if random.random() < density else 1 for _col in range(cols)]
            for _row in range(rows)
        ]
        start = Point(random.randrange(rows), 0)
        goal = Point(random.randrange(rows), cols - 1)
        grid[start.row][start.col] = 1
        grid[goal.row][goal.col] = 1

        grid_map = GridMap(grid)
        if _path_exists(grid_map, start, goal):
            return grid, start, goal

    fallback_grid = [[1 for _col in range(cols)] for _row in range(rows)]
    fallback_start = Point(rows // 4, 0)
    fallback_goal = Point((rows * 3) // 4, cols - 1)
    return fallback_grid, fallback_start, fallback_goal


def run_cli_demo() -> None:
    run_cli_demo_with_algorithms(["astar"])


def format_results_table(results: list[dict[str, object]]) -> str:
    headers = [
        "algorithm",
        "path_found",
        "moves",
        "runtime_ms",
        "visited_count",
        "expanded_count",
    ]
    rows = [[str(result[header]) for header in headers] for result in results]
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def build_row(values: list[str]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        )

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join(
        [
            build_row(headers),
            separator,
            *(build_row(row) for row in rows),
        ]
    )


def run_cli_demo_with_algorithms(algorithms: str | list[str]) -> None:
    grid, start, goal = build_demo_layout()
    grid_map = GridMap(grid)

    results = run_algorithms(algorithms, grid_map, start, goal)
    path = results[0].path if results else find_path(grid_map, start, goal)

    print("Grid legend: A=start, B=goal, *=path, .=road, #=blocked")
    print()
    print(grid_map.render(path=path, start=start, goal=goal))
    print()
    print("Algorithm comparison:")
    print(
        format_results_table(
            [
                {
                    "algorithm": result.algorithm_name,
                    "path_found": result.path_found,
                    "moves": result.moves,
                    "runtime_ms": result.runtime_ms,
                    "visited_count": result.visited_count,
                    "expanded_count": result.expanded_count,
                }
                for result in results
            ]
        )
    )
    print()

    if path:
        print("Path found:")
        print(" -> ".join(f"({point.row}, {point.col})" for point in path))
        print(f"Total moves: {len(path) - 1}")
    else:
        print("No path found between A and B.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid traversal demo.")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the text-based demo instead of the simple UI.",
    )
    parser.add_argument(
        "--algorithm",
        action="append",
        help=(
            "Algorithm to run in CLI mode. Repeat this flag to compare multiple "
            f"algorithms. Available: {', '.join(list_algorithms())}, or use 'all'."
        ),
    )
    args = parser.parse_args()

    if args.cli:
        selected_algorithms: str | list[str]
        if not args.algorithm:
            selected_algorithms = ["astar"]
        elif len(args.algorithm) == 1 and args.algorithm[0].strip().lower() == "all":
            selected_algorithms = "all"
        else:
            selected_algorithms = args.algorithm
        run_cli_demo_with_algorithms(selected_algorithms)
        return

    demo_grid, start, goal = build_demo_layout()
    output_path = launch_demo_ui(demo_grid, start, goal)
    print(f"UI generated at: {output_path}")
    print("Open that HTML file in your browser to view the demo.")


if __name__ == "__main__":
    main()
