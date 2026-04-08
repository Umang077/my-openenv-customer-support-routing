"""
Async HTTP client for the Customer Support Routing environment.
Supports two connection modes:
  - from_docker_image() : spin up a Docker container automatically
  - from_url()          : connect to an already-running server (e.g. HF Space)
"""

import asyncio
import subprocess
import time
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel


AVAILABLE_TEAMS      = ["billing", "technical", "returns", "general_inquiry", "security"]
AVAILABLE_PRIORITIES = ["low", "medium", "high"]


# ── Pydantic models (mirrors server response schema) ──────────────────────────

class CSRoutingObservation(BaseModel):
    ticket_id: str
    ticket_subject: str
    ticket_text: str
    available_teams: List[str]
    available_priorities: List[str]
    tickets_completed: int
    tickets_total: int
    current_score: float
    task_name: str
    task_difficulty: str


class CSRoutingAction(BaseModel):
    team: str
    priority: str = "medium"
    notes: Optional[str] = None


class StepResult(BaseModel):
    observation: CSRoutingObservation
    reward: float
    done: bool
    info: Dict[str, Any] = {}


# ── Client ────────────────────────────────────────────────────────────────────

class CSRoutingEnv:
    """Async client for the Customer Support Routing OpenEnv environment."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
        self._container_id: Optional[str] = None

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    async def from_docker_image(
        cls,
        image_name: str,
        host_port: int = 8765,
        startup_timeout: int = 60,
    ) -> "CSRoutingEnv":
        """
        Pull and start a Docker container from image_name,
        wait for it to become healthy, then return a connected env.
        """
        container_name = f"cs-routing-env-{host_port}"

        # Remove any stale container with the same name
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        proc = subprocess.Popen(
            [
                "docker", "run", "-d", "--rm",
                "--name", container_name,
                "-p", f"{host_port}:7860",
                image_name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"docker run failed:\n{stderr.decode()}")

        container_id = stdout.decode().strip()
        instance = cls(f"http://localhost:{host_port}")
        instance._container_id = container_id

        # Poll /health until the server is ready
        deadline = time.monotonic() + startup_timeout
        while time.monotonic() < deadline:
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(
                        f"{instance.base_url}/health",
                        timeout=aiohttp.ClientTimeout(total=2),
                    ) as r:
                        if r.status == 200:
                            print(
                                f"[DEBUG] Server ready at {instance.base_url}",
                                flush=True,
                            )
                            return instance
            except Exception:
                pass
            await asyncio.sleep(1)

        raise TimeoutError(
            f"Server did not become healthy within {startup_timeout} seconds."
        )

    @classmethod
    def from_url(cls, base_url: str) -> "CSRoutingEnv":
        """Connect to an already-running server (e.g. a deployed HF Space)."""
        return cls(base_url)

    # ── Session management ────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # ── OpenEnv API ───────────────────────────────────────────────────────────

    async def reset(self, task: str = "simple_routing") -> StepResult:
        """Start a new episode for the given task."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/reset",
            json={"task": task},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return StepResult(**data)

    async def step(self, action: CSRoutingAction) -> StepResult:
        """Submit a routing decision and get the next observation."""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/step",
            json=action.model_dump(exclude_none=True),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return StepResult(**data)

    async def state(self) -> Dict[str, Any]:
        """Get current episode state without advancing it."""
        session = await self._get_session()
        async with session.get(f"{self.base_url}/state") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def close(self) -> None:
        """Close HTTP session and stop Docker container (if any)."""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._container_id:
            subprocess.run(
                ["docker", "stop", self._container_id],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._container_id = None