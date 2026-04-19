def adjust_urgency(intent_score, risk_score):
    """
    Base urgency from intent_score alone.
    Risk >= 20 always downgrades urgency one step.
    """
    if intent_score >= 75:
        urgency = "high"
    elif intent_score >= 50:
        urgency = "medium"
    else:
        urgency = "low"

    base_urgency  = urgency
    risk_adjusted = False

    if risk_score >= 20:
        if urgency == "high":
            urgency       = "medium"
            risk_adjusted = True
        elif urgency == "medium":
            urgency       = "low"
            risk_adjusted = True

    return urgency, base_urgency, risk_adjusted


def generate_strategy(lead, intent_score, risk_score, product, label=""):
    """
    Urgency driven by intent_score, then risk-adjusted if risk_score >= 20.
    Warm leads are capped at medium urgency regardless of intent.
    """
    tech = [t.lower() for t in lead.get("tech", [])]

    if "aws" in tech:
        hook  = "rising AWS costs"
        angle = "cost reduction"
    elif "kubernetes" in tech:
        hook  = "Kubernetes scaling inefficiencies"
        angle = "infrastructure optimization"
    elif "azure" in tech:
        hook  = "Azure cost management challenges"
        angle = "cloud optimization"
    else:
        hook  = "cloud spend inefficiency"
        angle = "optimization"

    urgency, base_urgency, risk_adjusted = adjust_urgency(intent_score, risk_score)

    # Warm leads should never carry high urgency — cap it
    if label == "Warm" and urgency == "high":
        urgency       = "medium"
        risk_adjusted = True

    return {
        "angle":           angle,
        "hook":            hook,
        "product_context": product,
        "urgency":         urgency,
        "base_urgency":    base_urgency,
        "risk_adjusted":   risk_adjusted,
        "label":           label,
    }
