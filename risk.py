print("🔥 RISK FILE LOADED")

def compute_risk(lead):

    risk = 0
    reasons = []

    tech = [t.lower() for t in lead.get("tech", [])]
    size = lead.get("size", 0)
    hiring = lead.get("hiring")
    funding = lead.get("funding")
    github = lead.get("github_activity")

    # ---------------------------
    # Company size risk (nuanced, not binary)
    # ---------------------------
    if size < 50:
        risk += 25
        reasons.append("Very small company — budget risk")
    elif size < 100:
        risk += 12
        reasons.append("Small company — limited budget")
    elif size > 1000:
        risk += 8
        reasons.append("Enterprise — long sales cycle")

    # ---------------------------
    # Hiring signal
    # ---------------------------
    if hiring == "Low":
        risk += 18
        reasons.append("Not actively hiring — low growth signal")
    elif hiring == "High" and funding in ["Seed", None]:
        risk += 5
        reasons.append("Hiring fast but early-stage — budget risk")

    # ---------------------------
    # Funding risk (nuanced)
    # ---------------------------
    if funding == "Seed":
        risk += 15
        reasons.append("Early stage — limited runway")
    elif funding == "Series A":
        risk += 5
        reasons.append("Series A — budget may be constrained")
    elif not funding:
        risk += 10
        reasons.append("No funding data")
    # Series B/C → no penalty (positive signal)

    # ---------------------------
    # Tech risk
    # ---------------------------
    if "legacy" in tech:
        risk += 15
        reasons.append("Legacy tech stack")
    if not tech:
        risk += 10
        reasons.append("No tech data")

    # ---------------------------
    # GitHub activity
    # ---------------------------
    if github == "Low":
        risk += 10
        reasons.append("Low GitHub activity")
    if size > 500 and github == "Low":
        risk += 7        # Extra penalty: large but inactive
        reasons.append("Large company with low eng activity")

    # ---------------------------
    # Mixed signal penalty (nuanced combination risk)
    # ---------------------------
    if hiring == "Low" and funding in ["Seed", "Series A"]:
        risk += 8
        reasons.append("Low hiring + early stage — weak signals")

    if len(tech) > 3:
        risk += 5
        reasons.append("Complex multi-tool stack")

    # ---------------------------
    # FINAL CAP
    # ---------------------------
    risk = min(risk, 100)

    return risk, reasons
