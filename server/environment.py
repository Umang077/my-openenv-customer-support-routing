"""
Core episode state management for the Customer Support Routing environment.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .graders import score_ticket
from .tasks import AVAILABLE_PRIORITIES, AVAILABLE_TEAMS, TaskConfig, TicketData, TASKS


@dataclass
class EpisodeState:
    task_name: str
    task_config: TaskConfig
    tickets: List[TicketData]
    current_index: int = 0
    rewards: List[float] = field(default_factory=list)
    done: bool = False

    @property
    def current_ticket(self) -> Optional[TicketData]:
        if self.current_index < len(self.tickets):
            return self.tickets[self.current_index]
        return None

    @property
    def tickets_total(self) -> int:
        return len(self.tickets)

    @property
    def tickets_completed(self) -> int:
        return self.current_index

    @property
    def current_score(self) -> float:
        if not self.rewards:
            return 0.0
        return round(sum(self.rewards) / len(self.rewards), 4)


class CSRoutingEnvironment:
    """
    Customer Support Routing OpenEnv environment.

    The agent sees one ticket at a time and must choose:
      - team     : which team to route the ticket to
      - priority : how urgent the ticket is (low / medium / high)

    Calling reset(task=...) begins a fresh episode for that task.
    Each call to step() processes one ticket and returns the next.
    The episode ends when all tickets in the task have been routed.
    """

    def __init__(self) -> None:
        self._state: Optional[EpisodeState] = None

    # ── OpenEnv API ──────────────────────────────────────────────────────────

    def reset(self, task: str = "simple_routing") -> Dict[str, Any]:
        """Start a new episode for the given task. Returns the first observation."""
        if task not in TASKS:
            raise ValueError(
                f"Unknown task {task!r}. Valid tasks: {list(TASKS.keys())}"
            )
        config = TASKS[task]
        self._state = EpisodeState(
            task_name=task,
            task_config=config,
            tickets=list(config["tickets"]),  # copy so original data is not mutated
        )
        return self._build_result(reward=0.0, done=False)

    def step(
        self,
        team: str,
        priority: str = "medium",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process the agent's routing decision for the current ticket."""
        if self._state is None:
            raise RuntimeError("Call reset() before step().")
        if self._state.done:
            raise RuntimeError("Episode is already done. Call reset() to start a new episode.")

        # Normalise and validate inputs — silently fall back to safe defaults
        team     = team.lower().strip()
        priority = priority.lower().strip()
        if team not in AVAILABLE_TEAMS:
            team = "general_inquiry"
        if priority not in AVAILABLE_PRIORITIES:
            priority = "medium"

        # Score the current ticket
        ticket = self._state.current_ticket
        config = self._state.task_config
        reward = score_ticket(
            predicted_team=team,
            predicted_priority=priority,
            correct_team=ticket["correct_team"],
            correct_priority=ticket["correct_priority"],
            team_weight=config["team_weight"],
            priority_weight=config["priority_weight"],
        )

        self._state.rewards.append(reward)
        self._state.current_index += 1

        done = self._state.current_index >= self._state.tickets_total
        self._state.done = done

        return self._build_result(reward=reward, done=done)

    def state(self) -> Dict[str, Any]:
        """Return the current episode state (does not advance the episode)."""
        if self._state is None:
            return {"status": "not_started"}
        s = self._state
        return {
            "task_name":          s.task_name,
            "difficulty":         s.task_config["difficulty"],
            "tickets_completed":  s.tickets_completed,
            "tickets_total":      s.tickets_total,
            "rewards":            s.rewards,
            "current_score":      s.current_score,
            "done":               s.done,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_result(self, reward: float, done: bool) -> Dict[str, Any]:
        s = self._state
        config = s.task_config

        if done or s.current_ticket is None:
            observation = {
                "ticket_id":          "",
                "ticket_subject":     "Episode complete",
                "ticket_text":        (
                    f"All {s.tickets_total} tickets routed. "
                    f"Final score: {s.current_score:.4f}"
                ),
                "available_teams":      AVAILABLE_TEAMS,
                "available_priorities": AVAILABLE_PRIORITIES,
                "tickets_completed":    s.tickets_completed,
                "tickets_total":        s.tickets_total,
                "current_score":        s.current_score,
                "task_name":            s.task_name,
                "task_difficulty":      config["difficulty"],
            }
        else:
            ticket = s.current_ticket
            observation = {
                "ticket_id":          ticket["id"],
                "ticket_subject":     ticket["subject"],
                "ticket_text":        ticket["text"],
                "available_teams":      AVAILABLE_TEAMS,
                "available_priorities": AVAILABLE_PRIORITIES,
                "tickets_completed":    s.tickets_completed,
                "tickets_total":        s.tickets_total,
                "current_score":        s.current_score,
                "task_name":            s.task_name,
                "task_difficulty":      config["difficulty"],
            }

        return {
            "observation": observation,
            "reward":      reward,
            "done":        done,
            "info": {
                "episode_score": s.current_score,
                "rewards_so_far": s.rewards,
            },
        }