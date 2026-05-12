-- Database persistence flow for one full pathfinding experiment.
-- This is the key database-execution milestone for the project.

-- 1. Create one route_experiments row when the user clicks "Run all".
--    The experiment groups BFS, DFS, Dijkstra, A*, Greedy Best-First,
--    and Weighted A* results for the same map/start/goal/settings.
insert into route_experiments (
    map_id,
    start_node_id,
    end_node_id,
    traffic_enabled,
    stoplights_enabled,
    metadata
)
values (
    '<map-id>',
    '<start-node-id>',
    '<end-node-id>',
    true,
    true,
    '{"ui_action":"run_all","grid_size":"30x40"}'::jsonb
)
returning id;

-- 2. Insert one algorithm_runs row per algorithm.
--    The existing save_algorithm_run_with_path RPC in sql/functions.sql can do this
--    atomically with its path nodes. Algorithms now include DFS.
select save_algorithm_run_with_path(
    p_experiment_id := '<experiment-id>',
    p_map_id := '<map-id>',
    p_algorithm := 'dfs',
    p_start_node_id := '<start-node-id>',
    p_end_node_id := '<end-node-id>',
    p_status := 'completed',
    p_total_cost := 42.0,
    p_total_distance_meters := null,
    p_total_duration_seconds := null,
    p_visited_count := 80,
    p_runtime_ms := 3,
    p_metadata := '{
        "time_complexity":"O(V + E)",
        "space_complexity":"O(V)",
        "optimality":"not_guaranteed",
        "tradeoff":"DFS tests reachability but does not guarantee shortest path"
    }'::jsonb,
    p_path_nodes := '[
        {"node_id":"<start-node-id>","step_index":0,"cumulative_cost":0,"reached":false},
        {"node_id":"<end-node-id>","step_index":1,"cumulative_cost":42,"reached":true}
    ]'::jsonb
);

-- 3. Query all runs for the experiment.
--    Supported by idx_algorithm_runs_experiment_id and
--    idx_algorithm_runs_experiment_algorithm.
select *
from algorithm_runs
where experiment_id = '<experiment-id>'
order by algorithm;

-- 4. Reconstruct one algorithm path in order.
--    Supported by idx_run_path_nodes_run_step.
select *
from run_path_nodes
where run_id = '<run-id>'
order by step_index;

-- 5. Use the comparison view for presentation-friendly ranking.
select *
from algorithm_comparison_summary
where experiment_id = '<experiment-id>'
order by cost_rank, speed_rank;
