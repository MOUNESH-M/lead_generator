import hashlib
from modules.context import extract_keywords

print("🔥 INTENT FILE LOADED")


def _pick(options, seed_str):
    idx = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % len(options)
    return options[idx]


# ── SIGNAL STRENGTH WEIGHTS ──────────────────────────────────────────────────
# Each raw signal is scored 0–100, then multiplied by its weight.
# Final intent_score = weighted sum, capped at 100.
#
#   hiring_signal   × 0.40  ← strongest: direct buying trigger
#   funding_signal  × 0.30  ← strong: budget + mandate
#   tech_signal     × 0.20  ← medium: fit, not urgency
#   github_signal   × 0.10  ← supporting: culture signal only
#
_WEIGHTS = {
    "hiring":  0.40,
    "funding": 0.30,
    "tech":    0.20,
    "github":  0.10,
}


def compute_intent(lead, product):

    signals  = []
    name     = lead.get("name", "")
    keywords = extract_keywords(product)
    tech     = [t.lower() for t in lead.get("tech", [])]

    # ── HIRING SIGNAL (0–100) ─────────────────────────────────────────────
    hiring_raw = 0
    if lead.get("hiring") == "High":
        hiring_raw = 100
        phrases = [
            "Actively expanding the engineering team.",
            "Hiring signal is strong — headcount growing.",
            "High hiring pace suggests infrastructure investment is coming.",
            "Team growth underway — tooling decisions likely imminent.",
            "Recruiting heavily, which usually precedes a budget cycle.",
        ]
        signals.append(_pick(phrases, name + "hiring"))
    elif lead.get("hiring") == "Moderate":
        hiring_raw = 50
        signals.append("Moderate hiring activity — steady growth signal.")

    # ── FUNDING SIGNAL (0–100) ────────────────────────────────────────────
    funding     = lead.get("funding")
    funding_raw = 0
    if funding in ["Series B", "Series C"]:
        funding_raw = 100
        phrases = [
            "{} funded — budget and mandate to scale.".format(funding),
            "Raised {} — in active growth mode.".format(funding),
            "{} stage means they have both the money and the urgency.".format(funding),
            "Post-{} companies are prime buyers — runway and pressure.".format(funding),
        ]
        signals.append(_pick(phrases, name + "funding"))
    elif funding == "Series A":
        funding_raw = 60
        phrases = [
            "Series A stage — building the foundation, decisions being made now.",
            "Post-Series A companies are setting up their core infra stack.",
            "Series A funded — early growth, high value-per-decision.",
        ]
        signals.append(_pick(phrases, name + "funding"))
    elif funding == "Seed":
        funding_raw = 20
        signals.append("Seed stage — early, but signals worth watching.")

    # ── TECH SIGNAL (0–100) ───────────────────────────────────────────────
    tech_raw = 0
    matches  = set(tech) & set(keywords)
    if matches:
        tech_raw = 100
        readable = ", ".join(sorted(matches))
        phrases  = [
            "Their stack ({}) aligns directly with the product.".format(readable),
            "Running {} — strong product-market fit signal.".format(readable),
            "Tech overlap detected: {} matches core use case.".format(readable),
            "Infrastructure includes {} — relevant buying context.".format(readable),
            "{} in their stack puts them squarely in the ICP.".format(readable),
        ]
        signals.append(_pick(phrases, name + "tech"))
    elif tech:
        tech_raw = 30   # Has tech data, just no keyword overlap

    # ── GITHUB SIGNAL (0–100) ─────────────────────────────────────────────
    github_raw = 0
    if lead.get("github_activity") == "High":
        github_raw = 100
        phrases = [
            "High GitHub activity — engineers are actively shipping.",
            "Strong OSS presence signals a technical, tool-savvy team.",
            "Active repos suggest an engineering culture that values tooling.",
            "High commit activity — team moves fast and values efficiency.",
        ]
        signals.append(_pick(phrases, name + "github"))
    elif lead.get("github_activity") == "Moderate":
        github_raw = 50

    # ── WEIGHTED SCORE ────────────────────────────────────────────────────
    raw_score = (
        hiring_raw  * _WEIGHTS["hiring"]  +
        funding_raw * _WEIGHTS["funding"] +
        tech_raw    * _WEIGHTS["tech"]    +
        github_raw  * _WEIGHTS["github"]
    )

    # Deterministic jitter: -5 to +5 per lead, stable across runs
    jitter = (int(hashlib.md5(name.encode()).hexdigest(), 16) % 11) - 5
    score  = int(max(0, min(100, raw_score + jitter)))

    return score, signals
