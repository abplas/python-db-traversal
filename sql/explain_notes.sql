-- Example analysis queries for before/after index comparisons.
-- Replace the placeholder UUID values with real ids from your environment.

-- Example 1: compare lookup speed for one algorithm on one map before/after
-- idx_algorithm_runs_map_algorithm_created_at.
--
-- explain analyze
-- select *
-- from algorithm_runs
-- where map_id = '<map-id>'
--   and algorithm = 'astar'
-- order by created_at desc;


-- Example 2: compare ordered path reconstruction before/after
-- idx_run_path_nodes_run_step.
--
-- explain analyze
-- select *
-- from run_path_nodes
-- where run_id = '<run-id>'
-- order by step_index asc;


-- Example 3: compare node lookup by map coordinate before/after
-- idx_nodes_map_row_col.
--
-- explain analyze
-- select *
-- from nodes
-- where map_id = '<map-id>'
--   and row = 10
--   and col = 15;


-- Example 4: compare experiment comparison queries before/after
-- idx_algorithm_runs_experiment.
--
-- explain analyze
-- select *
-- from algorithm_comparison_summary
-- where experiment_id = '<experiment-id>'
-- order by cost_rank, speed_rank;


-- Example 5: compare recent saved-map history lookups before/after
-- idx_maps_created_at.
--
-- explain analyze
-- select id, name, slug, description, created_at
-- from maps
-- order by created_at desc
-- limit 20;


-- Example 6: compare per-map experiment history lookups before/after
-- idx_route_experiments_map_created_at.
--
-- explain analyze
-- select *
-- from route_experiments
-- where map_id = '<map-id>'
-- order by created_at desc;
