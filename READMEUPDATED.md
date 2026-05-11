# Python DB Traversal

Python DB Traversal is a small-scale routing and pathfinding project. It models a city-style road network as a Manhattan grid and compares multiple pathfinding algorithms across roadblocks, traffic weights, and stoplight delays.

The goal is to make a simplified version of a routing system like Google Maps while also demonstrating database concepts for a database class.

---

## Current Project Status

The project currently supports:

- Manhattan-style grid routing
- Roadblocks / blocked cells
- Directional traffic weights
- Stoplight delays at intersections
- Multiple pathfinding algorithms
- Algorithm comparison by runtime, cost, visited nodes, expanded nodes, and reliability
- FastAPI backend
- Generated HTML/JavaScript browser demo
- CLI demo
- SQL planning files for future Supabase/PostgreSQL integration

The project does **not** fully connect to Supabase/PostgreSQL yet. SQL files and serialization helpers exist, but the actual database persistence layer still needs to be added.

---

## Current Algorithms

The app currently supports these algorithms:

| Algorithm | Registered Name | Weighted? | Optimal? | Purpose |
|---|---|---:|---:|---|
| BFS | `bfs` | No | Only for fewest moves | Simple unweighted baseline |
| Dijkstra | `dijkstra` | Yes | Yes | Reliable weighted shortest path |
| A* | `astar` | Yes | Yes, with valid heuristic | Faster guided weighted search |
| Greedy Best-First | `greedy_best_first` | Partially / heuristic-only | No | Fast but less reliable |
| Weighted A* | `weighted_astar` | Yes | Not always | Speed vs route-quality tradeoff |

The main comparison idea is:

- **BFS** may find the fewest moves, but not the fastest route when traffic and stoplights exist.
- **Dijkstra** is reliable and optimal for weighted costs, but may explore more nodes.
- **A\*** is usually optimal and faster than Dijkstra because it uses Manhattan distance.
- **Greedy Best-First** may be fast, but can choose worse routes.
- **Weighted A\*** may be faster than normal A*, but may sacrifice optimality.

---

## Cost Model

Every final route is evaluated using the same weighted cost model:

```text
movement cost =
base movement cost
+ directional traffic cost
+ stoplight delay at the destination/intersection node
```

This means every algorithm can be compared fairly, even if the algorithm itself searches differently.

For example:

```text
base movement cost = 1
traffic delay = 4
stoplight delay = 15

movement cost = 20
```

Important behavior:

- Roadblocks cannot be crossed.
- Traffic increases the cost of moving between cells.
- Stoplights add delay when the path enters a stoplight intersection.
- Stoplights are intended to appear on valid four-way intersections.
- The start and goal should not randomly receive stoplights.

---

## Stoplights

Stoplights are modeled as intersection/node delays.

A stoplight can include:

- row
- col
- average wait seconds
- optional light cycle seconds
- metadata

The app can randomly generate stoplights on four-way intersections.

A four-way intersection is a traversable cell where all four neighbors are also traversable:

```text
up = road
down = road
left = road
right = road
```

This keeps the grid in a Manhattan style while making it feel more like a small street map.

---

## Project Structure

```text
main.py
src/
  traversal/
    __init__.py
    api.py
    grid.py
    models.py
    pathfinding.py
    runner.py
    serialization.py
    ui.py
tests/
  test_api.py
  test_pathfinding.py
  test_ui.py
sql/
  schema_extensions.sql
  indexes.sql
  views.sql
  functions.sql
  explain_notes.sql
demo_output/
  traversal_demo.html
README.md
pyproject.toml
```

### Important Files

| File | Purpose |
|---|---|
| `main.py` | CLI entry point and HTML demo generator |
| `src/traversal/grid.py` | Grid model, nodes, roadblocks, traffic, stoplights, movement cost |
| `src/traversal/pathfinding.py` | BFS, Dijkstra, A*, Greedy Best-First, Weighted A*, cost evaluation |
| `src/traversal/models.py` | Shared `PathfindingResult` model |
| `src/traversal/runner.py` | Algorithm registry and runner functions |
| `src/traversal/api.py` | FastAPI backend endpoints |
| `src/traversal/serialization.py` | Converts algorithm results into database-shaped rows |
| `src/traversal/ui.py` | Generates the browser demo HTML/JS |
| `sql/schema_extensions.sql` | Database schema additions such as route experiments |
| `sql/indexes.sql` | Database indexes for performance |
| `sql/views.sql` | SQL views for algorithm comparison |
| `sql/functions.sql` | Future database functions/RPC for atomic saves |
| `sql/explain_notes.sql` | Example `EXPLAIN ANALYZE` queries |
| `tests/` | Unit tests for algorithms, API, UI, and serialization |

---

# Setup Instructions

## 1. Clone or Pull the Project

If cloning for the first time:

```bash
git clone <your-repo-url>
cd python-db-traversal
```

If the project is already cloned:

```bash
git pull
```

Make sure you are in the folder that contains:

```text
main.py
src/
tests/
sql/
pyproject.toml
```

---

## 2. Check Python Version

Run:

```bash
python3 --version
```

Use Python 3.10 or newer.

Python 3.12 is recommended if everyone in the group wants to standardize on the same version.

---

## 3. Install Dependencies

Dependencies are listed in `pyproject.toml`, but they are **not installed automatically** when someone pulls the repo.

From the project root, run:

```bash
python3 -m pip install -e .
```

If test dependencies are needed, run:

```bash
python3 -m pip install -e ".[test]"
```

If that does not work, manually install the main packages:

```bash
python3 -m pip install fastapi uvicorn httpx
```

Supabase dependencies are not fully required yet unless working on database integration.

Later, for Supabase integration, install:

```bash
python3 -m pip install supabase python-dotenv
```

---

## 4. Run Tests

Run:

```bash
python3 -m unittest discover -s tests
```

Expected result:

```text
OK
```

The exact number of tests may change as more features are added.

---

# Running the Application

The browser demo uses two terminals:

```text
Terminal 1: FastAPI backend
Terminal 2: HTML demo server
```

---

## Terminal 1: Start FastAPI Backend

From the project root, run:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

You should see something like:

```text
Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal running.

Check the backend:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Terminal 2: Generate and Serve the HTML Demo

In a second terminal, from the project root, run:

```bash
python3 main.py
```

This generates:

```text
demo_output/traversal_demo.html
```

Then serve the project locally:

```bash
python3 -m http.server 8080
```

Open the demo:

```text
http://127.0.0.1:8080/demo_output/traversal_demo.html
```

Use this local server URL instead of double-clicking the HTML file.

---

# Using the Browser Demo

After both terminals are running:

1. Open the demo page.
2. Generate or edit the grid.
3. Add roadblocks if needed.
4. Enable or randomize traffic if available.
5. Enable or randomize stoplights.
6. Select algorithms:
   - BFS
   - Dijkstra
   - A*
   - Greedy Best-First
   - Weighted A*
   - Run all
7. Click `Run selected algorithms`.
8. View the route overlays.
9. View the algorithm comparison table.

The comparison table shows values like:

- algorithm
- category
- path found
- moves
- total cost
- runtime in milliseconds
- visited nodes
- expanded nodes
- stoplights crossed
- stoplight delay
- traffic cost
- reliability / tradeoff label

Small grids may show `runtime_ms` as `0` because the algorithms finish in less than one millisecond.

---

# Expected Backend Output

When the browser successfully calls the backend, the FastAPI terminal should show something like:

```text
OPTIONS /run-pathfinding HTTP/1.1 200 OK
POST /run-pathfinding HTTP/1.1 200 OK
```

The `OPTIONS` request is normal. It is the browser checking CORS before sending the real `POST` request.

---

# Running the CLI Demo

The CLI version works without the browser.

Run the default CLI:

```bash
python3 main.py --cli
```

Run A* and Dijkstra:

```bash
python3 main.py --cli --algorithm astar --algorithm dijkstra
```

Run all algorithms:

```bash
python3 main.py --cli --algorithm all
```

Run one specific algorithm:

```bash
python3 main.py --cli --algorithm bfs
python3 main.py --cli --algorithm dijkstra
python3 main.py --cli --algorithm astar
python3 main.py --cli --algorithm greedy_best_first
python3 main.py --cli --algorithm weighted_astar
```

The CLI prints:

- grid
- selected route
- algorithm comparison table
- final path
- total moves
- total cost

---

# API Usage

## Health Check

```text
GET /health
```

Expected:

```json
{
  "status": "ok"
}
```

---

## List Algorithms

```text
GET /algorithms
```

This returns the currently registered algorithms.

There may also be an algorithm metadata endpoint depending on the current implementation.

---

## Run Pathfinding

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
  "algorithms": ["bfs", "dijkstra", "astar", "greedy_best_first", "weighted_astar"],
  "stoplights": [
    {
      "row": 1,
      "col": 0,
      "average_wait_seconds": 10
    }
  ]
}
```

Run all algorithms:

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
  "selected_algorithms": ["bfs", "dijkstra", "astar"],
  "best_path_cost": 7.0,
  "fastest_runtime_ms": 0,
  "results": [
    {
      "algorithm_name": "astar",
      "path": [
        { "row": 0, "col": 0 },
        { "row": 0, "col": 1 },
        { "row": 0, "col": 2 }
      ],
      "path_found": true,
      "path_cost": 7.0,
      "path_length_nodes": 6,
      "moves": 5,
      "runtime_ms": 0,
      "visited_count": 8,
      "expanded_count": 6,
      "frontier_pushes": 8,
      "cumulative_costs": [0.0, 1.0, 2.0, 4.0, 6.0, 7.0],
      "metadata": {
        "heuristic": "manhattan",
        "supports_weights": true,
        "uses_stoplights": true,
        "uses_directional_traffic": true,
        "base_movement_cost_total": 5.0,
        "traffic_cost_total": 0.0,
        "stoplight_delay_total": 2.0,
        "stoplights_crossed": 1,
        "reliability_category": "reliable",
        "optimality": "optimal_with_admissible_heuristic",
        "tradeoff": "balanced speed and reliability"
      },
      "cost_ratio_to_best": 1.0,
      "comparison_label": "optimal or near optimal"
    }
  ]
}
```

---

# Database Plan

The database work is the main unfinished part of the project.

The goal is to store routing experiments and algorithm results in Supabase/PostgreSQL.

The database should eventually answer questions like:

- Which algorithm was fastest?
- Which algorithm found the lowest-cost route?
- Which algorithm visited the fewest nodes?
- How much did stoplights affect each route?
- How much did traffic affect each route?
- Which algorithms are fast but less reliable?
- Which algorithms are reliable but slower?

---

## Planned Database Tables

The project is designed around these tables:

| Table | Purpose |
|---|---|
| `maps` | Stores each map or grid |
| `nodes` | Stores intersections/grid cells |
| `edges` | Stores roads between nodes |
| `traffic_signals` | Stores stoplights at intersections |
| `route_experiments` | Groups one map/start/goal/traffic/stoplight setup |
| `algorithm_runs` | Stores one result per algorithm |
| `run_path_nodes` | Stores the exact path for each algorithm run |

---

## Why `route_experiments` Matters

One click of `Run all` should create one experiment.

Example:

```text
Experiment:
map = demo map
start = node A
goal = node B
traffic = enabled
stoplights = enabled

Algorithm runs:
BFS
Dijkstra
A*
Greedy Best-First
Weighted A*
```

This lets the database compare algorithms fairly because they all ran on the same map, start, goal, traffic, and stoplight setup.

---

## Database Concepts Used

This project is meant to demonstrate several database concepts.

### 1. Normalization

The data is split into separate tables:

```text
maps
nodes
edges
traffic_signals
route_experiments
algorithm_runs
run_path_nodes
```

Each table has one job.

---

### 2. Foreign Keys

Foreign keys connect data safely.

Examples:

```text
nodes.map_id -> maps.id
edges.from_node_id -> nodes.id
traffic_signals.node_id -> nodes.id
algorithm_runs.experiment_id -> route_experiments.id
run_path_nodes.run_id -> algorithm_runs.id
```

This prevents invalid records from being saved.

---

### 3. Constraints

Constraints should protect data quality.

Examples:

```text
runtime_ms >= 0
visited_count >= 0
distance_meters > 0
average_wait_seconds >= 0
step_index >= 0
```

---

### 4. Indexes

Indexes speed up common queries.

Useful indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_edges_from_node_id
ON public.edges(from_node_id);

CREATE INDEX IF NOT EXISTS idx_edges_to_node_id
ON public.edges(to_node_id);

CREATE INDEX IF NOT EXISTS idx_algorithm_runs_experiment_id
ON public.algorithm_runs(experiment_id);

CREATE INDEX IF NOT EXISTS idx_algorithm_runs_map_algorithm_created
ON public.algorithm_runs(map_id, algorithm, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_run_path_nodes_run_step
ON public.run_path_nodes(run_id, step_index);

CREATE INDEX IF NOT EXISTS idx_traffic_signals_map_node
ON public.traffic_signals(map_id, node_id);
```

The most important node lookup is:

```text
Point(row, col) -> nodes.id
```

So `nodes` should have `row` and `col` columns and a unique constraint like:

```sql
ALTER TABLE public.nodes
ADD CONSTRAINT nodes_map_row_col_unique UNIQUE (map_id, row, col);
```

---

### 5. Transactions

Saving one full experiment requires multiple inserts:

```text
route_experiments
algorithm_runs
run_path_nodes
```

These should be saved atomically.

That means:

```text
If any insert fails, the whole save should roll back.
```

This prevents half-saved runs.

---

### 6. Views

SQL views can summarize algorithm performance.

Useful view ideas:

```text
algorithm_performance_summary
algorithm_comparison_summary
algorithm_run_rankings
```

These can calculate:

- average runtime
- average cost
- best cost
- fastest algorithm
- cost ratio to best
- speed label
- reliability label

---

### 7. Window Functions

Window functions can rank algorithms inside the same experiment.

Example:

```text
best cost per experiment
fastest runtime per experiment
cost ratio to best route
speed ranking
```

This helps label algorithms as:

```text
highly reliable
near optimal
less reliable
fastest
fast
slower
```

---

### 8. EXPLAIN ANALYZE

`EXPLAIN ANALYZE` should be used to compare query performance before and after indexes.

Example:

```sql
EXPLAIN ANALYZE
SELECT *
FROM public.algorithm_runs
WHERE map_id = '<map-id>'
  AND algorithm = 'astar'
ORDER BY created_at DESC;
```

This is useful for the final presentation because it shows how indexing changes database query performance.

---

# Current SQL Files

The project includes SQL planning files:

| File | Purpose |
|---|---|
| `sql/schema_extensions.sql` | Adds route experiments and related schema changes |
| `sql/indexes.sql` | Adds useful indexes |
| `sql/views.sql` | Adds performance and comparison views |
| `sql/functions.sql` | Plans future database function/RPC for atomic saves |
| `sql/explain_notes.sql` | Example `EXPLAIN ANALYZE` queries |

Before running SQL in Supabase, review each file and make sure it matches the live schema.

---

# Supabase Integration: Not Done Yet

The project does not fully connect to Supabase yet.

Still missing:

- real Supabase client
- environment variables
- `.env.example`
- repository/persistence layer
- database health check endpoint
- saving route experiments
- saving algorithm runs
- saving run path nodes
- UI option to save results to the database
- saved results page or summary display

---

# Next Supabase Steps

## Step 1: Add Environment Files

Create:

```text
.env.example
```

Example:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Create a local `.env` file for real keys:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-real-key
```

Do **not** commit `.env`.

Add this to `.gitignore`:

```gitignore
.env
```

---

## Step 2: Add Supabase Dependencies

Install:

```bash
python3 -m pip install supabase python-dotenv
```

Then add these dependencies to `pyproject.toml`:

```text
supabase
python-dotenv
```

---

## Step 3: Add Supabase Client

Create:

```text
src/traversal/supabase_client.py
```

Its job should only be to create the Supabase client.

Example structure:

```python
import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def get_supabase_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)
```

Do not put Supabase code inside the pathfinding algorithms.

---

## Step 4: Add Repository Layer

Create:

```text
src/traversal/repository.py
```

This should handle database operations.

Possible functions:

```python
load_nodes_for_map(map_id)
load_edges_for_map(map_id)
load_traffic_signals_for_map(map_id)
build_point_to_node_id(map_id)
save_route_experiment(...)
save_algorithm_run(...)
save_run_path_nodes(...)
save_experiment_results(...)
```

Keep this separate from:

```text
pathfinding.py
runner.py
api.py
```

---

## Step 5: Add Database Health Endpoint

Add:

```text
GET /db-health
```

This should confirm:

```text
FastAPI is running
Supabase credentials work
database is reachable
```

---

## Step 6: Save One Full Experiment

When the user runs all algorithms, the save flow should eventually be:

```text
1. Create one route_experiments row
2. Save one algorithm_runs row per algorithm
3. Save path steps into run_path_nodes
4. Use weighted cumulative_costs from PathfindingResult
5. Return saved IDs to the API/UI
```

---

## Step 7: Use Transactions or RPC

The cleanest final version should save everything atomically.

Options:

```text
Option A: Python-managed transaction using direct PostgreSQL connection
Option B: Supabase PostgreSQL function/RPC
```

The SQL file `sql/functions.sql` is intended for this future atomic save behavior.

---

## Step 8: Add UI Save Option

Eventually add a UI checkbox or button like:

```text
[ ] Save results to database
```

or:

```text
Save this experiment
```

The API request could include:

```json
{
  "save": true,
  "map_id": "..."
}
```

---

## Step 9: Add Saved Results View

Add an endpoint or UI section to display saved results.

Possible endpoint:

```text
GET /experiments
GET /algorithm-summary
GET /experiments/{id}/results
```

This can read from the SQL views.

---

# Recommended Next Work Order

Follow this order:

```text
1. Update README.md and remove/ignore READMEUPDATED.md if no longer needed.
2. Clean .gitignore.
3. Run tests.
4. Test CLI with all algorithms.
5. Test browser UI with all algorithms.
6. Review SQL files.
7. Apply schema_extensions.sql in Supabase.
8. Apply indexes.sql in Supabase.
9. Apply views.sql in Supabase.
10. Add .env.example.
11. Add local .env.
12. Add Supabase dependencies.
13. Add supabase_client.py.
14. Add repository.py.
15. Add GET /db-health.
16. Add save route_experiment.
17. Add save algorithm_runs.
18. Add save run_path_nodes.
19. Add transaction/RPC save.
20. Add UI save option.
21. Add saved-results summary UI or API endpoint.
22. Add EXPLAIN ANALYZE results for final presentation.
```

---

# Common Issues

## Browser Cannot Reach FastAPI

Make sure the backend is running:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Then refresh the page.

---

## `uvicorn` Not Found

Install dependencies:

```bash
python3 -m pip install -e .
```

or:

```bash
python3 -m pip install fastapi uvicorn
```

---

## `ModuleNotFoundError: No module named 'traversal'`

Use:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

---

## `OPTIONS /run-pathfinding 405 Method Not Allowed`

This means CORS is not configured or the server is running old code.

Pull the latest code and restart:

```bash
git pull
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Expected output:

```text
OPTIONS /run-pathfinding HTTP/1.1 200 OK
POST /run-pathfinding HTTP/1.1 200 OK
```

---

## `runtime_ms` Shows 0

This is normal on small grids.

The algorithms may complete in less than one millisecond.

Use larger maps to see larger runtime values.

---

## Supabase Key Accidentally Committed

Remove it immediately and rotate the key in Supabase.

Never commit:

```text
.env
SUPABASE_SERVICE_ROLE_KEY
real database passwords
```

---

# Current Limitations

- Supabase is not connected yet.
- Database persistence is not implemented yet.
- The browser fallback does not fully implement every backend algorithm.
- Runtime values can be 0 on very small maps.
- Generated/cache files may need cleanup.
- The app still uses a simplified grid, not real map coordinates.
- Bellman-Ford and K-shortest paths are not implemented yet.

---

# Future Algorithm Ideas

Possible later algorithms:

| Algorithm | Why Add It |
|---|---|
| Bellman-Ford | Educational comparison, handles negative weights, not needed for normal traffic |
| Bidirectional Dijkstra | Faster reliable search on larger graphs |
| Bidirectional A* | More advanced guided search |
| Yen’s K-Shortest Paths | Multiple route options like Google Maps |
| Floyd-Warshall | All-pairs shortest paths for very small maps |

Do not add these until Supabase persistence is working.

---

# Final Project Goal

The final project should show this complete flow:

```text
1. Generate a Manhattan-style road map.
2. Add roadblocks.
3. Add directional traffic.
4. Add stoplights at intersections.
5. Run BFS, Dijkstra, A*, Greedy Best-First, and Weighted A*.
6. Compare speed, cost, visited nodes, and reliability.
7. Save the experiment and results to Supabase/PostgreSQL.
8. Store the full path for each algorithm.
9. Use indexes to speed up lookups.
10. Use SQL views to rank algorithms.
11. Use EXPLAIN ANALYZE to show query performance changes.
```

The final project story:

```text
We built a simplified routing system inspired by Google Maps.
It compares multiple pathfinding algorithms on a Manhattan grid with roadblocks, traffic, and stoplights.
The backend tracks runtime, cost, visited nodes, expanded nodes, and route quality.
The database stores experiments, algorithm runs, and path nodes.
We use normalization, foreign keys, constraints, indexes, transactions, SQL views, and EXPLAIN ANALYZE to demonstrate database concepts.
```

---

# Repo Hygiene Notes

Make sure `.gitignore` includes:

```gitignore
__pycache__/
*.pyc
*.egg-info/
.env
.venv/
```

Decide as a group whether to track:

```text
demo_output/traversal_demo.html
```

It is generated by `python3 main.py`, so it can be ignored if the team wants cleaner commits.

---

# How to Commit README Changes

After replacing the old README:

```bash
git add README.md
git commit -m "Update README with current app status and database roadmap"
git push
```