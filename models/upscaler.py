"""
SupplierClarity AI - Unified Super-Resolution & Image Upscaler Engine
Supports Real-ESRGAN (2x & 4x), EDSR, SRCNN, and Bicubic baselines.
"""

import os
import time
import math
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import torch
import torch.nn.functional as F

from basicsr.archs.srvgg_arch import SRVGGNetCompact
from basicsr.archs.rrdbnet_arch import RRDBNet
from models.srcnn import SRCNN
from models.edsr import EDSR


class SupplierClarityUpscaler:
    """
    Production-ready Super-Resolution engine tailored for e-commerce vendor images.
    Preserves original product colors, restores fine textures and package typography,
    and provides controllable sharpening and artifact mitigation.
    """
    def __init__(self, device: str = None, weights_dir: str = "models/weights"):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
            
        self.weights_dir = weights_dir
        os.makedirs(self.weights_dir, exist_ok=True)
        
        # Model cache to avoid re-instantiating heavy neural nets on every request
        self._models = {}
        print(f"[SupplierClarity Engine] Initialized on device: {self.device}")

    # -----------------------------------------------------------------
    # MODEL LOADING & CACHING
    # -----------------------------------------------------------------
    def _load_realesrgan_4x(self):
        if "realesrgan_4x" in self._models:
            return self._models["realesrgan_4x"]
            
        weight_path = os.path.join(self.weights_dir, "realesr-general-x4v3.pth")
        if not os.path.exists(weight_path):
            import urllib.request
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth"
            print(f"[SupplierClarity Engine] Downloading Real-ESRGAN 4x weights from {url}...")
            urllib.request.urlretrieve(url, weight_path)
            
        model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
        state_dict = torch.load(weight_path, map_location=self.device)
        key = "params_ema" if "params_ema" in state_dict else "params"
        model.load_state_dict(state_dict[key] if key in state_dict else state_dict, strict=True)
        model.to(self.device)
        model.eval()
        self._models["realesrgan_4x"] = model
        return model

    def _load_realesrgan_2x(self):
        if "realesrgan_2x" in self._models:
            return self._models["realesrgan_2x"]
            
        weight_path = os.path.join(self.weights_dir, "RealESRGAN_x2plus.pth")
        if not os.path.exists(weight_path):
            import urllib.request
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
            print(f"[SupplierClarity Engine] Downloading Real-ESRGAN 2x weights from {url}...")
            urllib.request.urlretrieve(url, weight_path)
            
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        state_dict = torch.load(weight_path, map_location=self.device)
        key = "params_ema" if "params_ema" in state_dict else "params"
        model.load_state_dict(state_dict[key] if key in state_dict else state_dict, strict=True)
        model.to(self.device)
        model.eval()
        self._models["realesrgan_2x"] = model
        return model

    def _load_edsr(self, scale: int = 4):
        key = f"edsr_{scale}x"
        if key in self._models:
            return self._models[key]
            
        weight_path = os.path.join(self.weights_dir, f"edsr_{scale}x.pth")
        model = EDSR(n_resblocks=8, n_feats=64, scale=scale, num_channels=3)
        if os.path.exists(weight_path):
            model.load_state_dict(torch.load(weight_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        self._models[key] = model
        return model

    def _load_srcnn(self):
        if "srcnn" in self._models:
            return self._models["srcnn"]
            
        weight_path = os.path.join(self.weights_dir, "srcnn.pth")
        model = SRCNN(num_channels=3)
        if os.path.exists(weight_path):
            model.load_state_dict(torch.load(weight_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        self._models["srcnn"] = model
        return model

    # -----------------------------------------------------------------
    # INFERENCE PIPELINE
    # -----------------------------------------------------------------
    def upscale(
        self,
        image_input,
        scale: int = 4,
        method: str = "realesrgan",
        denoise: bool = True,
        sharpen: bool = True,
        sharpen_strength: float = 1.15,
        product_preset: dict = None
    ) -> dict:
        """
        Enhance a low-resolution vendor image using the specified Super-Resolution method.
        Supports 2x, 4x, and 8x AI super-resolution with product-specific presets.
        
        Args:
            image_input: PIL Image, NumPy ndarray (RGB/BGR), or file path.
            scale: Upscaling factor (2, 4, or 8).
            method: 'realesrgan', 'edsr', 'srcnn', 'bicubic', or 'bilinear'.
            denoise: Apply pre/post bilateral edge-preserving artifact smoothing.
            sharpen: Apply unsharp masking to enhance package text and edges.
            sharpen_strength: Multiplier for sharpening mask.
            product_preset: Optional dictionary with product-specific tuning parameters.
            
        Returns:
            Dictionary with enhanced PIL image, resolution metadata, and latency.
        """
        start_time = time.time()
        
        # 1. Normalize input to PIL RGB
        if isinstance(image_input, str):
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            if image_input.shape[2] == 4:
                image_input = cv2.cvtColor(image_input, cv2.COLOR_RGBA2RGB)
            elif len(image_input.shape) == 2:
                image_input = cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
            pil_img = Image.fromarray(image_input)
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise ValueError("Unsupported image input type.")

        # Preset overrides if provided
        contrast_boost = 1.0
        if product_preset and isinstance(product_preset, dict):
            if "sharpen_strength" in product_preset:
                sharpen_strength = float(product_preset["sharpen_strength"])
            if "contrast_boost" in product_preset:
                contrast_boost = float(product_preset["contrast_boost"])

        orig_w, orig_h = pil_img.size
        target_w, target_h = orig_w * scale, orig_h * scale
        
        # Pre-process: mild noise suppression for vendor compression if requested
        if denoise:
            np_img = np.array(pil_img)
            # Bilateral filter preserves sharp geometric product edges while smoothing JPEG macroblocks
            sigma_val = 30 if (product_preset and product_preset.get("name") == "Apparel & Footwear") else 35
            np_img = cv2.bilateralFilter(np_img, d=5, sigmaColor=sigma_val, sigmaSpace=sigma_val)
            pil_img = Image.fromarray(np_img)

        # 2. Execute selected Super-Resolution model
        method_norm = method.lower().strip()
        
        if method_norm in ["bicubic", "baseline_bicubic"]:
            enhanced_pil = pil_img.resize((target_w, target_h), Image.BICUBIC)
            
        elif method_norm in ["bilinear", "baseline_bilinear"]:
            enhanced_pil = pil_img.resize((target_w, target_h), Image.BILINEAR)
            
        elif method_norm == "srcnn":
            enhanced_pil = self._infer_srcnn(pil_img, scale=scale)
            
        elif method_norm == "edsr":
            enhanced_pil = self._infer_edsr(pil_img, scale=scale)
            
        else:  # Default: Real-ESRGAN
            enhanced_pil = self._infer_realesrgan(pil_img, scale=scale)

        # 3. Post-processing: Edge-aware sharpening for label & typography clarity
        if sharpen and sharpen_strength > 0:
            enhanced_pil = self._apply_unsharp_mask(enhanced_pil, strength=sharpen_strength)

        # Apply preset contrast boost if configured
        if contrast_boost != 1.0:
            enhanced_pil = ImageEnhance.Contrast(enhanced_pil).enhance(contrast_boost)

        # Ensure exact target dimensions
        if enhanced_pil.size != (target_w, target_h):
            enhanced_pil = enhanced_pil.resize((target_w, target_h), Image.LANCZOS)

        elapsed_sec = time.time() - start_time
        
        return {
            "image": enhanced_pil,
            "original_size": (orig_w, orig_h),
            "enhanced_size": (target_w, target_h),
            "scale": scale,
            "method": method_norm,
            "latency_seconds": round(elapsed_sec, 3),
            "latency_ms": round(elapsed_sec * 1000, 1)
        }

    # -----------------------------------------------------------------
    # SPECIFIC MODEL INFERENCE HELPERS
    # -----------------------------------------------------------------
    def _infer_realesrgan(self, img_pil: Image.Image, scale: int = 4) -> Image.Image:
        """Run Real-ESRGAN deep model inference with tile support."""
        if scale == 8:
            # 8x progressive cascaded super-resolution: 4x pass followed by 2x pass
            inter_4x = self._infer_realesrgan(img_pil, scale=4)
            out_8x = self._infer_realesrgan(inter_4x, scale=2)
            return out_8x

        if scale == 2:
            model = self._load_realesrgan_2x()
            native_scale = 2
        else:
            model = self._load_realesrgan_4x()
            native_scale = 4

        # Convert PIL to Tensor [1, 3, H, W] in [0, 1]
        img_np = np.array(img_pil).astype(np.float32) / 255.0
        # Channels: RGB
        tensor = torch.from_numpy(img_np.transpose((2, 0, 1))).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # If image is very large, tile inference to conserve memory
            h, w = tensor.shape[2], tensor.shape[3]
            tile_size = 512
            if h > tile_size or w > tile_size:
                output = self._tile_forward(model, tensor, tile_size=tile_size, scale=native_scale)
            else:
                output = model(tensor)
                
            output = torch.clamp(output, 0.0, 1.0)
            
        # Convert back to uint8 PIL
        out_np = (output.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
        out_pil = Image.fromarray(out_np)
        
        # If user asked for 2x scale using 4x model (or vice-versa), resize cleanly
        target_w, target_h = img_pil.width * scale, img_pil.height * scale
        if out_pil.size != (target_w, target_h):
            out_pil = out_pil.resize((target_w, target_h), Image.LANCZOS)
            
        return out_pil

    def _infer_srcnn(self, img_pil: Image.Image, scale: int = 4) -> Image.Image:
        """Run SRCNN on bicubic-upsampled tensor."""
        target_w, target_h = img_pil.width * scale, img_pil.height * scale
        bicubic_pil = img_pil.resize((target_w, target_h), Image.BICUBIC)
        
        model = self._load_srcnn()
        img_np = np.array(bicubic_pil).astype(np.float32) / 255.0
        tensor = torch.from_numpy(img_np.transpose((2, 0, 1))).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = model(tensor)
            output = torch.clamp(output, 0.0, 1.0)
            
        out_np = (output.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
        return Image.fromarray(out_np)

    def _infer_edsr(self, img_pil: Image.Image, scale: int = 4) -> Image.Image:
        """Run EDSR residual model."""
        if scale == 8:
            inter_4x = self._infer_edsr(img_pil, scale=4)
            return inter_4x.resize((img_pil.width * 8, img_pil.height * 8), Image.LANCZOS)
            
        model = self._load_edsr(scale=scale if scale in [2, 4] else 4)
        img_np = np.array(img_pil).astype(np.float32) / 255.0
        tensor = torch.from_numpy(img_np.transpose((2, 0, 1))).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = model(tensor)
            output = torch.clamp(output, 0.0, 1.0)
            
        out_np = (output.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255.0).astype(np.uint8)
        return Image.fromarray(out_np)

    def _tile_forward(self, model: torch.nn.Module, x: torch.Tensor, tile_size: int = 512, tile_pad: int = 16, scale: int = 4) -> torch.Tensor:
        """Tile-based inference to process high-resolution vendor images without OOM."""
        batch, channel, height, width = x.shape
        out_h, out_w = height * scale, width * scale
        output = torch.zeros((batch, channel, out_h, out_w), dtype=x.dtype, device=x.device)
        
        num_tiles_y = math.ceil(height / tile_size)
        num_tiles_x = math.ceil(width / tile_size)
        
        for y in range(num_tiles_y):
            for x_idx in range(num_tiles_x):
                # Coordinates in input
                y1 = y * tile_size
                y2 = min(y1 + tile_size, height)
                x1 = x_idx * tile_size
                x2 = min(x1 + tile_size, width)
                
                # Add padding
                y1_pad = max(0, y1 - tile_pad)
                y2_pad = min(height, y2 + tile_pad)
                x1_pad = max(0, x1 - tile_pad)
                x2_pad = min(width, x2 + tile_pad)
                
                tile = x[:, :, y1_pad:y2_pad, x1_pad:x2_pad]
                with torch.no_grad():
                    tile_out = model(tile)
                    
                # Crop padding from output tile
                top_pad = (y1 - y1_pad) * scale
                left_pad = (x1 - x1_pad) * scale
                tile_h = (y2 - y1) * scale
                tile_w = (x2 - x1) * scale
                
                output[:, :, y1 * scale:y2 * scale, x1 * scale:x2 * scale] = \
                    tile_out[:, :, top_pad:top_pad + tile_h, left_pad:left_pad + tile_w]
                    
        return output

    @staticmethod
    def _apply_unsharp_mask(pil_img: Image.Image, radius: float = 1.0, strength: float = 1.15) -> Image.Image:
        """
        Enhances edge definition around logos, product labels, and seams
        using an unsharp masking convolution filter.
        """
        blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))
        # High pass = Original - Blurred
        img_np = np.array(pil_img, dtype=np.float32)
        blur_np = np.array(blurred, dtype=np.float32)
        high_pass = img_np - blur_np
        sharpened = np.clip(img_np + strength * high_pass, 0, 255).astype(np.uint8)
        return Image.fromarray(sharpened)
