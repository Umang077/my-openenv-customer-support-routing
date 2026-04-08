"""
Customer Support Routing — Inference Script
===========================================
MANDATORY environment variables:
    API_BASE_URL   LLM API endpoint        (default: HF router)
    MODEL_NAME     Model identifier        (default: Qwen2.5-72B-Instruct)
    HF_TOKEN       HuggingFace / API key

Optional:
    IMAGE_NAME     Docker image name  — set this to run via Docker
    SERVER_URL     Running server URL — used when IMAGE_NAME is not set
                   (default: http://localhost:8000 for local, or your HF Space URL)

STDOUT FORMAT (one block per task):
    [START] task=<name> env=customer-support-routing model=<model>
    [STEP]  step=<n> action=<str> reward=<0.00> done=<bool> error=<str|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import asyncio
import json
import os
import re
import textwrap
from typing import List, Optional

from openai import OpenAI

from cs_routing_env.client import CSRoutingEnv, CSRoutingAction

from dotenv import load_dotenv
load_dotenv()
# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL") 
API_KEY      = os.getenv("HF_TOKEN") 
MODEL_NAME   = os.getenv("MODEL_NAME")
IMAGE_NAME   = os.getenv("IMAGE_NAME")                         # Docker mode
SERVER_URL   = os.getenv("SERVER_URL", "http://localhost:8000") # URL mode

BENCHMARK          = "customer-support-routing"
TASKS              = ["simple_routing", "priority_routing", "batch_routing"]
MAX_STEPS          = 10    # safety cap per episode (env terminates sooner)
TEMPERATURE        = 0.2
MAX_TOKENS         = 150
SUCCESS_THRESHOLD  = 0.5   # score >= this → success = true

AVAILABLE_TEAMS      = ["billing", "technical", "returns", "general_inquiry", "security"]
AVAILABLE_PRIORITIES = ["low", "medium", "high"]

SYSTEM_PROMPT = textwrap.dedent("""
    You are a customer support ticket routing specialist.

    You will receive a support ticket (subject + message body).
    Your job:
      1. Choose the TEAM that should handle this ticket.
      2. Choose the PRIORITY level.

    Valid teams:
      billing         — payment issues, invoices, charges, refund amounts, subscriptions
      technical       — app/website bugs, crashes, API errors, slow performance,
                        password reset (only when there is NO suspicious login activity)
      returns         — product returns, exchanges, damaged goods, return labels, return status
      general_inquiry — store info, hours, product catalogue, pricing (non-account questions)
      security        — hacked accounts, suspicious logins from unknown locations,
                        phishing emails, fraud prevention

    Valid priorities:
      low    — informational, no deadline, minor inconvenience
      medium — standard issue, normal resolution time is fine
      high   — financial risk, account compromised, imminent deadline (<48h), business-blocking

    Reply with ONLY a single JSON object on one line. No markdown, no explanation.
    Example: {"team": "billing", "priority": "high"}
""").strip()


# ── Logging helpers ───────────────────────────────────────────────────────────

def log_start(task: str, model: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    err = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={str(done).lower()} error={err}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── Action parsing ────────────────────────────────────────────────────────────

def parse_action(response_text: str) -> CSRoutingAction:
    """
    Extract team and priority from the model's raw output.
    Tries JSON first, then keyword fallback.
    """
    text = response_text.strip()

    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`")

    # Try to parse JSON
    try:
        match = re.search(r"\{[^}]+\}", text, re.DOTALL)
        if match:
            data     = json.loads(match.group(0))
            team     = str(data.get("team", "general_inquiry")).lower().strip()
            priority = str(data.get("priority", "medium")).lower().strip()
            if team not in AVAILABLE_TEAMS:
                team = _closest_team(team)
            if priority not in AVAILABLE_PRIORITIES:
                priority = "medium"
            return CSRoutingAction(team=team, priority=priority)
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Fallback: keyword scan
    team     = _first_match(text, AVAILABLE_TEAMS,      default="general_inquiry")
    priority = _first_match(text, AVAILABLE_PRIORITIES, default="medium")
    return CSRoutingAction(team=team, priority=priority)


def _first_match(text: str, options: List[str], default: str) -> str:
    text_lower = text.lower()
    for option in options:
        if option in text_lower:
            return option
    return default


def _closest_team(raw: str) -> str:
    aliases = {
        "bill": "billing",   "charge": "billing",  "payment": "billing",
        "invoice": "billing", "subscription": "billing",
        "tech": "technical", "bug": "technical",   "crash": "technical",
        "api": "technical",  "software": "technical",
        "return": "returns", "refund": "returns",  "exchange": "returns",
        "general": "general_inquiry", "inquiry": "general_inquiry",
        "info": "general_inquiry",    "question": "general_inquiry",
        "secur": "security", "hack": "security",   "fraud": "security",
        "phish": "security", "breach": "security",
    }
    for key, team in aliases.items():
        if key in raw:
            return team
    return "general_inquiry"


# ── Model call ────────────────────────────────────────────────────────────────

def call_model(client: OpenAI, ticket_subject: str, ticket_text: str) -> str:
    user_prompt = textwrap.dedent(f"""
        Subject: {ticket_subject}

        Message:
        {ticket_text}

        Route this ticket.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] Model call failed: {exc}", flush=True)
        return '{"team": "general_inquiry", "priority": "medium"}'


# ── Episode runner ────────────────────────────────────────────────────────────

async def run_task(env: CSRoutingEnv, client: OpenAI, task_name: str) -> None:
    rewards:     List[float] = []
    steps_taken: int         = 0
    score:       float       = 0.0
    success:     bool        = False

    log_start(task=task_name, model=MODEL_NAME)

    try:
        result = await env.reset(task=task_name)
        obs    = result.observation

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            # Ask the model to route this ticket
            raw_response = call_model(client, obs.ticket_subject, obs.ticket_text)
            action       = parse_action(raw_response)
            action_str   = f"route(team={action.team},priority={action.priority})"

            # Apply the action
            result = await env.step(action)
            obs    = result.observation

            rewards.append(result.reward)
            steps_taken = step

            log_step(
                step=step,
                action=action_str,
                reward=result.reward,
                done=result.done,
                error=None,
            )

            if result.done:
                break

        # Final score = mean per-ticket reward (already in [0, 1])
        score   = sum(rewards) / max(len(rewards), 1)
        score   = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_name} error: {exc}", flush=True)
        score   = 0.0
        success = False
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    if IMAGE_NAME:
        print(f"[DEBUG] Starting Docker container from image: {IMAGE_NAME}", flush=True)
        env = await CSRoutingEnv.from_docker_image(IMAGE_NAME)
    else:
        print(f"[DEBUG] Connecting to server at: {SERVER_URL}", flush=True)
        env = CSRoutingEnv.from_url(SERVER_URL)

    try:
        for task_name in TASKS:
            await run_task(env, client, task_name)
    finally:
        await env.close()


if __name__ == "__main__":
    asyncio.run(main())