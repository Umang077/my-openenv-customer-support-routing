---
title: Customer Support Routing
emoji: 🎫
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
tags:
  - openenv
---

# Customer Support Routing — OpenEnv Environment

An OpenEnv environment where an AI agent triages customer support tickets by
routing each one to the correct team and assigning an appropriate priority level.
This simulates real tier-1 support triage as performed by agents at scale.

## Motivation

Support teams at SaaS companies route hundreds of tickets per day. Misrouting
wastes agent time, increases resolution time, and hurts CSAT scores. An AI that
can accurately triage tickets is immediately useful in production.

## Action Space

| Field      | Type   | Values                                                      |
|------------|--------|-------------------------------------------------------------|
| `team`     | string | `billing`, `technical`, `returns`, `general_inquiry`, `security` |
| `priority` | string | `low`, `medium`, `high`                                     |
| `notes`    | string | optional free-text routing notes                           |

## Observation Space

| Field                | Type         | Description                                  |
|----------------------|--------------|----------------------------------------------|
| `ticket_id`          | string       | Unique ticket identifier                     |
| `ticket_subject`     | string       | One-line subject from the customer           |
| `ticket_text`        | string       | Full message body                            |
| `available_teams`    | list[string] | Valid routing targets                        |
| `available_priorities` | list[string] | Valid priority levels                      |
| `tickets_completed`  | int          | Number of tickets routed so far             |
| `tickets_total`      | int          | Total tickets in this task                  |
| `current_score`      | float        | Running mean score in [0, 1]                |
| `task_name`          | string       | Active task name                            |
| `task_difficulty`    | string       | `easy` / `medium` / `hard`                  |

## Tasks

| Task               | Difficulty | Tickets | Team weight | Priority weight | Description |
|--------------------|------------|---------|-------------|-----------------|-------------|
| `simple_routing`   | easy       | 5       | 1.0         | 0.0             | Clear unambiguous tickets; only team is graded |
| `priority_routing` | medium     | 6       | 0.6         | 0.4             | Both team and priority evaluated; some urgency cues |
| `batch_routing`    | hard       | 8       | 0.5         | 0.5             | Misleading subject lines; agent must read full body |

## Reward Function

Each ticket is scored in **[0.0, 1.0]**:

- **Team**: exact match = 1.0, any mismatch = 0.0  
- **Priority**: exact = 1.0, off by one level = 0.5, off by two = 0.0  
- **Episode score** = mean of per-ticket rewards

This gives meaningful partial-progress signal throughout the episode rather than
sparse end-of-episode binary reward.

## API Endpoints

| Method | Path      | Description                        |
|--------|-----------|------------------------------------|
| POST   | `/reset`  | Start new episode (`{"task": "..."}`) |
| POST   | `/step`   | Route current ticket               |
| GET    | `/state`  | Inspect episode state              |
| GET    | `/health` | Health check                       |

## Setup

### Run server locally
```bash
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### Run with Docker
```bash
docker build -t cs-routing-env .
docker run -p 7860:7860 cs-routing-env
```

### Run inference script
```bash
pip install -r requirements-inference.txt

export HF_TOKEN=hf_your_token_here
export SERVER_URL=http://localhost:8000   # or your HF Space URL

python inference.py
```

## Baseline Scores

Tested with `Qwen/Qwen2.5-72B-Instruct` via HF Inference Router:

| Task               | Score  | Notes                                          |
|--------------------|--------|------------------------------------------------|
| `simple_routing`   | ~0.900 | Obvious keywords; most frontier models ace this |
| `priority_routing` | ~0.680 | Urgency detection is harder                    |
| `batch_routing`    | ~0.490 | Misleading subjects require careful reading    |