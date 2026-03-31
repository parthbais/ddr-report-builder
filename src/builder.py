from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import os

def create_ddr_docx(ddr_json: dict, assets_dir: str = "assets", output_path: str = "output/Final_DDR.docx") -> str:
    """
    Takes the structured JSON from Claude and assembles a professional DOCX file,
    embedding images under the correct observations.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = Document()
    
    # Title
    title = doc.add_heading("Detailed Diagnostic Report (DDR)", 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # 1. Property Issue Summary
    doc.add_heading("1. Property Issue Summary", level=1)
    doc.add_paragraph(ddr_json.get("property_issue_summary", "Not Available"))

    # 2. Area-wise Observations (with images)
    doc.add_heading("2. Area-wise Observations", level=1)
    observations = ddr_json.get("area_wise_observations", [])
    
    if not observations:
        doc.add_paragraph("No specific area observations noted.")
    else:
        for obs in observations:
            doc.add_heading(obs.get("area_name", "Unknown Area"), level=2)
            doc.add_paragraph(obs.get("observation", "No details provided."))
            
            # Insert relevant images if they exist
            images = obs.get("relevant_images", [])
            if images:
                for img_filename in images:
                    img_path = os.path.join(assets_dir, img_filename)
                    if os.path.exists(img_path):
                        # Add image and center it
                        p = doc.add_paragraph()
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        run = p.add_run()
                        run.add_picture(img_path, width=Inches(4.5))
                    else:
                        doc.add_paragraph(f"[Image '{img_filename}' Not Found in Assets]")
            else:
                p = doc.add_paragraph()
                run = p.add_run("[Image Not Available]")
                run.italic = True

    # 3. Probable Root Cause
    doc.add_heading("3. Probable Root Cause", level=1)
    doc.add_paragraph(ddr_json.get("probable_root_cause", "Not Available"))

    # 4. Severity Assessment
    doc.add_heading("4. Severity Assessment", level=1)
    severity = ddr_json.get("severity_assessment", {})
    p = doc.add_paragraph()
    p.add_run("Level: ").bold = True
    p.add_run(f"{severity.get('level', 'Not Available')}\n")
    p.add_run("Reasoning: ").bold = True
    p.add_run(severity.get("reasoning", "Not Available"))

    # 5. Recommended Actions
    doc.add_heading("5. Recommended Actions", level=1)
    actions = ddr_json.get("recommended_actions", [])
    if actions:
        for action in actions:
            doc.add_paragraph(action, style="List Bullet")
    else:
        doc.add_paragraph("Not Available")

    # 6. Additional Notes
    doc.add_heading("6. Additional Notes", level=1)
    doc.add_paragraph(ddr_json.get("additional_notes", "Not Available"))

    # 7. Missing or Unclear Information
    doc.add_heading("7. Missing or Unclear Information", level=1)
    doc.add_paragraph(ddr_json.get("missing_or_unclear_information", "None"))

    doc.save(output_path)
    return output_path