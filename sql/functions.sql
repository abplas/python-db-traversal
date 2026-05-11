-- Example helper for saving one algorithm run and all path steps atomically.
-- This is a natural future RPC candidate for Supabase.

create or replace function save_algorithm_run_with_path(
    p_experiment_id uuid,
    p_map_id uuid,
    p_algorithm text,
    p_start_node_id uuid,
    p_end_node_id uuid,
    p_status text,
    p_total_cost double precision,
    p_total_distance_meters double precision,
    p_total_duration_seconds double precision,
    p_visited_count integer,
    p_runtime_ms integer,
    p_metadata jsonb,
    p_path_nodes jsonb
)
returns uuid
language plpgsql
as $$
declare
    v_run_id uuid;
begin
    insert into algorithm_runs (
        experiment_id,
        map_id,
        algorithm,
        start_node_id,
        end_node_id,
        status,
        total_cost,
        total_distance_meters,
        total_duration_seconds,
        visited_count,
        runtime_ms,
        metadata
    )
    values (
        p_experiment_id,
        p_map_id,
        p_algorithm,
        p_start_node_id,
        p_end_node_id,
        p_status,
        p_total_cost,
        p_total_distance_meters,
        p_total_duration_seconds,
        p_visited_count,
        p_runtime_ms,
        coalesce(p_metadata, '{}'::jsonb)
    )
    returning id into v_run_id;

    insert into run_path_nodes (
        run_id,
        node_id,
        step_index,
        cumulative_cost,
        reached
    )
    select
        v_run_id,
        path_step.node_id,
        path_step.step_index,
        path_step.cumulative_cost,
        path_step.reached
    from jsonb_to_recordset(coalesce(p_path_nodes, '[]'::jsonb)) as path_step(
        node_id uuid,
        step_index integer,
        cumulative_cost double precision,
        reached boolean
    );

    return v_run_id;
end;
$$;
