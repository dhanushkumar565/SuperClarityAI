"""
SupplierClarity AI - Production Flask Application & Advanced E-Commerce AI Engine
Provides multi-model super-resolution (2x, 4x, 8x), product-aware enhancement,
AI editing studio, multi-model laboratory, explainability heatmaps, visual search,
catalog management, batch processing, and marketplace exports.
"""

import os
import io
import time
import base64
import json
import uuid
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import cv2

from models.upscaler import SupplierClarityUpscaler
from models.chatbot import SupplierClarityChatbot
from models.llm_provider import (
    PROVIDER_DEFAULTS,
    generate_llm_reply,
    normalize_provider,
)
from models.product_analyzer import ProductAnalyzer
from models.studio_editor import StudioEditor
from models.explainability import ExplainabilityEngine
from models.visual_search import VisualSearchEngine
from batch_processor import BatchProcessor
from export_presets import ExportCenter
import database
from dataset_pipeline import setup_demo_and_eval_datasets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "superclarity_ai_production_secret_key_2026")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload
if os.environ.get("VERCEL"):
    app.config["UPLOAD_FOLDER"] = os.path.join("/tmp", "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join("/tmp", "outputs")
else:
    app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
    app.config["OUTPUT_FOLDER"] = os.path.join("static", "outputs")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Initialize Core AI Engines
upscaler = SupplierClarityUpscaler()
# Isolated engines let Model Lab run all four methods concurrently without
# sharing mutable model caches across threads.
comparison_engines = {
    name: SupplierClarityUpscaler()
    for name in ("realesrgan", "edsr", "srcnn", "bicubic")
}
chatbot = SupplierClarityChatbot()
analyzer = ProductAnalyzer()
studio = StudioEditor()
explainer = ExplainabilityEngine()
visual_searcher = VisualSearchEngine()
batch_engine = BatchProcessor()
exporter = ExportCenter()

# Initialize benchmark datasets & SQLite schema
setup_demo_and_eval_datasets(base_dir="data")
database.init_db()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "jfif", "bmp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def pil_to_base64(img: Image.Image, format: str = "PNG") -> str:
    buffered = io.BytesIO()
    if format.upper() in ["JPEG", "JPG"] and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def decode_image_from_request(req):
    """
    Universal helper to extract a PIL image from multipart file, base64 string,
    sample ID, or existing server filepath.
    """
    # 1. File upload
    if "file" in req.files and req.files["file"].filename != "":
        file = req.files["file"]
        if not allowed_file(file.filename):
            raise ValueError("Invalid file format. Supported: PNG, JPG, JPEG, WEBP, BMP")
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{int(time.time())}_{filename}")
        file.save(save_path)
        img = Image.open(save_path)
        return img, save_path, filename

    # 2. Base64 encoded payload
    img_b64 = req.form.get("image_base64")
    if not img_b64 and req.is_json:
        img_b64 = req.json.get("image_base64")

    if img_b64:
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        raw_bytes = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(raw_bytes))
        temp_name = f"b64_{int(time.time()*1000)}.png"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_name)
        img.save(save_path, format="PNG")
        return img, save_path, temp_name

    # 3. Existing file path
    img_path = (
        req.form.get("image_path")
        or req.form.get("original_path")
        or req.form.get("path")
        or (
            (req.json.get("image_path") or req.json.get("original_path") or req.json.get("path"))
            if req.is_json
            else None
        )
    )
    if img_path:
        # Strip leading slash if relative
        rel_path = img_path.lstrip("/\\")
        if os.path.exists(img_path):
            img = Image.open(img_path)
            return img, img_path, os.path.basename(img_path)
        elif os.path.exists(rel_path):
            img = Image.open(rel_path)
            return img, rel_path, os.path.basename(rel_path)

    # 4. Sample product ID
    sample_id = req.form.get("sample_id") or (req.json.get("sample_id") if req.is_json else None)
    if sample_id:
        for p in [
            os.path.join("data", "samples", f"{sample_id}_supplier_input.jpg"),
            os.path.join("static", "samples", f"{sample_id}_supplier_input.jpg"),
            os.path.join("data", "eval_dataset", "lr", f"{sample_id}_lr.jpg"),
        ]:
            if os.path.exists(p):
                img = Image.open(p)
                return img, p, f"{sample_id}.jpg"

    raise ValueError("No image provided in request.")


# =====================================================================
# 1. CORE VIEWS & SAMPLES
# =====================================================================

@app.route("/")
def index():
    """Renders the upgraded SuperClarity AI Enterprise Workbench."""
    return render_template("index.html")


@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Returns the list of available pre-loaded vendor sample products."""
    samples = [
        {
            "id": "luxury_watch",
            "name": "Luxury Chronograph Watch",
            "category": "Horology & Jewelry",
            "description": "Minute tick marks, sub-dials, serif brand typography, brushed steel bezel.",
            "path": "/static/samples/luxury_watch_supplier_input.jpg"
        },
        {
            "id": "sneaker_shoe",
            "name": "Athletic Running Sneaker",
            "category": "Apparel & Footwear",
            "description": "Mesh fabric weave, leather stitching lines, rubber sole tread pattern, logo badge.",
            "path": "/static/samples/sneaker_shoe_supplier_input.jpg"
        },
        {
            "id": "cosmetic_serum",
            "name": "Lumiere Skincare Serum Bottle",
            "category": "Beauty & Personal Care",
            "description": "Frosted glass dropper bottle, fine '30ml / 1.0 fl.oz' typography, gold collar.",
            "path": "/static/samples/cosmetic_serum_supplier_input.jpg"
        },
        {
            "id": "organic_coffee_pack",
            "name": "Artisan Coffee Packaging & Barcode",
            "category": "Packaged Foods & Pantry",
            "description": "Kraft pouch texture, roast typography, heat-seal lines, scannable barcode.",
            "path": "/static/samples/organic_coffee_pack_supplier_input.jpg"
        },
        {
            "id": "wireless_earbuds",
            "name": "SonicPro Wireless ANC Earbuds",
            "category": "Consumer Electronics",
            "description": "Pebble charging case seam, micro acoustic grilles, LED status indicator.",
            "path": "/static/samples/wireless_earbuds_supplier_input.jpg"
        }
    ]
    return jsonify({"success": True, "samples": samples})


@app.route("/api/sample/<sample_id>", methods=["GET"])
def get_sample_image(sample_id):
    """Loads a specific sample image and returns base64 string and metadata."""
    sample_path = os.path.join("data", "samples", f"{sample_id}_supplier_input.jpg")
    if not os.path.exists(sample_path):
        return jsonify({"success": False, "error": f"Sample '{sample_id}' not found."}), 404
        
    img = Image.open(sample_path).convert("RGB")
    b64_str = pil_to_base64(img, format="JPEG")
    file_size_kb = round(os.path.getsize(sample_path) / 1024, 1)
    
    gt_path = os.path.join("data", "eval_dataset", "hr", f"{sample_id}_hr.png")
    has_gt = os.path.exists(gt_path)
    
    return jsonify({
        "success": True,
        "sample_id": sample_id,
        "image_base64": f"data:image/jpeg;base64,{b64_str}",
        "width": img.width,
        "height": img.height,
        "resolution": f"{img.width}x{img.height}",
        "file_size_kb": file_size_kb,
        "has_ground_truth": has_gt
    })


# =====================================================================
# 2. AI SUPER-RESOLUTION (2x, 4x, 8x with Product-Aware Presets)
# =====================================================================

@app.route("/api/upscale", methods=["POST"])
def upscale_image():
    """
    Main image restoration and super-resolution endpoint.
    Supports 2x, 4x, and 8x upscaling with automatic product category tuning.
    """
    try:
        scale = int(request.form.get("scale", 4))
        if scale not in [2, 4, 8]:
            scale = 4
            
        method = request.form.get("method", "realesrgan").lower()
        denoise = request.form.get("denoise", "true").lower() in ["true", "1", "yes"]
        sharpen = request.form.get("sharpen", "true").lower() in ["true", "1", "yes"]
        auto_preset = request.form.get("auto_preset", "true").lower() in ["true", "1", "yes"]
        save_catalog = request.form.get("save_catalog", "false").lower() in ["true", "1", "yes"]
        sample_id = request.form.get("sample_id", None)
        
        input_pil, upload_path, filename = decode_image_from_request(request)
        orig_file_size_kb = round(os.path.getsize(upload_path) / 1024, 1)

        # Dimension validation
        orig_w, orig_h = input_pil.size
        if orig_w < 32 or orig_h < 32:
            return jsonify({"success": False, "error": "Image is too small (minimum 32x32 pixels required)."}), 400
        if orig_w > 2048 or orig_h > 2048:
            return jsonify({"success": False, "error": "Image is too large (maximum 2048x2048 input supported)."}), 400

        # Product-aware analysis & preset selection
        analysis = analyzer.analyze(input_pil)
        preset = analysis["recommended_preset"] if auto_preset else None

        # Execute Super-Resolution Inference
        res = upscaler.upscale(
            image_input=input_pil,
            scale=scale,
            method=method,
            denoise=denoise,
            sharpen=sharpen,
            product_preset=preset
        )
        
        enhanced_pil = res["image"]
        enhanced_w, enhanced_h = enhanced_pil.size
        
        # Save output for downloading
        timestamp_id = int(time.time() * 1000)
        output_png_filename = f"enhanced_{timestamp_id}.png"
        output_jpg_filename = f"enhanced_{timestamp_id}.jpg"
        
        output_png_path = os.path.join(app.config["OUTPUT_FOLDER"], output_png_filename)
        output_jpg_path = os.path.join(app.config["OUTPUT_FOLDER"], output_jpg_filename)
        
        enhanced_pil.save(output_png_path, format="PNG")
        enhanced_pil.save(output_jpg_path, format="JPEG", quality=95)
        enhanced_file_size_kb = round(os.path.getsize(output_png_path) / 1024, 1)
        
        # Compute sharpness metrics
        gray_orig = cv2.cvtColor(np.array(input_pil.convert("RGB")), cv2.COLOR_RGB2GRAY)
        gray_enh = cv2.cvtColor(np.array(enhanced_pil.convert("RGB")), cv2.COLOR_RGB2GRAY)
        orig_sharpness = round(float(cv2.Laplacian(gray_orig, cv2.CV_64F).var()), 1)
        enh_sharpness = round(float(cv2.Laplacian(gray_enh, cv2.CV_64F).var()), 1)
        sharpness_boost = round(enh_sharpness / max(1.0, orig_sharpness), 1)

        metrics = {
            "has_ground_truth": False,
            "orig_sharpness": orig_sharpness,
            "enhanced_sharpness": enh_sharpness,
            "sharpness_boost": f"{sharpness_boost}x",
            "psnr": None,
            "psnr_db": None,
            "ssim": None
        }
        
        # Ground truth comparison if sample
        is_sample = bool(sample_id)
        if is_sample and sample_id:
            gt_path = os.path.join("data", "eval_dataset", "hr", f"{sample_id}_hr.png")
            if os.path.exists(gt_path):
                from skimage.metrics import peak_signal_noise_ratio as compute_psnr
                from skimage.metrics import structural_similarity as compute_ssim
                gt_img = Image.open(gt_path).convert("RGB")
                if gt_img.size == enhanced_pil.size:
                    gt_np = np.array(gt_img).astype(np.float32) / 255.0
                    en_np = np.array(enhanced_pil).astype(np.float32) / 255.0
                    psnr_val = round(float(compute_psnr(gt_np, en_np, data_range=1.0)), 2)
                    ssim_val = round(float(compute_ssim(gt_np, en_np, data_range=1.0, channel_axis=2)), 4)
                    metrics.update({
                        "has_ground_truth": True,
                        "psnr": f"{psnr_val} dB",
                        "psnr_db": psnr_val,
                        "ssim": ssim_val
                    })

        # Save to database catalog if requested
        catalog_id = None
        if save_catalog:
            catalog_id = database.add_catalog_item(
                title=f"{analysis['category']} - {scale}x {method.upper()}",
                original_path=upload_path,
                enhanced_path=output_png_path,
                category=analysis["category"],
                original_filename=filename,
                original_resolution=f"{orig_w}x{orig_h}",
                enhanced_resolution=f"{enhanced_w}x{enhanced_h}",
                scale=scale,
                method=method,
                quality_score=analysis["quality_score"],
                phash=visual_searcher.compute_dhash(enhanced_pil)
            )

        # Base64 encodings
        enhanced_b64 = pil_to_base64(enhanced_pil, format="PNG")
        original_b64 = pil_to_base64(input_pil, format="JPEG")

        return jsonify({
            "success": True,
            "enhanced_image": f"data:image/png;base64,{enhanced_b64}",
            "original_image": f"data:image/jpeg;base64,{original_b64}",
            "original_resolution": f"{orig_w}x{orig_h}",
            "enhanced_resolution": f"{enhanced_w}x{enhanced_h}",
            "scale": scale,
            "method": method,
            "latency_ms": res["latency_ms"],
            "latency_seconds": res["latency_seconds"],
            "original_file_size_kb": orig_file_size_kb,
            "enhanced_file_size_kb": enhanced_file_size_kb,
            "metrics": metrics,
            "analysis": analysis,
            "download_png": f"/api/download/{output_png_filename}",
            "download_jpg": f"/api/download/{output_jpg_filename}",
            "download_png_url": f"/api/download/{output_png_filename}",
            "download_jpg_url": f"/api/download/{output_jpg_filename}",
            "original_image_path": upload_path,
            "enhanced_image_path": output_png_path,
            "output_png_path": output_png_path,
            "catalog_id": catalog_id
        })

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 3. PRODUCT-AWARE ANALYSIS & QUALITY DIAGNOSTICS
# =====================================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_product():
    """Evaluates product category, blur/noise/exposure defects, and quality grade."""
    try:
        img_pil, _, _ = decode_image_from_request(request)
        result = analyzer.analyze(img_pil)
        return jsonify({"success": True, "analysis": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =====================================================================
# 4. AI IMAGE EDITING STUDIO
# =====================================================================

@app.route("/api/studio/adjust", methods=["POST"])
def studio_adjust():
    """Applies brightness, contrast, saturation, sharpness, rotation, or flip."""
    try:
        req_data = request.json if request.is_json else request.form
        img_pil, _, _ = decode_image_from_request(request)
        brightness = float(req_data.get("brightness", 1.0))
        contrast = float(req_data.get("contrast", 1.0))
        saturation = float(req_data.get("saturation", 1.0))
        sharpness = float(req_data.get("sharpness", 1.0))
        rotation = int(req_data.get("rotation", 0))
        flip_h = str(req_data.get("flip_h", "false")).lower() in ["true", "1"]
        flip_v = str(req_data.get("flip_v", "false")).lower() in ["true", "1"]

        adjusted = studio.apply_adjustments(
            img_pil, brightness=brightness, contrast=contrast,
            saturation=saturation, sharpness=sharpness,
            rotation=rotation, flip_h=flip_h, flip_v=flip_v
        )

        out_name = f"studio_adj_{int(time.time()*1000)}.png"
        out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)
        adjusted.save(out_path, format="PNG")
        b64 = pil_to_base64(adjusted, format="PNG")

        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{b64}",
            "image_base64": f"data:image/png;base64,{b64}",
            "download_url": f"/api/download/{out_name}",
            "resolution": f"{adjusted.width}x{adjusted.height}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/studio/bg-remove", methods=["POST"])
def studio_bg_remove():
    """Removes background or composites product onto pure white (#FFFFFF)."""
    try:
        req_data = request.json if request.is_json else request.form
        img_pil, _, _ = decode_image_from_request(request)
        mode = (req_data.get("mode") or req_data.get("bg_mode") or "white").lower()

        if mode == "white":
            result_img = studio.make_white_background(img_pil)
            fmt = "JPEG"
            mime = "image/jpeg"
        else:
            result_img = studio.remove_background(img_pil)
            fmt = "PNG"
            mime = "image/png"

        out_name = f"studio_bg_{mode}_{int(time.time()*1000)}.{fmt.lower()}"
        out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)
        result_img.save(out_path, format=fmt)
        b64 = pil_to_base64(result_img, format=fmt)

        return jsonify({
            "success": True,
            "image": f"data:{mime};base64,{b64}",
            "image_base64": f"data:{mime};base64,{b64}",
            "mode": mode,
            "download_url": f"/api/download/{out_name}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/studio/shadow", methods=["POST"])
def studio_shadow():
    """Adds a realistic soft contact shadow or specular floor reflection."""
    try:
        req_data = request.json if request.is_json else request.form
        img_pil, _, _ = decode_image_from_request(request)
        shadow_type = (req_data.get("shadow_type") or req_data.get("type") or "drop_shadow").lower()

        if shadow_type == "reflection":
            result_img = studio.add_floor_reflection(img_pil)
        else:
            result_img = studio.add_drop_shadow(img_pil)

        out_name = f"studio_fx_{shadow_type}_{int(time.time()*1000)}.png"
        out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)
        result_img.save(out_path, format="PNG")
        b64 = pil_to_base64(result_img, format="PNG")

        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{b64}",
            "image_base64": f"data:image/png;base64,{b64}",
            "shadow_type": shadow_type,
            "download_url": f"/api/download/{out_name}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/studio/nl-command", methods=["POST"])
def studio_natural_language():
    """Parses natural-language editing instructions and executes corresponding transformation."""
    try:
        req_data = request.json if request.is_json else request.form
        command = (req_data.get("command") or req_data.get("instruction") or "").strip()
        if not command:
            return jsonify({"success": False, "error": "Command text is required."}), 400

        img_pil, _, _ = decode_image_from_request(request)
        parsed = studio.parse_natural_language_command(command)
        action = parsed["action"]

        result_img = img_pil
        if action == "white_background":
            result_img = studio.make_white_background(img_pil)
        elif action == "remove_background":
            result_img = studio.remove_background(img_pil)
        elif action == "add_shadow":
            result_img = studio.add_drop_shadow(img_pil)
        elif action == "add_reflection":
            result_img = studio.add_floor_reflection(img_pil)
        elif action == "crop_ratio":
            result_img = studio.crop_to_aspect_ratio(img_pil, ratio=parsed["parameters"].get("ratio", "1:1"))
        elif action == "adjust":
            params = parsed["parameters"]
            result_img = studio.apply_adjustments(
                img_pil,
                brightness=params.get("brightness", 1.0),
                contrast=params.get("contrast", 1.0),
                sharpness=params.get("sharpness", 1.0)
            )

        out_name = f"studio_nl_{int(time.time()*1000)}.png"
        out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)
        result_img.save(out_path, format="PNG")
        b64 = pil_to_base64(result_img, format="PNG")

        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{b64}",
            "image_base64": f"data:image/png;base64,{b64}",
            "parsed_command": parsed,
            "download_url": f"/api/download/{out_name}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 5. MULTI-MODEL LABORATORY (Side-by-Side Comparison)
# =====================================================================

@app.route("/api/models/compare", methods=["POST"])
def compare_models():
    """Run all four super-resolution models in parallel on the same image."""
    try:
        req_data = request.json if request.is_json else request.form
        img_pil, _, _ = decode_image_from_request(request)
        # Fully load and detach from the source file before sharing across threads.
        base_img = img_pil.copy()
        base_img.load()
        scale = int(req_data.get("scale", 4))
        models_to_test = ["realesrgan", "edsr", "srcnn", "bicubic"]

        def run_model(model_name):
            try:
                result = comparison_engines[model_name].upscale(
                    base_img.copy(), scale=scale, method=model_name,
                    denoise=True, sharpen=True
                )
                out_img = result["image"]
                b64 = pil_to_base64(out_img, format="JPEG")
                gray = cv2.cvtColor(np.array(out_img), cv2.COLOR_RGB2GRAY)
                sharpness = round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1)
                return model_name, {
                    "success": True,
                    "method_name": "Real-ESRGAN" if model_name == "realesrgan" else model_name.upper(),
                    "image_base64": f"data:image/jpeg;base64,{b64}",
                    "resolution": f"{out_img.width}x{out_img.height}",
                    "latency_ms": result["latency_ms"],
                    "sharpness": sharpness,
                    "is_recommended": model_name == "realesrgan",
                }
            except Exception as exc:
                return model_name, {"success": False, "error": str(exc)}

        comparison_results = {}
        with ThreadPoolExecutor(max_workers=len(models_to_test)) as executor:
            futures = {executor.submit(run_model, m): m for m in models_to_test}
            for future in as_completed(futures):
                model_name, payload = future.result()
                comparison_results[model_name] = payload

        completed = sum(1 for value in comparison_results.values() if value.get("success"))
        return jsonify({
            "success": completed > 0,
            "scale": scale,
            "parallel": True,
            "completed_count": completed,
            "total_count": len(models_to_test),
            "comparison": comparison_results,
            "results": comparison_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 6. AI EXPLAINABILITY & HALLUCINATION DETECTION
# =====================================================================

@app.route("/api/explainability", methods=["POST"])
def explain_enhancement():
    """Produces reconstruction heatmaps, ΔE color deviation, and hallucination risk."""
    try:
        req_data = request.json if request.is_json else request.form
        
        orig_img = None
        orig_path = req_data.get("original_path") or req_data.get("image_path")
        if orig_path and os.path.exists(orig_path):
            orig_img = Image.open(orig_path).convert("RGB")
        elif orig_path and os.path.exists(orig_path.lstrip("/\\")):
            orig_img = Image.open(orig_path.lstrip("/\\")).convert("RGB")
            
        if orig_img is None:
            orig_img, _, _ = decode_image_from_request(request)
        
        enh_img = None
        enh_path = req_data.get("enhanced_path")
        if enh_path and os.path.exists(enh_path):
            enh_img = Image.open(enh_path).convert("RGB")
        elif enh_path and os.path.exists(enh_path.lstrip("/\\")):
            enh_img = Image.open(enh_path.lstrip("/\\")).convert("RGB")

        if enh_img is None:
            # Check if an enhanced image is passed or if we enhance on the fly
            enh_b64 = req_data.get("enhanced_base64")
            if enh_b64:
                if "," in enh_b64:
                    enh_b64 = enh_b64.split(",", 1)[1]
                enh_img = Image.open(io.BytesIO(base64.b64decode(enh_b64))).convert("RGB")
            else:
                scale = int(req_data.get("scale", 4))
                res = upscaler.upscale(orig_img, scale=scale, method="realesrgan")
                enh_img = res["image"]

        report = explainer.analyze_reconstruction(orig_img, enh_img)
        heatmap_b64 = pil_to_base64(report["heatmap_image"], format="PNG")

        conf_raw = report["confidence_score"]
        conf_int = int(float(str(conf_raw).replace("%", "").strip()))

        metrics_dict = {
            "delta_e_color_deviation": report["mean_delta_e"],
            "mean_delta_e": report["mean_delta_e"],
            "max_delta_e": report["max_delta_e"],
            "color_fidelity_rating": report["color_fidelity_rating"],
            "reconstruction_density_pct": report["reconstruction_density_pct"],
            "hallucination_risk": report["hallucination_risk"],
            "hallucination_warning": report["hallucination_warning"],
            "confidence_score": report["confidence_score"],
            "confidence_pct": conf_int
        }

        return jsonify({
            "success": True,
            "heatmap_image": f"data:image/png;base64,{heatmap_b64}",
            "reconstruction_heatmap": f"data:image/png;base64,{heatmap_b64}",
            "mean_delta_e": report["mean_delta_e"],
            "max_delta_e": report["max_delta_e"],
            "color_fidelity_rating": report["color_fidelity_rating"],
            "reconstruction_density_pct": report["reconstruction_density_pct"],
            "hallucination_risk": report["hallucination_risk"],
            "hallucination_warning": report["hallucination_warning"],
            "confidence_score": report["confidence_score"],
            "metrics": metrics_dict
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 7. ASYNCHRONOUS BATCH PROCESSING
# =====================================================================

@app.route("/api/batch/upload", methods=["POST"])
def batch_upload():
    """Accepts multiple vendor images and queues background batch processing."""
    try:
        files = request.files.getlist("files")
        if not files or len(files) == 0:
            return jsonify({"success": False, "error": "No files uploaded."}), 400

        scale = int(request.form.get("scale", 4))
        method = request.form.get("method", "realesrgan")
        auto_preset = request.form.get("auto_preset", "true").lower() in ["true", "1"]

        saved_paths = []
        for f in files:
            if f and allowed_file(f.filename):
                safe_name = f"{int(time.time()*1000)}_{secure_filename(f.filename)}"
                dest = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
                f.save(dest)
                saved_paths.append(dest)

        if not saved_paths:
            return jsonify({"success": False, "error": "No valid image files found."}), 400

        job_id = batch_engine.submit_batch(
            file_paths=saved_paths,
            scale=scale,
            method=method,
            auto_preset=auto_preset
        )

        return jsonify({
            "success": True,
            "job_id": job_id,
            "total_files": len(saved_paths),
            "status_url": f"/api/batch/status/{job_id}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/batch/status/<job_id>", methods=["GET"])
def batch_status(job_id):
    """Polls real-time progress of a batch processing job."""
    status = batch_engine.get_status(job_id)
    if not status:
        return jsonify({"success": False, "error": f"Job '{job_id}' not found."}), 404
    return jsonify({"success": True, "job": status})


@app.route("/api/batch/cancel/<job_id>", methods=["POST"])
def batch_cancel(job_id):
    """Cancels an in-flight batch job."""
    res = batch_engine.cancel_job(job_id)
    return jsonify({"success": res, "message": "Job cancellation signal sent." if res else "Job not found."})


# =====================================================================
# 8. PRODUCT CATALOG & VISUAL VECTOR SEARCH
# =====================================================================

@app.route("/api/catalog/list", methods=["GET"])
def list_catalog():
    """Fetches user catalog items with optional filtering by category or keyword."""
    category = request.args.get("category", None)
    search = request.args.get("search", None)
    is_fav = request.args.get("favorite")
    is_fav_bool = True if is_fav in ["true", "1"] else None

    items = database.get_catalog_items(category=category, search=search, is_favorite=is_fav_bool)
    return jsonify({"success": True, "count": len(items), "items": items})


@app.route("/api/catalog/save", methods=["POST"])
def save_catalog_item():
    """Commits an enhanced image to the persistent catalog database."""
    try:
        title = request.form.get("title", "Product Asset")
        category = request.form.get("category", "General")
        orig_path = request.form.get("original_path", "")
        enh_path = request.form.get("enhanced_path", "")
        orig_res = request.form.get("original_resolution", "128x128")
        enh_res = request.form.get("enhanced_resolution", "512x512")
        scale = int(request.form.get("scale", 4))
        method = request.form.get("method", "realesrgan")
        score = int(request.form.get("quality_score", 85))

        phash = None
        if os.path.exists(enh_path):
            phash = visual_searcher.compute_dhash(Image.open(enh_path))

        item_id = database.add_catalog_item(
            title=title,
            original_path=orig_path,
            enhanced_path=enh_path,
            category=category,
            original_resolution=orig_res,
            enhanced_resolution=enh_res,
            scale=scale,
            method=method,
            quality_score=score,
            phash=phash
        )
        return jsonify({"success": True, "catalog_id": item_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/catalog/favorite/<int:item_id>", methods=["POST"])
def toggle_catalog_favorite(item_id):
    """Toggles bookmark status on a catalog item."""
    res = database.toggle_favorite(item_id)
    return jsonify({"success": True, "is_favorite": res})


@app.route("/api/catalog/delete/<int:item_id>", methods=["DELETE", "POST"])
def delete_catalog_item_route(item_id):
    """Deletes a catalog item."""
    database.delete_catalog_item(item_id)
    return jsonify({"success": True, "deleted_id": item_id})


@app.route("/api/catalog/search-visual", methods=["POST"])
@app.route("/api/search/visual", methods=["POST"])
def search_visual_similarity():
    """Performs visual vector similarity search or text search across user catalog."""
    try:
        req_data = request.json if request.is_json else request.form
        query_text = req_data.get("query_text") or req_data.get("query")
        if query_text:
            items = database.get_catalog_items(query=query_text)
            return jsonify({"success": True, "matches": items, "count": len(items)})

        query_img, _, _ = decode_image_from_request(request)
        all_items = database.get_catalog_items(limit=100)
        matches = visual_searcher.find_similar_items(query_img, all_items, top_k=8)
        return jsonify({"success": True, "matches": matches, "query_count": len(matches)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 9. E-COMMERCE EXPORT CENTER
# =====================================================================

@app.route("/api/export/preset", methods=["POST"])
def export_preset():
    """Formats and validates an image against Amazon, Shopify, or Flipkart presets."""
    try:
        req_data = request.json if request.is_json else request.form
        img_pil, _, _ = decode_image_from_request(request)

        preset_key = req_data.get("preset") or req_data.get("platform") or "amazon"
        custom_w = req_data.get("custom_width") or req_data.get("width")
        custom_h = req_data.get("custom_height") or req_data.get("height")
        custom_format = req_data.get("custom_format") or req_data.get("format")
        custom_quality = req_data.get("custom_quality") or req_data.get("quality")
        force_white = str(req_data.get("force_white", "false")).lower() in ["true", "1"]

        res = exporter.process_export(
            img_pil=img_pil,
            preset_key=preset_key,
            custom_width=int(custom_w) if custom_w else None,
            custom_height=int(custom_h) if custom_h else None,
            custom_format=custom_format,
            custom_quality=int(custom_quality) if custom_quality else None,
            force_white_bg=force_white
        )

        out_name = f"export_{preset_key}_{int(time.time()*1000)}.{res['extension']}"
        out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)
        with open(out_path, "wb") as f:
            f.write(res["buffer"])

        b64 = base64.b64encode(res["buffer"]).decode("utf-8")

        return jsonify({
            "success": True,
            "image": f"data:{res['mime_type']};base64,{b64}",
            "download_url": f"/api/download/{out_name}",
            "filename": out_name,
            "resolution": res["resolution"],
            "file_size_kb": res["file_size_kb"],
            "preset_used": res["preset_used"],
            "is_compliant": res["is_compliant"],
            "compliance_issues": res["compliance_issues"],
            "compliance": {
                "is_compliant": res["is_compliant"],
                "issues": res["compliance_issues"]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 10. ACCESSIBILITY & METADATA EXTRACTION
# =====================================================================

@app.route("/api/metadata", methods=["POST"])
def get_metadata():
    """Extracts image metadata and generates SEO Alt-Text descriptions."""
    try:
        img_pil, _, filename = decode_image_from_request(request)
        analysis = analyzer.analyze(img_pil)
        w, h = img_pil.size
        
        # Color profile & format
        mode = img_pil.mode
        dpi = img_pil.info.get("dpi", (72, 72))
        
        # Auto-generated Alt-Text
        alt_text = f"High-resolution {analysis['category']} product photograph, {w}x{h} px with sharp packaging detail on neutral background."

        return jsonify({
            "success": True,
            "filename": filename,
            "dimensions": f"{w}x{h}",
            "aspect_ratio": analysis["aspect_ratio"],
            "color_mode": mode,
            "dpi": f"{dpi[0]} DPI",
            "detected_category": analysis["category"],
            "generated_alt_text": alt_text,
            "quality_grade": analysis["quality_grade"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 11. USER AUTHENTICATION
# =====================================================================

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json(silent=True) or request.form
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "error": "Username and password required."}), 400
    res = database.register_user(username, password)
    return jsonify(res)


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(silent=True) or request.form
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    res = database.authenticate_user(username, password)
    if res["success"]:
        session["user_id"] = res["user"]["id"]
        session["username"] = res["user"]["username"]
    return jsonify(res)


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    user_id = session.get("user_id", 1)
    user = database.get_user_by_id(user_id)
    return jsonify({"success": True, "user": user})


# =====================================================================
# 12. DOWNLOAD & BENCHMARK ROUTES
# =====================================================================

@app.route("/api/download/<filename>", methods=["GET"])
def download_image(filename):
    """Delivers generated assets from the outputs directory."""
    safe_filename_clean = secure_filename(filename)
    file_path = os.path.join(app.config["OUTPUT_FOLDER"], safe_filename_clean)
    if not os.path.exists(file_path):
        fallback_path = os.path.join("static", "outputs", safe_filename_clean)
        if os.path.exists(fallback_path):
            file_path = fallback_path
        else:
            return jsonify({"success": False, "error": "File not found or expired."}), 404
        
    ext = os.path.splitext(safe_filename_clean)[1].lower()
    mime_type = "image/png"
    if ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif ext == ".webp":
        mime_type = "image/webp"
    elif ext == ".zip":
        mime_type = "application/zip"

    return send_file(
        os.path.abspath(file_path),
        mimetype=mime_type,
        as_attachment=True,
        download_name=safe_filename_clean
    )


@app.route("/api/benchmark", methods=["GET"])
def get_benchmark_results():
    """Returns stored quantitative evaluation metrics and baseline comparisons."""
    summary_path = os.path.join("evaluation", "results", "evaluation_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "error": "Evaluation summary not found."}), 404


@app.route("/api/chat/languages", methods=["GET"])
def get_chat_languages():
    """Returns the supported multilingual options for text and voice."""
    return jsonify({
        "success": True,
        "languages": [
            {"code": "en", "name": "English", "locale": "en-US", "flag": "🇬🇧"},
            {"code": "te", "name": "తెలుగు", "locale": "te-IN", "flag": "🇮🇳"},
            {"code": "hi", "name": "हिंदी", "locale": "hi-IN", "flag": "🇮🇳"}
        ]
    })


def _markdown_to_speech(text: str) -> str:
    """Create a clean voiceover string from markdown answer text."""
    cleaned = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    cleaned = re.sub(r"[#*_`>|\[\]]", " ", cleaned)
    cleaned = re.sub(r"^\s*[-+]\s+", "", cleaned, flags=re.M)
    return re.sub(r"\s+", " ", cleaned).strip()[:1200]


def _llm_system_prompt(language: str, context: dict, provider_label: str, model_name: str) -> str:
    """Ground an optional hosted model in this app and its active session."""
    language_names = {"en": "English", "te": "Telugu", "hi": "Hindi"}
    language_line = (
        f"Reply only in {language_names[language]}."
        if language in language_names
        else "Detect the user's language and reply in the same language."
    )
    parts = [
        chatbot.SYSTEM_PROMPT,
        "You are answering inside the SuperClarity AI product-image workspace.",
        (
            "When asked which model or who trained you, say you are the SuperClarity "
            f"Assistant and that this workspace is currently configured with "
            f"{provider_label} ({model_name}). Do not invent a training organisation "
            "or claim to be a different product."
        ),
        language_line,
        "Keep answers direct, practical, and under 180 words unless the user asks for detail.",
        "Use short markdown headings and bullet points when they improve clarity.",
    ]
    active_bits = []
    if context.get("active_sample"):
        active_bits.append(f"active sample: {context['active_sample']}")
    if context.get("scale"):
        active_bits.append(f"selected upscale: {context['scale']}x")
    if context.get("method"):
        active_bits.append(f"method: {context['method']}")
    if context.get("has_enhanced_image"):
        active_bits.append("an enhanced image is currently loaded")
    if active_bits:
        parts.append("Active session: " + "; ".join(active_bits) + ".")
    return " ".join(parts)


@app.route("/api/chat/providers", methods=["GET"])
def chat_providers():
    """Expose safe provider defaults (never any stored key)."""
    return jsonify({
        "success": True,
        "providers": [
            {
                "id": key,
                "label": value["label"],
                "default_model": value["model"],
                "default_base_url": value["base_url"],
            }
            for key, value in PROVIDER_DEFAULTS.items()
        ],
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Multilingual assistant endpoint. Uses the built-in guide by default, or a
    user-supplied Groq / Gemini / NVIDIA NIM key when present in the request.
    Keys are used for this request only and are never stored server-side.
    """
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "error": "Query message cannot be empty."}), 400

        language = data.get("language", "auto")
        if language == "auto":
            language = None
        if language not in chatbot.SUPPORTED_LANGUAGES:
            language = None

        context = data.get("context", {}) or {}
        result = chatbot.generate_response(
            query=message,
            preferred_lang=language,
            context=context
        )
        result["provider_used"] = "Built-in guide"

        provider = normalize_provider(data.get("provider"))
        api_key = str(data.get("api_key") or "").strip()
        if provider and api_key:
            model_name = str(data.get("model") or "").strip() or PROVIDER_DEFAULTS[provider]["model"]
            base_url = str(data.get("base_url") or "").strip()
            active_language = language or result.get("active_language", "en")
            system_prompt = _llm_system_prompt(
                active_language,
                context,
                PROVIDER_DEFAULTS[provider]["label"],
                model_name,
            )
            try:
                reply = generate_llm_reply(
                    provider=provider,
                    api_key=api_key,
                    message=message,
                    system_prompt=system_prompt,
                    model=model_name,
                    base_url=base_url,
                )
                result.update({
                    "response_markdown": reply["text"],
                    "speech_text": _markdown_to_speech(reply["text"]),
                    "intent": "external_llm",
                    "provider_used": reply["provider_label"],
                    "model_used": reply["model"],
                    "active_language": active_language,
                    "language_name": chatbot.SUPPORTED_LANGUAGES.get(
                        active_language, chatbot.SUPPORTED_LANGUAGES["en"]
                    )["name"],
                    "notice": "",
                })
            except Exception as exc:
                result["notice"] = (
                    f"{PROVIDER_DEFAULTS[provider]['label']} could not be reached; "
                    f"used the built-in guide. {exc}"
                )

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Chat processing failed: {str(e)}"}), 500


if __name__ == "__main__":
    print("\n=======================================================")
    print("  SuperClarity AI Enterprise Server Running")
    print("  Local URL: http://127.0.0.1:5050")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=5050, debug=False)
