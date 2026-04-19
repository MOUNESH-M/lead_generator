import random
import re


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def normalize_role(role):
    role = role.lower()

    if "cto" in role:
        return "CTO"
    if "vp" in role:
        return "VP Engineering"
    if "head" in role:
        return "Head of Infrastructure"

    return role.title()


def clean_text(text):
    import re

    text = re.sub(r'\(.*?\)', '', text)  # remove ()
    
    # replace long phrases
    text = text.replace("Software as a Service", "SaaS")
    
    words = text.split()
    return "".join(word.capitalize() for word in words)


def clean_email(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()


# -------------------------------
# 1. MOCK LEAD GENERATOR
# -------------------------------
def generate_mock_leads(icp, count=200):
    leads = []

    roles = icp.get("target_roles", ["CTO"])
    industries = icp.get("industries", ["Tech"])

    if not roles:
        roles = ["CTO"]
    if not industries:
        industries = ["Tech"]

    for i in range(count):
        raw_role = roles[i % len(roles)]
        role = normalize_role(raw_role)

        raw_industry = industries[i % len(industries)]
        industry = clean_text(raw_industry)

        company_name = f"{industry}Corp{i}"
        safe_company = clean_email(company_name)

        lead = {
            "name": f"Person_{i}",
            "role": role,
            "company": company_name,
            "email": f"person{i}@{safe_company}.com",
            "linkedin": f"https://linkedin.com/in/person{i}",
            "source": "mock"
        }

        # 🔥 ADD NOISE HERE (CORRECT PLACE)
        if i % 20 == 0:
            lead["email"] = "invalid_email"

        if i % 25 == 0:
            lead["company"] = ""

        leads.append(lead)

    return leads


# -------------------------------
# 2. FILTER BASED ON ICP
# -------------------------------
def filter_leads_by_icp(leads, icp):
    filtered = []

    # normalize ICP roles also
    target_roles = [normalize_role(r) for r in icp.get("target_roles", [])]

    for lead in leads:
        if lead["role"] in target_roles:
            filtered.append(lead)

    return filtered


# -------------------------------
# 3. ADD QUALITY SCORE
# -------------------------------
def add_quality_score(leads):
    for lead in leads:
        score = 0

        if lead.get("email"):
            score += 50
        if lead.get("linkedin"):
            score += 50

        lead["quality_score"] = score

    return leads


# -------------------------------
# 4. MAIN FUNCTION
# -------------------------------
def generate_leads(icp):
    leads = generate_mock_leads(icp, count=200)

    leads = filter_leads_by_icp(leads, icp)

    leads = add_quality_score(leads)

    return leads