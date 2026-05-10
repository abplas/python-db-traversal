from pathlib import Path
import argparse
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


def build_demo_grid() -> list[list[int]]:
    return [
        [1, 1, 1, 1, 1, 0, 1],
        [0, 0, 1, 0, 1, 0, 1],
        [1, 1, 1, 0, 1, 1, 1],
        [1, 0, 0, 0, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1],
    ]


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
    grid_map = GridMap(build_demo_grid())
    start = Point(0, 0)
    goal = Point(4, 6)

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

    output_path = launch_demo_ui(build_demo_grid(), Point(0, 0), Point(4, 6))
    print(f"UI generated at: {output_path}")
    print("Open that HTML file in your browser to view the demo.")


if __name__ == "__main__":
    main()
