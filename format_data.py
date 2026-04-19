import csv
import json
import re


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def extract_size(size_str):
    if not size_str:
        return 0

    nums = re.findall(r'\d+', size_str.replace(",", ""))
    return int(nums[0]) if nums else 0


def parse_tech_stack(tech_str):
    if not tech_str:
        return []

    # remove brackets and quotes
    tech_str = tech_str.replace("[", "").replace("]", "").replace("'", "")
    return [t.strip() for t in tech_str.split(",") if t.strip()]


def normalize_hiring(hiring, intent):
    if hiring == "True":
        return "High"
    if hiring == "False":
        return "Low"

    # fallback using intent
    if intent == "High":
        return "High"
    return "Low"


def normalize_role(role):
    role = role.lower()

    if "cto" in role:
        return "CTO"
    if "vp" in role:
        return "VP Engineering"

    return role.title()


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def convert_csv_to_json(input_file, output_file="formatted_leads.json"):
    output = []

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            lead = {
                "company": row.get("company", ""),
                "name": row.get("name", ""),
                "role": normalize_role(row.get("role", "")),
                "title": normalize_role(row.get("role", "")),
                "email": row.get("email", ""),
                "linkedin": row.get("linkedin", ""),
                "source": row.get("source", "apollo"),
                "size": extract_size(row.get("company_size", "")),
                "tech": parse_tech_stack(row.get("tech_stack", "")),
                "funding": row.get("funding", ""),
                "hiring": normalize_hiring(
                    row.get("hiring SIGNALS", ""),
                    row.get("intent_signal", "")
                ),
                "github_activity": "Unknown"   # optional (future)
            }

            output.append(lead)

    # save JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print(f"✅ Converted to {output_file}")