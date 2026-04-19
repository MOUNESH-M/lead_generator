def compute_score(intent_score, risk_score, lead):
    """
    score = intent_score - (risk_score * 0.5)
    Risk genuinely penalises the score.

    When risk_score = 0: score == intent_score (correct — no penalty).
    When risk_score > 0: score < intent_score (risk applied).

    Thresholds:
      >= 75  -> Hot
      >= 50  -> Warm
      <  50  -> Cold
    """
    score = intent_score - int(risk_score * 0.5)
    score = max(0, min(100, score))

    if score >= 75:
        label = "Hot"
    elif score >= 50:
        label = "Warm"
    else:
        label = "Cold"

    return score, label
