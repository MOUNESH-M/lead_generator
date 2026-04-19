import requests
import json


# -------------------------------
# 1. BUILD PROMPT
# -------------------------------
def build_icp_prompt(user_input):
    return f"""
You are an expert in B2B sales and GTM strategy.

Convert the following product into a HIGH-QUALITY Ideal Customer Profile (ICP).

Return ONLY valid JSON.
Do NOT include explanation.
Do NOT include markdown or ```.

Make sure:
- Fill ALL fields (no empty lists)
- Be specific (avoid generic words like "cloud")
- Target decision makers (CTO, VP Engineering)

Format:
{{
  "industries": ["example"],
  "company_size": "example",
  "tech_stack": ["example"],
  "target_roles": ["example"],
  "buying_signals": ["example"],
  "pain_points": ["example"],
  "exclude": ["example"]
}}

Product: {user_input['product']}
Target Market: {user_input.get('target_market', '')}
Region: {user_input.get('region', '')}
"""


# -------------------------------
# 2. CALL OLLAMA
# -------------------------------
def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            print("⚠️ Ollama error:", response.text)
            return ""

        return response.json().get("response", "")

    except requests.exceptions.ConnectionError:
        print("⚠️ Ollama not running — using built-in ICP fallback")
        return ""
    except Exception as e:
        print("⚠️ Ollama API error:", e)
        return ""


# -------------------------------
# 3. CLEAN + PARSE RESPONSE
# -------------------------------
def parse_icp(response_text):
    try:
        if not response_text:
            raise ValueError("Empty response")

        text = response_text.strip()

        # remove markdown blocks
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]

        # extract JSON part
        start = text.find("{")
        end = text.rfind("}")

        if start == -1:
            raise ValueError("No JSON start found")

        if end == -1:
            # 🔥 FIX: add missing closing bracket
            text = text + "}"
            end = len(text) - 1

        clean_json = text[start:end + 1]

        return json.loads(clean_json)

    except Exception as e:
        print("⚠️ Failed to parse ICP:", e)

        return {
            "industries": ["B2B SaaS", "FinTech", "AI/ML"],
            "company_size": "50-1000 employees",
            "tech_stack": ["AWS", "Kubernetes", "Azure", "GCP", "Docker", "Terraform"],
            "target_roles": ["CTO", "VP Engineering", "Director of Engineering", "Founder"],
            "buying_signals": ["Scaling infrastructure", "Hiring engineers", "Recent funding round"],
            "pain_points": ["High cloud cost", "Unpredictable AWS bills", "Kubernetes overhead"],
            "exclude": ["Government", "Non-profit"]
        }


# -------------------------------
# 4. VALIDATE ICP
# -------------------------------
def validate_icp(icp):
    required_keys = {
        "industries": [],
        "company_size": "",
        "tech_stack": [],
        "target_roles": [],
        "buying_signals": [],
        "pain_points": []
    }

    for key, default in required_keys.items():
        if key not in icp or icp[key] is None:
            icp[key] = default

    if "exclude" not in icp:
        icp["exclude"] = []

    # ✅ normalize SaaS
    if "Software as a Service" in icp["industries"]:
        icp["industries"] = [
            "SaaS" if i == "Software as a Service" else i
            for i in icp["industries"]
        ]

    # ✅ ADD THIS HERE
    if isinstance(icp["company_size"], list):
        icp["company_size"] = icp["company_size"][0]

    return icp


# -------------------------------
# 5. FILL MISSING VALUES
# -------------------------------
def fill_missing_fields(icp):
    if not icp["company_size"]:
        icp["company_size"] = "50-1000 employees"

    if not icp["buying_signals"]:
        icp["buying_signals"] = ["Scaling infrastructure"]

    if not icp["pain_points"]:
        icp["pain_points"] = ["High cloud cost"]

    if not icp["industries"]:
        icp["industries"] = ["B2B SaaS"]

    if not icp["target_roles"]:
        icp["target_roles"] = ["CTO", "VP Engineering"]

    return icp


# -------------------------------
# 6. MAIN FUNCTION
# -------------------------------
def generate_icp(user_input):
    prompt = build_icp_prompt(user_input)

    raw_response = call_ollama(prompt)

    # 🔍 Print raw response as formatted JSON
    print("\nRAW RESPONSE:")
    try:
        _start = raw_response.find("{")
        _end   = raw_response.rfind("}") + 1
        if _start != -1 and _end > _start:
            _parsed = json.loads(raw_response[_start:_end])
            print(json.dumps(_parsed, indent=2))
        else:
            print(raw_response)
    except Exception:
        print(raw_response)

    icp = parse_icp(raw_response)

    icp = validate_icp(icp)

    icp = fill_missing_fields(icp)

    return icp