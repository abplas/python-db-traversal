from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from traversal import GridMap, Point, find_path
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
    grid_map = GridMap(build_demo_grid())
    start = Point(0, 0)
    goal = Point(4, 6)

    path = find_path(grid_map, start, goal)

    print("Grid legend: A=start, B=goal, *=path, .=road, #=blocked")
    print()
    print(grid_map.render(path=path, start=start, goal=goal))
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
    args = parser.parse_args()

    if args.cli:
        run_cli_demo()
        return

    output_path = launch_demo_ui(build_demo_grid(), Point(0, 0), Point(4, 6))
    print(f"UI generated at: {output_path}")
    print("Open that HTML file in your browser to view the demo.")


if __name__ == "__main__":
    main()
