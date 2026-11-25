"""
SupplierClarity AI - Dataset Preparation & Degradation Pipeline
Author: SupplierClarity AI Development Team
Domain: E-Commerce & Retail Product Image Super-Resolution
"""

import os
import io
import math
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)


# =====================================================================
# 1. REALISTIC DEGRADATION OPERATORS
# =====================================================================

def apply_gaussian_blur(image_np: np.ndarray, kernel_size: int = 5, sigma: float = 1.2) -> np.ndarray:
    """Simulate lens defocus or vendor camera shake."""
    if kernel_size % 2 == 0:
        kernel_size += 1
    return cv2.GaussianBlur(image_np, (kernel_size, kernel_size), sigma)


def apply_downsampling(image_np: np.ndarray, scale: int = 4, interpolation: int = cv2.INTER_CUBIC) -> np.ndarray:
    """Downsample image by given scale factor."""
    h, w = image_np.shape[:2]
    new_h, new_w = max(1, h // scale), max(1, w // scale)
    return cv2.resize(image_np, (new_w, new_h), interpolation=interpolation)


def apply_sensor_noise(image_np: np.ndarray, noise_sigma: float = 8.0) -> np.ndarray:
    """Simulate low-light smartphone or sensor CMOS noise."""
    noise = np.random.normal(0, noise_sigma, image_np.shape).astype(np.float32)
    noisy = np.clip(image_np.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return noisy


def apply_jpeg_compression(image_np: np.ndarray, quality: int = 35) -> np.ndarray:
    """Simulate lossy JPEG compression from supplier upload portals/ERP/chat apps."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), max(10, min(100, quality))]
    result, encimg = cv2.imencode('.jpg', image_np, encode_param)
    if result:
        return cv2.imdecode(encimg, cv2.IMREAD_COLOR)
    return image_np


def apply_realistic_vendor_degradation(
    hr_bgr: np.ndarray,
    scale: int = 4,
    blur: bool = True,
    noise: bool = True,
    jpeg: bool = True,
    jpeg_quality: int = 40
) -> np.ndarray:
    """
    Composite degradation pipeline modeling real-world vendor photo degradation:
    HR -> Gaussian Blur -> Downsampling -> Sensor Noise -> JPEG Compression -> LR
    """
    img = hr_bgr.copy()
    
    # 1. Blur
    if blur:
        k_size = random.choice([3, 5])
        sigma = random.uniform(0.6, 1.5)
        img = apply_gaussian_blur(img, kernel_size=k_size, sigma=sigma)
        
    # 2. Downsample
    interp = random.choice([cv2.INTER_CUBIC, cv2.INTER_LINEAR, cv2.INTER_AREA])
    img = apply_downsampling(img, scale=scale, interpolation=interp)
    
    # 3. Add sensor noise
    if noise:
        noise_level = random.uniform(3.0, 9.0)
        img = apply_sensor_noise(img, noise_sigma=noise_level)
        
    # 4. JPEG compression artifacts
    if jpeg:
        q = jpeg_quality if jpeg_quality else random.randint(30, 55)
        img = apply_jpeg_compression(img, quality=q)
        
    return img


# =====================================================================
# 2. SYNTHETIC HIGH-DETAIL E-COMMERCE PRODUCT GENERATOR
# =====================================================================

def create_high_detail_product_image(product_type: str, size: int = 512) -> Image.Image:
    """
    Generates realistic, studio-quality e-commerce product imagery with high-frequency
    textures, fine typography, edge geometry, and packaging text for benchmarking.
    """
    img = Image.new("RGB", (size, size), (245, 246, 248))
    draw = ImageDraw.Draw(img)
    
    # Soft studio backdrop shadow/gradient
    for y in range(size):
        ratio = y / size
        c = int(248 - ratio * 18)
        draw.line([(0, y), (size, y)], fill=(c, c, c + 3))

    # Fallback default font
    try:
        font_large = ImageFont.truetype("arial.ttf", int(size * 0.055))
        font_med = ImageFont.truetype("arial.ttf", int(size * 0.035))
        font_small = ImageFont.truetype("arial.ttf", int(size * 0.022))
        font_tiny = ImageFont.truetype("arial.ttf", int(size * 0.016))
    except Exception:
        font_large = font_med = font_small = font_tiny = ImageFont.load_default()

    center_x, center_y = size // 2, int(size * 0.48)

    if product_type == "luxury_watch":
        # 1. Luxury Watch with intricate dial, tick marks, roman numerals, and brushed steel
        # Drop shadow
        draw.ellipse([center_x - 170, center_y + 110, center_x + 170, center_y + 170], fill=(210, 212, 218))
        # Watch Case / Bezel
        draw.ellipse([center_x - 160, center_y - 160, center_x + 160, center_y + 160], fill=(45, 52, 65), outline=(190, 195, 205), width=6)
        # Inner Gold Ring
        draw.ellipse([center_x - 148, center_y - 148, center_x + 148, center_y + 148], fill=(22, 26, 35), outline=(212, 175, 55), width=3)
        # Watch Dial Face
        draw.ellipse([center_x - 140, center_y - 140, center_x + 140, center_y + 140], fill=(16, 20, 28))
        
        # 60 Minute tick marks & 12 Hour indices
        for i in range(60):
            angle = i * (2 * math.pi / 60)
            r_outer = 135
            r_inner = 122 if i % 5 == 0 else 129
            w = 3 if i % 5 == 0 else 1
            col = (220, 190, 80) if i % 5 == 0 else (160, 170, 185)
            x1 = center_x + int(r_inner * math.sin(angle))
            y1 = center_y - int(r_inner * math.cos(angle))
            x2 = center_x + int(r_outer * math.sin(angle))
            y2 = center_y - int(r_outer * math.cos(angle))
            draw.line([(x1, y1), (x2, y2)], fill=col, width=w)
            
        # Chronograph Sub-dials
        for sub_x, sub_y in [(center_x - 50, center_y), (center_x + 50, center_y), (center_x, center_y + 55)]:
            draw.ellipse([sub_x - 28, sub_y - 28, sub_x + 28, sub_y + 28], fill=(24, 28, 38), outline=(180, 185, 195), width=1)
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                draw.line([(sub_x + int(20 * math.sin(rad)), sub_y - int(20 * math.cos(rad))),
                           (sub_x + int(26 * math.sin(rad)), sub_y - int(26 * math.cos(rad)))],
                          fill=(180, 185, 195), width=1)

        # Brand Text
        draw.text((center_x - 48, center_y - 80), "CHRONO", fill=(230, 235, 245), font=font_med)
        draw.text((center_x - 40, center_y - 62), "AUTOMATIC", fill=(212, 175, 55), font=font_tiny)
        draw.text((center_x - 30, center_y + 95), "SWISS MADE", fill=(170, 175, 185), font=font_tiny)

        # Hands
        # Hour Hand
        draw.line([(center_x, center_y), (center_x + 45, center_y - 45)], fill=(230, 230, 235), width=5)
        # Minute Hand
        draw.line([(center_x, center_y), (center_x - 15, center_y - 95)], fill=(245, 245, 250), width=3)
        # Second Hand (Red needle)
        draw.line([(center_x - 10, center_y + 20), (center_x + 70, center_y + 40)], fill=(235, 45, 45), width=2)
        draw.ellipse([center_x - 6, center_y - 6, center_x + 6, center_y + 6], fill=(235, 45, 45))

    elif product_type == "sneaker_shoe":
        # 2. Athletic Sneaker with detailed mesh, stitching, sole texture, and logo
        # Shadow
        draw.ellipse([center_x - 180, center_y + 115, center_x + 180, center_y + 165], fill=(208, 210, 218))
        
        # Sole (White/Grey thick running sole)
        sole_points = [
            (center_x - 170, center_y + 80),
            (center_x - 140, center_y + 115),
            (center_x + 150, center_y + 115),
            (center_x + 180, center_y + 70),
            (center_x + 160, center_y + 60),
            (center_x - 10, center_y + 75),
            (center_x - 160, center_y + 65)
        ]
        draw.polygon(sole_points, fill=(240, 242, 245), outline=(190, 195, 205))
        # Sole tread patterns (micro grooves)
        for gx in range(center_x - 130, center_x + 140, 8):
            draw.line([(gx, center_y + 95), (gx + 4, center_y + 110)], fill=(180, 185, 195), width=2)

        # Upper Body (Cobalt Blue + Teal mesh)
        upper_points = [
            (center_x - 160, center_y + 65),
            (center_x - 110, center_y - 30),
            (center_x - 30, center_y - 75),
            (center_x + 40, center_y - 25),
            (center_x + 130, center_y + 20),
            (center_x + 160, center_y + 60),
            (center_x - 10, center_y + 75)
        ]
        draw.polygon(upper_points, fill=(35, 95, 215), outline=(20, 65, 160), width=2)

        # Mesh texture pattern
        for mx in range(center_x - 100, center_x + 120, 7):
            for my in range(center_y - 30, center_y + 55, 7):
                if mx + my < center_x + center_y + 90:
                    draw.point((mx, my), fill=(60, 130, 255))
                    draw.point((mx + 1, my), fill=(20, 70, 180))

        # Dynamic swoosh overlay (Neon Orange/Coral)
        swoosh_pts = [
            (center_x - 70, center_y + 35),
            (center_x - 20, center_y + 15),
            (center_x + 80, center_y - 35),
            (center_x + 110, center_y - 45),
            (center_x + 60, center_y + 10),
            (center_x - 10, center_y + 45)
        ]
        draw.polygon(swoosh_pts, fill=(255, 90, 40), outline=(230, 60, 15), width=2)

        # Stitching lines
        stitch_pts = [(center_x - 150, center_y + 60), (center_x - 100, center_y - 20), (center_x - 25, center_y - 65)]
        for i in range(len(stitch_pts) - 1):
            p1, p2 = stitch_pts[i], stitch_pts[i+1]
            steps = 15
            for s in range(steps):
                if s % 2 == 0:
                    sx1 = p1[0] + (p2[0] - p1[0]) * (s / steps)
                    sy1 = p1[1] + (p2[1] - p1[1]) * (s / steps)
                    sx2 = p1[0] + (p2[0] - p1[0]) * ((s + 0.8) / steps)
                    sy2 = p1[1] + (p2[1] - p1[1]) * ((s + 0.8) / steps)
                    draw.line([(sx1, sy1), (sx2, sy2)], fill=(255, 255, 255), width=2)

        # Laces
        for lx in range(center_x - 50, center_x + 30, 18):
            draw.line([(lx, center_y - 45 + (lx - center_x) // 3), (lx + 20, center_y - 25 + (lx - center_x) // 3)], fill=(250, 250, 250), width=4)

        draw.text((center_x - 45, center_y + 125), "AERO-PACE RUNNER 4X", fill=(90, 100, 115), font=font_small)

    elif product_type == "cosmetic_serum":
        # 3. Luxury Cosmetic Dropper Bottle with fine typography, glass reflection, and gold accents
        # Shadow
        draw.ellipse([center_x - 90, center_y + 140, center_x + 90, center_y + 180], fill=(215, 218, 225))
        
        # Glass Bottle Body
        draw.rounded_rectangle([center_x - 75, center_y - 60, center_x + 75, center_y + 150], radius=18, fill=(235, 140, 105), outline=(190, 95, 65), width=2)
        # Liquid Fill with glass gradient highlight
        draw.rounded_rectangle([center_x - 68, center_y - 30, center_x + 68, center_y + 142], radius=12, fill=(220, 105, 70))
        # Glass specular sheen
        draw.line([(center_x - 55, center_y - 50), (center_x - 55, center_y + 130)], fill=(255, 230, 220), width=5)
        draw.line([(center_x - 46, center_y - 40), (center_x - 46, center_y + 110)], fill=(255, 215, 200), width=2)

        # Luxury Metallic Gold Collar
        draw.rectangle([center_x - 42, center_y - 95, center_x + 42, center_y - 60], fill=(225, 185, 75), outline=(175, 140, 45), width=2)
        # Rubber Bulb Dropper Top
        draw.ellipse([center_x - 30, center_y - 145, center_x + 30, center_y - 90], fill=(245, 245, 250), outline=(200, 205, 215), width=2)

        # Product Label Card (Matte White)
        draw.rounded_rectangle([center_x - 58, center_y - 10, center_x + 58, center_y + 110], radius=4, fill=(254, 254, 255), outline=(220, 225, 230))
        
        # Label Typography (Testing fine character resolution & edge definition)
        draw.text((center_x - 42, center_y), "L U M I E R E", fill=(30, 30, 35), font=font_small)
        draw.line([(center_x - 35, center_y + 22), (center_x + 35, center_y + 22)], fill=(210, 170, 60), width=1)
        draw.text((center_x - 48, center_y + 28), "HYALURONIC B5", fill=(60, 65, 75), font=font_tiny)
        draw.text((center_x - 50, center_y + 44), "Intense Hydration Serum", fill=(100, 105, 115), font=font_tiny)
        draw.text((center_x - 45, center_y + 62), "Dermatologist Tested", fill=(120, 125, 135), font=font_tiny)
        draw.text((center_x - 32, center_y + 88), "30 ml / 1.0 fl.oz", fill=(40, 45, 55), font=font_tiny)

    elif product_type == "organic_coffee_pack":
        # 4. Packaged Coffee Pouch with barcode, seal lines, and nutrition text
        # Shadow
        draw.ellipse([center_x - 110, center_y + 140, center_x + 110, center_y + 185], fill=(212, 215, 222))
        
        # Pouch shape (Kraft Brown)
        pouch_pts = [
            (center_x - 90, center_y - 140),
            (center_x + 90, center_y - 140),
            (center_x + 105, center_y + 150),
            (center_x - 105, center_y + 150)
        ]
        draw.polygon(pouch_pts, fill=(195, 155, 115), outline=(150, 110, 75), width=2)
        
        # Heat seal crimp lines at top
        for cy in range(center_y - 138, center_y - 120, 3):
            draw.line([(center_x - 88, cy), (center_x + 88, cy)], fill=(160, 120, 85), width=1)
            
        # Pouch degassing valve
        draw.ellipse([center_x - 12, center_y - 105, center_x + 12, center_y - 81], fill=(175, 135, 95), outline=(135, 95, 60), width=2)
        draw.point((center_x, center_y - 93), fill=(60, 40, 20))

        # Front Product Label
        draw.rounded_rectangle([center_x - 80, center_y - 70, center_x + 80, center_y + 130], radius=6, fill=(28, 32, 40), outline=(200, 160, 90), width=2)
        draw.text((center_x - 62, center_y - 55), "ARTISAN ROAST", fill=(225, 185, 110), font=font_med)
        draw.text((center_x - 48, center_y - 30), "ETHIOPIAN YIRGACHEFFE", fill=(245, 245, 250), font=font_tiny)
        draw.text((center_x - 52, center_y - 14), "Notes: Jasmine, Bergamot, Citrus", fill=(190, 195, 205), font=font_tiny)
        draw.text((center_x - 30, center_y + 5), "WHOLE BEAN", fill=(210, 165, 85), font=font_tiny)

        # Barcode (testing line resolution and fine pitch)
        bx_start, by_start = center_x - 60, center_y + 50
        draw.rectangle([bx_start - 6, by_start - 6, bx_start + 126, by_start + 50], fill=(255, 255, 255))
        barcode_pattern = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1]
        for idx, bar in enumerate(barcode_pattern * 2):
            if bar:
                draw.line([(bx_start + idx * 2, by_start), (bx_start + idx * 2, by_start + 36)], fill=(0, 0, 0), width=1)
        draw.text((bx_start + 14, by_start + 38), "0 12345 67890 5", fill=(0, 0, 0), font=font_tiny)

    else: # wireless_earbuds
        # 5. Consumer Electronics (Wireless Earbuds & Charging Case)
        # Shadow
        draw.ellipse([center_x - 130, center_y + 100, center_x + 130, center_y + 155], fill=(210, 214, 222))
        
        # Earbud Charging Case (Pebble Matte Black / Gunmetal)
        draw.rounded_rectangle([center_x - 110, center_y - 70, center_x + 110, center_y + 90], radius=55, fill=(35, 38, 44), outline=(75, 82, 95), width=2)
        # Case Lid Seam line
        draw.line([(center_x - 105, center_y - 5), (center_x + 105, center_y - 5)], fill=(20, 22, 26), width=3)
        # LED Status Indicator (Glowing Cyan)
        draw.ellipse([center_x - 4, center_y + 25, center_x + 4, center_y + 33], fill=(0, 240, 255))

        # Left Earbud resting next to case
        draw.ellipse([center_x - 145, center_y - 120, center_x - 85, center_y - 60], fill=(42, 46, 54), outline=(90, 98, 112), width=2)
        # Acoustic driver metallic mesh
        draw.ellipse([center_x - 125, center_y - 105, center_x - 105, center_y - 85], fill=(18, 20, 24), outline=(180, 185, 195), width=1)
        for gx in range(center_x - 122, center_x - 106, 3):
            draw.line([(gx, center_y - 102), (gx, center_y - 88)], fill=(120, 125, 135), width=1)
        # Earbud stem
        draw.rounded_rectangle([center_x - 122, center_y - 75, center_x - 108, center_y - 10], radius=6, fill=(32, 35, 42), outline=(75, 82, 95))

        # Brand Logo on Case
        draw.text((center_x - 38, center_y - 45), "SONIC", fill=(230, 235, 245), font=font_med)
        draw.text((center_x + 30, center_y - 45), "PRO", fill=(0, 210, 255), font=font_med)
        draw.text((center_x - 55, center_y + 55), "ANC ACTIVE NOISE CANCEL", fill=(140, 145, 155), font=font_tiny)

    return img


# =====================================================================
# 3. PYTORCH DATASET FOR TRAINING & FINE-TUNING
# =====================================================================

class SupplierProductSRDataset(Dataset):
    """
    PyTorch Dataset for paired Super-Resolution training.
    Can operate on pairs of HR and LR images, or dynamically synthesize LR
    images on-the-fly using the realistic degradation pipeline.
    """
    def __init__(self, hr_dir: str, lr_dir: str = None, scale: int = 4, crop_size: int = 256, is_train: bool = True):
        self.hr_dir = hr_dir
        self.lr_dir = lr_dir
        self.scale = scale
        self.crop_size = crop_size
        self.is_train = is_train
        
        self.hr_files = sorted([
            os.path.join(hr_dir, f) for f in os.listdir(hr_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]) if os.path.exists(hr_dir) else []
        
    def __len__(self):
        return len(self.hr_files)
        
    def __getitem__(self, idx):
        hr_path = self.hr_files[idx]
        hr_img = Image.open(hr_path).convert('RGB')
        
        # Random or center crop to consistent training patch size
        w, h = hr_img.size
        if w < self.crop_size or h < self.crop_size:
            hr_img = hr_img.resize((max(w, self.crop_size), max(h, self.crop_size)), Image.BICUBIC)
            w, h = hr_img.size
            
        if self.is_train:
            top = random.randint(0, h - self.crop_size)
            left = random.randint(0, w - self.crop_size)
            hr_crop = hr_img.crop((left, top, left + self.crop_size, top + self.crop_size))
            
            # Data augmentations: Random horizontal flip, vertical flip, 90-deg rotation
            if random.random() < 0.5:
                hr_crop = TF.hflip(hr_crop)
            if random.random() < 0.3:
                hr_crop = TF.vflip(hr_crop)
            if random.random() < 0.3:
                hr_crop = hr_crop.rotate(90)
        else:
            left = (w - self.crop_size) // 2
            top = (h - self.crop_size) // 2
            hr_crop = hr_img.crop((left, top, left + self.crop_size, top + self.crop_size))

        # Check if pre-computed LR exists, otherwise apply realistic degradation
        lr_loaded = False
        if self.lr_dir and os.path.exists(self.lr_dir):
            base_name = os.path.basename(hr_path)
            lr_path = os.path.join(self.lr_dir, base_name)
            if os.path.exists(lr_path):
                lr_img = Image.open(lr_path).convert('RGB')
                lr_w, lr_h = self.crop_size // self.scale, self.crop_size // self.scale
                lr_crop = lr_img.resize((lr_w, lr_h), Image.BILINEAR)
                lr_loaded = True
                
        if not lr_loaded:
            # Generate realistic degraded LR on the fly
            hr_np = np.array(hr_crop)[:, :, ::-1] # RGB to BGR
            lr_np = apply_realistic_vendor_degradation(
                hr_np, scale=self.scale, blur=True, noise=True, jpeg=True, jpeg_quality=40
            )
            lr_crop = Image.fromarray(lr_np[:, :, ::-1]) # BGR to RGB
            
        # Convert to PyTorch tensors normalized in [0, 1]
        hr_tensor = TF.to_tensor(hr_crop)
        lr_tensor = TF.to_tensor(lr_crop)
        
        return {"lr": lr_tensor, "hr": hr_tensor, "filename": os.path.basename(hr_path)}


# =====================================================================
# 4. INITIALIZE EVALUATION & SAMPLE SUITES
# =====================================================================

def setup_demo_and_eval_datasets(base_dir: str = "data"):
    """
    Builds the official directory structure and populates:
    1. data/samples/ (degraded vendor uploads for web app demo)
    2. data/eval_dataset/hr/ (ground-truth reference images)
    3. data/eval_dataset/lr/ (degraded supplier inputs)
    """
    samples_dir = os.path.join(base_dir, "samples")
    hr_dir = os.path.join(base_dir, "eval_dataset", "hr")
    lr_dir = os.path.join(base_dir, "eval_dataset", "lr")
    
    os.makedirs(samples_dir, exist_ok=True)
    os.makedirs(hr_dir, exist_ok=True)
    os.makedirs(lr_dir, exist_ok=True)
    
    products = [
        ("luxury_watch", "Luxury Chronograph Watch"),
        ("sneaker_shoe", "Athletic Running Sneaker"),
        ("cosmetic_serum", "Lumiere Skincare Serum Bottle"),
        ("organic_coffee_pack", "Artisan Coffee Packaging & Barcode"),
        ("wireless_earbuds", "SonicPro Wireless ANC Earbuds")
    ]
    
    print(f"[Dataset Pipeline] Generating benchmark e-commerce dataset in '{base_dir}'...")
    
    manifest = []
    
    for prod_id, prod_title in products:
        # 1. Generate high-resolution 512x512 ground-truth
        hr_image = create_high_detail_product_image(prod_id, size=512)
        hr_path = os.path.join(hr_dir, f"{prod_id}_hr.png")
        hr_image.save(hr_path, format="PNG")
        
        # 2. Generate 4x degraded vendor input (128x128 with realistic blur, sensor noise, jpeg compression)
        hr_np_bgr = cv2.cvtColor(np.array(hr_image), cv2.COLOR_RGB2BGR)
        lr_np_bgr = apply_realistic_vendor_degradation(
            hr_np_bgr, scale=4, blur=True, noise=True, jpeg=True, jpeg_quality=38
        )
        lr_image = Image.fromarray(cv2.cvtColor(lr_np_bgr, cv2.COLOR_BGR2RGB))
        
        lr_path = os.path.join(lr_dir, f"{prod_id}_lr.png")
        lr_image.save(lr_path, format="PNG")
        
        # 3. Also save to data/samples/ for instant demo in web UI
        sample_path = os.path.join(samples_dir, f"{prod_id}_supplier_input.jpg")
        # Save as JPEG with vendor compression
        lr_image.save(sample_path, format="JPEG", quality=45)
        
        manifest.append({
            "id": prod_id,
            "title": prod_title,
            "hr_path": hr_path,
            "lr_path": lr_path,
            "sample_path": sample_path,
            "hr_res": f"{hr_image.width}x{hr_image.height}",
            "lr_res": f"{lr_image.width}x{lr_image.height}",
            "scale": 4
        })
        print(f" -> Generated: {prod_title} (HR: 512x512 -> LR: 128x128 with vendor noise/blur/compression)")
        
    print(f"[Dataset Pipeline] Dataset successfully initialized. Total products: {len(manifest)}")
    return manifest


if __name__ == "__main__":
    setup_demo_and_eval_datasets()
