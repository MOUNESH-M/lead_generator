from pipeline.intelligence_pipeline import process_leads

product = "AI resume screening tool"

leads = [
    {
        "company": "Datadog",
        "name": "John",
        "role": "CTO",
        "size": 300,
        "tech": ["AWS", "AI"],
        "funding": "Series B",
        "hiring": "High",
        "github_activity": "High"
    },
    {
        "company": "StartupX",
        "name": "Alice",
        "role": "VP Engineering",
        "size": 10,
        "tech": ["Legacy"],
        "hiring": "Low"
    }
]

results = process_leads(leads, product)

for r in results:
    print("\n", r)