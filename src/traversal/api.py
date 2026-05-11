from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from traversal.grid import Point, Stoplight
from traversal.runner import (
    list_algorithm_metadata,
    list_algorithms,
    run_pathfinding_request,
)


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


@app.post("/run-pathfinding")
def run_pathfinding(payload: PathfindingRequest) -> dict[str, object]:
    start = Point(payload.start.row, payload.start.col)
    goal = Point(payload.goal.row, payload.goal.col)
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
        return run_pathfinding_request(
            payload.grid,
            start,
            goal,
            payload.algorithms,
            traffic=payload.traffic,
            stoplights=stoplights,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
