from src.extractor import extract_pdf, get_full_text
from src.merger import generate_ddr_json, save_ddr_json

print("Extracting Sample Report...")
inspection = extract_pdf("uploads/Sample Report.pdf")
inspection_text = get_full_text(inspection)

print("Extracting Thermal Images...")
thermal = extract_pdf("uploads/Thermal Images.pdf")
thermal_text = get_full_text(thermal)

print("Sending to Claude...")
ddr = generate_ddr_json(inspection_text, thermal_text)

save_ddr_json(ddr)

import json
print("\n=== DDR PREVIEW ===")
print(json.dumps(ddr, indent=2)[:2000])