"""
Asset & Figure Extractor
Extracts embedded images and diagrams, saving them to disk or encoding as inline Base64 data URIs.
"""

import io
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from PIL import Image

from aerodoc.config import ConversionConfig


class ImageExtractor:
    """Extracts graphics from PDF documents with multi-format export support."""

    @classmethod
    def extract_page_images(
        cls,
        doc: fitz.Document,
        page_index: int,
        config: ConversionConfig,
        assets_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts all valid raster images from a specific page.
        Returns list of dicts with:
        - img_ref: markdown image link string
        - filename: path or empty if embedded
        - width, height
        """
        page = doc[page_index]
        image_list = page.get_images(full=True)
        results = []

        if not image_list or not config.extract_images:
            return results

        if not config.embed_images and assets_dir:
            assets_dir.mkdir(parents=True, exist_ok=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image.get("ext", "png")
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Skip tiny icon or decorative pixel spacers
                if width < config.min_image_width or height < config.min_image_height:
                    continue

                # Ensure valid RGB/PNG representation
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
                        pil_img = pil_img.convert("RGBA")
                        save_format = "PNG"
                        ext_to_use = "png"
                    elif pil_img.mode != "RGB":
                        pil_img = pil_img.convert("RGB")
                        save_format = "PNG"
                        ext_to_use = "png"
                    else:
                        save_format = "PNG" if image_ext.lower() == "png" else "JPEG"
                        ext_to_use = image_ext.lower()

                    buf = io.BytesIO()
                    pil_img.save(buf, format=save_format)
                    final_bytes = buf.getvalue()
                except Exception:
                    final_bytes = image_bytes
                    ext_to_use = image_ext

                # Check embedding mode
                if config.embed_images:
                    # Single-file standalone mode: inline base64
                    mime_type = "image/png" if ext_to_use == "png" else f"image/{ext_to_use}"
                    b64_str = base64.b64encode(final_bytes).decode("utf-8")
                    img_src = f"data:{mime_type};base64,{b64_str}"
                    md_link = f"![Page {page_index + 1} Figure {img_idx + 1}]({img_src})"
                    results.append({
                        "markdown": md_link,
                        "width": width,
                        "height": height,
                        "is_embedded": True,
                        "xref": xref
                    })
                else:
                    # Assets directory mode
                    filename = f"page_{page_index + 1}_fig_{img_idx + 1}.{ext_to_use}"
                    if assets_dir:
                        out_file = assets_dir / filename
                        out_file.write_bytes(final_bytes)
                        # Relative markdown link
                        rel_path = f"{config.assets_dir_name}/{filename}"
                    else:
                        rel_path = filename

                    md_link = f"![Page {page_index + 1} Figure {img_idx + 1}]({rel_path})"
                    results.append({
                        "markdown": md_link,
                        "filename": filename,
                        "width": width,
                        "height": height,
                        "is_embedded": False,
                        "xref": xref
                    })

            except Exception:
                continue

        return results
