import hashlib


def _pick(options, seed_str):
    idx = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % len(options)
    return options[idx]


def generate_outreach(lead, strategy):

    name       = lead.get("name", "there")
    company    = lead.get("company", "your company")
    role       = lead.get("role", "")
    tech_list  = lead.get("tech", [])
    tech_lower = [t.lower() for t in tech_list]
    tech_str   = ", ".join(tech_list) if tech_list else "your stack"
    funding    = lead.get("funding", "")
    hiring     = lead.get("hiring", "")
    urgency    = strategy.get("urgency", "medium")
    seed       = name + company

    # Role-aware context line
    _role_lines = {
        "CTO":                     "as the CTO",
        "VP Engineering":          "as VP Engineering",
        "Founder":                 "as a founder managing unit economics",
        "Director of Engineering": "as the engineering director",
        "Head of Engineering":     "as head of engineering",
        "Engineering Manager":     "as an engineering manager",
    }
    role_context = _role_lines.get(role, "at your level")

    # Pain detection
    if "aws" in tech_lower:
        pain     = "runaway AWS spend"
        pain_fix = "cut AWS costs by 20-35%"
    elif "kubernetes" in tech_lower:
        pain     = "Kubernetes overhead slowing velocity"
        pain_fix = "streamline Kubernetes ops and reduce waste"
    elif "azure" in tech_lower:
        pain     = "unpredictable Azure billing"
        pain_fix = "bring Azure costs under control"
    else:
        pain     = "cloud spend growing faster than usage"
        pain_fix = "reduce cloud overhead without touching your architecture"

    # ── OPENERS (7 variants per profile, company name embedded) ──────────
    if hiring == "High" and funding in ["Series B", "Series C"]:
        openers = [
            "{} just hit {} and is scaling the team — that combination usually triggers some big infra decisions.".format(company, funding),
            "Came across {} while researching fast-growing {} companies. The hiring pace caught my eye.".format(company, funding),
            "Congrats on the {} round. Teams at that stage usually start feeling {} around now.".format(funding, pain),
            "{} standing out — {} funded and actively growing the engineering org is a strong signal.".format(company, funding),
            "Noticed {} is in a big hiring push post-{}. That tends to surface {} sooner than expected.".format(company, funding, pain),
            "Researching high-growth {} teams — {} came up immediately.".format(funding, company),
            "{} is exactly the profile we work with: {} stage, engineering team expanding fast.".format(company, funding),
        ]
    elif hiring == "High":
        openers = [
            "Noticed {} is on an active hiring push — that usually means infra decisions aren't far behind.".format(company),
            "{}'s engineering headcount growth caught my attention. Fast-scaling teams tend to hit {} earlier than expected.".format(company, pain),
            "Saw {} is expanding the team. That tends to trigger a fresh look at the tooling stack.".format(company),
            "Came across {} while researching teams scaling their engineering org quickly.".format(company),
            "{} stood out — rapid team growth is usually a leading indicator of {} becoming a real issue.".format(company, pain),
            "Your hiring pace at {} is notable. Engineering growth at that speed usually surfaces some interesting infrastructure questions.".format(company),
            "Researching engineering teams on a growth trajectory — {} stood out immediately.".format(company),
        ]
    elif funding in ["Series B", "Series C"]:
        openers = [
            "Congrats on the {} round — that's a real milestone for {}.".format(funding, company),
            "Saw the {} announcement. Post-{} is when {} usually becomes impossible to ignore.".format(funding, funding, pain),
            "{} at {} stage — you're at exactly the point where cloud costs start demanding attention.".format(company, funding),
            "{} came up while I was researching {} companies optimising their infrastructure spend.".format(company, funding),
            "The {} raise at {} puts you in an interesting position — growth is on, but so is scrutiny on spend.".format(funding, company),
            "Noticed {} closed {}. Teams at that stage usually find {} sneaking up on them.".format(company, funding, pain),
            "Post-{} at {} — infra costs are usually the next line item that gets a hard look.".format(funding, company),
        ]
    elif funding:
        openers = [
            "Congrats on the {} round — big milestone for {}.".format(funding, company),
            "Saw {} closed {}. Growth stage is when {} tends to become urgent.".format(company, funding, pain),
            "{} is at an interesting inflection point — {} funded and building out the stack.".format(company, funding),
            "Noticed {} raised {}. That's usually when engineering teams start making some meaningful tooling calls.".format(company, funding),
            "{} came up while researching {} companies thinking carefully about their infrastructure costs.".format(company, funding),
            "Post-{} companies like {} are usually in the sweet spot for what we do.".format(funding, company),
            "Saw the {} funding for {}. Teams at that stage usually have both the budget and the urgency.".format(funding, company),
        ]
    else:
        openers = [
            "Came across {} while researching engineering teams running {}.".format(company, tech_str),
            "{}'s stack caught my attention — {} at scale has a well-known cost profile.".format(company, tech_str),
            "Noticed {} is running {}. Teams at that scale usually hit an inflection point around infrastructure costs.".format(company, tech_str),
            "Researching teams using {} — {} stood out as a strong fit.".format(tech_str, company),
            "Saw {} is using {}. There's a specific pattern we see with that setup that I wanted to flag.".format(company, tech_str),
            "{} came up in research around teams with {} infrastructure looking to optimise spend.".format(company, tech_str),
            "Your infrastructure setup at {} caught my eye — {} tends to surface {} at your scale.".format(company, tech_str, pain),
        ]

    opener = _pick(openers, seed + "opener")

    # ── VALUE PROPS (6 variants) ──────────────────────────────────────────
    value_props = [
        "We help engineering teams {}. Most see results in the first 30 days, without architectural changes.".format(pain_fix),
        "We built a platform that helps teams like {} {} — typically 20-35% reduction in the first quarter.".format(company, pain_fix),
        "Specialise in helping teams on {} {}. Engineers keep full control; we remove the waste.".format(tech_str, pain_fix),
        "For someone {}, the clearest win is usually {}. No architectural changes needed.".format(role_context, pain_fix),
        "We've helped similar teams on {} {}, usually without a single line of code changed.".format(tech_str, pain_fix),
        "We work with {} stage companies to {} — it's the exact problem we were built to solve.".format(funding or "growth", pain_fix),
    ]
    value = _pick(value_props, seed + "value")

    # ── CTAs (5 variants per urgency) ────────────────────────────────────
    label = strategy.get("label", "")

    if urgency == "high":
        ctas = [
            "Worth a 15-minute call this week?",
            "Open to a quick call? I can show you what this looks like for a team your size.",
            "Happy to run a fast cost estimate for your stack — want me to put one together?",
            "Could be worth 15 minutes. Open to it?",
            "If the timing works, I'd love to show you a quick breakdown. Interested?",
        ]
    elif urgency == "medium" and label == "Warm":
        # Softer, exploratory CTAs for Warm leads
        ctas = [
            "Would it be useful to explore whether there's a fit here?",
            "Happy to share a few examples — no commitment, just worth a look?",
            "Open to a relaxed 15-minute conversation to see if this resonates?",
            "Could be worth a low-key chat. Curious what you're seeing on your end.",
            "No pressure at all — happy to send over some context first if that's easier.",
        ]
    elif urgency == "medium":
        ctas = [
            "Would it make sense to connect briefly?",
            "Open to a short conversation if the timing is right?",
            "Worth a quick chat to see if there's a fit?",
            "Happy to send over more context if useful — or jump on a short call.",
            "Let me know if it's worth exploring. Happy to keep it to 15 minutes.",
        ]
    else:
        ctas = [
            "No pressure — happy to share more when the timing makes sense.",
            "Just flagging it for now. Reach out whenever it feels relevant.",
            "Feel free to come back to this whenever it's a better moment.",
            "Happy to send over a one-pager if that's easier than a call.",
            "No rush on this — reach out if it becomes timely.",
        ]

    cta = _pick(ctas, seed + "cta")

    # ── EMAIL STRUCTURES (4 distinct layouts) ────────────────────────────
    structure_idx = int(hashlib.md5((seed + "structure").encode()).hexdigest(), 16) % 4

    if structure_idx == 0:
        # Classic: opener → value → CTA
        body = "{}\n\n{}\n\n{}".format(opener, value, cta)

    elif structure_idx == 1:
        # Problem-first: opener → pain framing → value → CTA
        pain_frame = "At {}'s scale on {}, {} is usually one of the first things that needs attention.".format(
            company, tech_str, pain)
        body = "{}\n\n{}\n\n{}\n\n{}".format(opener, pain_frame, value, cta)

    elif structure_idx == 2:
        # Value-first: value → opener → CTA
        body = "{}\n\n{}\n\n{}".format(value, opener, cta)

    else:
        # Question-led: opener → rhetorical question → value → CTA
        question = "Has {} been on your radar at {}?".format(pain, company)
        body = "{}\n\n{}\n\n{}\n\n{}".format(opener, question, value, cta)

    return "Hi {},\n\n{}".format(name, body)
