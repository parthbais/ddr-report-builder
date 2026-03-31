import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_ddr_json(inspection_text: str, thermal_text: str) -> dict:
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""You are an expert building inspection analyst.
Read the two documents below and merge them into a Detailed Diagnostic Report (DDR).

STRICT RULES:
- DO NOT invent facts not present in the documents
- If information conflicts between documents → flag it as [CONFLICT: description]
- If information is missing → write "Not Available"
- Use simple, client-friendly language
- Return ONLY valid JSON. No markdown, no explanation, no code fences.

=== INSPECTION REPORT ===
{inspection_text}

=== THERMAL REPORT ===
{thermal_text}

Return this exact JSON structure:
{{
  "property_info": {{
    "client_name": "",
    "address": "",
    "inspection_date": "",
    "inspected_by": "",
    "property_type": "",
    "floors": "",
    "age_years": "",
    "previous_audit": "",
    "previous_repairs": ""
  }},
  "property_issue_summary": "",
  "area_wise_observations": [
    {{
      "area": "",
      "negative_observations": "",
      "positive_observations": "",
      "thermal_reading": "",
      "image_anchor": ""
    }}
  ],
  "probable_root_cause": "",
  "severity_assessment": [
    {{
      "area": "",
      "severity": "",
      "reasoning": ""
    }}
  ],
  "recommended_actions": [
    {{
      "action": "",
      "area": "",
      "priority": ""
    }}
  ],
  "additional_notes": "",
  "missing_or_unclear_info": ""
}}

For image_anchor: write the exact heading closest to where images of that area appear.
For thermal_reading: include hotspot/coldspot temperatures from the thermal report.
For severity: use Critical / High / Moderate / Low only.
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def save_ddr_json(ddr: dict, output_path: str = "output/ddr.json"):
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(ddr, f, indent=2)
    print(f"DDR JSON saved to {output_path}")