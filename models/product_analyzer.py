"""
SuperClarity AI - Product Analyzer & Quality Diagnostic Engine
Performs automatic product category detection, blind image quality scoring,
defect diagnosis (blur, noise, overexposure), and adaptive enhancement recommendations.
"""

import numpy as np
import cv2
from PIL import Image
import math


class ProductAnalyzer:
    """
    Intelligent product-aware diagnostic engine for e-commerce assets.
    """
    
    CATEGORIES = [
        "Horology & Jewelry",
        "Apparel & Footwear",
        "Beauty & Cosmetics",
        "Packaged Goods & Pantry",
        "Consumer Electronics",
        "Furniture & Home"
    ]

    PRESETS = {
        "Horology & Jewelry": {
            "name": "Horology & Jewelry",
            "denoise_strength": 0.4,
            "sharpen_strength": 1.45,
            "contrast_boost": 1.08,
            "texture_preservation": "specular_metallic",
            "description": "Accentuates watch sub-dials, metal reflections, facet cuts, and gemstone brilliance."
        },
        "Apparel & Footwear": {
            "name": "Apparel & Footwear",
            "denoise_strength": 0.35,
            "sharpen_strength": 0.95,
            "contrast_boost": 1.02,
            "texture_preservation": "knit_weave",
            "description": "Preserves micro-fabric knits, leather grain, and rubber sole treads without synthetic over-sharpening."
        },
        "Beauty & Cosmetics": {
            "name": "Beauty & Cosmetics",
            "denoise_strength": 0.6,
            "sharpen_strength": 1.25,
            "contrast_boost": 1.05,
            "texture_preservation": "smooth_glass",
            "description": "Smooths glass bottle gradients while crisping fine volume and ingredient typography."
        },
        "Packaged Goods & Pantry": {
            "name": "Packaged Goods & Pantry",
            "denoise_strength": 0.5,
            "sharpen_strength": 1.5,
            "contrast_boost": 1.06,
            "texture_preservation": "micro_typography",
            "description": "Maximizes barcode line separation and fine nutritional panel text contrast."
        },
        "Consumer Electronics": {
            "name": "Consumer Electronics",
            "denoise_strength": 0.55,
            "sharpen_strength": 1.15,
            "contrast_boost": 1.04,
            "texture_preservation": "matte_plastic",
            "description": "Suppresses sensor noise on matte polymers and refines acoustic grilles and port edges."
        },
        "Furniture & Home": {
            "name": "Furniture & Home",
            "denoise_strength": 0.45,
            "sharpen_strength": 1.05,
            "contrast_boost": 1.03,
            "texture_preservation": "wood_upholstery",
            "description": "Refines wood grains, upholstery contours, and dimensional perspective lines."
        }
    }

    def analyze(self, img_pil: Image.Image) -> dict:
        """
        Runs comprehensive analysis on an input image.
        Returns category detection, quality metrics, issues, and preset tuning.
        """
        # Convert PIL to CV2 formats
        rgb = np.array(img_pil.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # 1. Image Quality Diagnostics
        quality_diag = self._evaluate_quality(rgb, gray, w, h)
        
        # 2. Product Category Classification
        category_result = self._classify_category(rgb, gray, w, h, quality_diag)
        
        # 3. Actionable Recommendations
        recommendations = self._generate_recommendations(w, h, quality_diag, category_result["category"])
        
        # 4. Preset enhancement parameters
        recommended_preset = self.PRESETS.get(category_result["category"], self.PRESETS["Consumer Electronics"])

        return {
            "category": category_result["category"],
            "category_confidence": category_result["confidence"],
            "all_category_scores": category_result["scores"],
            "quality_score": quality_diag["score"],
            "overall_score": quality_diag["score"],
            "quality_grade": quality_diag["grade"],
            "resolution": f"{w}x{h}",
            "aspect_ratio": quality_diag["aspect_ratio_str"],
            "diagnostics": quality_diag,
            "recommendations": recommendations,
            "recommended_preset": recommended_preset,
            "recommended_settings": recommended_preset
        }

    def _evaluate_quality(self, rgb: np.ndarray, gray: np.ndarray, w: int, h: int) -> dict:
        """Computes objective blind quality indicators."""
        # 1. Blur Detection via Laplacian variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < 120.0

        # 2. Noise Estimation (high-pass residual MAD)
        sigma = 1.0
        blurred = cv2.GaussianBlur(gray, (5, 5), sigma)
        noise_diff = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
        noise_level = float(np.mean(noise_diff))
        is_noisy = noise_level > 6.5

        # 3. Exposure and Histogram Analysis
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        total_pixels = float(w * h)
        overexposed_ratio = float(np.sum(hist[245:]) / total_pixels)
        underexposed_ratio = float(np.sum(hist[:15]) / total_pixels)
        
        is_overexposed = overexposed_ratio > 0.40  # Note: retail white backgrounds are common
        is_underexposed = underexposed_ratio > 0.35

        # 4. Contrast (RMS dynamic range)
        contrast = float(gray.std())

        # 5. Colorfulness metric (Hasler and Süsstrunk)
        R = rgb[:, :, 0].astype(np.float32)
        G = rgb[:, :, 1].astype(np.float32)
        B = rgb[:, :, 2].astype(np.float32)
        rg = np.abs(R - G)
        yb = np.abs(0.5 * (R + G) - B)
        colorfulness = float(np.sqrt(np.std(rg)**2 + np.std(yb)**2) + 0.3 * np.sqrt(np.mean(rg)**2 + np.mean(yb)**2))

        # 6. Overall Quality Score (0-100 scale)
        sharp_pts = min(40.0, (laplacian_var / 500.0) * 40.0)
        res_pts = min(30.0, (min(w, h) / 1024.0) * 30.0)
        noise_pen = min(15.0, max(0.0, (noise_level - 3.0) * 3.0))
        contrast_pts = min(20.0, (contrast / 64.0) * 20.0)
        color_pts = min(10.0, (colorfulness / 40.0) * 10.0)

        raw_score = sharp_pts + res_pts + contrast_pts + color_pts - noise_pen
        final_score = int(np.clip(raw_score, 10.0, 99.0))

        if final_score >= 85:
            grade = "A (Catalog-Ready)"
        elif final_score >= 70:
            grade = "B (Good / Needs Light Polish)"
        elif final_score >= 50:
            grade = "C (Fair / Moderate Enhancement Required)"
        else:
            grade = "D (Low Quality / Critical Upscaling Needed)"

        # Aspect ratio detection
        gcd_val = math.gcd(w, h)
        aspect_ratio_str = f"{round(w / h, 2)}:1" if h != 0 else "1:1"
        if abs(w - h) <= 10:
            aspect_ratio_str = "1:1 (Square)"
        elif abs(w * 3 - h * 4) <= 20:
            aspect_ratio_str = "4:3 (Landscape)"
        elif abs(w * 4 - h * 3) <= 20:
            aspect_ratio_str = "3:4 (Portrait)"
        elif abs(w * 9 - h * 16) <= 20:
            aspect_ratio_str = "16:9 (Wide)"

        return {
            "score": final_score,
            "grade": grade,
            "sharpness_var": round(laplacian_var, 1),
            "is_blurry": is_blurry,
            "noise_level": round(noise_level, 2),
            "is_noisy": is_noisy,
            "overexposed_ratio": round(overexposed_ratio * 100, 1),
            "is_overexposed": is_overexposed,
            "underexposed_ratio": round(underexposed_ratio * 100, 1),
            "is_underexposed": is_underexposed,
            "contrast": round(contrast, 1),
            "colorfulness": round(colorfulness, 1),
            "aspect_ratio_str": aspect_ratio_str
        }

    def _classify_category(self, rgb: np.ndarray, gray: np.ndarray, w: int, h: int, diag: dict) -> dict:
        """Classifies product category using visual semantics & structure."""
        ar = w / float(h)
        scores = {cat: 10.0 for cat in self.CATEGORIES}

        # Structure analysis: edge density and orientation
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        # Color characteristics
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        mean_sat = float(np.mean(sat))
        mean_val = float(np.mean(val))

        # Check for circular features (Horology watches/jewelry or round earbuds)
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
            param1=100, param2=45, minRadius=int(min(w, h) * 0.1), maxRadius=int(min(w, h) * 0.48)
        )
        has_prominent_circle = circles is not None and len(circles[0]) > 0

        # Heuristic Scoring Matrix:
        if has_prominent_circle:
            scores["Horology & Jewelry"] += 35.0
            scores["Consumer Electronics"] += 15.0

        # Aspect ratio clues
        if ar < 0.75:  # Tall vertical bottle or package
            scores["Beauty & Cosmetics"] += 30.0
            scores["Packaged Goods & Pantry"] += 15.0
        elif 0.85 <= ar <= 1.15:  # Square
            scores["Horology & Jewelry"] += 15.0
            scores["Consumer Electronics"] += 15.0
            scores["Packaged Goods & Pantry"] += 15.0
        elif ar > 1.3:  # Wide (shoe or furniture)
            scores["Apparel & Footwear"] += 35.0
            scores["Furniture & Home"] += 25.0

        # Texture and edge density clues
        if edge_density > 0.08:  # Complex knit / typography
            scores["Apparel & Footwear"] += 20.0
            scores["Packaged Goods & Pantry"] += 25.0
        elif edge_density < 0.03:  # Smooth plastic or cosmetic glass
            scores["Beauty & Cosmetics"] += 15.0
            scores["Consumer Electronics"] += 15.0

        # Metallic highlight detection (high brightness, low saturation)
        metallic_mask = (val > 200) & (sat < 40)
        metallic_ratio = float(np.mean(metallic_mask))
        if metallic_ratio > 0.12:
            scores["Horology & Jewelry"] += 20.0
            scores["Consumer Electronics"] += 15.0

        # Normalize to probability percentages
        total_score = sum(scores.values())
        norm_scores = {cat: round((val / total_score) * 100, 1) for cat, val in scores.items()}
        best_cat = max(norm_scores, key=norm_scores.get)
        confidence = norm_scores[best_cat]

        return {
            "category": best_cat,
            "confidence": f"{confidence}%",
            "scores": norm_scores
        }

    def _generate_recommendations(self, w: int, h: int, diag: dict, category: str) -> list:
        """Produces actionable e-commerce seller recommendations."""
        recs = []

        # Resolution checks
        min_dim = min(w, h)
        if min_dim < 500:
            recs.append({
                "type": "critical",
                "badge": "Resolution Warning",
                "message": f"Input is {w}x{h} px. Major marketplaces (Amazon/Shopify) require at least 1000px (2000px recommended for hover-zoom). Apply 4× or 8× super-resolution."
            })
        elif min_dim < 1000:
            recs.append({
                "type": "warning",
                "badge": "Scale Boost",
                "message": f"Resolution ({w}x{h} px) supports standard display. Apply 2× or 4× to enable ultra-HD catalog zoom."
            })
        else:
            recs.append({
                "type": "success",
                "badge": "Resolution Passed",
                "message": f"High native resolution ({w}x{h} px). 2× scaling is optimal to polish textures without exceeding file size limits."
            })

        # Sharpness / Blur
        if diag["is_blurry"]:
            recs.append({
                "type": "warning",
                "badge": "Lens Blur Detected",
                "message": f"Laplacian sharpness is low ({diag['sharpness_var']}). Enable High-Frequency Typography Sharpening to restore edge contrast."
            })

        # Noise / JPEG blocks
        if diag["is_noisy"]:
            recs.append({
                "type": "warning",
                "badge": "Artifact Noise",
                "message": f"Detected sensor CMOS or JPEG compression noise ({diag['noise_level']}). Bilateral Edge-Preserving Denoising is strongly advised."
            })

        # Category-specific guidance
        if category == "Packaged Goods & Pantry":
            recs.append({
                "type": "info",
                "badge": "Barcode Notice",
                "message": "Verify barcode lines and nutritional facts are legible after enhancement for regulatory compliance."
            })
        elif category == "Horology & Jewelry":
            recs.append({
                "type": "info",
                "badge": "Facet Definition",
                "message": "Preserve authentic dial typography and metallic bezel brushing without geometric distortion."
            })
        elif category == "Apparel & Footwear":
            recs.append({
                "type": "info",
                "badge": "Fabric Integrity",
                "message": "Adaptive knit-weave preservation is active. Fabric grain will remain natural and uncompressed."
            })

        return recs
