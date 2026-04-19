import random
import re
import hashlib

def _stable_hash(s, mod):
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % mod


print("🔥 ENRICH FILE LOADED")

# -------------------------------
# HELPER: EXTRACT NUMERIC COMPANY SIZE
# -------------------------------
def extract_size_range(size_str):
    nums = re.findall(r'\d+', size_str.replace(",", ""))
    return int(nums[0]) if nums else 0


# -------------------------------
# MOCK DATA POOLS
# -------------------------------
COMPANY_SIZES = [
    "50-100 employees",
    "100-500 employees",
    "500-1000 employees",
    "1000+ employees"
]

FUNDING_STAGES = [
    "Seed",
    "Series A",
    "Series B",
    "Series C"
]


# -------------------------------
# ENRICH SINGLE LEAD
# -------------------------------
def enrich_lead(lead, icp):

    # ---------------------------
    # Numeric Size + consistent company_size label
    # ---------------------------
    # Deterministic size per lead — consistent across runs
    size_seed = _stable_hash(lead.get('company', '') + lead.get('name', ''), 5)
    size = [50, 100, 200, 500, 1000][size_seed]
    lead["size"] = size

    if size < 100:
        lead["company_size"] = "0-100 employees"
    elif size < 500:
        lead["company_size"] = "100-500 employees"
    else:
        lead["company_size"] = "500+ employees"


    # ---------------------------
    # Tech Stack
    # ---------------------------
    # Tech Stack — only assign if lead has none; preserve source tech
    if not lead.get("tech"):
        techs = icp.get("tech_stack", ["AWS"])
        if len(techs) >= 2:
            lead["tech"] = random.sample(techs, 2)
        else:
            lead["tech"] = techs

    # ---------------------------
    # Funding — preserve source value, only fill if missing
    # ---------------------------
    if not lead.get("funding"):
        lead["funding"] = random.choice(FUNDING_STAGES)

    # ---------------------------
    # Hiring — preserve source value, only fill if missing
    # ---------------------------
    if not lead.get("hiring"):
        lead["hiring"] = random.choices(["High", "Low"], weights=[65, 35])[0]

    # ---------------------------
    # Intent Signal
    # ---------------------------
    lead["intent_signal"] = "High" if lead["hiring"] == "High" else "Medium"

    # ---------------------------
    # GitHub Activity — deterministic per lead via name hash
    # Same lead always gets same value; 60% High / 40% Low split
    # ---------------------------
    if not lead.get("github_activity") or lead["github_activity"] == "Unknown":
        seed = _stable_hash(lead.get("name", "") + lead.get("company", ""), 100)
        lead["github_activity"] = "High" if seed < 60 else "Low"

    # ---------------------------
    # Location
    # ---------------------------
    lead["location"] = icp.get("region", "USA") or "USA"

    return lead


# -------------------------------
# ENRICH ALL LEADS
# -------------------------------
def enrich_leads(leads, icp):
    return [enrich_lead(lead, icp) for lead in leads]
