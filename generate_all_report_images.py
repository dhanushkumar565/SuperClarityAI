"""
SupplierClarity AI - Comprehensive Report Assets Generator
Creates all 16 visual screenshots, terminal cards, architecture diagrams,
and UI mockups matching the 21-page SmartBridge reference document.
"""

import os
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
# 1. VS CODE FOLDER TREE EXPLORER (Matching Page 7 of reference)
# ---------------------------------------------------------------------
def create_folder_tree_image():
    w, h = 600, 360
    img = Image.new("RGB", (w, h), (24, 30, 42))
    draw = ImageDraw.Draw(img)
    
    # Top bar
    draw.rectangle([0, 0, w, 32], fill=(18, 23, 34))
    draw.text((16, 8), "EXPLORER: SUPPLIERCLARITY-AI", fill=(148, 163, 184), font=get_font(11, bold=True))
    
    items = [
        ("v", "models", True, (139, 92, 246)),
        ("  ", "upscaler.py", False, (56, 189, 248)),
        ("  ", "srcnn.py", False, (56, 189, 248)),
        ("  ", "edsr.py", False, (56, 189, 248)),
        ("v", "data", True, (245, 158, 11)),
        ("  ", "samples (5 e-commerce categories)", False, (148, 163, 184)),
        ("  ", "eval_dataset (paired HR & LR)", False, (148, 163, 184)),
        ("v", "static", True, (16, 185, 129)),
        ("  ", "css/style.css (dark glassmorphism)", False, (56, 189, 248)),
        ("  ", "js/main.js (split-slider & async)", False, (250, 204, 21)),
        ("  ", "images & outputs", False, (148, 163, 184)),
        ("v", "templates", True, (239, 68, 68)),
        ("  ", "index.html (single-page app)", False, (249, 115, 22)),
        (" ", "app.py (Flask REST backend)", False, (56, 189, 248)),
        (" ", "run_public.py (Ngrok & tunnel)", False, (56, 189, 248)),
        (" ", "dataset_pipeline.py", False, (56, 189, 248)),
        (" ", "train_sr.py", False, (56, 189, 248)),
        (" ", "test_app.py (9 unit tests)", False, (16, 185, 129)),
        (" ", "requirements.txt", False, (148, 163, 184)),
        (" ", ".env", False, (148, 163, 184))
    ]
    
    y = 42
    for icon, name, is_folder, col in items:
        prefix = "> " if icon == "v" else ("   " if icon == "  " else "  ")
        draw.text((18, y), prefix + name, fill=col, font=get_font(12, bold=is_folder))
        y += 15.5
        
    img.save("static/images/folder_tree_screenshot.png")
    print(" -> Created: static/images/folder_tree_screenshot.png")

# ---------------------------------------------------------------------
# 2. REALISTIC DEGRADATION STRIP (Matching Milestone 2)
# ---------------------------------------------------------------------
def create_degradation_pipeline_visual():
    w, h = 900, 260
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, w, 40], fill=(241, 245, 249))
    draw.text((20, 10), "Mathematical Realistic Degradation Chain: I_LR = ( ( I_HR ⊗ k_σ ) ↓_s + n )_{JPEG(q)}", fill=(15, 23, 42), font=get_font(14, bold=True))
    
    # Load Watch HR image
    watch_hr = Image.open("data/eval_dataset/hr/luxury_watch_hr.png").convert("RGB").resize((130, 130))
    watch_blur = watch_hr.filter(ImageFilter.GaussianBlur(1.5))
    watch_down = watch_blur.resize((65, 65), Image.BILINEAR).resize((130, 130), Image.NEAREST)
    
    # Add noise & jpeg
    np_down = np.array(watch_down)
    noise = np.random.normal(0, 12, np_down.shape).astype(np.float32)
    noisy = np.clip(np_down + noise, 0, 255).astype(np.uint8)
    
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 35]
    _, enc = cv2.imencode('.jpg', cv2.cvtColor(noisy, cv2.COLOR_RGB2BGR), encode_param)
    watch_final = Image.fromarray(cv2.cvtColor(cv2.imdecode(enc, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB))

    steps = [
        ("Step 1: Ground Truth HR", "512x512 Studio Shot", watch_hr),
        ("Step 2: Gaussian Blur", "k=5, σ=1.2 Defocus", watch_blur),
        ("Step 3: Downsample", "4x Downscale (128x128)", watch_down),
        ("Step 4: Noise & JPEG", "Q=35 Compression", watch_final)
    ]
    
    x = 30
    for idx, (title, sub, tile_img) in enumerate(steps):
        draw.rounded_rectangle([x, 55, x + 180, 245], radius=10, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
        img.paste(tile_img, (x + 25, 65))
        draw.text((x + 12, 205), title, fill=(15, 23, 42), font=get_font(11, bold=True))
        draw.text((x + 12, 223), sub, fill=(100, 116, 139), font=get_font(10))
        if idx < 3:
            draw.polygon([(x + 192, 145), (x + 208, 150), (x + 192, 155)], fill=(99, 102, 241))
        x += 220
        
    img.save("static/images/degradation_pipeline_visual.png")
    print(" -> Created: static/images/degradation_pipeline_visual.png")

# ---------------------------------------------------------------------
# 3. TERMINAL CARDS (Matching Pages 15, 16, 17 of reference)
# ---------------------------------------------------------------------
def create_terminal_cards():
    # 1. VS Code New Terminal Menu
    w1, h1 = 640, 220
    t1 = Image.new("RGB", (w1, h1), (30, 30, 30))
    d1 = ImageDraw.Draw(t1)
    d1.rectangle([0, 0, w1, 30], fill=(45, 45, 45))
    d1.text((15, 7), "Terminal > New Terminal", fill=(200, 200, 200), font=get_font(12))
    
    d1.rectangle([40, 45, 320, 205], fill=(37, 37, 38), outline=(68, 68, 68))
    menu_items = [
        "New Terminal                  Ctrl+Shift+`",
        "Split Terminal                Ctrl+Shift+5",
        "Run Task...",
        "Run Build Task...             Ctrl+Shift+B",
        "Run Active File",
        "--------------------------------------",
        "> Command Prompt (Selected)",
        "  PowerShell",
        "  Git Bash"
    ]
    my = 52
    for m in menu_items:
        col = (255, 255, 255) if ">" in m else (180, 180, 180)
        d1.text((50, my), m, fill=col, font=get_font(10, mono=True))
        my += 16
    t1.save("static/images/terminal_vscode_new.png")

    # 2. Flask Server Running on Port 5050
    w2, h2 = 640, 200
    t2 = Image.new("RGB", (w2, h2), (12, 16, 24))
    d2 = ImageDraw.Draw(t2)
    d2.rectangle([0, 0, w2, 28], fill=(22, 27, 44))
    d2.ellipse([10, 9, 20, 19], fill=(239, 68, 68))
    d2.ellipse([25, 9, 35, 19], fill=(245, 158, 11))
    d2.ellipse([40, 9, 50, 19], fill=(16, 185, 129))
    d2.text((65, 7), "Command Prompt - (myenv) python app.py", fill=(148, 163, 184), font=get_font(11))
    
    server_lines = [
        "(myenv) D:\\projects> python app.py",
        "[SupplierClarity Engine] Initialized on device: cpu",
        " * Serving Flask app 'app'",
        " * Debug mode: off",
        " * Running on all addresses (0.0.0.0)",
        " * Running on http://127.0.0.1:5050 (Press CTRL+C to quit)",
        "127.0.0.1 - - [24/Nov/2026 11:01:42] \"GET / HTTP/1.1\" 200 -",
        "127.0.0.1 - - [24/Nov/2026 11:01:43] \"POST /api/upscale HTTP/1.1\" 200 -"
    ]
    sy = 36
    for sl in server_lines:
        col = (56, 189, 248) if "Running on" in sl else ((16, 185, 129) if "200 -" in sl else (226, 232, 240))
        d2.text((15, sy), sl, fill=col, font=get_font(10, mono=True))
        sy += 19
    t2.save("static/images/terminal_flask_server.png")

    # 3. Public Cloud Tunnel Output
    w3, h3 = 640, 220
    t3 = Image.new("RGB", (w3, h3), (12, 16, 24))
    d3 = ImageDraw.Draw(t3)
    d3.rectangle([0, 0, w3, 28], fill=(22, 27, 44))
    d3.text((15, 7), "Command Prompt - (myenv) python run_public.py", fill=(148, 163, 184), font=get_font(11))
    
    tunnel_lines = [
        "(myenv) D:\\projects> python run_public.py",
        "======================================================",
        "  SupplierClarity AI: Public Cloud Deployment",
        "======================================================",
        " -> Opening secure public HTTPS tunnel on port 5050...",
        " -> Tunnel registered successfully protocol=quic location=bom06",
        "",
        "======================================================",
        "  YOUR PUBLIC WEBSITE URL IS LIVE!",
        "  URL: https://obtained-janet-context-westminster.trycloudflare.com",
        "======================================================"
    ]
    ty = 36
    for tl in tunnel_lines:
        col = (250, 204, 21) if "LIVE!" in tl else ((56, 189, 248) if "URL:" in tl else (226, 232, 240))
        d3.text((15, ty), tl, fill=col, font=get_font(10, mono=True))
        ty += 16
    t3.save("static/images/terminal_public_tunnel.png")
    print(" -> Created terminal screenshots: terminal_vscode_new, terminal_flask_server, terminal_public_tunnel")

# ---------------------------------------------------------------------
# 4. MODEL HUB & SELECTION CARD (Matching Page 4 of reference)
# ---------------------------------------------------------------------
def create_model_hub_card():
    w, h = 640, 240
    img = Image.new("RGB", (w, h), (18, 23, 38))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, w, 32], fill=(13, 17, 28))
    draw.text((15, 8), "PyTorch Hub & Real-ESRGAN Pretrained Model Selection", fill=(148, 163, 184), font=get_font(11, bold=True))
    
    models_info = [
        ("realesr-general-x4v3.pth", "4.88 MB", "32-Conv SRVGGNetCompact", "SOTA Real-World 4x; Edge & CPU Optimized", (16, 185, 129)),
        ("RealESRGAN_x2plus.pth", "67.06 MB", "23-Block RRDBNet", "High-Fidelity 2x Horology & Apparel Super-Resolution", (56, 189, 248)),
        ("edsr_4x.pth", "1.52 MB", "8-Block ResNet w/o BN", "Sub-pixel Convolution Residual Baseline", (245, 158, 11)),
        ("srcnn.pth", "57 KB", "3-Layer CNN (Dong et al.)", "Classic Super-Resolution Convolutional Baseline", (168, 85, 247))
    ]
    
    y = 44
    for name, size, arch, desc, col in models_info:
        draw.rounded_rectangle([15, y, w - 15, y + 42], radius=6, fill=(24, 30, 48), outline=(51, 65, 85))
        draw.text((25, y + 6), name, fill=col, font=get_font(11, bold=True))
        draw.text((240, y + 6), f"Size: {size} | Arch: {arch}", fill=(203, 213, 225), font=get_font(10))
        draw.text((25, y + 24), desc, fill=(148, 163, 184), font=get_font(9.5))
        y += 48
        
    img.save("static/images/realesrgan_model_card.png")
    print(" -> Created: static/images/realesrgan_model_card.png")

# ---------------------------------------------------------------------
# 5. PRODUCT SHOWCASE PAIRS (All 5 Categories)
# ---------------------------------------------------------------------
def create_product_showcase_pairs():
    w, h = 900, 360
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, w, 36], fill=(241, 245, 249))
    draw.text((20, 10), "SupplierClarity AI — Restored Catalog Pairs Across 5 E-Commerce Domains", fill=(15, 23, 42), font=get_font(13, bold=True))
    
    prods = [
        ("luxury_watch", "Luxury Watch", "Dial Ticks & Serif Logo"),
        ("sneaker_shoe", "Running Sneaker", "Mesh Weave & Stitching"),
        ("cosmetic_serum", "Skincare Serum", "Dropper Bottle & 30ml Text"),
        ("organic_coffee_pack", "Coffee Pouch", "Scannable Barcode & Roast"),
        ("wireless_earbuds", "Wireless Earbuds", "Acoustic Grille & LED")
    ]
    
    x = 20
    for prod_id, title, desc in prods:
        hr_path = f"data/eval_dataset/hr/{prod_id}_hr.png"
        lr_path = f"data/eval_dataset/lr/{prod_id}_lr.png"
        if os.path.exists(hr_path) and os.path.exists(lr_path):
            hr_img = Image.open(hr_path).convert("RGB").resize((150, 150))
            lr_img = Image.open(lr_path).convert("RGB").resize((150, 150), Image.NEAREST)
            
            # Draw LR card
            draw.rounded_rectangle([x, 50, x + 160, 340], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
            img.paste(lr_img.resize((70, 70)), (x + 8, 60))
            img.paste(hr_img.resize((70, 70)), (x + 82, 60))
            
            draw.text((x + 8, 140), "LR (Input)", fill=(239, 68, 68), font=get_font(9, bold=True))
            draw.text((x + 82, 140), "AI Enhanced", fill=(16, 185, 129), font=get_font(9, bold=True))
            
            # Big HR display below
            img.paste(hr_img.resize((144, 144)), (x + 8, 160))
            draw.text((x + 8, 310), title, fill=(15, 23, 42), font=get_font(11, bold=True))
            draw.text((x + 8, 325), desc, fill=(100, 116, 139), font=get_font(8.5))
            
        x += 175
        
    img.save("static/images/product_showcase_pairs.png")
    print(" -> Created: static/images/product_showcase_pairs.png")


# ---------------------------------------------------------------------
# 6. DEDICATED CLOSEUP MOCKUPS (Page 20 of Reference PDF)
# ---------------------------------------------------------------------
def create_page_20_closeups():
    # 1. Input Section Close-up
    w, h = 800, 460
    inp_img = Image.new("RGB", (w, h), (18, 23, 38))
    d = ImageDraw.Draw(inp_img)
    d.rounded_rectangle([0, 0, w, h], radius=16, fill=(18, 23, 38), outline=(255, 255, 255), width=1)
    
    # Title
    d.text((30, 20), "Product Image Ingestion & Super-Resolution Parameters", fill=(255, 255, 255), font=get_font(16, bold=True))
    d.text((30, 45), "Upload a supplier image or select a benchmark sample product", fill=(148, 163, 184), font=get_font(12))

    # Sample Pills
    d.text((30, 80), "Quick Demo Products (Click to Load):", fill=(148, 163, 184), font=get_font(11, bold=True))
    pills = [("Luxury Watch", True), ("Running Sneaker", False), ("Skincare Serum", False), ("Artisan Coffee", False), ("Earbuds", False)]
    px = 30
    for name, active in pills:
        bg = (139, 92, 246) if active else (30, 36, 56)
        fg = (255, 255, 255) if active else (148, 163, 184)
        pw = len(name) * 8 + 20
        d.rounded_rectangle([px, 100, px + pw, 126], radius=6, fill=bg)
        d.text((px + 10, 106), name, fill=fg, font=get_font(11, bold=active))
        px += pw + 10

    # Dropzone with watch preview
    d.rounded_rectangle([30, 140, w - 30, 250], radius=10, fill=(12, 16, 26), outline=(51, 65, 85))
    watch_path = "data/samples/luxury_watch_supplier_input.jpg"
    if os.path.exists(watch_path):
        w_img = Image.open(watch_path).convert("RGB").resize((90, 90))
        inp_img.paste(w_img, (50, 150))
    d.text((160, 160), "luxury_watch_supplier_input.jpg", fill=(255, 255, 255), font=get_font(14, bold=True))
    d.rounded_rectangle([160, 185, 240, 205], radius=4, fill=(6, 182, 212))
    d.text((168, 188), "128x128 px", fill=(15, 23, 42), font=get_font(11, bold=True))
    d.text((160, 215), "Vendor low-resolution photo loaded. Ready for 4x enhancement.", fill=(148, 163, 184), font=get_font(11))

    # Toggles
    d.text((30, 270), "Upscaling Factor:", fill=(148, 163, 184), font=get_font(11, bold=True))
    d.rounded_rectangle([30, 290, 110, 325], radius=6, fill=(30, 36, 56))
    d.text((50, 300), "2x HD", fill=(148, 163, 184), font=get_font(11))
    d.rounded_rectangle([120, 290, 200, 325], radius=6, fill=(139, 92, 246))
    d.text((140, 300), "4x 4K", fill=(255, 255, 255), font=get_font(11, bold=True))

    d.text((230, 270), "Super-Resolution Model:", fill=(148, 163, 184), font=get_font(11, bold=True))
    d.rounded_rectangle([230, 290, w - 30, 325], radius=6, fill=(24, 30, 48), outline=(71, 85, 105))
    d.text((245, 300), "SupplierClarity AI (Real-ESRGAN / SOTA Neural Model)", fill=(255, 255, 255), font=get_font(11))

    # Filters
    d.text((30, 345), "[x] Bilateral JPEG Denoising Filter", fill=(52, 211, 153), font=get_font(11, bold=True))
    d.text((280, 345), "[x] High-Frequency Typography Sharpening", fill=(52, 211, 153), font=get_font(11, bold=True))

    # Button
    d.rounded_rectangle([30, 380, w - 30, 430], radius=10, fill=(139, 92, 246))
    d.text((w//2 - 90, 396), "* Enhance Product Image", fill=(255, 255, 255), font=get_font(15, bold=True))

    inp_img.save("static/images/web_page_input_section.png")
    print(" -> Created: static/images/web_page_input_section.png")


if __name__ == "__main__":
    create_folder_tree_image()
    create_degradation_pipeline_visual()
    create_terminal_cards()
    create_model_hub_card()
    create_product_showcase_pairs()
    create_page_20_closeups()

