import csv

def load_leads_csv(file_path):
    leads = []

    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # combine first + last name
            name = f"{row.get('First Name','')} {row.get('Last Name','')}".strip()

            lead = {
                "name": name,
                "role": row.get("Title") or "",
                "company": row.get("Company Name") or "",
                "email": row.get("Email") or "",
                "linkedin": row.get("Person Linkedin Url") or "",
                "source": "apollo"
            }

            leads.append(lead)

    return leads