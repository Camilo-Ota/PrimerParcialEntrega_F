"""FastAPI backend for the Emergency Control search agent."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import build_plan

app = FastAPI(title="Emergency Control API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCENARIO_PATH = Path(__file__).resolve().parents[2] / "scenarios" / "scenario.json"


def _load_default_scenario() -> dict[str, Any]:
    with SCENARIO_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenario")
def get_scenario() -> dict[str, Any]:
    return _load_default_scenario()


@app.post("/api/solve")
def solve(scenario: dict[str, Any]) -> dict[str, Any]:
    """Solve the supplied scenario with Uniform-Cost Graph Search."""
    data = scenario if scenario else _load_default_scenario()
    return build_plan(data)
