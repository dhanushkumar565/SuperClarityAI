"""
SupplierClarity AI - Flask Web Application
Domain: E-Commerce & Retail Product Image Upscaler
Reference: SmartBridge / Skill Wallet Project Workflow Architecture
"""

import os
import io
import time
import base64
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

from models.upscaler import SupplierClarityUpscaler
from models.chatbot import SupplierClarityChatbot
from dataset_pipeline import setup_demo_and_eval_datasets

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join("static", "outputs")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Initialize Super-Resolution Engine & Multilingual Assistant
upscaler = SupplierClarityUpscaler()
chatbot = SupplierClarityChatbot()

# Ensure samples exist
setup_demo_and_eval_datasets(base_dir="data")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "jfif", "bmp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def pil_to_base64(img: Image.Image, format: str = "PNG") -> str:
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


@app.route("/")
def index():
    """Renders the main SupplierClarity AI glassmorphism interface."""
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
    
    # Check if ground-truth exists for this sample
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


@app.route("/api/upscale", methods=["POST"])
def upscale_image():
    """
    Main image restoration and super-resolution endpoint.
    Accepts multipart file upload or sample_id, scale (2 or 4), and options.
    """
    try:
        scale = int(request.form.get("scale", 4))
        if scale not in [2, 4]:
            scale = 4
            
        method = request.form.get("method", "realesrgan").lower()
        denoise = request.form.get("denoise", "true").lower() in ["true", "1", "yes"]
        sharpen = request.form.get("sharpen", "true").lower() in ["true", "1", "yes"]
        sample_id = request.form.get("sample_id", None)
        
        input_pil = None
        orig_file_size_kb = 0
        is_sample = False
        
        # 1. Check if user uploaded a file
        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            if not allowed_file(file.filename):
                return jsonify({"success": False, "error": "Invalid file format. Supported: PNG, JPG, JPEG, WEBP"}), 400
                
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{int(time.time())}_{filename}")
            file.save(upload_path)
            orig_file_size_kb = round(os.path.getsize(upload_path) / 1024, 1)
            input_pil = Image.open(upload_path).convert("RGB")
            
        # 2. Or check if a sample was selected
        elif sample_id:
            sample_path = os.path.join("data", "samples", f"{sample_id}_supplier_input.jpg")
            if os.path.exists(sample_path):
                input_pil = Image.open(sample_path).convert("RGB")
                orig_file_size_kb = round(os.path.getsize(sample_path) / 1024, 1)
                is_sample = True
            else:
                return jsonify({"success": False, "error": f"Sample '{sample_id}' not found."}), 404
        else:
            return jsonify({"success": False, "error": "No image provided. Upload a file or select a sample."}), 400

        # Dimension validation
        orig_w, orig_h = input_pil.size
        if orig_w < 32 or orig_h < 32:
            return jsonify({"success": False, "error": "Image is too small (minimum 32x32 pixels required)."}), 400
        if orig_w > 2048 or orig_h > 2048:
            return jsonify({"success": False, "error": "Image is too large (maximum 2048x2048 input supported)."}), 400

        # 3. Execute Super-Resolution Inference
        res = upscaler.upscale(
            image_input=input_pil,
            scale=scale,
            method=method,
            denoise=denoise,
            sharpen=sharpen
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
        import cv2
        gray_orig = cv2.cvtColor(np.array(input_pil), cv2.COLOR_RGB2GRAY)
        gray_enh = cv2.cvtColor(np.array(enhanced_pil), cv2.COLOR_RGB2GRAY)
        orig_sharpness = round(float(cv2.Laplacian(gray_orig, cv2.CV_64F).var()), 1)
        enh_sharpness = round(float(cv2.Laplacian(gray_enh, cv2.CV_64F).var()), 1)
        sharpness_boost = round(enh_sharpness / max(1.0, orig_sharpness), 1)

        # Ground truth comparison if available
        metrics = {
            "has_ground_truth": False,
            "orig_sharpness": orig_sharpness,
            "enhanced_sharpness": enh_sharpness,
            "sharpness_boost": f"{sharpness_boost}x"
        }
        
        if is_sample and sample_id:
            gt_path = os.path.join("data", "eval_dataset", "hr", f"{sample_id}_hr.png")
            if os.path.exists(gt_path):
                from skimage.metrics import peak_signal_noise_ratio as compute_psnr
                from skimage.metrics import structural_similarity as compute_ssim
                
                gt_pil = Image.open(gt_path).convert("RGB")
                gt_np = np.array(gt_pil)
                enh_np = np.array(enhanced_pil)
                
                if enh_np.shape == gt_np.shape:
                    psnr_val = round(float(compute_psnr(gt_np, enh_np, data_range=255)), 2)
                    ssim_val = round(float(compute_ssim(gt_np, enh_np, data_range=255, channel_axis=2)), 4)
                    metrics.update({
                        "has_ground_truth": True,
                        "psnr_db": psnr_val,
                        "ssim": ssim_val
                    })

        # Base64 encodings for responsive display
        orig_b64 = pil_to_base64(input_pil, format="JPEG")
        enh_b64 = pil_to_base64(enhanced_pil, format="PNG")
        
        return jsonify({
            "success": True,
            "method": method,
            "scale": scale,
            "original_image": f"data:image/jpeg;base64,{orig_b64}",
            "enhanced_image": f"data:image/png;base64,{enh_b64}",
            "original_resolution": f"{orig_w}x{orig_h}",
            "enhanced_resolution": f"{enhanced_w}x{enhanced_h}",
            "orig_file_size_kb": orig_file_size_kb,
            "enhanced_file_size_kb": enhanced_file_size_kb,
            "latency_seconds": res["latency_seconds"],
            "latency_ms": res["latency_ms"],
            "download_png_url": f"/api/download/{output_png_filename}",
            "download_jpg_url": f"/api/download/{output_jpg_filename}",
            "metrics": metrics
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Image enhancement failed: {str(e)}"}), 500


@app.route("/api/download/<filename>", methods=["GET"])
def download_image(filename):
    """Securely downloads the generated enhanced image."""
    safe_name = secure_filename(filename)
    file_path = os.path.join(app.config["OUTPUT_FOLDER"], safe_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "File not found."}), 404


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


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Intelligent Multilingual Voice-Enabled Assistant Endpoint.
    Accepts text or voice transcripts in English, Telugu, or Hindi,
    and returns context-aware guidance with speech synthesis payload.
    """
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "error": "Query message cannot be empty."}), 400

        language = data.get("language", "auto")
        if language == "auto":
            language = None

        context = data.get("context", {})

        result = chatbot.generate_response(
            query=message,
            preferred_lang=language,
            context=context
        )
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Chat processing failed: {str(e)}"}), 500


if __name__ == "__main__":
    print("\n=======================================================")
    print("  SupplierClarity AI Development Server Running")
    print("  Local URL: http://127.0.0.1:5050")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=5050, debug=False)
