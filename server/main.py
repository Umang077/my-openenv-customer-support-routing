"""
FastAPI server — exposes the Customer Support Routing environment
over HTTP following the OpenEnv spec.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .environment import CSRoutingEnvironment

app = FastAPI(
    title="Customer Support Routing Environment",
    description=(
        "OpenEnv-compatible environment. "
        "Routes customer support tickets to the correct team with priority assignment."
    ),
    version="1.0.0",
)

# Single global environment instance (one session at a time)
_env = CSRoutingEnvironment()


# ── Request models ────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task: str = "simple_routing"


class StepRequest(BaseModel):
    team: str
    priority: str = "medium"
    notes: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check — used by the validator and Docker HEALTHCHECK."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/reset")
def reset(request: ResetRequest = ResetRequest()):
    """
    Start a new episode.
    Returns the first ticket observation with reward=0.0 and done=false.
    """
    try:
        return _env.reset(task=request.task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/step")
def step(request: StepRequest):
    """
    Submit a routing decision for the current ticket.
    Returns the next ticket observation, reward, and done flag.
    """
    try:
        return _env.step(
            team=request.team,
            priority=request.priority,
            notes=request.notes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/state")
def state():
    """Return current episode state without advancing it."""
    return _env.state()

@app.get("/")
def home():
    return {"status": "Customer Support Routing API is running"}