# AI DDR Report Generator

## 📌 Overview
This project converts inspection and thermal reports into a structured DDR (Detailed Diagnostic Report) using AI. It leverages modern LLMs (like LLaMA 3 70B via Groq) to synthesize complex physical and thermal diagnostic data into professional, client-ready Word documents.

## ⚙️ How It Works
1. **Input**: Upload both the Visual Inspection PDF and Thermal Imaging PDF.
2. **Extract**: Automatically extracts text blocks and locates images by their nearest text anchors.
3. **Merge**: Intelligently merges overlapping field observations and removes duplicate entries.
4. **Handle**: Formats missing data cleanly as "Not Available" and explicitly handles conflicting entries.
5. **Generate**: Outputs a fully structured, branded DDR Word document (`.docx`) alongside raw JSON outputs.

## 🧠 Features
- Logical merging of multiple separate reports into one cohesive area-wise map.
- Safe missing data handling ("Not Available") to completely prevent AI hallucinations.
- Conflict detection between visual cracks and underlying thermal anomalies.
- Dynamic image extraction and physical placement inside the final `.docx` file relative to the area.
- Clean, structured, client-friendly professional output.

## ⚠️ Limitations
- Accuracy depends heavily on the formatting and text-layer quality of the source documents.
- Limited handling of highly unstructured, non-standard, or OCR-less image-only PDFs.

## 🚀 Future Improvements
- Better UI with batch processing and drag-and-drop workflows.
- More robust parsing pipelines integrated with raw OCR models.
- Support for more file formats (e.g., raw JPEG uploads from field agents).
- Enhanced structural reasoning using advanced long-context reasoning models.
