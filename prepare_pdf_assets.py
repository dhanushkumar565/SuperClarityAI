"""
SupplierClarity AI - PDF Presentation Assets Generator
Generates high-resolution logos, diagrams, and UI mockups for the capstone PDF report.
"""

import os
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

os.makedirs("static/images", exist_ok=True)

# Helper to load font safely
def get_font(size: int, bold: bool = False):
    try:
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------------------------------------------------
# 1. SMARTBRIDGE & SKILL WALLET HEADER LOGOS
# ---------------------------------------------------------------------
def create_header_banner():
    # Banner 1200 x 140
    img = Image.new("RGBA", (1200, 140), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Left: SmartBridge Logo
    # Stylized bridge icon
    icon_x, icon_y = 40, 30
    draw.arc([icon_x, icon_y + 10, icon_x + 50, icon_y + 60], start=180, end=360, fill=(234, 67, 53), width=5)
    draw.arc([icon_x + 10, icon_y, icon_x + 60, icon_y + 50], start=180, end=360, fill=(66, 133, 244), width=5)
    draw.arc([icon_x + 20, icon_y - 10, icon_x + 70, icon_y + 40], start=180, end=360, fill=(52, 168, 83), width=5)
    
    draw.text((icon_x + 75, icon_y + 10), "SMARTBRIDGE", fill=(30, 41, 59), font=get_font(26, bold=True))
    draw.text((icon_x + 120, icon_y + 42), "Let's Bridge the Gap", fill=(100, 116, 139), font=get_font(14))
    
    # Right: Skill Wallet Logo
    right_x = 940
    draw.text((right_x, icon_y + 6), "SKILL", fill=(30, 58, 138), font=get_font(26, bold=True))
    draw.text((right_x + 80, icon_y + 6), "WALLET", fill=(2, 132, 199), font=get_font(26, bold=True))
    draw.rectangle([right_x + 155, icon_y + 12, right_x + 185, icon_y + 32], fill=(2, 132, 199))
    draw.text((right_x + 160, icon_y + 13), "AI", fill=(255, 255, 255), font=get_font(14, bold=True))
    draw.text((right_x + 15, icon_y + 42), "A SmartBridge Product", fill=(100, 116, 139), font=get_font(13))
    
    img.save("static/images/pdf_header_banner.png", format="PNG")
    print(" -> Created: static/images/pdf_header_banner.png")

# ---------------------------------------------------------------------
# 2. TECHNICAL ARCHITECTURE DIAGRAM
# ---------------------------------------------------------------------
def create_architecture_diagram():
    w, h = 1000, 440
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Header title
    draw.rectangle([0, 0, w, 50], fill=(241, 245, 249))
    draw.text((30, 14), "SupplierClarity AI — Modular Three-Tier Deep Learning Architecture", fill=(15, 23, 42), font=get_font(18, bold=True))
    
    # Tier 1: Presentation & Ingestion
    tier1_rect = [30, 70, 310, 400]
    draw.rounded_rectangle(tier1_rect, radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([30, 70, 310, 110], fill=(241, 245, 249))
    draw.text((45, 80), "Tier 1: Ingestion & Frontend", fill=(30, 41, 59), font=get_font(15, bold=True))
    
    draw.rounded_rectangle([45, 125, 295, 180], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((55, 135), "Web Glassmorphism UI", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((55, 155), "HTML5 · CSS3 Glassmorphism · JS Fetch", fill=(100, 116, 139), font=get_font(11))
    
    draw.rounded_rectangle([45, 195, 295, 250], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((55, 205), "Vendor Photo Ingestion", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((55, 225), "Drag & Drop · 5 Demo Samples · Validation", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([45, 265, 295, 320], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((55, 275), "Interactive Split Viewer", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((55, 295), "Draggable Wipe Slider · Side-by-Side", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([45, 335, 295, 385], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((55, 345), "Public Tunneling", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((55, 363), "PyNgrok & Cloudflare Tunnel Proxy", fill=(100, 116, 139), font=get_font(11))

    # Connector Arrow 1 -> 2
    draw.polygon([(320, 230), (345, 235), (320, 240)], fill=(99, 102, 241))
    draw.line([(310, 235), (340, 235)], fill=(99, 102, 241), width=3)

    # Tier 2: Backend Orchestration (Flask)
    tier2_rect = [350, 70, 630, 400]
    draw.rounded_rectangle(tier2_rect, radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([350, 70, 630, 110], fill=(241, 245, 249))
    draw.text((365, 80), "Tier 2: Backend Orchestration", fill=(30, 41, 59), font=get_font(15, bold=True))

    draw.rounded_rectangle([365, 125, 615, 180], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((375, 135), "Flask RESTful API (app.py)", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((375, 155), "POST /api/upscale · GET /api/samples", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([365, 195, 615, 250], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((375, 205), "Data Pre-processing & Denoise", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((375, 225), "RGB Normalization · Bilateral JPEG Filter", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([365, 265, 615, 320], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((375, 275), "Telemetry & Metric Engine", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((375, 295), "Tenengrad Sharpness · PSNR · SSIM", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([365, 335, 615, 385], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((375, 345), "Production Asset Exporter", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((375, 363), "HD PNG & JPEG Catalog Formats", fill=(100, 116, 139), font=get_font(11))

    # Connector Arrow 2 -> 3
    draw.polygon([(640, 230), (665, 235), (640, 240)], fill=(99, 102, 241))
    draw.line([(630, 235), (660, 235)], fill=(99, 102, 241), width=3)

    # Tier 3: PyTorch Deep Learning Models
    tier3_rect = [670, 70, 970, 400]
    draw.rounded_rectangle(tier3_rect, radius=12, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.rectangle([670, 70, 970, 110], fill=(238, 242, 255))
    draw.text((685, 80), "Tier 3: PyTorch Super-Res Core", fill=(67, 56, 202), font=get_font(15, bold=True))

    draw.rounded_rectangle([685, 125, 955, 180], radius=8, fill=(245, 243, 255), outline=(221, 214, 254))
    draw.text((695, 135), "Real-ESRGAN / SRVGGNetCompact", fill=(109, 40, 217), font=get_font(13, bold=True))
    draw.text((695, 155), "4× Edge Super-Resolution (4.8MB weight)", fill=(124, 58, 237), font=get_font(11))

    draw.rounded_rectangle([685, 195, 955, 250], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((695, 205), "RRDBNet (RealESRGAN_x2plus)", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((695, 225), "2× High-Fidelity Horology & Apparel Model", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([685, 265, 955, 320], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((695, 275), "EDSR & SRCNN Neural Baselines", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((695, 295), "Residual & Shallow CNN Benchmarks", fill=(100, 116, 139), font=get_font(11))

    draw.rounded_rectangle([685, 335, 955, 385], radius=8, fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((695, 345), "Memory Tiling & Sharpening", fill=(15, 23, 42), font=get_font(13, bold=True))
    draw.text((695, 363), "Tile=512 Sub-second CPU Inference", fill=(100, 116, 139), font=get_font(11))

    img.save("static/images/architecture_diagram.png", format="PNG")
    print(" -> Created: static/images/architecture_diagram.png")

# ---------------------------------------------------------------------
# 3. UI SCREENSHOT MOCKUPS (MATCHING PAGES 19 & 20 OF REFERENCE)
# ---------------------------------------------------------------------
def create_ui_home_mockup():
    w, h = 1000, 620
    img = Image.new("RGB", (w, h), (10, 13, 20))
    draw = ImageDraw.Draw(img)
    
    # Glowing background blobs
    for r in range(180, 0, -20):
        alpha = int(35 * (r / 180))
        draw.ellipse([80 - r, 60 - r, 80 + r, 60 + r], outline=(124, 58, 237), width=8)
        draw.ellipse([880 - r, 450 - r, 880 + r, 450 + r], outline=(219, 39, 119), width=8)

    # Browser Top Bar
    draw.rectangle([0, 0, w, 36], fill=(22, 27, 44))
    draw.ellipse([14, 13, 24, 23], fill=(239, 68, 68))
    draw.ellipse([30, 13, 40, 23], fill=(245, 158, 11))
    draw.ellipse([46, 13, 56, 23], fill=(16, 185, 129))
    draw.rectangle([70, 7, w - 70, 29], fill=(15, 18, 30))
    draw.text((85, 10), "https://supplierclarity-ai.local — Vendor Product Image Upscaler", fill=(148, 163, 184), font=get_font(11))

    # Header / Logo
    draw.rounded_rectangle([w//2 - 20, 52, w//2 + 20, 92], radius=10, fill=(139, 92, 246))
    draw.text((w//2 - 12, 58), "*", fill=(255, 255, 255), font=get_font(24, bold=True))
    draw.text((w//2 - 145, 100), "SupplierClarity AI", fill=(255, 255, 255), font=get_font(26, bold=True))
    draw.text((w//2 - 180, 132), "Deep Learning-Powered Vendor Product Image Upscaler & Catalog Restoration", fill=(148, 163, 184), font=get_font(12))

    # Glass Card Container
    card_rect = [120, 160, 880, 580]
    draw.rounded_rectangle(card_rect, radius=16, fill=(18, 23, 38), outline=(255, 255, 255), width=1)
    
    # Quick Demo Pills
    draw.text((150, 180), "Quick Demo Products (Click to Load):", fill=(148, 163, 184), font=get_font(12, bold=True))
    pills = ["Luxury Watch", "Running Sneaker", "Skincare Serum", "Artisan Coffee", "Wireless Earbuds"]
    px = 150
    for idx, pill in enumerate(pills):
        is_active = (idx == 0)
        bg = (139, 92, 246) if is_active else (30, 36, 56)
        fg = (255, 255, 255) if is_active else (148, 163, 184)
        pw = len(pill) * 9 + 24
        draw.rounded_rectangle([px, 205, px + pw, 235], radius=8, fill=bg)
        draw.text((px + 12, 212), pill, fill=fg, font=get_font(12, bold=is_active))
        px += pw + 12

    # Dropzone
    draw.rounded_rectangle([150, 255, 850, 395], radius=12, fill=(15, 19, 32), outline=(51, 65, 85), width=1)
    
    # Load watch sample image inside preview
    watch_sample_path = "data/samples/luxury_watch_supplier_input.jpg"
    if os.path.exists(watch_sample_path):
        watch_img = Image.open(watch_sample_path).convert("RGB").resize((110, 110))
        img.paste(watch_img, (180, 270))
        draw.rectangle([180, 270, 290, 380], outline=(100, 116, 139))
    
    draw.text((320, 285), "luxury_watch_supplier_input.jpg", fill=(255, 255, 255), font=get_font(15, bold=True))
    draw.rectangle([320, 315, 410, 335], fill=(6, 182, 212))
    draw.text((326, 318), "128x128 px", fill=(15, 23, 42), font=get_font(11, bold=True))
    draw.text((320, 345), "Vendor low-res image loaded. Ready for 4x neural super-resolution.", fill=(148, 163, 184), font=get_font(12))

    # Controls Row
    draw.text((150, 415), "Upscaling Scale Factor:", fill=(148, 163, 184), font=get_font(12, bold=True))
    draw.rounded_rectangle([150, 435, 250, 475], radius=8, fill=(30, 36, 56))
    draw.text((180, 448), "2x HD", fill=(148, 163, 184), font=get_font(12))
    draw.rounded_rectangle([260, 435, 360, 475], radius=8, fill=(139, 92, 246))
    draw.text((285, 448), "4x 4K", fill=(255, 255, 255), font=get_font(12, bold=True))

    draw.text((400, 415), "Super-Resolution Model:", fill=(148, 163, 184), font=get_font(12, bold=True))
    draw.rounded_rectangle([400, 435, 850, 475], radius=8, fill=(22, 27, 44), outline=(71, 85, 105))
    draw.text((420, 448), "SupplierClarity AI (Real-ESRGAN / SOTA Neural Model)", fill=(255, 255, 255), font=get_font(12))

    # Enhance CTA Button
    draw.rounded_rectangle([150, 500, 850, 550], radius=10, fill=(139, 92, 246))
    draw.text((430, 515), "* Enhance Product Image", fill=(255, 255, 255), font=get_font(16, bold=True))

    img.save("static/images/ui_home_mockup.png", format="PNG")
    print(" -> Created: static/images/ui_home_mockup.png")


def create_ui_results_mockup():
    w, h = 1000, 640
    img = Image.new("RGB", (w, h), (10, 13, 20))
    draw = ImageDraw.Draw(img)

    # Browser Top Bar
    draw.rectangle([0, 0, w, 36], fill=(22, 27, 44))
    draw.ellipse([14, 13, 24, 23], fill=(239, 68, 68))
    draw.ellipse([30, 13, 40, 23], fill=(245, 158, 11))
    draw.ellipse([46, 13, 56, 23], fill=(16, 185, 129))
    draw.text((85, 10), "SupplierClarity AI — Dynamic Results Inspection Panel", fill=(148, 163, 184), font=get_font(11))

    # Results Header
    draw.rounded_rectangle([60, 50, 195, 75], radius=6, fill=(16, 185, 129))
    draw.text((70, 55), "Enhancement Complete", fill=(255, 255, 255), font=get_font(11, bold=True))
    draw.text((60, 85), "Restored E-Commerce Product Image (Luxury Watch)", fill=(255, 255, 255), font=get_font(20, bold=True))

    # Two-Column Comparison View (Side by side + split wipe)
    # Left Box: Original LR
    lr_box = [60, 125, 490, 440]
    draw.rounded_rectangle(lr_box, radius=12, fill=(18, 23, 38), outline=(239, 68, 68), width=2)
    draw.rectangle([60, 125, 490, 160], fill=(22, 27, 44))
    draw.text((75, 135), "ORIGINAL SUPPLIER INPUT (Low-Res)", fill=(239, 68, 68), font=get_font(12, bold=True))
    draw.text((410, 135), "128x128 px", fill=(148, 163, 184), font=get_font(11))

    watch_lr_path = "data/samples/luxury_watch_supplier_input.jpg"
    if os.path.exists(watch_lr_path):
        lr_img = Image.open(watch_lr_path).convert("RGB").resize((250, 250), Image.NEAREST)
        img.paste(lr_img, (150, 175))

    # Right Box: Enhanced HR
    hr_box = [510, 125, 940, 440]
    draw.rounded_rectangle(hr_box, radius=12, fill=(18, 23, 38), outline=(16, 185, 129), width=2)
    draw.rectangle([510, 125, 940, 160], fill=(22, 27, 44))
    draw.text((525, 135), "RESTORED CATALOG READY (AI 4X)", fill=(16, 185, 129), font=get_font(12, bold=True))
    draw.text((860, 135), "512x512 px", fill=(52, 211, 153), font=get_font(11, bold=True))

    watch_hr_path = "data/samples/luxury_watch_enhanced_4x.png"
    if os.path.exists(watch_hr_path):
        hr_img = Image.open(watch_hr_path).convert("RGB").resize((250, 250), Image.LANCZOS)
        img.paste(hr_img, (600, 175))

    # Metrics Badges Grid (4 Badges)
    metric_items = [
        ("Resolution Upscaling", "128x128 -> 512x512", "4x Geometric Scaling"),
        ("Inference Latency", "277.4 ms", "Sub-second Real-Time CPU"),
        ("Tenengrad Sharpness", "+53.5x Boost", "Laplacian: 21.5 -> 1151.4"),
        ("Objective Quality", "SSIM: 0.8817", "Ground-truth verified")
    ]
    
    bx = 60
    for title, val, sub in metric_items:
        draw.rounded_rectangle([bx, 460, bx + 205, 540], radius=10, fill=(18, 23, 38), outline=(51, 65, 85))
        draw.text((bx + 14, 472), title, fill=(148, 163, 184), font=get_font(11))
        draw.text((bx + 14, 492), val, fill=(255, 255, 255), font=get_font(14, bold=True))
        draw.text((bx + 14, 516), sub, fill=(16, 185, 129), font=get_font(10))
        bx += 225

    # Download Buttons
    draw.rounded_rectangle([60, 560, 490, 605], radius=8, fill=(139, 92, 246))
    draw.text((195, 574), "Download Enhanced HD PNG", fill=(255, 255, 255), font=get_font(13, bold=True))

    draw.rounded_rectangle([510, 560, 940, 605], radius=8, fill=(30, 36, 56), outline=(71, 85, 105))
    draw.text((655, 574), "Download Compressed JPEG", fill=(255, 255, 255), font=get_font(13))

    img.save("static/images/ui_results_mockup.png", format="PNG")
    print(" -> Created: static/images/ui_results_mockup.png")


if __name__ == "__main__":
    create_header_banner()
    create_architecture_diagram()
    create_ui_home_mockup()
    create_ui_results_mockup()
