# Python DB Traversal

This project models a road network as a grid-based graph and finds a path between
two points using Manhattan-distance pathfinding.

## Concept

- Each traversable grid cell is a node.
- Each road connection between neighboring cells is an edge.
- Movement is limited to up, down, left, and right.
- No diagonal movement is allowed.
- Manhattan distance is used as the heuristic for pathfinding.

This makes the project a good fit for city-block style traversal where roads
behave like a rectangular grid.

## Setup

This project requires Python `3.10+`.

If you are using VS Code:

- open the project folder
- select a Python `3.10+` interpreter
- use the VS Code terminal in this project directory

Install the project and test dependencies with:

```bash
python3 -m pip install -e '.[test]'
```

The quotes matter in `zsh`, where `.[test]` can otherwise be treated as a
filename pattern.

## Supabase setup

To connect the FastAPI backend to Supabase:

1. Install dependencies:

```bash
python3 -m pip install -e '.[test]'
```

2. Create a local environment file from the example:

```bash
cp .env.example .env
```

3. Set these values in `.env`:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

4. Start the FastAPI backend:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

5. Test the database connection:

```bash
curl http://127.0.0.1:8000/db-health
```

Do not commit `.env` to git.

## Save graphs and history

The FastAPI backend can now save generated graphs and later attach algorithm
experiments to those saved maps.

Useful endpoints:

- `GET /db-health`
- `GET /maps`
- `POST /maps`
- `GET /maps/{map_id}`
- `GET /maps/{map_id}/experiments`
- `GET /experiments/{experiment_id}/results`
- `GET /runs/{run_id}/path`
- `POST /run-pathfinding`

Typical workflow:

1. Generate or edit a grid in the demo UI.
2. Save the graph to Supabase with `POST /maps`.
3. Load the saved `map_id` and point-to-node mapping.
4. Run algorithms.
5. Save experiment results with `POST /run-pathfinding` and `save=true`.
6. View saved experiment history by map and experiment id.

To save a graph from the API, send a payload like:

```json
{
  "name": "Generated Manhattan Map",
  "slug": "generated-manhattan-map",
  "description": "Saved from the demo UI",
  "grid": [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
  "traffic": null,
  "stoplights": [
    { "row": 0, "col": 1, "average_wait_seconds": 10 }
  ]
}
```

To save algorithm results after a map already exists, call `POST /run-pathfinding`
with:

```json
{
  "grid": [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
  "start": { "row": 0, "col": 0 },
  "goal": { "row": 2, "col": 2 },
  "algorithms": ["astar", "dijkstra"],
  "save": true,
  "map_id": "<saved-map-id>",
  "start_node_id": "<node-id-for-start>",
  "end_node_id": "<node-id-for-goal>"
}
```

The easiest way to explore the API interactively is:

```bash
PYTHONPATH=src python3 -m uvicorn traversal.api:app --reload
```

Then open:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Project structure

- `src/traversal/grid.py`: grid and node modeling
- `src/traversal/pathfinding.py`: Manhattan-distance A* traversal
- `main.py`: runnable example
- `tests/test_pathfinding.py`: basic pathfinding tests

## Run the demo UI

```bash
python3 main.py
```

This generates a simple HTML page at `demo_output/traversal_demo.html`.
On macOS, you can open it with:

```bash
open demo_output/traversal_demo.html
```

Open that file in your browser to show:

- point A
- point B
- blocked cells
- traversable roads
- the final non-diagonal route
- save graph controls
- saved map loading
- saved experiment history

## Run the console demo

```bash
python3 main.py --cli
```

## Run tests

```bash
python3 -m unittest discover -s tests
```

## Database concepts demonstrated

This project is set up to show several database-class ideas:

- Normalized schema design across `maps`, `nodes`, `edges`, `traffic_signals`, `route_experiments`, `algorithm_runs`, and `run_path_nodes`
- Foreign keys between maps, nodes, edges, signals, experiments, runs, and path steps
- Indexes for node lookup, edge traversal, experiment history, and ordered path reconstruction
- SQL views for algorithm summaries and experiment comparisons
- RPC / function-based atomic saving for one algorithm run and its path steps
- `EXPLAIN ANALYZE` examples for before/after index comparisons
- JSONB metadata for map generation details and algorithm result annotations
