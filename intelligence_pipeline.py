"""
intelligence_pipeline.py — Full final build
All 14 checklist items implemented.
"""

import re
import math
import hashlib as _hl
from datetime import datetime, timezone

from modules.intent import compute_intent, _WEIGHTS as _INTENT_WEIGHTS
from modules.risk import compute_risk
from modules.scoring import compute_score
from modules.messaging import generate_strategy
from modules.outreach import generate_outreach
from modules.ab_test import generate_ab


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _pick(options, name, key):
    idx = int(_hl.md5((name + key).encode()).hexdigest(), 16) % len(options)
    return options[idx]


def _now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _days_since(iso_str):
    """Return days between an ISO-8601 UTC string and now. None if unparseable."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — CORE DATA UPGRADES
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. TIME INTELLIGENCE ─────────────────────────────────────────────────────

def compute_signal_recency(lead):
    """
    Reads lead.last_updated (ISO-8601). Returns:
        fresh  → < 7 days   → score boost  +8
        warm   → 7–30 days  → no change     0
        stale  → > 30 days  → score penalty -10
        unknown → no date   → no change     0
    """
    days = _days_since(lead.get("last_updated"))
    if days is None:
        return "unknown", 0
    if days < 7:
        return "fresh", +8
    if days <= 30:
        return "warm", 0
    return "stale", -10


# ── 2. CONVERSION PROBABILITY ────────────────────────────────────────────────

def compute_conversion_probability(score, risk_score, confidence):
    """
    Base range from score band, then nudged by risk and confidence.

    score > 80  → base 0.70 – 0.90
    score 50–80 → base 0.40 – 0.70
    score < 50  → base 0.10 – 0.40

    Adjustment: ±0.10 from confidence, −0.10 per 25pts of risk above 25.
    """
    if score > 80:
        base = 0.70 + (score - 80) / 100         # 0.70 – 0.90
    elif score >= 50:
        base = 0.40 + (score - 50) / 100         # 0.40 – 0.70
    else:
        base = 0.10 + score / 250                 # 0.10 – 0.30

    confidence_adj = (confidence - 0.5) * 0.20   # ±0.10
    risk_adj       = -max(0, (risk_score - 25) / 25) * 0.10

    return round(max(0.05, min(0.95, base + confidence_adj + risk_adj)), 2)


# ── 3. CONFIDENCE SCORE ──────────────────────────────────────────────────────

def compute_confidence(lead, intent_score, risk_score):
    """
    raw = (intent_score × 0.5) + (completeness × 0.3) − (risk_score × 0.2)
    Normalised over actual range [−20, 50.3] → 0.0–1.0
    """
    key_fields   = ["company", "name", "tech", "funding", "hiring",
                    "title", "industry", "email", "linkedin"]
    filled       = sum(1 for f in key_fields if lead.get(f))
    completeness = filled / len(key_fields)

    raw        = (intent_score * 0.5) + (completeness * 0.3) - (risk_score * 0.2)
    normalised = (raw - (-20)) / (50.3 - (-20))
    return round(max(0.0, min(1.0, normalised)), 2)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — INTELLIGENCE LAYER
# ─────────────────────────────────────────────────────────────────────────────

# ── 4. WEIGHTED INTENT SIGNAL OBJECTS (built inside compute_intent already) ──
#    Pipeline surfaces them as structured dicts — see _build_signal_objects()

def _build_signal_objects(lead, raw_signals):
    """
    Convert plain-text signal strings into structured weight-annotated objects.
    Matches signal text back to its source dimension and attaches its weight.
    """
    hiring  = (lead.get("hiring") or "").lower()
    funding = lead.get("funding") or ""
    tech    = [t.lower() for t in lead.get("tech", [])]
    github  = (lead.get("github_activity") or "").lower()

    # Dimension → weight mapping (mirrors _WEIGHTS in intent.py)
    dim_weights = {
        "hiring":  0.40,
        "funding": 0.30,
        "tech":    0.20,
        "github":  0.10,
    }

    objects = []
    for sig in raw_signals:
        sig_lower = sig.lower()
        if any(w in sig_lower for w in ("hiring", "headcount", "recruiting", "team growth")):
            dim = "hiring"
        elif any(w in sig_lower for w in ("funded", "funding", "stage", "raised", "series", "seed")):
            dim = "funding"
        elif any(w in sig_lower for w in ("stack", "tech", "infrastructure", "running", "icp")):
            dim = "tech"
        elif any(w in sig_lower for w in ("github", "commit", "oss", "repos")):
            dim = "github"
        else:
            dim = "other"

        objects.append({
            "type":   sig,
            "weight": dim_weights.get(dim, 0.05),
            "source": dim,
        })

    return objects


# ── 5. RISK FLAGS (structured) ───────────────────────────────────────────────
#    risk.py already returns risk_reasons as plain strings.
#    We surface them as structured flags here.

def _build_risk_flags(risk_reasons, risk_score):
    """
    Convert risk_reasons into flag objects with severity levels.
    """
    HIGH_RISK_KEYWORDS   = {"budget", "runway", "very small", "competitor"}
    MEDIUM_RISK_KEYWORDS = {"small", "limited", "early", "complex", "missing",
                            "low growth", "legacy", "no tech", "no funding"}

    flags = []
    for reason in risk_reasons:
        lower = reason.lower()
        if any(k in lower for k in HIGH_RISK_KEYWORDS):
            severity = "high"
        elif any(k in lower for k in MEDIUM_RISK_KEYWORDS):
            severity = "medium"
        else:
            severity = "low"

        # Slug the reason into a machine-readable flag key
        slug = re.sub(r"[^a-z0-9]+", "_", lower).strip("_")[:40]
        flags.append({"flag": slug, "detail": reason, "severity": severity})

    return flags


# ── 6. SEGMENT TAGGING ───────────────────────────────────────────────────────

def compute_segments(lead, label, intent_score, risk_score):
    tags    = []
    tech    = [t.lower() for t in lead.get("tech", [])]
    size    = lead.get("size", 0) or 0
    hiring  = (lead.get("hiring") or "").lower()
    funding = lead.get("funding") or ""
    industry = (lead.get("industry") or "").lower()

    # Growth profile
    if hiring in ("high", "aggressive") and funding in ("Series B", "Series C"):
        tags.append("High-growth")
    elif hiring in ("high", "aggressive"):
        tags.append("Scaling")
    elif label == "Cold":
        tags.append("Low-momentum")

    # Size band
    if size and size < 50:
        tags.append("Startup")
    elif size and size < 250:
        tags.append("SMB")
    elif size and size >= 1000:
        tags.append("Enterprise")
    elif size:
        tags.append("Mid-market")

    # Tech profile
    devops_tech = {"kubernetes", "docker", "terraform", "ansible", "jenkins"}
    if devops_tech & set(tech):
        tags.append("DevOps-heavy")
    if any(t in tech for t in ("aws", "azure", "gcp", "google cloud platform")):
        tags.append("Cloud-native")
    if "legacy" in tech:
        tags.append("Legacy-stack")

    # Industry
    if any(w in industry for w in ("saas", "software", "tech")):
        tags.append("SaaS")
    elif any(w in industry for w in ("fintech", "finance", "banking")):
        tags.append("Fintech")
    elif any(w in industry for w in ("health", "medical", "biotech")):
        tags.append("HealthTech")

    # Cost/risk sensitivity
    if intent_score >= 60 and risk_score <= 20:
        tags.append("Cost-sensitive")
    elif intent_score >= 60 and risk_score > 20:
        tags.append("Risk-flagged")

    return " | ".join(tags) if tags else "Unclassified"


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — SYSTEM EVOLUTION
# ─────────────────────────────────────────────────────────────────────────────

# ── 7. OUTCOME / FEEDBACK LOOP ───────────────────────────────────────────────
#    Outcome is written by downstream tools (CRM, SDR notes).
#    Pipeline preserves existing outcome; new leads default to None.
#    Score modifiers for similar leads can be applied in a future retraining pass.

_VALID_OUTCOMES = {"won", "lost", "no_response", None}


def _resolve_outcome(lead):
    outcome = lead.get("outcome")
    return outcome if outcome in _VALID_OUTCOMES else None


# ── 8. ACCOUNT-LEVEL AGGREGATION ─────────────────────────────────────────────
#    Built after all leads are processed; injected back into each lead.

def build_account_map(results):
    """
    Groups processed leads by normalised company name.
    Returns dict: slug → { company, account_score, total_leads, lead_names }
    """
    accounts = {}
    for lead in results:
        company = lead.get("company", "Unknown")
        slug    = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

        if slug not in accounts:
            accounts[slug] = {
                "company":      company,
                "account_score": 0,
                "total_leads":  0,
                "lead_names":   [],
                "scores":       [],
            }

        accounts[slug]["total_leads"]  += 1
        accounts[slug]["lead_names"].append(lead.get("name", "?"))
        accounts[slug]["scores"].append(lead.get("score", 0))

    # Compute account_score = average of lead scores (rounded)
    for slug, acc in accounts.items():
        acc["account_score"] = round(sum(acc["scores"]) / len(acc["scores"]))
        del acc["scores"]

    return accounts


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — PIPELINE (dedup / validation delegated to preprocess.py)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_STATUS  = "new"
_VALID_STATUSES  = {"new", "contacted", "replied", "closed", "lost"}

_FOLLOWUP_DAYS   = {"Hot": 1, "Warm": 4, "Cold": 14}

def _build_sequence(label, lead):
    """Generate a role-personalised outreach sequence."""
    role    = lead.get("role", "")
    funding = lead.get("funding", "")
    tech    = [t.lower() for t in lead.get("tech", [])]

    cto_or_vp = role in ("CTO", "VP Engineering", "Head of Engineering", "Director of Engineering")

    if label == "Hot":
        step1 = "Personalised cold email — reference {} funding and {} stack pain point".format(
            funding or "growth-stage", tech[0] if tech else "cloud")
        step3 = ("Follow-up — share a cost benchmark specific to their tech stack"
                 if any(t in tech for t in ("aws","kubernetes","azure","gcp"))
                 else "Follow-up — add relevant case study from a similar company")
        step5 = ("Offer a free 30-min cloud cost audit for their stack"
                 if cto_or_vp
                 else "Final value-add — offer a quick infrastructure estimate")
        return [
            {"day": 1,  "channel": "Email",    "action": step1},
            {"day": 3,  "channel": "LinkedIn", "action": "Connect request — reference the email, keep it brief"},
            {"day": 5,  "channel": "Email",    "action": step3},
            {"day": 8,  "channel": "LinkedIn", "action": "Engage with a recent post before second touch"},
            {"day": 10, "channel": "Email",    "action": step5},
        ]
    elif label == "Warm":
        step1 = ("Soft intro — explore {} pain, no hard pitch".format(tech[0] if tech else "cloud cost")
                 if cto_or_vp
                 else "Soft intro email — exploratory, no hard ask")
        step3 = ("Send {} cost benchmark data — no ask, just value".format(
                 tech[0].upper() if tech else "cloud")
                 if any(t in tech for t in ("aws","kubernetes","azure","gcp"))
                 else "Follow-up with relevant insight or benchmark data")
        return [
            {"day": 1,  "channel": "Email",    "action": step1},
            {"day": 5,  "channel": "LinkedIn", "action": "Connect request — keep it conversational"},
            {"day": 10, "channel": "Email",    "action": step3},
            {"day": 18, "channel": "LinkedIn", "action": "Comment on or share their content to build rapport"},
            {"day": 25, "channel": "Email",    "action": "Check-in — ask if timing has changed"},
        ]
    else:  # Cold
        trigger = "funding or hiring signal change" if not funding else "{} milestone".format(funding)
        return [
            {"day": 1,  "channel": "Email",    "action": "Low-pressure awareness email — plant a seed"},
            {"day": 14, "channel": "LinkedIn", "action": "Connect request only — no message yet"},
            {"day": 30, "channel": "Email",    "action": "Nurture touch — share useful content, no ask"},
            {"day": 60, "channel": "Email",    "action": "Re-evaluation check-in — watch for {}".format(trigger)},
        ]


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5 — OUTPUT QUALITY
# ─────────────────────────────────────────────────────────────────────────────

# ── 12. EXPLAINABLE REASON ───────────────────────────────────────────────────

def build_reason(lead, intent_signals, risk_flags, label):
    """
    One-line human-readable reason for the label.
    e.g. "Hiring engineers + Series B + AWS → strong ICP match"
    """
    parts = []

    hiring  = (lead.get("hiring") or "").lower()
    funding = lead.get("funding") or ""
    tech    = lead.get("tech") or []

    if hiring in ("high", "aggressive"):
        parts.append("active hiring")
    if funding in ("Series B", "Series C"):
        parts.append(funding)
    if tech:
        parts.append(" + ".join(tech[:2]))

    if not parts and intent_signals:
        # Fall back to first signal text, truncated
        parts.append(intent_signals[0][:50])

    signal_str = " + ".join(parts) if parts else "limited signals"

    suffix = {
        "Hot":  "→ strong ICP match, prioritise now",
        "Warm": "→ promising fit, nurture approach recommended",
        "Cold": "→ weak signals, revisit later",
    }.get(label, "")

    return "{} {}".format(signal_str, suffix).strip()


# ── 13. NEXT ACTION RECOMMENDATION ──────────────────────────────────────────

_NEXT_ACTIONS = {
    "Hot": [
        "Send personalised cost-optimisation email today",
        "Book a 15-min discovery call this week",
        "Run a quick infrastructure cost estimate and share it",
    ],
    "Warm": [
        "Send a low-pressure intro email with a relevant case study",
        "Connect on LinkedIn and engage with recent content first",
        "Share a benchmark report — no ask, just value",
    ],
    "Cold": [
        "Add to nurture sequence — check back in 30 days",
        "Monitor for funding or hiring signal changes",
        "Send a one-pager, no follow-up for 60 days",
    ],
}

def build_next_action(lead, label):
    idx = int(_hl.md5((lead.get("name","") + label).encode()).hexdigest(), 16) % 3
    return _NEXT_ACTIONS[label][idx]


# ── EXPLAINABILITY SCORE ─────────────────────────────────────────────────────

def compute_explainability(lead, intent_score, risk_score, confidence, signals):
    key_fields        = ["company", "name", "tech", "funding", "hiring",
                         "title", "industry", "size", "github_activity"]
    filled            = sum(1 for f in key_fields if lead.get(f))
    data_completeness = filled / len(key_fields)
    max_signals       = len(_INTENT_WEIGHTS)
    signal_clarity    = min(len(signals), max_signals) / max_signals
    raw               = (signal_clarity * 0.40) + (data_completeness * 0.35) + (confidence * 0.25)
    return round(max(0.0, min(1.0, raw)), 2)


# ── WHY-NOW ───────────────────────────────────────────────────────────────────

def _why_now(lead, intent_score, risk_score, label):
    triggers = []
    funding  = (lead.get("funding") or "").lower()
    hiring   = (lead.get("hiring")  or "").lower()
    tech     = [t.lower() for t in lead.get("tech", [])]

    if any(s in funding for s in ("series b", "series c", "series d")):
        triggers.append(funding.title())
    elif "series a" in funding:
        triggers.append("Series A")

    if hiring in ("high", "aggressive"):
        triggers.append("aggressive hiring pace")
    elif hiring == "moderate":
        triggers.append("steady hiring")

    if "aws" in tech and intent_score >= 60:
        triggers.append("AWS cost exposure")
    if "kubernetes" in tech:
        triggers.append("K8s scaling pressure")

    if risk_score >= 30 and label != "Hot":
        triggers.append("elevated risk (watch closely)")

    if not triggers:
        return None
    if len(triggers) == 1:
        return "{} = act now".format(triggers[0])
    return "{} + {} = decision window open".format(
        ", ".join(triggers[:-1]), triggers[-1]
    )


def generate_explanation(lead, intent_score, risk_score, label):
    tech    = ", ".join(lead.get("tech", [])) or "their stack"
    funding = lead.get("funding") or "unknown funding"
    hiring  = (lead.get("hiring") or "unknown").lower()
    company = lead.get("company") or "this company"
    name    = lead.get("name") or ""

    why_now      = _why_now(lead, intent_score, risk_score, label)
    why_now_line = "\n📍 Why now: {}".format(why_now) if why_now else ""

    if label == "Hot":
        intros = [
            "Strong fit — intent score {} with risk at only {}.".format(intent_score, risk_score),
            "{} scores {} on intent with minimal risk ({}) — top-tier prospect.".format(company, intent_score, risk_score),
            "High-confidence lead. Intent {}, risk {} — worth immediate attention.".format(intent_score, risk_score),
        ]
        details = [
            "Using {}, {} funded, {} hiring pace. Classic buying profile.".format(tech, funding, hiring),
            "Stack ({}), funding ({}), and {} hiring all pointing in the same direction.".format(tech, funding, hiring),
            "With {} in the stack and {} stage funding, conversion probability is high.".format(tech, funding),
        ]
    elif label == "Warm":
        intros = [
            "{} shows promising signals — worth exploring further before committing to a push.".format(company),
            "Solid potential here. Intent {} is encouraging; risk {} is something to keep an eye on.".format(intent_score, risk_score),
            "Good fit on paper — the data suggests a value-driven conversation rather than a hard pitch.",
        ]
        details = [
            "Tech ({}) and {} funding suggest readiness, but {} hiring pace calls for a softer touch.".format(tech, funding, hiring),
            "Lead with curiosity — explore their pain around {} before positioning a solution.".format(tech),
            "Right account, not quite the right moment. Build rapport and let them come to the ask.",
        ]
    else:
        intros = [
            "Low intent ({}) and elevated risk ({}). Not the right moment.".format(intent_score, risk_score),
            "{} scores {} on intent — weak signals relative to risk ({}).".format(company, intent_score, risk_score),
            "Intent {} does not justify the risk profile ({}) right now.".format(intent_score, risk_score),
        ]
        details = [
            "At {} stage with {} hiring, revisit in 60-90 days.".format(funding, hiring),
            "Flag for nurture sequence. Check back when funding or hiring signal improves.",
            "Low priority — fundamentals are not aligned for a near-term close.",
        ]

    body = _pick(intros, name, "intro") + "\n" + _pick(details, name, "detail")
    return "{} lead\n\n".format(label) + body + why_now_line


# ── COMPANY ID ────────────────────────────────────────────────────────────────

def make_company_id(company, seen_counts):
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")
    seen_counts[slug] = seen_counts.get(slug, 0) + 1
    return "{}_{}".format(slug, str(seen_counts[slug]).zfill(3))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def process_leads(leads, product):

    if not leads:
        return []

    results             = []
    seen_company_counts = {}
    processed_at        = _now_utc()

    for lead in leads:

        if not lead.get("company") or not lead.get("name"):
            continue

        # ── Scores ────────────────────────────────────────────────────────
        intent_score, raw_signals = compute_intent(lead, product)
        risk_score, risk_reasons  = compute_risk(lead)

        intent_score = max(0, min(100, intent_score))
        risk_score   = max(0, min(100, risk_score))

        # ── Time intelligence ──────────────────────────────────────────────
        signal_recency, recency_delta = compute_signal_recency(lead)
        if not lead.get("last_updated"):
            lead["last_updated"] = processed_at   # stamp on first processing

        # Apply recency delta to score
        score_raw, label_raw = compute_score(intent_score, risk_score, lead)
        score = max(0, min(100, score_raw + recency_delta))

        # Re-derive label after recency adjustment
        if score >= 75:
            label = "Hot"
        elif score >= 50:
            label = "Warm"
        else:
            label = "Cold"

        # ── Intelligence layer ─────────────────────────────────────────────
        confidence          = compute_confidence(lead, intent_score, risk_score)
        conversion_prob     = compute_conversion_probability(score, risk_score, confidence)
        intent_signal_objs  = _build_signal_objects(lead, raw_signals)
        risk_flags          = _build_risk_flags(risk_reasons, risk_score)
        segment             = compute_segments(lead, label, intent_score, risk_score)

        # ── Output quality ─────────────────────────────────────────────────
        strategy            = generate_strategy(lead, intent_score, risk_score, product, label=label)
        outreach_email      = generate_outreach(lead, strategy)
        ab                  = generate_ab(lead, strategy)
        explanation         = generate_explanation(lead, intent_score, risk_score, label)
        explainability      = compute_explainability(lead, intent_score, risk_score, confidence, raw_signals)
        reason              = build_reason(lead, raw_signals, risk_flags, label)
        next_action         = build_next_action(lead, label)

        # ── CRM fields ────────────────────────────────────────────────────
        company_id          = make_company_id(lead["company"], seen_company_counts)
        status              = lead.get("status", _DEFAULT_STATUS)
        if status not in _VALID_STATUSES:
            status = _DEFAULT_STATUS
        outcome             = _resolve_outcome(lead)

        # ── Maps ──────────────────────────────────────────────────────────
        priority_map = {"Hot": "High",  "Warm": "Medium", "Cold": "Low"}
        action_map   = {
            "Hot":  "Immediate outreach recommended",
            "Warm": "Nurture with targeted messaging",
            "Cold": "Low priority — revisit later",
        }

        lead.update({
            # Identity
            "company_id":             company_id,
            "processed_at":           processed_at,

            # Phase 1 — core data
            "last_updated":           lead.get("last_updated"),
            "signal_recency":         signal_recency,

            # Scores
            "intent_score":           intent_score,
            "risk_score":             risk_score,
            "score":                  score,
            "label":                  label,
            "confidence_score":       confidence,
            "conversion_probability": conversion_prob,
            "explainability_score":   explainability,

            # Phase 2 — intelligence
            "intent_signals":         intent_signal_objs,
            "risk_flags":             risk_flags,
            "risk_reasons":           risk_reasons,
            "segment":                segment,

            # Phase 3 — evolution
            "status":                 status,
            "outcome":                outcome,

            # Phase 4 — pipeline
            "priority":               priority_map[label],
            "action":                 action_map[label],
            "next_followup_days":     _FOLLOWUP_DAYS[label],
            "sequence":               _build_sequence(label, lead),

            # Phase 5 — output
            "reason":                 reason,
            "next_action":            next_action,
            "explanation":            explanation.strip(),
            "outreach_email":         outreach_email.strip(),
            "ab_test":                ab,
            "strategy":               strategy,
        })

        results.append(lead)

    results.sort(key=lambda x: x["score"], reverse=True)

    # ── Phase 3 — account aggregation (post-sort) ─────────────────────────
    account_map = build_account_map(results)
    for lead in results:
        slug = re.sub(r"[^a-z0-9]+", "_", lead.get("company", "").lower()).strip("_")
        lead["account"] = account_map.get(slug, {})

    return results
