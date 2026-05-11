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
