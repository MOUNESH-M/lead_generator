"""
run_pipeline.py — Full Phase 1 + Phase 2 pipeline entry point
"""
import json
from format_data import convert_csv_to_json
from pipeline.intelligence_pipeline import process_leads
from enrich import enrich_leads
from preprocess import preprocess_leads
from icp import generate_icp

# ── USER INPUT ────────────────────────────────────────────────────────────────

print("🔹 User Input:")
product = input("Enter your product description: ").strip()
while not product:
    print("⚠️  Product cannot be empty")
    product = input("Enter your product description: ").strip()

target_market = input("Target market (optional, press Enter to skip): ").strip()
region        = input("Region (optional, press Enter to skip): ").strip() or "USA"

print()

# ── PHASE 1: ICP GENERATION + DATA PIPELINE ──────────────────────────────────

user_input = {
    "product":       product,
    "target_market": target_market,
    "region":        region,
}

print("⚙️  Generating ICP...")
icp = generate_icp(user_input)

print("\n🔹 Generated ICP:")
print(icp)
print()

# Step 1: Convert clay-enriched CSV → JSON
convert_csv_to_json("clay_enriched_leads.csv")

# Step 2: Load formatted leads
with open("formatted_leads.json", "r") as f:
    leads = json.load(f)

# Step 3: Clean, validate, deduplicate
leads = preprocess_leads(leads)

# ── PHASE 2: INTELLIGENCE + SCORING + OUTREACH ───────────────────────────────

print("\n" + "=" * 60)
print("PHASE 2: INTELLIGENCE + SCORING + OUTREACH")
print("=" * 60)

# Enrich leads with ICP signals
print("\n[1/2] Enriching leads with intent/risk signals ...")
leads = enrich_leads(leads, icp)

# Run full intelligence pipeline
print("[2/2] Running intelligence pipeline ...")
results = process_leads(leads, product)

# ── SAVE OUTPUT ───────────────────────────────────────────────────────────────

with open("final_results.json", "w") as f:
    json.dump(results, f, indent=4)

# ── SUMMARY ───────────────────────────────────────────────────────────────────

hot  = sum(1 for r in results if r["label"] == "Hot")
warm = sum(1 for r in results if r["label"] == "Warm")
cold = sum(1 for r in results if r["label"] == "Cold")

print("\n" + "=" * 60)
print("✅ PIPELINE COMPLETE")
print("=" * 60)
print(f"   Total processed : {len(results)}")
print(f"   🔥 Hot          : {hot}")
print(f"   🌡  Warm         : {warm}")
print(f"   ❄️  Cold          : {cold}")
print(f"\n   Output saved to : final_results.json")
