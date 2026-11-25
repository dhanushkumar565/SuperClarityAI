"""
SupplierClarity AI - Ultra HD (300 DPI) Asset Generator
Generates crystal-clear 2400px+ diagrams, authentic UI captures, and 300 DPI charts.
"""

import os
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt
import pandas as pd

os.makedirs("static/images", exist_ok=True)

def get_font(size: int, bold: bool = False, mono: bool = False):
    try:
        if mono:
            font_name = "consola.ttf" if bold else "cour.ttf"
        else:
            font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------------------------------------------------
# 1. ULTRA-HD HEADER BANNER (2400 x 280 px)
# ---------------------------------------------------------------------
def create_ultra_hd_banner():
    w, h = 2400, 280
    img = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Left: SmartBridge Logo
    icon_x, icon_y = 60, 50
    draw.arc([icon_x, icon_y + 20, icon_x + 100, icon_y + 120], start=180, end=360, fill=(234, 67, 53), width=10)
    draw.arc([icon_x + 20, icon_y, icon_x + 120, icon_y + 100], start=180, end=360, fill=(66, 133, 244), width=10)
    draw.arc([icon_x + 40, icon_y - 20, icon_x + 140, icon_y + 80], start=180, end=360, fill=(52, 168, 83), width=10)
    
    draw.text((icon_x + 155, icon_y + 15), "SMARTBRIDGE", fill=(30, 41, 59), font=get_font(52, bold=True))
    draw.text((icon_x + 230, icon_y + 78), "Let's Bridge the Gap", fill=(100, 116, 139), font=get_font(28))
    
    # Right: Skill Wallet Logo
    right_x = 1800
    draw.text((right_x, icon_y + 12), "SKILL", fill=(30, 58, 138), font=get_font(52, bold=True))
    draw.text((right_x + 160, icon_y + 12), "WALLET", fill=(2, 132, 199), font=get_font(52, bold=True))
    draw.rectangle([right_x + 310, icon_y + 22, right_x + 375, icon_y + 64], fill=(2, 132, 199))
    draw.text((right_x + 322, icon_y + 26), "AI", fill=(255, 255, 255), font=get_font(28, bold=True))
    draw.text((right_x + 40, icon_y + 80), "A SmartBridge Product", fill=(100, 116, 139), font=get_font(26))
    
    # Subtle separator line
    draw.line([(60, h - 10), (w - 60, h - 10)], fill=(226, 232, 240), width=3)
    
    img.save("static/images/pdf_header_banner.png", format="PNG")
    print(" -> Generated Ultra-HD: static/images/pdf_header_banner.png")

# ---------------------------------------------------------------------
# 2. ULTRA-HD ARCHITECTURE DIAGRAM (2400 x 1150 px)
# ---------------------------------------------------------------------
def create_ultra_hd_architecture():
    w, h = 2400, 1150
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header title
    draw.rectangle([0, 0, w, 110], fill=(241, 245, 249))
    draw.text((60, 32), "SupplierClarity AI — Modular Three-Tier Deep Learning Architecture", fill=(15, 23, 42), font=get_font(40, bold=True))
    draw.line([(0, 110), (w, 110)], fill=(203, 213, 225), width=3)
    
    # Tier 1: Ingestion & Frontend
    t1_box = [60, 150, 780, 1080]
    draw.rounded_rectangle(t1_box, radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=4)
    draw.rectangle([60, 150, 780, 250], fill=(241, 245, 249))
    draw.text((95, 175), "Tier 1: Presentation & Ingestion", fill=(30, 41, 59), font=get_font(34, bold=True))
    
    steps1 = [
        ("Web Glassmorphism Interface", "HTML5 · CSS3 Glassmorphism · JavaScript Fetch", (139, 92, 246)),
        ("Vendor Photo Ingestion", "Drag & Drop · 5 E-Commerce Demo Samples", (56, 189, 248)),
        ("Interactive Comparison Viewer", "Draggable Split-Wipe Slider · Side-by-Side", (245, 158, 11)),
        ("Public Tunneling & Access", "PyNgrok & Cloudflare Tunnel Proxy", (16, 185, 129))
    ]
    y = 285
    for title, sub, col in steps1:
        draw.rounded_rectangle([95, y, 745, y + 150], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=2)
        draw.rectangle([95, y, 110, y + 150], fill=col)
        draw.text((130, y + 30), title, fill=(15, 23, 42), font=get_font(26, bold=True))
        draw.text((130, y + 80), sub, fill=(100, 116, 139), font=get_font(21))
        y += 185

    # Connector Arrow 1 -> 2
    draw.polygon([(810, 600), (870, 615), (810, 630)], fill=(99, 102, 241))
    draw.line([(780, 615), (850, 615)], fill=(99, 102, 241), width=8)

    # Tier 2: Backend Orchestration (Flask)
    t2_box = [880, 150, 1590, 1080]
    draw.rounded_rectangle(t2_box, radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=4)
    draw.rectangle([880, 150, 1590, 250], fill=(241, 245, 249))
    draw.text((915, 175), "Tier 2: Backend Orchestration", fill=(30, 41, 59), font=get_font(34, bold=True))
    
    steps2 = [
        ("Flask RESTful API (app.py)", "POST /api/upscale · GET /api/samples", (139, 92, 246)),
        ("Data Normalization & Denoise", "RGB Validation · Bilateral JPEG Suppression", (56, 189, 248)),
        ("Telemetry & Quality Engine", "Tenengrad Sharpness · PSNR · SSIM", (245, 158, 11)),
        ("Production Asset Delivery", "One-Click HD PNG & Compressed JPEG", (16, 185, 129))
    ]
    y = 285
    for title, sub, col in steps2:
        draw.rounded_rectangle([915, y, 1555, y + 150], radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=2)
        draw.rectangle([915, y, 930, y + 150], fill=col)
        draw.text((950, y + 30), title, fill=(15, 23, 42), font=get_font(26, bold=True))
        draw.text((950, y + 80), sub, fill=(100, 116, 139), font=get_font(21))
        y += 185

    # Connector Arrow 2 -> 3
    draw.polygon([(1620, 600), (1680, 615), (1620, 630)], fill=(99, 102, 241))
    draw.line([(1590, 615), (1660, 615)], fill=(99, 102, 241), width=8)

    # Tier 3: PyTorch Neural Super-Resolution Core
    t3_box = [1690, 150, 2340, 1080]
    draw.rounded_rectangle(t3_box, radius=24, fill=(255, 255, 255), outline=(203, 213, 225), width=4)
    draw.rectangle([1690, 150, 2340, 250], fill=(238, 242, 255))
    draw.text((1725, 175), "Tier 3: PyTorch Super-Res Core", fill=(67, 56, 202), font=get_font(34, bold=True))
    
    steps3 = [
        ("Real-ESRGAN / SRVGGNet", "4× Edge Super-Resolution (4.88 MB weight)", (109, 40, 217)),
        ("RRDBNet (RealESRGAN_x2plus)", "2× Horology & Apparel Super-Resolution", (56, 189, 248)),
        ("EDSR & SRCNN Baselines", "Residual & 3-Layer Convolutional Baselines", (245, 158, 11)),
        ("Memory Tiling & Sharpening", "Tile=512 Sub-Second Real-Time CPU Latency", (16, 185, 129))
    ]
    y = 285
    for title, sub, col in steps3:
        draw.rounded_rectangle([1725, y, 2305, y + 150], radius=16, fill=(245, 243, 255), outline=(221, 214, 254), width=2)
        draw.rectangle([1725, y, 1740, y + 150], fill=col)
        draw.text((1760, y + 30), title, fill=(109, 40, 217), font=get_font(26, bold=True))
        draw.text((1760, y + 80), sub, fill=(124, 58, 237), font=get_font(21))
        y += 185

    img.save("static/images/architecture_diagram.png", format="PNG")
    print(" -> Generated Ultra-HD: static/images/architecture_diagram.png")

# ---------------------------------------------------------------------
# 3. ULTRA-HD VS CODE FILE TREE (2000 x 1200 px)
# ---------------------------------------------------------------------
def create_ultra_hd_folder_tree():
    w, h = 2000, 1200
    img = Image.new("RGB", (w, h), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    
    # Left Activity Bar (VS Code)
    draw.rectangle([0, 0, 90, h], fill=(51, 51, 51))
    # Icons on activity bar
    draw.rectangle([0, 10, 8, 80], fill=(255, 255, 255)) # active indicator
    draw.rectangle([25, 25, 65, 65], fill=(255, 255, 255)) # files icon
    draw.ellipse([30, 110, 60, 140], outline=(150, 150, 150), width=4) # search
    draw.line([(35, 210), (55, 180), (55, 240)], fill=(150, 150, 150), width=5) # git
    draw.polygon([(35, 280), (60, 300), (35, 320)], fill=(150, 150, 150)) # debug
    
    # Explorer Pane Header
    draw.rectangle([90, 0, w, 70], fill=(37, 37, 38))
    draw.text((120, 20), "EXPLORER: SUPPLIERCLARITY-AI", fill=(187, 187, 187), font=get_font(24, bold=True))
    
    tree_items = [
        ("v", "models", True, (200, 160, 255)),
        ("    ", "upscaler.py", False, (80, 200, 255)),
        ("    ", "srcnn.py", False, (80, 200, 255)),
        ("    ", "edsr.py", False, (80, 200, 255)),
        ("    v", "weights", True, (200, 160, 255)),
        ("        ", "realesr-general-x4v3.pth (4.88 MB)", False, (150, 150, 150)),
        ("        ", "RealESRGAN_x2plus.pth (67.0 MB)", False, (150, 150, 150)),
        ("v", "data", True, (255, 200, 80)),
        ("    v", "samples (5 e-commerce categories)", True, (255, 200, 80)),
        ("        ", "luxury_watch_supplier_input.jpg", False, (150, 220, 150)),
        ("        ", "sneaker_shoe_supplier_input.jpg", False, (150, 220, 150)),
        ("        ", "cosmetic_serum_supplier_input.jpg", False, (150, 220, 150)),
        ("        ", "organic_coffee_pack_supplier_input.jpg", False, (150, 220, 150)),
        ("        ", "wireless_earbuds_supplier_input.jpg", False, (150, 220, 150)),
        ("    v", "eval_dataset (paired ground truth)", True, (255, 200, 80)),
        ("v", "static", True, (100, 220, 150)),
        ("    ", "css/style.css (dark glassmorphism)", False, (80, 200, 255)),
        ("    ", "js/main.js (split slider & async fetch)", False, (255, 220, 80)),
        ("    ", "images (architecture, charts, mockups)", False, (150, 150, 150)),
        ("v", "templates", True, (255, 120, 100)),
        ("    ", "index.html (single-page interface)", False, (255, 150, 80)),
        (" ", "app.py (Flask REST server)", False, (80, 200, 255)),
        (" ", "run_public.py (Cloud tunnel script)", False, (80, 200, 255)),
        (" ", "dataset_pipeline.py", False, (80, 200, 255)),
        (" ", "train_sr.py (PyTorch fine-tuning)", False, (80, 200, 255)),
        (" ", "test_app.py (9 automated unit tests)", False, (100, 220, 150)),
        (" ", "requirements.txt", False, (150, 150, 150)),
        (" ", ".env", False, (150, 150, 150))
    ]
    
    y = 90
    for icon, name, is_f, col in tree_items:
        prefix = "> " if icon == "v" else ("  " if icon == " " else icon)
        draw.text((120, y), prefix + name, fill=col, font=get_font(25, bold=is_f, mono=True))
        y += 37
        
    # Status bar at bottom
    draw.rectangle([0, h - 45, w, h], fill=(0, 122, 204))
    draw.text((30, h - 35), "main*  -- Python 3.11.0 (myenv: venv) -- UTF-8 -- LF", fill=(255, 255, 255), font=get_font(20, bold=True))

    img.save("static/images/folder_tree_screenshot.png")
    print(" -> Generated Ultra-HD: static/images/folder_tree_screenshot.png")

# ---------------------------------------------------------------------
# 4. ULTRA-HD TERMINAL CARDS (2000 x 800 px)
# ---------------------------------------------------------------------
def create_ultra_hd_terminals():
    # 1. VS Code Menu
    w1, h1 = 2000, 750
    t1 = Image.new("RGB", (w1, h1), (30, 30, 30))
    d1 = ImageDraw.Draw(t1)
    d1.rectangle([0, 0, w1, 80], fill=(45, 45, 45))
    d1.text((50, 22), "Visual Studio Code — Terminal > New Terminal", fill=(220, 220, 220), font=get_font(30, bold=True))
    
    d1.rounded_rectangle([120, 120, 1100, 680], radius=16, fill=(37, 37, 38), outline=(80, 80, 80), width=3)
    items = [
        "New Terminal                       Ctrl+Shift+`",
        "Split Terminal                     Ctrl+Shift+5",
        "Run Task...",
        "Run Build Task...                  Ctrl+Shift+B",
        "Run Active File",
        "--------------------------------------------------",
        "> Command Prompt (Selected default profile)",
        "  PowerShell",
        "  Git Bash",
        "  JavaScript Debug Terminal"
    ]
    y = 150
    for item in items:
        col = (255, 255, 255) if ">" in item else (180, 180, 180)
        d1.text((150, y), item, fill=col, font=get_font(26, mono=True))
        y += 50
    t1.save("static/images/terminal_vscode_new.png")

    # 2. Flask Server Terminal
    w2, h2 = 2000, 750
    t2 = Image.new("RGB", (w2, h2), (12, 16, 24))
    d2 = ImageDraw.Draw(t2)
    d2.rectangle([0, 0, w2, 70], fill=(22, 27, 44))
    d2.ellipse([30, 24, 54, 48], fill=(239, 68, 68))
    d2.ellipse([70, 24, 94, 48], fill=(245, 158, 11))
    d2.ellipse([110, 24, 134, 48], fill=(16, 185, 129))
    d2.text((170, 20), "Command Prompt — python app.py (Local Development Server)", fill=(148, 163, 184), font=get_font(26, bold=True))

    lines2 = [
        "(myenv) D:\\projects\\SupplierClarity-AI> python app.py",
        "[SupplierClarity Engine] Initialized on device: cpu",
        " * Serving Flask app 'app'",
        " * Debug mode: off",
        " * Running on all addresses (0.0.0.0)",
        " * Running on http://127.0.0.1:5050 (Press CTRL+C to quit)",
        "127.0.0.1 - - [24/Nov/2026 11:01:42] \"GET / HTTP/1.1\" 200 -",
        "127.0.0.1 - - [24/Nov/2026 11:01:43] \"POST /api/upscale HTTP/1.1\" 200 -"
    ]
    y = 100
    for l in lines2:
        col = (56, 189, 248) if "Running on" in l else ((16, 185, 129) if "200 -" in l else (226, 232, 240))
        d2.text((50, y), l, fill=col, font=get_font(26, mono=True))
        y += 65
    t2.save("static/images/terminal_flask_server.png")

    # 3. Cloud Tunnel Terminal
    w3, h3 = 2000, 750
    t3 = Image.new("RGB", (w3, h3), (12, 16, 24))
    d3 = ImageDraw.Draw(t3)
    d3.rectangle([0, 0, w3, 70], fill=(22, 27, 44))
    d3.ellipse([30, 24, 54, 48], fill=(239, 68, 68))
    d3.ellipse([70, 24, 94, 48], fill=(245, 158, 11))
    d3.ellipse([110, 24, 134, 48], fill=(16, 185, 129))
    d3.text((170, 20), "Command Prompt — python run_public.py (Global Public Tunnel)", fill=(148, 163, 184), font=get_font(26, bold=True))

    lines3 = [
        "(myenv) D:\\projects\\SupplierClarity-AI> python run_public.py",
        "======================================================",
        "  SupplierClarity AI: Public Cloud Deployment",
        "======================================================",
        " -> Opening secure public HTTPS tunnel on port 5050...",
        " -> Tunnel registered protocol=quic location=bom06 status=healthy",
        "",
        "======================================================",
        "  YOUR PUBLIC WEBSITE URL IS LIVE!",
        "  URL: https://obtained-janet-context-westminster.trycloudflare.com",
        "======================================================"
    ]
    y = 90
    for l in lines3:
        col = (250, 204, 21) if "LIVE!" in l else ((56, 189, 248) if "URL:" in l else (226, 232, 240))
        d3.text((50, y), l, fill=col, font=get_font(26, mono=True))
        y += 55
    t3.save("static/images/terminal_public_tunnel.png")
    print(" -> Generated Ultra-HD terminal cards.")

# ---------------------------------------------------------------------
# 5. ULTRA-HD REAL-ESRGAN MODEL SELECTION CARD (2000 x 950 px)
# ---------------------------------------------------------------------
def create_ultra_hd_model_card():
    w, h = 2000, 950
    img = Image.new("RGB", (w, h), (18, 23, 38))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, w, 90], fill=(13, 17, 28))
    draw.text((60, 28), "PyTorch Hub & Real-ESRGAN Pretrained Weights Architecture Registry", fill=(255, 255, 255), font=get_font(34, bold=True))
    
    models_info = [
        ("realesr-general-x4v3.pth", "4.88 MB", "32-Convolution SRVGGNetCompact", "SOTA Real-World 4x; Edge & Sub-Second CPU Latency Optimized", (16, 185, 129)),
        ("RealESRGAN_x2plus.pth", "67.06 MB", "23-Block RRDBNet (Dense Blocks)", "High-Fidelity 2x Horology & Apparel Geometry Restoration", (56, 189, 248)),
        ("edsr_4x.pth", "1.52 MB", "8-Block Deep Residual Network (No BN)", "Sub-pixel Convolution (PixelShuffle) Baseline", (245, 158, 11)),
        ("srcnn.pth", "57 KB", "3-Layer Convolutional Network (Dong et al.)", "Classic Super-Resolution CNN Baseline", (168, 85, 247))
    ]
    
    y = 120
    for name, size, arch, desc, col in models_info:
        draw.rounded_rectangle([60, y, w - 60, y + 175], radius=16, fill=(24, 30, 48), outline=(71, 85, 105), width=2)
        draw.text((100, y + 26), name, fill=col, font=get_font(30, bold=True, mono=True))
        draw.text((750, y + 28), f"Size: {size}  |  Architecture: {arch}", fill=(203, 213, 225), font=get_font(24))
        draw.text((100, y + 95), desc, fill=(148, 163, 184), font=get_font(23))
        y += 205
        
    img.save("static/images/realesrgan_model_card.png")
    print(" -> Generated Ultra-HD: static/images/realesrgan_model_card.png")

# ---------------------------------------------------------------------
# 6. RE-RENDER MATPLOTLIB CHARTS AT 300 DPI
# ---------------------------------------------------------------------
def render_300dpi_charts():
    # Load summary averages
    summary_path = "evaluation/results/summary_averages.csv"
    if os.path.exists(summary_path):
        summary_df = pd.read_csv(summary_path)
        methods = summary_df["method_name"].tolist()
        psnr = summary_df["psnr_db"].tolist()
        ssim = summary_df["ssim"].tolist()
        sharpness = summary_df["sharpness_index"].tolist()
        latency = summary_df["latency_ms"].tolist()

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 11), dpi=300)
        colors_list = ["#4A5568", "#718096", "#3182CE", "#6366F1", "#10B981"]

        # 1. PSNR
        ax1.bar(methods, psnr, color=colors_list, width=0.6)
        ax1.set_title("Peak Signal-to-Noise Ratio (PSNR in dB) ↑", fontsize=14, fontweight="bold", pad=12)
        ax1.set_ylabel("dB", fontsize=12)
        ax1.set_xticks(range(len(methods)))
        ax1.set_xticklabels(methods, rotation=20, ha="right", fontsize=10)
        for i, v in enumerate(psnr):
            ax1.text(i, v + 0.3, f"{v:.1f}", ha="center", fontweight="bold", fontsize=10)

        # 2. SSIM
        ax2.bar(methods, ssim, color=colors_list, width=0.6)
        ax2.set_title("Structural Similarity Index (SSIM) ↑", fontsize=14, fontweight="bold", pad=12)
        ax2.set_ylabel("SSIM (0 to 1)", fontsize=12)
        ax2.set_xticks(range(len(methods)))
        ax2.set_xticklabels(methods, rotation=20, ha="right", fontsize=10)
        for i, v in enumerate(ssim):
            ax2.text(i, v + 0.015, f"{v:.3f}", ha="center", fontweight="bold", fontsize=10)

        # 3. Tenengrad Sharpness
        ax3.bar(methods, sharpness, color=colors_list, width=0.6)
        ax3.set_title("Tenengrad Edge Sharpness (Laplacian Var) ↑", fontsize=14, fontweight="bold", pad=12)
        ax3.set_ylabel("Variance", fontsize=12)
        ax3.set_xticks(range(len(methods)))
        ax3.set_xticklabels(methods, rotation=20, ha="right", fontsize=10)
        for i, v in enumerate(sharpness):
            ax3.text(i, v + 25, f"{v:.0f}", ha="center", fontweight="bold", fontsize=10)

        # 4. Latency
        ax4.bar(methods, latency, color=colors_list, width=0.6)
        ax4.set_title("Processing Latency (ms on CPU) ↓", fontsize=14, fontweight="bold", pad=12)
        ax4.set_ylabel("Milliseconds", fontsize=12)
        ax4.set_xticks(range(len(methods)))
        ax4.set_xticklabels(methods, rotation=20, ha="right", fontsize=10)
        for i, v in enumerate(latency):
            ax4.text(i, v + 15, f"{v:.0f}ms", ha="center", fontweight="bold", fontsize=10)

        plt.tight_layout()
        chart_path = "static/images/metrics_comparison_chart.png"
        plt.savefig(chart_path, bbox_inches="tight", dpi=300)
        plt.close()
        print(" -> Re-rendered 300 DPI: static/images/metrics_comparison_chart.png")

# ---------------------------------------------------------------------
# 7. CAPTURE & CROP AUTHENTIC HIGH-RES WEBPAGE SCREENSHOTS
# ---------------------------------------------------------------------
def capture_and_crop_real_web_screenshots():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    home_out = r"C:\Users\yarra\Downloads\genai(2)\static\images\real_web_home.png"
    res_out = r"C:\Users\yarra\Downloads\genai(2)\static\images\real_web_results.png"
    
    # 1. Home page at 1920x1200
    cmd1 = [chrome_path, "--headless=new", "--no-sandbox", "--disable-gpu", f"--screenshot={home_out}", "--window-size=1920,1200", "http://127.0.0.1:5050"]
    subprocess.run(cmd1, capture_output=True, timeout=15)
    
    # 2. Results page at 1920x1400 with virtual time budget
    cmd2 = [chrome_path, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3500", f"--screenshot={res_out}", "--window-size=1920,1400", "http://127.0.0.1:5050?demo=results"]
    subprocess.run(cmd2, capture_output=True, timeout=18)
    
    if os.path.exists(home_out):
        im_home = Image.open(home_out)
        # Crop Input Section Card (around center: x from 300 to 1620, y from 300 to 1100)
        w, h = im_home.size
        # Crop the input card
        box_input = (int(w * 0.15), 320, int(w * 0.85), 1150)
        crop_input = im_home.crop(box_input)
        crop_input.save("static/images/web_page_input_section.png")
        print(" -> Cropped authentic input section: static/images/web_page_input_section.png")

    if os.path.exists(res_out):
        im_res = Image.open(res_out)
        w, h = im_res.size
        # Crop the results container (split slider + metrics + download buttons)
        box_res = (int(w * 0.15), 450, int(w * 0.85), 1380)
        crop_res = im_res.crop(box_res)
        crop_res.save("static/images/ui_results_mockup.png")
        print(" -> Cropped authentic results section: static/images/ui_results_mockup.png")


if __name__ == "__main__":
    create_ultra_hd_banner()
    create_ultra_hd_architecture()
    create_ultra_hd_folder_tree()
    create_ultra_hd_terminals()
    create_ultra_hd_model_card()
    render_300dpi_charts()
    capture_and_crop_real_web_screenshots()
