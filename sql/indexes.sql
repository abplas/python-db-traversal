-- Core routing and analytics indexes.

create unique index if not exists idx_nodes_map_row_col
    on nodes (map_id, row, col);

create index if not exists idx_edges_from_node
    on edges (from_node_id);

create index if not exists idx_edges_to_node
    on edges (to_node_id);

create index if not exists idx_algorithm_runs_experiment
    on algorithm_runs (experiment_id);

create index if not exists idx_algorithm_runs_map_algorithm_created_at
    on algorithm_runs (map_id, algorithm, created_at desc);

create index if not exists idx_run_path_nodes_run_step
    on run_path_nodes (run_id, step_index);

create index if not exists idx_traffic_signals_map_node
    on traffic_signals (map_id, node_id);

-- Experiment dashboards usually show newest experiments for one map first.
create index if not exists idx_route_experiments_map_created_at
    on route_experiments (map_id, created_at desc);

-- The report/presentation can filter comparisons by algorithm family, including DFS.
create index if not exists idx_algorithm_runs_experiment_algorithm
    on algorithm_runs (experiment_id, algorithm);

-- Fast lookup for successful/failed runs inside an experiment.
create index if not exists idx_algorithm_runs_experiment_status
    on algorithm_runs (experiment_id, status);

-- JSONB metadata can store complexity, tradeoff labels, and route cost breakdowns.
-- This GIN index helps if we later query inside metadata, such as finding all DFS runs
-- with a specific reliability category.
create index if not exists idx_algorithm_runs_metadata_gin
    on algorithm_runs using gin (metadata);
