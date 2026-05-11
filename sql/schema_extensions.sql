-- Group multiple algorithm runs that share the same map, start/goal, traffic,
-- and stoplight setup so comparisons can be queried as one experiment.

create table if not exists route_experiments (
    id uuid primary key default gen_random_uuid(),
    map_id uuid not null references maps(id) on delete cascade,
    start_node_id uuid not null references nodes(id) on delete restrict,
    end_node_id uuid not null references nodes(id) on delete restrict,
    traffic_enabled boolean not null default false,
    stoplights_enabled boolean not null default false,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

alter table algorithm_runs
    add column if not exists experiment_id uuid references route_experiments(id) on delete set null;
