# Python DB Traversal

This project models a road network as a grid-based graph and finds paths between two points using pathfinding algorithms.

The project currently supports:

- A* pathfinding using Manhattan distance
- Dijkstra’s algorithm
- Running one selected algorithm
- Running multiple selected algorithms
- Running all registered algorithms
- Comparing algorithm results by moves, runtime, visited nodes, and expanded nodes
- A FastAPI backend for running algorithms through HTTP
- An interactive HTML demo that calls the backend and displays algorithm comparison results

Supabase/PostgreSQL integration is planned, but the project does not save algorithm results to the database yet.

---

## Concept

- Each traversable grid cell is a node.
- Each road connection between neighboring cells is an edge.
- Movement is limited to up, down, left, and right.
- No diagonal movement is allowed.
- A* uses Manhattan distance as its heuristic.
- Dijkstra uses uniform movement cost.
- Blocked cells cannot be crossed.

This makes the project a good fit for city-block style traversal where roads behave like a rectangular grid.

---

## Project Structure

- `main.py`: main entry point for the CLI demo and HTML demo generation
- `src/traversal/grid.py`: grid and node modeling
- `src/traversal/pathfinding.py`: A*, Dijkstra, and pathfinding helpers
- `src/traversal/models.py`: shared `PathfindingResult` result model
- `src/traversal/runner.py`: algorithm registry and API-style runner functions
- `src/traversal/api.py`: FastAPI backend endpoints
- `src/traversal/serialization.py`: helper functions for future Supabase/PostgreSQL row formatting
- `src/traversal/ui.py`: generates the interactive HTML demo
- `tests/test_pathfinding.py`: pathfinding and algorithm runner tests
- `tests/test_api.py`: FastAPI endpoint tests
- `tests/test_ui.py`: HTML demo generation tests
- `demo_output/traversal_demo.html`: generated demo file

---

# Setup Instructions

## 1. Pull or Clone the Project

If you already have the project cloned, run:

```bash
git pull
```

If you are cloning the project for the first time, run:

```bash
git clone <your-repo-url>
cd python-db-traversal
```

Make sure you are inside the folder that contains:

```text
main.py
src/
tests/
pyproject.toml
demo_output/
```

---

## 2. Check Python Version

Run:

```bash
python3 --version
```

Use Python 3.10 or newer.

---

## 3. Install Dependencies

Dependencies are listed in `pyproject.toml`, but they are not installed automatically when you pull the repo.

From the project root, run:

```bash
python3 -m pip install -e .
```

If you also want test dependencies, run:

```bash
python3 -m pip install -e ".[test]"
```

If that does not work, manually install the required packages:

```bash
python3 -m pip install fastapi uvicorn httpx
```

---

## 4. Run Tests

Before running the app, check that everything works:

```bash
python3 -m unittest discover -s tests
```

Expected result:

```text
OK
```

The exact number of tests may change as more tests are added.

---

# Running the Application

The browser demo requires two terminals:

```text
Terminal 1: FastAPI backend
Terminal 2: HTML demo server
```

---

## Terminal 1: Start the FastAPI Backend

From the project root, run:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

You should see something like:

```text
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal running.

To confirm the backend is working, open this in your browser:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

You can also open the API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Terminal 2: Generate and Serve the HTML Demo

Open a second terminal.

From the project root, generate the demo:

```bash
python3 main.py
```

This creates:

```text
demo_output/traversal_demo.html
```

Then start a local HTML server:

```bash
python3 -m http.server 8080
```

Leave this terminal running.

Open the demo in your browser:

```text
http://127.0.0.1:8080/demo_output/traversal_demo.html
```

Use this local server URL instead of double-clicking the HTML file.

---

# Using the Browser Demo

After both terminals are running:

1. Open the demo page.
2. Select `A*`, `Dijkstra`, or `Run all`.
3. Click `Run selected algorithms`.
4. View the route on the grid.
5. View the algorithm comparison table.

The comparison table shows:

- algorithm name
- whether a path was found
- moves
- runtime in milliseconds
- visited nodes
- expanded nodes
- frontier pushes
- path cost

Small grids may show `runtime_ms` as `0`. This is normal because the algorithms finish in less than one millisecond.

---

# Expected Backend Output

When the browser successfully calls the backend, the FastAPI terminal should show something like:

```text
OPTIONS /run-pathfinding HTTP/1.1 200 OK
POST /run-pathfinding HTTP/1.1 200 OK
```

The `OPTIONS` request is normal. It is the browser checking CORS before sending the real request.

---

# Running the Console Demo

The CLI version works without opening the browser.

Run the default CLI demo:

```bash
python3 main.py --cli
```

Run A* only:

```bash
python3 main.py --cli --algorithm astar
```

Run A* and Dijkstra:

```bash
python3 main.py --cli --algorithm astar --algorithm dijkstra
```

Run all registered algorithms:

```bash
python3 main.py --cli --algorithm all
```

The CLI prints:

- the grid
- the selected route
- an algorithm comparison table
- the final path
- total moves

---

# API Usage

The main backend endpoint is:

```text
POST /run-pathfinding
```

Example request:

```json
{
  "grid": [
    [1, 1, 1, 1],
    [1, 0, 0, 1],
    [1, 1, 1, 1]
  ],
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 3 },
  "algorithms": ["astar", "dijkstra"]
}
```

You can also run all registered algorithms:

```json
{
  "grid": [
    [1, 1, 1, 1],
    [1, 0, 0, 1],
    [1, 1, 1, 1]
  ],
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 3 },
  "algorithms": "all"
}
```

Example response shape:

```json
{
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 3 },
  "selected_algorithms": ["astar", "dijkstra"],
  "results": [
    {
      "algorithm_name": "astar",
      "path": [
        { "row": 0, "col": 0 },
        { "row": 0, "col": 1 }
      ],
      "path_found": true,
      "path_cost": 5,
      "path_length_nodes": 6,
      "moves": 5,
      "runtime_ms": 0,
      "visited_count": 8,
      "expanded_count": 6,
      "frontier_pushes": 8,
      "metadata": {
        "heuristic": "manhattan"
      }
    }
  ]
}
```

---

# Current Algorithms

## A*

A* uses Manhattan distance to guide the search toward the goal.

It is usually more efficient than Dijkstra on this grid because it uses a heuristic.

Registered name:

```text
astar
```

---

## Dijkstra

Dijkstra explores paths based on cost from the start node.

Since the current grid uses uniform movement cost, Dijkstra should find the same shortest path length as A* but may visit more nodes.

Registered name:

```text
dijkstra
```

---

# Common Issues and Fixes

## Browser Says It Cannot Reach FastAPI

Make sure the backend is running:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Then refresh the demo page.

---

## `uvicorn` Is Not Found

Install dependencies:

```bash
python3 -m pip install -e .
```

Or manually install:

```bash
python3 -m pip install fastapi uvicorn
```

---

## `ModuleNotFoundError: No module named 'traversal'`

Use:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Do not run Uvicorn without `PYTHONPATH=src` unless your environment is already configured.

---

## `Address Already in Use`

Port `8000` is already being used.

Stop the old FastAPI server with:

```text
Control + C
```

Then restart:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

For now, use port `8000` because the HTML demo expects the backend at:

```text
http://127.0.0.1:8000/run-pathfinding
```

---

## `OPTIONS /run-pathfinding 405 Method Not Allowed`

This means the CORS fix is missing or the server is running old code.

Fix:

```bash
git pull
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Expected output after the fix:

```text
OPTIONS /run-pathfinding HTTP/1.1 200 OK
POST /run-pathfinding HTTP/1.1 200 OK
```

---

## `runtime_ms` Shows 0

This is normal on small grids.

The algorithms are running so quickly that the measured time is less than one millisecond.

Larger maps should show larger runtime values.

---

# Current Limitations

- Supabase/PostgreSQL is not connected yet.
- Algorithm results are not saved to the database yet.
- The current grid is mostly unweighted.
- Bellman-Ford is not implemented yet.
- The HTML demo currently draws the first successful returned path when multiple algorithms are run.
- Future work can draw different algorithm paths in different colors.

---

# Planned Supabase/PostgreSQL Integration

The project already includes helper code for shaping future database rows, but it does not insert records yet.

Planned database flow:

1. Load a map from Supabase.
2. Load nodes and edges for that map.
3. Convert database nodes into grid points.
4. Run selected algorithms.
5. Insert one row per algorithm into `algorithm_runs`.
6. Insert each route step into `run_path_nodes`.

Important future mapping:

```text
Point(row, col) -> nodes.id
```

The `nodes` table should include `row` and `col` columns so Python grid points can map cleanly to Supabase node UUIDs.

---

# Summary

The project now supports a full local pathfinding comparison flow:

```text
HTML demo
-> FastAPI backend
-> Python algorithm runner
-> A* / Dijkstra
-> JSON response
-> browser comparison table
```

The next major feature is Supabase persistence for saving algorithm runs and route paths.

---

# Commit the README Update

After editing `README.md`, commit and push it:

```bash
git add README.md
git commit -m "Update README with setup and run instructions"
git push
```