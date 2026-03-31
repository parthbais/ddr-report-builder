import fitz  # PyMuPDF
import os
import json
from pathlib import Path


def extract_pdf(pdf_path: str, assets_dir: str = "assets") -> dict:
    """
    Extracts text blocks and images from a PDF.
    Returns a structured dict with pages, text, and image metadata.
    """
    Path(assets_dir).mkdir(exist_ok=True)
    doc = fitz.open(pdf_path)
    pdf_name = Path(pdf_path).stem

    result = {
        "source": pdf_name,
        "pages": []
    }

    for page_num, page in enumerate(doc):
        page_data = {
            "page": page_num + 1,
            "text_blocks": [],
            "images": []
        }

        # --- Extract text blocks with bbox ---
        blocks = page.get_text("blocks")  # returns (x0, y0, x1, y1, text, block_no, block_type)
        text_blocks = []
        for block in blocks:
            text = block[4].strip()
            if text:  # skip empty blocks
                text_blocks.append({
                    "bbox": [block[0], block[1], block[2], block[3]],
                    "text": text
                })
        page_data["text_blocks"] = text_blocks

        # --- Extract images with nearest heading ---
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]

                # Save image to assets/
                img_filename = f"{pdf_name}_p{page_num+1}_img{img_index+1}.{ext}"
                img_path = os.path.join(assets_dir, img_filename)
                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                # Find image bbox on page
                img_bbox = _get_image_bbox(page, xref)

                # Find nearest text above the image (caption/heading anchor)
                nearest_text = _get_nearest_text_above(text_blocks, img_bbox)

                page_data["images"].append({
                    "filename": img_filename,
                    "path": img_path,
                    "page": page_num + 1,
                    "bbox": img_bbox,
                    "nearest_heading": nearest_text
                })

            except Exception as e:
                print(f"[WARN] Could not extract image {img_index} on page {page_num+1}: {e}")

        result["pages"].append(page_data)

    doc.close()
    return result


def _get_image_bbox(page, xref) -> list:
    """Gets the bounding box of an image on the page by xref."""
    try:
        for item in page.get_image_info():
            if item.get("xref") == xref:
                r = item.get("bbox") or item.get("rect", [0, 0, 0, 0])
                return list(r)
    except Exception:
        pass
    return [0, 0, 0, 0]


def _get_nearest_text_above(text_blocks: list, img_bbox: list) -> str:
    """
    Finds the closest text block that appears ABOVE the image.
    This becomes the anchor key for placing the image in the report.
    """
    if not img_bbox or img_bbox == [0, 0, 0, 0]:
        return "General"

    img_top = img_bbox[1]  # y0 of image

    candidates = []
    for block in text_blocks:
        block_bottom = block["bbox"][3]  # y1 of text block
        if block_bottom <= img_top:  # text is above image
            distance = img_top - block_bottom
            candidates.append((distance, block["text"]))

    if candidates:
        candidates.sort(key=lambda x: x[0])  # closest first
        return candidates[0][1][:120]  # trim long headings

    return "General"


def get_full_text(extracted: dict) -> str:
    """Flattens all text blocks from an extracted PDF into a single string."""
    lines = []
    for page in extracted["pages"]:
        for block in page["text_blocks"]:
            lines.append(block["text"])
    return "\n".join(lines)


def get_all_images(extracted: dict) -> list:
    """Returns a flat list of all image metadata from an extracted PDF."""
    images = []
    for page in extracted["pages"]:
        images.extend(page["images"])
    return images