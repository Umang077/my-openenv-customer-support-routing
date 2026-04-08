"""
Scoring logic for each ticket routing decision.
All scores are in [0.0, 1.0].
"""

PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def score_ticket(
    predicted_team: str,
    predicted_priority: str,
    correct_team: str,
    correct_priority: str,
    team_weight: float,
    priority_weight: float,
) -> float:
    """
    Score a single ticket routing action.

    Team scoring   : exact match → 1.0, any mismatch → 0.0
    Priority scoring:
        exact match   → 1.0
        off by 1 step → 0.5   (e.g. medium when high is correct)
        off by 2 steps → 0.0  (e.g. low when high is correct)

    Final reward = team_weight * team_score + priority_weight * priority_score
    """
    # ── Team score ────────────────────────────────────────────────────────────
    team_score = 1.0 if predicted_team.lower().strip() == correct_team.lower() else 0.0

    # ── Priority score ────────────────────────────────────────────────────────
    pred_rank = PRIORITY_ORDER.get(predicted_priority.lower().strip(), 1)
    corr_rank = PRIORITY_ORDER.get(correct_priority.lower(), 1)
    diff = abs(pred_rank - corr_rank)
    if diff == 0:
        priority_score = 1.0
    elif diff == 1:
        priority_score = 0.5
    else:
        priority_score = 0.0

    # When priority_weight == 0 (easy task) only team matters
    if priority_weight == 0.0:
        return team_score

    return team_weight * team_score + priority_weight * priority_score