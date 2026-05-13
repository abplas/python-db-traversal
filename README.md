# Python DB Traversal

Python DB Traversal is a small-scale routing system inspired by Google Maps. It models a city-style road network as a Manhattan grid, lets users add roadblocks, directional traffic, and stoplight delays, runs multiple pathfinding algorithms, and can store/analyze results with Supabase/PostgreSQL.

The project is meant to connect algorithms to database concepts: the grid becomes graph data, algorithms produce measurable run data, and saved results can be queried, indexed, compared, and reconstructed later.

## What The Project Does

- Generates a Manhattan-style road network as a grid.
- Treats traversable cells as nodes and valid movements as edges.
- Supports roadblocks, directional traffic weights, and stoplight delays.
- Runs BFS, DFS, Dijkstra, A*, Greedy Best-First, and Weighted A*.
- Compares moves, total cost, runtime, visited nodes, expanded nodes, and reliability/tradeoff labels.
- Provides a FastAPI backend and generated browser UI.
- Saves maps, graph nodes/edges, route experiments, algorithm runs, and path steps in Supabase/PostgreSQL.
- Includes SQL files for schema extensions, stoplights, indexes, views, functions, and EXPLAIN examples.

## Requirements

- Python 3.10+
- pip
- Supabase account, if you want database persistence

## Project Structure

```text
main.py
src/
  traversal/
    api.py
    grid.py
    models.py
    pathfinding.py
    repository.py
    runner.py
    serialization.py
    supabase_client.py
    ui.py
sql/
  schema_extensions.sql
  stoplights.sql
  indexes.sql
  views.sql
  functions.sql
  explain_notes.sql
tests/
demo_output/
  traversal_demo.html
README.md
pyproject.toml
```

Important files:

| File | Purpose |
|---|---|
| `main.py` | CLI entry point and HTML demo generator |
| `src/traversal/grid.py` | Grid model, roadblocks, traffic, stoplights, and movement costs |
| `src/traversal/pathfinding.py` | BFS, DFS, Dijkstra, A*, Greedy Best-First, Weighted A*, and cost evaluation |
| `src/traversal/runner.py` | Algorithm registry and comparison helpers |
| `src/traversal/api.py` | FastAPI endpoints |
| `src/traversal/repository.py` | Supabase persistence layer |
| `src/traversal/serialization.py` | Converts algorithm results into database-shaped rows |
| `src/traversal/ui.py` | Generates the browser demo HTML/JS |
| `sql/` | Database schema extensions, indexes, views, and functions |

## Install Dependencies

From the project root:

```bash
python3 -m pip install -e .
```

For test dependencies:

```bash
python3 -m pip install -e '.[test]'
```

If needed, install manually:

```bash
python3 -m pip install fastapi uvicorn supabase python-dotenv httpx
```

## Supabase Setup

### 1. Create A Supabase Project

Go to Supabase, create a project, then open:

```text
Project Settings -> API
```

Copy:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

Use the service role key only in the local backend. Do not expose it in browser JavaScript.

### 2. Create `.env`

In the project root:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Do not commit `.env`.

### 3. Create Database Tables

Open the Supabase SQL Editor and run the project SQL. The current SQL files assume your base tables already exist:

```text
maps
nodes
edges
algorithm_runs
run_path_nodes
```

Then run these files:

```text
sql/stoplights.sql
sql/schema_extensions.sql
sql/functions.sql
sql/views.sql
sql/indexes.sql
```

If your Supabase project is completely empty, create the base tables first, then run the files above.

Verify tables:

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

You should see tables such as:

```text
maps
nodes
edges
traffic_signals
route_experiments
algorithm_runs
run_path_nodes
```

## Run The Backend

Terminal 1:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Check the backend:

```text
http://127.0.0.1:8000/health
```

Expected:

```json
{ "status": "ok" }
```

Check Supabase:

```text
http://127.0.0.1:8000/db-health
```

A working database connection should return a successful status. If it fails, check `.env`, your Supabase key, and whether the required tables exist.

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Run The Browser UI

Terminal 2:

```bash
python3 main.py
python3 -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080/demo_output/traversal_demo.html
```

Use the local server URL instead of double-clicking the file so browser API requests work properly.

## Demo Flow

1. Start the backend.
2. Start the UI server.
3. Open the demo page.
4. Generate or edit a grid.
5. Add roadblocks, traffic, and stoplights if desired.
6. Click `Save graph` to store the graph in Supabase.
7. Load saved graphs if needed.
8. Select algorithms.
9. Optionally check `Save results to database`.
10. Click `Run selected algorithms`.
11. Compare route overlays and algorithm metrics.
12. Load graph history or saved experiment results.

## Algorithms

| Algorithm | Registered Name | Weighted? | Main Use |
|---|---|---:|---|
| BFS | `bfs` | No | Fewest moves on an unweighted graph |
| DFS | `dfs` | No | Reachability/depth-first exploration |
| Dijkstra | `dijkstra` | Yes | Reliable lowest-cost route for nonnegative weights |
| A* | `astar` | Yes | Guided weighted search using Manhattan distance |
| Greedy Best-First | `greedy_best_first` | Partially | Fast heuristic-first search, not guaranteed optimal |
| Weighted A* | `weighted_astar` | Yes | Speed vs route-quality tradeoff |

The key comparison idea:

- BFS and DFS are useful baselines, but they do not optimize traffic or stoplight weights.
- Dijkstra is reliable for weighted costs.
- A* is usually faster than Dijkstra because it uses a heuristic.
- Greedy Best-First and Weighted A* may be faster but can sacrifice route quality.

## Cost Model

Every route is evaluated with the same cost model:

```text
movement cost = base movement cost + directional traffic delay + stoplight delay
```

Important rules:

- Roadblocks cannot be crossed.
- Movement is only up, down, left, and right.
- Diagonal movement is not allowed.
- Traffic can make one direction more expensive than another.
- Stoplights add delay when entering an intersection node.

## API Endpoints

Useful endpoints:

```text
GET  /health
GET  /db-health
GET  /algorithms
GET  /algorithm-metadata
GET  /maps
POST /maps
GET  /maps/{map_id}
GET  /maps/{map_id}/nodes
GET  /maps/{map_id}/experiments
GET  /maps/{map_id}/performance
GET  /experiments/{experiment_id}/comparison
GET  /experiments/{experiment_id}/results
GET  /runs/{run_id}/path
POST /run-pathfinding
```

Example `POST /run-pathfinding` request:

```json
{
  "grid": [
    [1, 1, 1, 1],
    [1, 0, 0, 1],
    [1, 1, 1, 1]
  ],
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 3 },
  "algorithms": ["bfs", "dfs", "dijkstra", "astar"],
  "stoplights": [
    {
      "row": 1,
      "col": 0,
      "average_wait_seconds": 10
    }
  ]
}
```

To save algorithm results, first save a graph with `POST /maps`, then call `POST /run-pathfinding` with:

```json
{
  "grid": [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 2 },
  "algorithms": "all",
  "save": true,
  "map_id": "<saved-map-id>",
  "start_node_id": "<node-id-for-start>",
  "end_node_id": "<node-id-for-goal>"
}
```

## CLI Demo

Run the CLI version without the browser:

```bash
python3 main.py --cli
```

Run selected algorithms:

```bash
python3 main.py --cli --algorithm bfs --algorithm dfs --algorithm dijkstra --algorithm astar
```

Run all algorithms:

```bash
python3 main.py --cli --algorithm all
```

## Database Concepts Demonstrated

This project demonstrates database concepts through graph persistence and algorithm-result analysis.

### Normalization

Data is split into related tables:

```text
maps
nodes
edges
traffic_signals
route_experiments
algorithm_runs
run_path_nodes
```

### Relationships

Examples:

```text
nodes.map_id -> maps.id
edges.from_node_id -> nodes.id
edges.to_node_id -> nodes.id
traffic_signals.node_id -> nodes.id
algorithm_runs.experiment_id -> route_experiments.id
run_path_nodes.run_id -> algorithm_runs.id
```

### Persistence Flow

One `Run all` action should create:

```text
1 route_experiments row
1 algorithm_runs row per algorithm
many run_path_nodes rows per algorithm path
```

This makes the algorithms produce database records instead of only drawing a route on screen.

### Indexes

Indexes are used for common queries:

- finding a node by `(map_id, row, col)`
- loading edges by `from_node_id` or `to_node_id`
- retrieving runs for an experiment
- reconstructing path steps with `(run_id, step_index)`
- loading stoplights for a map/node

### Views

The SQL views summarize algorithm behavior:

```text
algorithm_performance_summary
algorithm_comparison_summary
```

### Functions / RPC

`save_algorithm_run_with_path(...)` saves one algorithm run and all path steps together, which helps keep related database writes consistent.

### EXPLAIN ANALYZE

Use `EXPLAIN ANALYZE` to compare query plans before and after indexing. Examples are in:

```text
sql/explain_notes.sql
```

## Run Tests

```bash
python3 -m unittest discover -s tests
```

Expected:

```text
OK
```

## Common Issues

### Backend Not Running

Start it with:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

### UI Cannot Reach Backend

Use the local HTTP server:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/demo_output/traversal_demo.html
```

### Supabase Not Working

Check:

- `.env` exists
- `SUPABASE_URL` is correct
- `SUPABASE_SERVICE_ROLE_KEY` is correct
- required tables exist in Supabase
- `/db-health` works

### Port Already In Use

Use another port:

```bash
python3 -m http.server 8081
```

Then open:

```text
http://127.0.0.1:8081/demo_output/traversal_demo.html
```

## Summary

This project combines pathfinding, visualization, and database persistence. The algorithms are the computation layer, but the database concepts come from modeling the grid as graph data, storing experiments and runs, reconstructing paths from saved rows, indexing common queries, and analyzing algorithm results with SQL.
