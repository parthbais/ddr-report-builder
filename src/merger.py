from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_ddr_json(inspection_text: str, thermal_text: str) -> dict:

    # Use 5500 chars each = ~1375 tokens each → safe within Groq free TPM
    inspection_text = inspection_text[:5500]
    thermal_text    = thermal_text[:5500]

    prompt = f"""You are a senior building health assessment engineer at UrbanRoof Pvt Ltd.
Your job is to read both the Visual Inspection Report and the Thermal Imaging Report below,
and synthesise them into a comprehensive, professional Detailed Diagnostic Report (DDR).

═══════════════════════════════════
MANDATORY RULES:
═══════════════════════════════════
- Extract ONLY facts present in the documents. Do NOT invent or assume.
- Where documents conflict → write [CONFLICT: <brief description>]
- Where data is missing → write "Not Available"
- Be specific: include measurements, crack widths, temperature values, floor levels, room names wherever mentioned.
- Use professional but client-readable language (no jargon without explanation).
- Write in full sentences. Be thorough — this is a formal engineering document.
- Return ONLY valid JSON. No markdown, no code fences, no explanation outside JSON.

═══════════════════════════════════
INSPECTION REPORT:
═══════════════════════════════════
{inspection_text}

═══════════════════════════════════
THERMAL IMAGING REPORT:
═══════════════════════════════════
{thermal_text}

═══════════════════════════════════
OUTPUT — Return this EXACT JSON structure (fill every field thoroughly):
═══════════════════════════════════
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
    "previous_repairs": "",
    "tools_used": ""
  }},
  "executive_summary": "",
  "property_issue_summary": "",
  "area_wise_observations": [
    {{
      "area": "",
      "floor_level": "",
      "negative_observations": "",
      "positive_observations": "",
      "structural_condition": "",
      "moisture_readings": "",
      "thermal_reading": "",
      "affected_surface": "",
      "image_anchor": ""
    }}
  ],
  "probable_root_cause": "",
  "leakage_sources": "",
  "severity_assessment": [
    {{
      "area": "",
      "severity": "",
      "urgency": "",
      "reasoning": ""
    }}
  ],
  "recommended_actions": [
    {{
      "action": "",
      "area": "",
      "treatment_method": "",
      "priority": "",
      "estimated_scope": ""
    }}
  ],
  "waterproofing_recommendations": "",
  "structural_recommendations": "",
  "additional_notes": "",
  "missing_or_unclear_info": ""
}}

FIELD GUIDANCE:
- executive_summary: 3-4 sentence overview of the entire property health.
- property_issue_summary: Detailed paragraph covering all major issues found.
- area_wise_observations: One entry per distinct area (Bathroom, Balcony, Terrace, External Wall, etc).
  - negative_observations: All defects seen (dampness, cracks, spalling, gaps, efflorescence etc) with specifics.
  - positive_observations: What appears intact or what is the suspected source side.
  - structural_condition: RCC/plaster/tile condition if mentioned.
  - moisture_readings: Any moisture % or pH readings if available.
  - thermal_reading: Hotspot/coldspot temps, delta-T values from thermal report.
  - affected_surface: e.g. "ceiling, skirting level, adjacent wall".
  - image_anchor: The exact heading text from the document that appears closest to images of this area.
- probable_root_cause: Single consolidated root cause explanation.
- leakage_sources: Where exactly the water is entering and its likely travel path.
- severity_assessment[].severity: Use ONLY Critical / High / Moderate / Low.
- severity_assessment[].urgency: Use ONLY Immediate / Within 1 Month / Within 3 Months / Planned.
- recommended_actions[].treatment_method: e.g. "Polyurethane injection grouting", "Crystalline waterproofing", "Epoxy crack filling".
- recommended_actions[].priority: Use ONLY Immediate / High / Medium / Low.
- recommended_actions[].estimated_scope: e.g. "Full terrace treatment ~800 sqft" or "Spot treatment at 3 bathroom joints".
- waterproofing_recommendations: Specific waterproofing system recommended for the property.
- structural_recommendations: Any RCC repair, carbon fibre wrap, guniting, or structural intervention needed.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.15,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

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