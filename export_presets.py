"""
SuperClarity AI - E-Commerce Marketplace Export Center
Formats, scales, compresses, and validates product images for Amazon, Shopify,
Flipkart, and custom e-commerce channels.
"""

import os
import io
import numpy as np
from PIL import Image

class ExportCenter:
    """
    Standardized multi-channel e-commerce asset packaging and compliance engine.
    """

    PRESETS = {
        "amazon": {
            "name": "Amazon Marketplace",
            "target_resolution": (2000, 2000),
            "aspect_ratio": "1:1",
            "format": "JPEG",
            "quality": 92,
            "max_file_size_mb": 10.0,
            "background": "#FFFFFF",
            "min_product_fill": 0.85,
            "description": "2000x2000 px, 1:1 Square, pure white background (#FFFFFF) with hover-zoom support."
        },
        "shopify": {
            "name": "Shopify Storefront",
            "target_resolution": (2048, 2048),
            "aspect_ratio": "1:1",
            "format": "WEBP",
            "quality": 90,
            "max_file_size_mb": 4.0,
            "background": "transparent_or_white",
            "min_product_fill": 0.80,
            "description": "2048x2048 px WebP, highly compressed for rapid mobile page load times."
        },
        "flipkart": {
            "name": "Flipkart Catalog",
            "target_resolution": (1600, 1600),
            "aspect_ratio": "1:1",
            "format": "JPEG",
            "quality": 90,
            "max_file_size_mb": 5.0,
            "background": "#FFFFFF",
            "min_product_fill": 0.80,
            "description": "1600x1600 px, 1:1 Square, sharp edge borders on neutral backdrop."
        },
        "custom": {
            "name": "Custom Channel",
            "target_resolution": (1200, 1200),
            "aspect_ratio": "1:1",
            "format": "PNG",
            "quality": 95,
            "max_file_size_mb": 16.0,
            "background": "any",
            "min_product_fill": 0.70,
            "description": "Fully customizable dimensions, aspect ratio, and compression quality."
        }
    }

    def process_export(
        self,
        img_pil: Image.Image,
        preset_key: str = "amazon",
        custom_width: int = None,
        custom_height: int = None,
        custom_format: str = None,
        custom_quality: int = None,
        force_white_bg: bool = False
    ) -> dict:
        """
        Processes an image against the selected marketplace specifications.
        Returns the export PIL image, compliance status, and byte data.
        """
        preset = self.PRESETS.get(preset_key.lower(), self.PRESETS["custom"]).copy()
        
        target_w, target_h = preset["target_resolution"]
        if custom_width and custom_height:
            target_w, target_h = int(custom_width), int(custom_height)
            
        fmt = (custom_format if custom_format else preset["format"]).upper()
        quality = int(custom_quality if custom_quality else preset["quality"])

        # Handle transparency & white background
        if fmt in ["JPEG", "JPG"] or force_white_bg or preset["background"] == "#FFFFFF":
            if img_pil.mode in ("RGBA", "LA") or (img_pil.mode == "P" and "transparency" in img_pil.info):
                canvas = Image.new("RGB", img_pil.size, (255, 255, 255))
                canvas.paste(img_pil, (0, 0), mask=img_pil.convert("RGBA").split()[3])
                img_pil = canvas
            else:
                img_pil = img_pil.convert("RGB")
        elif fmt == "WEBP" and img_pil.mode != "RGBA":
            img_pil = img_pil.convert("RGB")

        # Resize with aspect-ratio letterbox padding (preserves product shape completely)
        orig_w, orig_h = img_pil.size
        scale = min(target_w / orig_w, target_h / orig_h)
        scaled_w = int(orig_w * scale)
        scaled_h = int(orig_h * scale)
        
        resized_product = img_pil.resize((scaled_w, scaled_h), Image.LANCZOS)
        
        # Create output canvas
        bg_color = (255, 255, 255)
        if fmt == "PNG" and not force_white_bg and preset["background"] != "#FFFFFF":
            output_canvas = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 0))
            paste_mask = resized_product.split()[3] if resized_product.mode == "RGBA" else None
        else:
            output_canvas = Image.new("RGB", (target_w, target_h), bg_color)
            paste_mask = resized_product.split()[3] if resized_product.mode == "RGBA" else None

        pos_x = (target_w - scaled_w) // 2
        pos_y = (target_h - scaled_h) // 2
        output_canvas.paste(resized_product, (pos_x, pos_y), mask=paste_mask)

        # Buffer to compute file size & verify compliance
        buffer = io.BytesIO()
        if fmt in ["JPEG", "JPG"]:
            output_canvas.save(buffer, format="JPEG", quality=quality, optimize=True)
            mime = "image/jpeg"
            ext = "jpg"
        elif fmt == "WEBP":
            output_canvas.save(buffer, format="WEBP", quality=quality)
            mime = "image/webp"
            ext = "webp"
        else:
            output_canvas.save(buffer, format="PNG", optimize=True)
            mime = "image/png"
            ext = "png"

        size_bytes = buffer.tell()
        size_kb = round(size_bytes / 1024, 1)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        # Compliance checks
        compliance_issues = []
        is_compliant = True

        if size_mb > preset["max_file_size_mb"]:
            compliance_issues.append(f"File size ({size_mb} MB) exceeds marketplace limit ({preset['max_file_size_mb']} MB).")
            is_compliant = False

        if preset_key == "amazon" and min(target_w, target_h) < 1000:
            compliance_issues.append("Resolution is under Amazon's 1000px minimum for zoom inspection.")
            is_compliant = False

        return {
            "image": output_canvas,
            "buffer": buffer.getvalue(),
            "mime_type": mime,
            "extension": ext,
            "resolution": f"{target_w}x{target_h}",
            "file_size_kb": size_kb,
            "file_size_mb": size_mb,
            "preset_used": preset["name"],
            "is_compliant": is_compliant,
            "compliance_issues": compliance_issues
        }
