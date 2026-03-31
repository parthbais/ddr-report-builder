from src.extractor import extract_pdf, get_full_text, get_all_images

result = extract_pdf("Sample_Report.pdf")
print("=== TEXT SAMPLE ===")
print(get_full_text(result)[:800])

print("\n=== IMAGES FOUND ===")
for img in get_all_images(result):
    print(f"  Page {img['page']} | {img['filename']} | Anchor: {img['nearest_heading'][:60]}")