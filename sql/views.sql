create or replace view algorithm_performance_summary as
select
    map_id,
    algorithm,
    count(*) as total_runs,
    avg(runtime_ms)::double precision as avg_runtime_ms,
    min(runtime_ms) as min_runtime_ms,
    max(runtime_ms) as max_runtime_ms,
    avg(visited_count)::double precision as avg_visited_count,
    avg(total_cost)::double precision as avg_total_cost,
    avg(case when status = 'completed' then 1 else 0 end)::double precision as success_rate
from algorithm_runs
group by map_id, algorithm;


create or replace view algorithm_comparison_summary as
with ranked_runs as (
    select
        ar.id,
        ar.experiment_id,
        ar.map_id,
        ar.algorithm,
        ar.status,
        ar.total_cost,
        ar.runtime_ms,
        ar.visited_count,
        min(ar.total_cost) filter (where ar.status = 'completed') over (partition by ar.experiment_id) as best_cost,
        min(ar.runtime_ms) filter (where ar.status = 'completed') over (partition by ar.experiment_id) as fastest_runtime_ms
    from algorithm_runs ar
    where ar.experiment_id is not null
)
select
    experiment_id,
    map_id,
    id as run_id,
    algorithm,
    status,
    total_cost,
    runtime_ms,
    visited_count,
    best_cost,
    fastest_runtime_ms,
    case
        when best_cost is null or total_cost is null then null
        when best_cost = 0 then 1.0
        else round((total_cost / best_cost)::numeric, 4)::double precision
    end as cost_ratio,
    rank() over (
        partition by experiment_id
        order by total_cost nulls last, runtime_ms nulls last, algorithm
    ) as cost_rank,
    rank() over (
        partition by experiment_id
        order by runtime_ms nulls last, total_cost nulls last, algorithm
    ) as speed_rank,
    case
        when status <> 'completed' then 'no route'
        when best_cost is null or total_cost is null then 'unknown'
        when best_cost = 0 then 'highly reliable'
        when total_cost / nullif(best_cost, 0) <= 1.02 then 'highly reliable'
        when total_cost / nullif(best_cost, 0) <= 1.10 then 'near optimal'
        else 'less reliable'
    end as reliability_label,
    case
        when status <> 'completed' then 'no route'
        when fastest_runtime_ms is null then 'unknown'
        when runtime_ms = fastest_runtime_ms then 'fastest'
        when runtime_ms <= fastest_runtime_ms * 1.25 then 'fast'
        else 'slower'
    end as speed_label
from ranked_runs;
