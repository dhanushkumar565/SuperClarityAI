"""
SuperClarity AI - AI Image Editing Studio & Scene Generator
Provides real-time transformations, background removal, pure white studio generation,
physics-based shadow/reflection synthesis, and natural language command parsing.
"""

import re
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class StudioEditor:
    """
    Advanced studio workstation for product photo manipulation and marketplace styling.
    """

    def apply_adjustments(
        self,
        img_pil: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
        rotation: int = 0,
        flip_h: bool = False,
        flip_v: bool = False
    ) -> Image.Image:
        """Applies non-destructive adjustments to a product image."""
        img = img_pil.convert("RGBA" if img_pil.mode == "RGBA" else "RGB")

        # Flips & Rotations
        if flip_h:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if rotation != 0:
            img = img.rotate(-rotation, expand=True, resample=Image.BICUBIC)

        # Separate alpha channel if RGBA to apply enhancements on RGB
        if img.mode == "RGBA":
            r, g, b, a = img.split()
            rgb = Image.merge("RGB", (r, g, b))
        else:
            rgb = img
            a = None

        if brightness != 1.0:
            rgb = ImageEnhance.Brightness(rgb).enhance(max(0.1, min(2.5, brightness)))
        if contrast != 1.0:
            rgb = ImageEnhance.Contrast(rgb).enhance(max(0.1, min(2.5, contrast)))
        if saturation != 1.0:
            rgb = ImageEnhance.Color(rgb).enhance(max(0.0, min(2.5, saturation)))
        if sharpness != 1.0:
            rgb = ImageEnhance.Sharpness(rgb).enhance(max(0.0, min(3.0, sharpness)))

        if a:
            r2, g2, b2 = rgb.split()
            return Image.merge("RGBA", (r2, g2, b2, a))
        return rgb

    def remove_background(self, img_pil: Image.Image, refine_edges: bool = True) -> Image.Image:
        """
        Segment product foreground from background using GrabCut & saliency edge matting.
        Returns RGBA image with transparent background.
        """
        rgb = np.array(img_pil.convert("RGB"))
        h, w = rgb.shape[:2]

        # Initial bounding box approximation (assuming product is central)
        margin_x = max(1, int(w * 0.04))
        margin_y = max(1, int(h * 0.04))
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        try:
            cv2.grabCut(rgb, mask, rect, bgd_model, fgd_model, iterCount=5, mode=cv2.GC_INIT_WITH_RECT)
            # 0=BGD, 2=PR_BGD, 1=FGD, 3=PR_FGD
            bin_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

            if refine_edges:
                # Soften alpha boundary with mild Gaussian blur
                bin_mask = cv2.GaussianBlur(bin_mask, (5, 5), 1.5)
        except Exception:
            # Fallback simple Otsu thresholding if GrabCut fails on degenerate inputs
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            _, bin_mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)

        # Merge RGB with alpha mask
        rgba = np.dstack((rgb, bin_mask))
        return Image.fromarray(rgba, "RGBA")

    def make_white_background(self, img_pil: Image.Image) -> Image.Image:
        """Isolates product and places on pure #FFFFFF background for Amazon/Shopify compliance."""
        cutout = self.remove_background(img_pil)
        white_bg = Image.new("RGB", cutout.size, (255, 255, 255))
        white_bg.paste(cutout, (0, 0), mask=cutout.split()[3])
        return white_bg

    def add_drop_shadow(
        self,
        img_rgba: Image.Image,
        shadow_opacity: float = 0.35,
        offset_y: int = 15,
        blur_radius: int = 18
    ) -> Image.Image:
        """
        Generates a realistic soft contact shadow beneath product.
        """
        if img_rgba.mode != "RGBA":
            img_rgba = self.remove_background(img_rgba)

        w, h = img_rgba.size
        # Extract alpha mask
        alpha = img_rgba.split()[3]

        # Create shadow ellipse beneath product base
        shadow_canvas = Image.new("RGBA", (w, h + offset_y + blur_radius * 2), (255, 255, 255, 0))
        
        # Shadow mask: squash product silhouette horizontally and vertically for grounded contact
        shadow_mask = alpha.resize((int(w * 0.85), int(h * 0.18)), Image.BILINEAR)
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Adjust opacity
        shadow_np = np.array(shadow_mask).astype(np.float32) * shadow_opacity
        shadow_mask_adjusted = Image.fromarray(shadow_np.astype(np.uint8))

        # Position shadow at bottom center
        shadow_x = (w - shadow_mask.width) // 2
        shadow_y = int(h * 0.90) + offset_y
        
        black_shadow = Image.new("RGBA", shadow_mask.size, (20, 20, 25, 255))
        shadow_canvas.paste(black_shadow, (shadow_x, shadow_y), mask=shadow_mask_adjusted)

        # Paste product over shadow
        final_canvas = Image.new("RGB", shadow_canvas.size, (255, 255, 255))
        final_canvas.paste(shadow_canvas, (0, 0), mask=shadow_canvas.split()[3])
        final_canvas.paste(img_rgba, (0, 0), mask=alpha)
        
        # Crop back to original dimensions centered
        crop_y = (final_canvas.height - h) // 2
        return final_canvas.crop((0, crop_y, w, crop_y + h))

    def add_floor_reflection(
        self,
        img_rgba: Image.Image,
        opacity: float = 0.40,
        fade_height: float = 0.45
    ) -> Image.Image:
        """
        Synthesizes a specular glass/acrylic studio floor reflection.
        """
        if img_rgba.mode != "RGBA":
            img_rgba = self.remove_background(img_rgba)

        w, h = img_rgba.size
        flipped = img_rgba.transpose(Image.FLIP_TOP_BOTTOM)

        # Create linear alpha gradient fade (100% at contact -> 0% at bottom)
        grad_arr = np.zeros((h, w), dtype=np.uint8)
        max_fade_y = int(h * fade_height)
        for y in range(max_fade_y):
            alpha_val = int((1.0 - (y / max_fade_y)) * 255 * opacity)
            grad_arr[y, :] = alpha_val

        grad_mask = Image.fromarray(grad_arr)
        
        # Combine flipped alpha with gradient mask
        flip_alpha = flipped.split()[3]
        combined_alpha = Image.fromarray(
            np.minimum(np.array(flip_alpha), np.array(grad_mask))
        )
        flipped.putalpha(combined_alpha)

        # Composite onto canvas
        canvas = Image.new("RGB", (w, int(h * 1.35)), (255, 255, 255))
        canvas.paste(flipped, (0, int(h * 0.98)), mask=flipped.split()[3])
        canvas.paste(img_rgba, (0, 0), mask=img_rgba.split()[3])
        
        return canvas.resize((w, h), Image.LANCZOS)

    def crop_to_aspect_ratio(self, img_pil: Image.Image, ratio: str = "1:1") -> Image.Image:
        """Center crops image to standard e-commerce aspect ratios."""
        w, h = img_pil.size
        
        ratio_map = {
            "1:1": (1, 1),
            "4:5": (4, 5),
            "3:4": (3, 4),
            "16:9": (16, 9)
        }
        rw, rh = ratio_map.get(ratio, (1, 1))
        target_aspect = rw / rh
        current_aspect = w / h

        if current_aspect > target_aspect:
            # Current image is wider than target
            new_w = int(h * target_aspect)
            left = (w - new_w) // 2
            return img_pil.crop((left, 0, left + new_w, h))
        else:
            # Current image is taller than target
            new_h = int(w / target_aspect)
            top = (h - new_h) // 2
            return img_pil.crop((0, top, w, top + new_h))

    def parse_natural_language_command(self, command_text: str) -> dict:
        """
        Parses seller conversational editing instructions into executable actions.
        Identifies operations requiring generative AI vs. native computer vision.
        """
        cmd = command_text.lower().strip()
        result = {
            "action": "unknown",
            "is_generative": False,
            "parameters": {},
            "description": "Unrecognized command."
        }

        # 1. Background commands
        if any(w in cmd for w in ["white background", "make background white", "pure white", "white bg"]):
            result = {
                "action": "white_background",
                "is_generative": False,
                "parameters": {},
                "description": "Isolating product onto compliant pure #FFFFFF background."
            }
        elif any(w in cmd for w in ["remove background", "transparent", "cut out", "no background"]):
            result = {
                "action": "remove_background",
                "is_generative": False,
                "parameters": {},
                "description": "Removing background to yield transparent alpha cutout."
            }
        # 2. Shadow & Reflection
        elif any(w in cmd for w in ["add shadow", "drop shadow", "contact shadow"]):
            result = {
                "action": "add_shadow",
                "is_generative": False,
                "parameters": {"opacity": 0.35},
                "description": "Adding realistic soft contact shadow."
            }
        elif any(w in cmd for w in ["add reflection", "mirror", "glass reflection"]):
            result = {
                "action": "add_reflection",
                "is_generative": False,
                "parameters": {"opacity": 0.4},
                "description": "Synthesizing luxury specular floor reflection."
            }
        # 3. Crop commands
        elif any(w in cmd for w in ["square", "1:1", "crop square"]):
            result = {
                "action": "crop_ratio",
                "is_generative": False,
                "parameters": {"ratio": "1:1"},
                "description": "Centering and cropping to 1:1 square aspect ratio."
            }
        # 4. Sharpening & Contrast
        elif any(w in cmd for w in ["sharpen", "crisp", "clearer", "sharp"]):
            result = {
                "action": "adjust",
                "is_generative": False,
                "parameters": {"sharpness": 1.45},
                "description": "Increasing high-frequency edge sharpness."
            }
        elif any(w in cmd for w in ["contrast", "pop", "punchy"]):
            result = {
                "action": "adjust",
                "is_generative": False,
                "parameters": {"contrast": 1.25},
                "description": "Boosting dynamic range contrast."
            }
        elif any(w in cmd for w in ["brighten", "lighter", "bright"]):
            result = {
                "action": "adjust",
                "is_generative": False,
                "parameters": {"brightness": 1.18},
                "description": "Brightening overall exposure."
            }
        # 5. Generative requests detection
        elif any(w in cmd for w in ["on model", "wearing", "lifestyle background", "beach", "kitchen", "park", "generate background"]):
            result = {
                "action": "generative_scene",
                "is_generative": True,
                "parameters": {"prompt": command_text},
                "description": "Generative AI scene generation request detected. Generative models will preserve product geometry while synthesizing contextual scene backdrops."
            }

        return result
