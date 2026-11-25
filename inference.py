"""
SupplierClarity AI - Command-Line & Programmatic Inference Interface
Usage:
    python inference.py --input data/samples/luxury_watch_supplier_input.jpg --output results/watch_enhanced.png --scale 4
"""

import os
import argparse
from PIL import Image
from models.upscaler import SupplierClarityUpscaler


def run_inference(
    input_path: str,
    output_path: str = None,
    scale: int = 4,
    method: str = "realesrgan",
    denoise: bool = True,
    sharpen: bool = True
):
    """Run inference on an input image and save enhanced result."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' not found.")
        
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_enhanced_{scale}x{ext}"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    upscaler = SupplierClarityUpscaler()
    print(f"[Inference] Loading '{input_path}'...")
    res = upscaler.upscale(
        image_input=input_path,
        scale=scale,
        method=method,
        denoise=denoise,
        sharpen=sharpen
    )
    
    enhanced_img = res["image"]
    enhanced_img.save(output_path)
    
    print(f"[Inference] Enhancement complete!")
    print(f" -> Method: {res['method']}")
    print(f" -> Resolution: {res['original_size']} -> {res['enhanced_size']} ({scale}x)")
    print(f" -> Latency: {res['latency_seconds']}s ({res['latency_ms']}ms)")
    print(f" -> Saved to: '{output_path}'")
    return res


def main():
    parser = argparse.ArgumentParser(description="SupplierClarity AI - Product Image Upscaler")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input low-resolution image")
    parser.add_argument("--output", "-o", type=str, default=None, help="Path to save enhanced image")
    parser.add_argument("--scale", "-s", type=int, default=4, choices=[2, 4], help="Upscaling scale factor (2 or 4)")
    parser.add_argument("--method", "-m", type=str, default="realesrgan", choices=["realesrgan", "edsr", "srcnn", "bicubic"], help="SR Method")
    parser.add_argument("--no-denoise", action="store_true", help="Disable bilateral artifact suppression")
    parser.add_argument("--no-sharpen", action="store_true", help="Disable unsharp mask post-processing")
    
    args = parser.parse_args()
    run_inference(
        input_path=args.input,
        output_path=args.output,
        scale=args.scale,
        method=args.method,
        denoise=not args.no_denoise,
        sharpen=not args.no_sharpen
    )


if __name__ == "__main__":
    main()
