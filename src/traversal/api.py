from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from traversal.grid import Point, Stoplight
from traversal.repository import (
    build_point_to_node_id,
    check_database_connection,
    create_map,
    create_route_experiment,
    get_algorithm_comparison_summary,
    get_algorithm_performance_summary,
    get_experiment_results,
    get_run_path,
    list_experiments_for_map,
    list_maps,
    load_map_graph,
    load_nodes_for_map,
    save_generated_map,
    save_algorithm_run_with_path,
)
from traversal.runner import (
    build_pathfinding_response,
    list_algorithm_metadata,
    list_algorithms,
    run_algorithms,
    run_pathfinding_request,
)
from traversal.serialization import build_algorithm_run_row, build_run_path_node_rows


class PointRequest(BaseModel):
    row: int
    col: int


class StoplightRequest(BaseModel):
    row: int
    col: int
    average_wait_seconds: float
    light_cycle_seconds: float | None = None
    has_stoplight: bool = True
    metadata: dict[str, object] | None = None


class PathfindingRequest(BaseModel):
    grid: list[list[int]]
    start: PointRequest
    goal: PointRequest
    algorithms: Literal["all"] | str | list[str]
    traffic: dict[str, list[list[float]]] | None = None
    stoplights: list[StoplightRequest] | None = None
    save: bool = False
    map_id: str | None = None
    start_node_id: str | None = None
    end_node_id: str | None = None


class MapSaveRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    grid: list[list[int]]
    traffic: dict[str, list[list[float]]] | None = None
    stoplights: list[StoplightRequest] | None = None
    metadata: dict[str, object] | None = None


app = FastAPI(title="Pathfinding API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _request: object, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Invalid request body.",
            "errors": exc.errors(),
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/algorithms")
def algorithms() -> dict[str, list[str]]:
    return {"algorithms": list_algorithms()}


@app.get("/algorithm-metadata")
def algorithm_metadata() -> dict[str, list[dict[str, object]]]:
    return {"algorithms": list_algorithm_metadata()}


@app.get("/db-health")
def db_health() -> dict[str, object]:
    try:
        return check_database_connection()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/maps")
def maps() -> dict[str, object]:
    try:
        return {"maps": list_maps()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/maps")
def save_map(payload: MapSaveRequest) -> dict[str, object]:
    stoplights = (
        [
            Stoplight(
                row=stoplight.row,
                col=stoplight.col,
                average_wait_seconds=stoplight.average_wait_seconds,
                light_cycle_seconds=stoplight.light_cycle_seconds,
                has_stoplight=stoplight.has_stoplight,
                metadata=stoplight.metadata or {},
            )
            for stoplight in payload.stoplights
        ]
        if payload.stoplights
        else None
    )

    try:
        return save_generated_map(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            grid=payload.grid,
            traffic=payload.traffic,
            stoplights=stoplights,
            metadata=dict(payload.metadata or {}),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save graph: {exc}") from exc


@app.get("/maps/{map_id}")
def load_map(map_id: str) -> dict[str, object]:
    try:
        return load_map_graph(map_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/maps/{map_id}/nodes")
def map_nodes(map_id: str) -> dict[str, object]:
    try:
        return {"nodes": load_nodes_for_map(map_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/experiments/{experiment_id}/comparison")
def experiment_comparison(experiment_id: str) -> dict[str, object]:
    try:
        return {"comparison": get_algorithm_comparison_summary(experiment_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/experiments/{experiment_id}/results")
def experiment_results(experiment_id: str) -> dict[str, object]:
    try:
        return {"results": get_experiment_results(experiment_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/runs/{run_id}/path")
def run_path(run_id: str) -> dict[str, object]:
    try:
        return {"path": get_run_path(run_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/maps/{map_id}/experiments")
def map_experiments(map_id: str) -> dict[str, object]:
    try:
        return {"experiments": list_experiments_for_map(map_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/maps/{map_id}/performance")
def map_performance(map_id: str) -> dict[str, object]:
    try:
        return {"performance": get_algorithm_performance_summary(map_id)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _build_stoplights(
    payload: PathfindingRequest,
) -> list[Stoplight] | None:
    return (
        [
            Stoplight(
                row=stoplight.row,
                col=stoplight.col,
                average_wait_seconds=stoplight.average_wait_seconds,
                light_cycle_seconds=stoplight.light_cycle_seconds,
                has_stoplight=stoplight.has_stoplight,
                metadata=stoplight.metadata or {},
            )
            for stoplight in payload.stoplights
        ]
        if payload.stoplights
        else None
    )


def _require_save_identifiers(payload: PathfindingRequest) -> None:
    if not payload.save:
        return

    missing = [
        field_name
        for field_name in ("map_id", "start_node_id", "end_node_id")
        if not getattr(payload, field_name)
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Saving pathfinding results requires "
                + ", ".join(missing)
                + "."
            ),
        )


def _save_results_to_database(
    *,
    payload: PathfindingRequest,
    start: Point,
    goal: Point,
    results: list[object],
) -> tuple[str, dict[str, str]]:
    point_to_node_id = build_point_to_node_id(str(payload.map_id))
    expected_start_node_id = point_to_node_id.get(start)
    expected_end_node_id = point_to_node_id.get(goal)

    if expected_start_node_id is None or expected_end_node_id is None:
        raise ValueError(
            "The database nodes for this map do not include the start and goal "
            "grid coordinates. Make sure the map nodes match the grid."
        )

    if expected_start_node_id != payload.start_node_id or expected_end_node_id != payload.end_node_id:
        raise ValueError(
            "The provided start_node_id or end_node_id does not match the grid "
            "coordinates for this map."
        )

    experiment_id = create_route_experiment(
        map_id=str(payload.map_id),
        start_node_id=str(payload.start_node_id),
        end_node_id=str(payload.end_node_id),
        traffic_enabled=payload.traffic is not None,
        stoplights_enabled=bool(payload.stoplights),
        metadata={
            "selected_algorithms": [result.algorithm_name for result in results],
            "grid_rows": len(payload.grid),
            "grid_cols": len(payload.grid[0]) if payload.grid else 0,
            "save_requested": True,
        },
    )

    saved_run_ids: dict[str, str] = {}
    for result in results:
        if not result.path_found:
            continue

        run_row = build_algorithm_run_row(
            result,
            experiment_id=experiment_id,
            map_id=str(payload.map_id),
            start=start,
            goal=goal,
            point_to_node_id=point_to_node_id,
        )
        path_rows = build_run_path_node_rows(
            result,
            point_to_node_id=point_to_node_id,
        )
        saved_run_ids[result.algorithm_name] = save_algorithm_run_with_path(
            experiment_id=experiment_id,
            map_id=str(run_row["map_id"]),
            algorithm=str(run_row["algorithm"]),
            start_node_id=str(run_row["start_node_id"]),
            end_node_id=str(run_row["end_node_id"]),
            status=str(run_row["status"]),
            total_cost=run_row["total_cost"],
            total_distance_meters=run_row["total_distance_meters"],
            total_duration_seconds=run_row["total_duration_seconds"],
            visited_count=int(run_row["visited_count"]),
            runtime_ms=int(run_row["runtime_ms"]),
            metadata=dict(run_row["metadata"]),
            path_nodes=path_rows,
        )

    return experiment_id, saved_run_ids


@app.post("/run-pathfinding")
def run_pathfinding(payload: PathfindingRequest) -> dict[str, object]:
    start = Point(payload.start.row, payload.start.col)
    goal = Point(payload.goal.row, payload.goal.col)
    stoplights = _build_stoplights(payload)

    try:
        if not payload.save:
            return run_pathfinding_request(
                payload.grid,
                start,
                goal,
                payload.algorithms,
                traffic=payload.traffic,
                stoplights=stoplights,
            )

        _require_save_identifiers(payload)
        results = run_algorithms(
            payload.algorithms,
            payload.grid,
            start,
            goal,
            traffic=payload.traffic,
            stoplights=stoplights,
        )
        response_payload = build_pathfinding_response(
            start=start,
            goal=goal,
            selected_algorithms=[result.algorithm_name for result in results],
            results=results,
        )
        experiment_id, saved_run_ids = _save_results_to_database(
            payload=payload,
            start=start,
            goal=goal,
            results=results,
        )
        response_payload["experiment_id"] = experiment_id
        response_payload["saved_run_ids"] = saved_run_ids
        return response_payload
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save pathfinding results: {exc}",
        ) from exc
