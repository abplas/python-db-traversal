-- Normalized stoplight storage for database-backed routing.
-- This keeps optional signal data separate from nodes while still
-- attaching each signal to a single map node.

create table if not exists traffic_signals (
    id uuid primary key default gen_random_uuid(),
    map_id uuid not null references maps(id) on delete cascade,
    node_id uuid not null references nodes(id) on delete cascade,
    average_wait_seconds double precision not null check (average_wait_seconds >= 0),
    light_cycle_seconds double precision check (light_cycle_seconds is null or light_cycle_seconds > 0),
    signal_type text not null default 'stoplight',
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (map_id, node_id)
);
