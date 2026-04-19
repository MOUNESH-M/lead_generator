"""
preprocess.py — Phase 4 upgraded preprocessing pipeline
Handles: normalisation, validation, deduplication
"""
import re
from datetime import datetime, timezone


# ── NORMALISATION ─────────────────────────────────────────────────────────────

_TITLE_MAP = {
    ("cto", "chief technology officer", "chief tech officer"):         "CTO",
    ("ceo", "chief executive officer"):                                 "CEO",
    ("coo", "chief operating officer"):                                 "COO",
    ("vp engineering", "vice president engineering",
     "vp of engineering", "vice president of engineering"):             "VP Engineering",
    ("vp product", "vice president product",
     "vp of product", "vice president of product"):                     "VP Product",
    ("head of engineering", "head of technology"):                      "Head of Engineering",
    ("director of engineering", "engineering director"):                "Director of Engineering",
    ("director", ):                                                     "Director",
    ("head", ):                                                         "Head",
    ("engineering manager", "eng manager"):                             "Engineering Manager",
    ("founder", "co-founder", "cofounder"):                             "Founder",
}

_COUNTRY_MAP = {
    "us": "USA", "usa": "USA", "united states": "USA", "u.s.": "USA",
    "uk": "UK",  "united kingdom": "UK", "gb": "UK",
    "canada": "Canada", "ca": "Canada",
    "australia": "Australia", "au": "Australia",
    "germany": "Germany", "de": "Germany",
    "india": "India", "in": "India",
}

_COMPANY_SUFFIXES = re.compile(
    r"\b(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?|gmbh|s\.a\.?)\s*$",
    re.IGNORECASE,
)


def _clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())


def _normalise_company(name):
    """Strip legal suffixes, fix whitespace, title-case."""
    name = _clean_text(name)
    name = _COMPANY_SUFFIXES.sub("", name).strip(" ,.")
    return name.title() if name else "Unknown"


def _normalise_title(title):
    if not title:
        return ""
    lower = title.lower().strip()
    for keys, normalised in _TITLE_MAP.items():
        if any(lower == k or lower.startswith(k) for k in keys):
            return normalised
    return title.title()


def _normalise_country(country):
    if not country:
        return ""
    return _COUNTRY_MAP.get(country.lower().strip(), country.title())


def _normalise_email(email):
    return _clean_text(email).lower()


def clean_lead(lead):
    lead["name"]    = _clean_text(lead.get("name", ""))
    lead["company"] = _normalise_company(lead.get("company", ""))
    lead["email"]   = _normalise_email(lead.get("email", ""))
    lead["title"]   = _normalise_title(lead.get("title") or lead.get("role", ""))
    lead["role"]    = lead["title"]   # keep both keys in sync

    raw_country     = lead.get("country") or lead.get("location", "")
    lead["country"] = _normalise_country(raw_country)

    # Normalise hiring casing
    hiring = str(lead.get("hiring", "")).strip().title()
    lead["hiring"] = hiring if hiring in ("High", "Moderate", "Low") else hiring

    return lead


def clean_leads(leads):
    return [clean_lead(lead) for lead in leads]


# ── VALIDATION ────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)+$", re.IGNORECASE)

_REQUIRED_FIELDS = ["name", "company"]

_VALID_TITLES = {
    "CTO", "CEO", "COO", "VP Engineering", "VP Product",
    "Head of Engineering", "Director of Engineering",
    "Director", "Head", "Engineering Manager", "Founder",
}


def validate_lead(lead):
    """
    Returns (is_valid: bool, reasons: list[str])
    Soft validation — only hard-fails on truly unusable data.
    """
    reasons = []

    # Required fields
    for field in _REQUIRED_FIELDS:
        if not lead.get(field):
            reasons.append(f"missing {field}")

    # Email — optional but validated if present
    email = lead.get("email", "")
    if email and not _EMAIL_RE.match(email):
        reasons.append(f"invalid email format: {email!r}")

    # LinkedIn — warn but don't reject
    if not lead.get("linkedin"):
        reasons.append("no linkedin (warning only)")

    return len([r for r in reasons if "warning" not in r]) == 0, reasons


def validate_leads(leads):
    valid, invalid = [], []
    for lead in leads:
        ok, reasons = validate_lead(lead)
        if ok:
            valid.append(lead)
        else:
            invalid.append({"lead": lead.get("name", "?"), "reasons": reasons})

    if invalid:
        print(f"⚠️  Removed {len(invalid)} invalid leads:")
        for item in invalid[:5]:   # show first 5 only
            print(f"   • {item['lead']}: {', '.join(item['reasons'])}")
        if len(invalid) > 5:
            print(f"   … and {len(invalid)-5} more")

    return valid


# ── DEDUPLICATION ─────────────────────────────────────────────────────────────

def deduplicate_leads(leads):
    """
    Dedup priority (highest to lowest): email → linkedin → name+company slug.
    Keeps first occurrence (assumed most complete).
    """
    seen   = set()
    unique = []

    for lead in leads:
        keys = []

        email    = lead.get("email", "").strip().lower()
        linkedin = lead.get("linkedin", "").strip().lower()
        name_co  = (
            re.sub(r"\s+", "_", lead.get("name", "").lower()) + "|" +
            re.sub(r"\s+", "_", lead.get("company", "").lower())
        )

        if email:
            keys.append(("email", email))
        if linkedin:
            keys.append(("linkedin", linkedin))
        keys.append(("name_company", name_co))

        # Use the most specific key available
        fingerprint = keys[0]

        if fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(lead)

    removed = len(leads) - len(unique)
    if removed:
        print(f"🧹 Deduplicated: removed {removed} duplicate lead(s)")

    return unique


# ── FULL PIPELINE ─────────────────────────────────────────────────────────────

def preprocess_leads(leads):
    leads = clean_leads(leads)
    leads = validate_leads(leads)
    leads = deduplicate_leads(leads)
    return leads
