# modules/ab_test.py
import hashlib


def _pick(options, seed_str):
    idx = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % len(options)
    return options[idx]


# ── ROLE-AWARE PERSONA LINES ─────────────────────────────────────────────────

_ROLE_CONTEXT = {
    "CTO": {
        "focus":    "architecture and engineering velocity",
        "worry":    "your infrastructure costs are scaling faster than your revenue",
        "outcome":  "engineering efficiency",
        "cta_a":    "Worth a 15-min technical chat?",
        "cta_b":    "Happy to share how other CTOs have approached this — useful?",
    },
    "VP Engineering": {
        "focus":    "team delivery speed and infra reliability",
        "worry":    "cloud spend is eating into your team's shipping capacity",
        "outcome":  "delivery speed",
        "cta_a":    "Open to a quick call this week?",
        "cta_b":    "Would it help to see how similar VP Eng teams solved this?",
    },
    "Founder": {
        "focus":    "unit economics and runway",
        "worry":    "cloud costs are one of the fastest-growing line items at your stage",
        "outcome":  "cost efficiency",
        "cta_a":    "Worth a short conversation?",
        "cta_b":    "Happy to share what founders at your stage typically find useful — interested?",
    },
    "Director of Engineering": {
        "focus":    "operational reliability and cost predictability",
        "worry":    "unpredictable cloud bills are making capacity planning harder",
        "outcome":  "infrastructure predictability",
        "cta_a":    "Open to a 15-minute chat?",
        "cta_b":    "Would benchmarks from similar engineering orgs be useful?",
    },
}

_ROLE_CONTEXT_DEFAULT = {
    "focus":    "infrastructure efficiency",
    "worry":    "cloud costs are scaling faster than expected",
    "outcome":  "operational efficiency",
    "cta_a":    "Worth a quick chat?",
    "cta_b":    "Happy to share relevant examples — would that be useful?",
}


# ── HYPOTHESIS BANK — varies by label + tech + funding ───────────────────────

def _choose_hypothesis(lead, strategy):
    """
    Pick a hypothesis that reflects a genuine strategic tradeoff
    based on this specific lead's profile.
    """
    label   = strategy.get("label", "Warm")
    tech    = [t.lower() for t in lead.get("tech", [])]
    funding = lead.get("funding", "")
    hiring  = lead.get("hiring", "")
    role    = lead.get("role", "")

    # Hot + Series B/C + hiring → urgency vs social proof
    if label == "Hot" and funding in ("Series B", "Series C") and hiring == "High":
        return (
            "Urgency framing (act now — decision window is open) "
            "vs Social proof framing (teams like yours already solved this)"
        )

    # Hot + AWS/Kubernetes → cost savings number vs engineering pain
    if label == "Hot" and any(t in tech for t in ("aws", "kubernetes")):
        return (
            "Concrete ROI framing (20-35% cost reduction) "
            "vs Engineering pain framing (infra complexity slowing velocity)"
        )

    # Warm + CTO/VP → curiosity-led vs benchmark data
    if label == "Warm" and any(r in role for r in ("CTO", "VP")):
        return (
            "Curiosity-led opener (question-first, no pitch) "
            "vs Benchmark data offer (industry comparison, low pressure)"
        )

    # Warm + early funding → risk-reduction vs growth enablement
    if label == "Warm" and funding in ("Seed", "Series A"):
        return (
            "Risk-reduction framing (protect runway, avoid surprises) "
            "vs Growth enablement framing (scale without cost explosion)"
        )

    # Cold → nurture vs re-engagement
    if label == "Cold":
        return (
            "Soft nurture (plant a seed, no ask) "
            "vs Trigger-based re-engagement (watch for hiring/funding signal)"
        )

    # Default fallback — still specific
    return (
        "Problem-first framing (lead with their pain) "
        "vs Outcome-first framing (lead with what they gain)"
    )


# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────

def generate_ab(lead, strategy):

    name    = lead.get("name", "there")
    company = lead.get("company", "your company")
    role    = lead.get("role", "")
    hook    = strategy.get("hook", "cloud spend inefficiency")
    angle   = strategy.get("angle", "cost reduction")
    label   = strategy.get("label", "Warm")
    funding = lead.get("funding", "")
    hiring  = lead.get("hiring", "")
    tech    = lead.get("tech", [])
    tech_str = ", ".join(tech) if tech else "your stack"

    # Role-aware persona context
    ctx = _ROLE_CONTEXT.get(role, _ROLE_CONTEXT_DEFAULT)

    # ── VARIANT A: Problem / Urgency framing ─────────────────────────────────
    if label == "Hot" and funding in ("Series B", "Series C") and hiring == "High":
        variant_a = (
            f"Hi {name},\n\n"
            f"As {role} at {company} — with {funding} funding and an active hiring push — "
            f"{ctx['worry']}.\n\n"
            f"We help engineering leaders at this stage fix that before it becomes a blocker. "
            f"Most see a 20-35% reduction without touching their architecture.\n\n"
            f"{ctx['cta_a']}"
        )
    elif label == "Hot":
        variant_a = (
            f"Hi {name},\n\n"
            f"For a {role} running {tech_str}, {ctx['worry']}.\n\n"
            f"We've helped teams on similar stacks {angle} — usually in the first 30 days.\n\n"
            f"{ctx['cta_a']}"
        )
    elif label == "Warm":
        variant_a = (
            f"Hi {name},\n\n"
            f"Working with a few {role}s at {funding or 'growth-stage'} companies right now "
            f"and {hook} keeps coming up as the pressure point.\n\n"
            f"Not sure if it's on your radar at {company}, but happy to share what's working "
            f"for teams with a similar setup.\n\n"
            f"{ctx['cta_a']}"
        )
    else:  # Cold
        variant_a = (
            f"Hi {name},\n\n"
            f"Flagging this for when the timing is right — {hook} tends to surface at {company}'s "
            f"stage, and we've helped teams get ahead of it before it becomes urgent.\n\n"
            f"No ask right now. Happy to share a one-pager if useful."
        )

    # ── VARIANT B: Curiosity / Outcome / Benchmark framing ───────────────────
    if label == "Hot" and funding in ("Series B", "Series C"):
        variant_b = (
            f"Hi {name},\n\n"
            f"Other {role}s at {funding} companies we work with usually describe the same inflection: "
            f"the stack that got you here starts fighting you as you scale.\n\n"
            f"We built something specifically for that moment — teams running {tech_str} see "
            f"the clearest results.\n\n"
            f"{ctx['cta_b']}"
        )
    elif label == "Hot":
        variant_b = (
            f"Hi {name},\n\n"
            f"Quick question — how are you currently managing {hook} at {company}?\n\n"
            f"We've seen {role}s on {tech_str} improve {ctx['outcome']} significantly with one "
            f"change to how they monitor spend. Happy to show you the benchmark data.\n\n"
            f"{ctx['cta_b']}"
        )
    elif label == "Warm":
        variant_b = (
            f"Hi {name},\n\n"
            f"We recently pulled benchmarks on {hook} across {funding or 'growth-stage'} "
            f"engineering teams — the variance is pretty striking.\n\n"
            f"Happy to send {company}'s peer comparison if that would be useful context "
            f"for your planning.\n\n"
            f"{ctx['cta_b']}"
        )
    else:  # Cold
        variant_b = (
            f"Hi {name},\n\n"
            f"Not the right moment? Totally fine — I'll check back when {company} hits a "
            f"hiring or funding milestone that usually signals {hook} becoming urgent.\n\n"
            f"In the meantime, happy to send over our {tech_str} cost benchmark if it's useful."
        )

    hypothesis = _choose_hypothesis(lead, strategy)

    return {
        "A":          variant_a,
        "B":          variant_b,
        "hypothesis": hypothesis,
    }
