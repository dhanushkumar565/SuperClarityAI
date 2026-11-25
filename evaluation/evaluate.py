"""
SupplierClarity AI - Experimental Evaluation & Benchmarking Suite
Evaluates Bicubic, Bilinear, SRCNN, EDSR, and Real-ESRGAN across E-Commerce Product Images.
Calculates PSNR, SSIM, Sharpness Variance (Laplacian), and Processing Latency.
Generates CSV tables, JSON metrics, and visual comparison grids.
"""

import os
import sys
import json
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import cv2
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from skimage.metrics import peak_signal_noise_ratio as compute_psnr
from skimage.metrics import structural_similarity as compute_ssim

from models.upscaler import SupplierClarityUpscaler


def calculate_sharpness(img_np: np.ndarray) -> float:
    """Calculates Tenengrad / Laplacian variance representing high-frequency edge energy."""
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def run_benchmark(
    eval_dir: str = "data/eval_dataset",
    output_dir: str = "evaluation/results",
    scale: int = 4
):
    """
    Executes benchmark comparison across test product suite.
    """
    os.makedirs(output_dir, exist_ok=True)
    hr_dir = os.path.join(eval_dir, "hr")
    lr_dir = os.path.join(eval_dir, "lr")
    
    if not os.path.exists(hr_dir) or not os.path.exists(lr_dir):
        raise FileNotFoundError(f"Evaluation dataset missing in '{eval_dir}'. Run dataset_pipeline.py first.")
        
    upscaler = SupplierClarityUpscaler()
    
    products = [
        "luxury_watch",
        "sneaker_shoe",
        "cosmetic_serum",
        "organic_coffee_pack",
        "wireless_earbuds"
    ]
    
    methods = [
        ("bilinear", "Bilinear Interpolation (Baseline)"),
        ("bicubic", "Bicubic Interpolation (Baseline)"),
        ("srcnn", "SRCNN (Dong et al.)"),
        ("edsr", "EDSR (Lim et al.)"),
        ("realesrgan", "SupplierClarity AI (Real-ESRGAN)")
    ]
    
    results_list = []
    comparison_images = {}
    
    print("\n" + "=" * 70)
    print("STARTING COMPREHENSIVE EXPERIMENTAL EVALUATION")
    print(f"Scale: {scale}x | Test Products: {len(products)} | Methods: {len(methods)}")
    print("=" * 70 + "\n")
    
    for prod_id in products:
        hr_path = os.path.join(hr_dir, f"{prod_id}_hr.png")
        lr_path = os.path.join(lr_dir, f"{prod_id}_lr.png")
        
        hr_pil = Image.open(hr_path).convert("RGB")
        lr_pil = Image.open(lr_path).convert("RGB")
        hr_np = np.array(hr_pil)
        
        # Ground-truth metrics
        gt_sharpness = calculate_sharpness(hr_np)
        
        print(f"--- Product: {prod_id.replace('_', ' ').title()} ---")
        comparison_images[prod_id] = {
            "hr": hr_pil,
            "lr": lr_pil,
            "outputs": {}
        }
        
        for method_key, method_name in methods:
            t0 = time.time()
            res = upscaler.upscale(
                lr_pil,
                scale=scale,
                method=method_key,
                denoise=(method_key == "realesrgan"),
                sharpen=(method_key == "realesrgan")
            )
            elapsed_sec = time.time() - t0
            
            enhanced_pil = res["image"]
            enhanced_np = np.array(enhanced_pil)
            
            # Save visual output in results
            method_save_dir = os.path.join(output_dir, "enhanced_images", method_key)
            os.makedirs(method_save_dir, exist_ok=True)
            enhanced_pil.save(os.path.join(method_save_dir, f"{prod_id}_{method_key}.png"))
            
            comparison_images[prod_id]["outputs"][method_key] = enhanced_pil
            
            # Ensure same dimensions for metric computation
            if enhanced_np.shape != hr_np.shape:
                enhanced_np = cv2.resize(enhanced_np, (hr_np.shape[1], hr_np.shape[0]))
                
            psnr = compute_psnr(hr_np, enhanced_np, data_range=255)
            ssim = compute_ssim(hr_np, enhanced_np, data_range=255, channel_axis=2)
            sharpness = calculate_sharpness(enhanced_np)
            
            record = {
                "product_id": prod_id,
                "product_name": prod_id.replace('_', ' ').title(),
                "method_key": method_key,
                "method_name": method_name,
                "psnr_db": round(float(psnr), 2),
                "ssim": round(float(ssim), 4),
                "sharpness_index": round(float(sharpness), 1),
                "gt_sharpness": round(float(gt_sharpness), 1),
                "latency_sec": round(float(elapsed_sec), 3),
                "latency_ms": round(float(elapsed_sec * 1000), 1),
                "input_res": f"{lr_pil.width}x{lr_pil.height}",
                "output_res": f"{enhanced_pil.width}x{enhanced_pil.height}"
            }
            results_list.append(record)
            print(f"[{method_name:32s}] PSNR: {psnr:6.2f} dB | SSIM: {ssim:6.4f} | Sharpness: {sharpness:7.1f} | Latency: {elapsed_sec*1000:6.1f} ms")
            
    # Save CSV and JSON
    df = pd.DataFrame(results_list)
    csv_path = os.path.join(output_dir, "evaluation_table.csv")
    df.to_csv(csv_path, index=False)
    
    # Method averages
    summary_df = df.groupby(["method_key", "method_name"]).agg({
        "psnr_db": "mean",
        "ssim": "mean",
        "sharpness_index": "mean",
        "latency_ms": "mean"
    }).reset_index().round({"psnr_db": 2, "ssim": 4, "sharpness_index": 1, "latency_ms": 1})
    
    summary_csv_path = os.path.join(output_dir, "summary_averages.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    
    json_path = os.path.join(output_dir, "evaluation_summary.json")
    with open(json_path, "w") as f:
        json.dump({
            "individual_results": results_list,
            "averages": summary_df.to_dict(orient="records"),
            "scale": scale,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)
        
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY ACROSS ALL 5 E-COMMERCE PRODUCT CATEGORIES")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    print("=" * 70)
    
    # Generate Visual Comparison Figure
    generate_visual_comparison_figure(comparison_images, output_dir)
    generate_metrics_bar_chart(summary_df, output_dir)
    
    print(f"\n[Evaluation Complete] Artifacts saved to: {output_dir}")
    return df, summary_df


def generate_visual_comparison_figure(comparison_images: dict, output_dir: str):
    """Generates a high-resolution side-by-side comparison figure across methods."""
    # We display 3 key representative products: luxury_watch, cosmetic_serum, organic_coffee_pack
    selected_prods = ["luxury_watch", "cosmetic_serum", "organic_coffee_pack"]
    method_keys = ["lr", "bicubic", "srcnn", "realesrgan", "hr"]
    method_titles = ["Input LR (128x128)", "Bicubic Baseline", "SRCNN", "SupplierClarity AI", "Ground Truth HR"]
    
    n_rows = len(selected_prods)
    n_cols = len(method_keys)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 11), dpi=200)
    plt.subplots_adjust(wspace=0.04, hspace=0.15)
    
    for row_idx, prod_id in enumerate(selected_prods):
        prod_data = comparison_images[prod_id]
        prod_title = prod_id.replace("_", " ").title()
        
        for col_idx, m_key in enumerate(method_keys):
            ax = axes[row_idx, col_idx]
            
            if m_key == "lr":
                img = prod_data["lr"].resize((512, 512), Image.NEAREST)
            elif m_key == "hr":
                img = prod_data["hr"]
            else:
                img = prod_data["outputs"][m_key]
                
            ax.imshow(img)
            ax.axis("off")
            
            if row_idx == 0:
                ax.set_title(method_titles[col_idx], fontsize=13, fontweight="bold", pad=8)
                
            if col_idx == 0:
                ax.text(-0.08, 0.5, prod_title, transform=ax.transAxes,
                        fontsize=12, fontweight="bold", va="center", ha="right", rotation=90)
                
    fig_path = os.path.join(output_dir, "visual_comparison_grid.png")
    plt.tight_layout()
    plt.savefig(fig_path, bbox_inches="tight", dpi=200)
    plt.close()
    print(f" -> Saved visual comparison figure: {fig_path}")


def generate_metrics_bar_chart(summary_df: pd.DataFrame, output_dir: str):
    """Generates comparative charts for PSNR, SSIM, and Sharpness Index."""
    methods = summary_df["method_name"].tolist()
    psnr = summary_df["psnr_db"].tolist()
    ssim = summary_df["ssim"].tolist()
    sharpness = summary_df["sharpness_index"].tolist()
    latency = summary_df["latency_ms"].tolist()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), dpi=180)
    colors = ["#4A5568", "#718096", "#3182CE", "#6366F1", "#10B981"]
    
    # 1. PSNR
    ax1.bar(methods, psnr, color=colors)
    ax1.set_title("Peak Signal-to-Noise Ratio (PSNR in dB) ↑", fontsize=12, fontweight="bold")
    ax1.set_ylabel("dB")
    ax1.set_xticklabels(methods, rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(psnr):
        ax1.text(i, v + 0.3, f"{v:.1f}", ha="center", fontweight="bold", fontsize=9)
        
    # 2. SSIM
    ax2.bar(methods, ssim, color=colors)
    ax2.set_title("Structural Similarity Index (SSIM) ↑", fontsize=12, fontweight="bold")
    ax2.set_ylabel("SSIM (0 to 1)")
    ax2.set_xticklabels(methods, rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(ssim):
        ax2.text(i, v + 0.015, f"{v:.3f}", ha="center", fontweight="bold", fontsize=9)
        
    # 3. Sharpness Variance (Perceptual Edge Energy)
    ax3.bar(methods, sharpness, color=colors)
    ax3.set_title("Tenengrad Edge Sharpness (Laplacian Var) ↑", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Variance")
    ax3.set_xticklabels(methods, rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(sharpness):
        ax3.text(i, v + 15, f"{v:.0f}", ha="center", fontweight="bold", fontsize=9)
        
    # 4. Latency
    ax4.bar(methods, latency, color=colors)
    ax4.set_title("Processing Latency (ms on CPU) ↓", fontsize=12, fontweight="bold")
    ax4.set_ylabel("Milliseconds")
    ax4.set_xticklabels(methods, rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(latency):
        ax4.text(i, v + 15, f"{v:.0f}ms", ha="center", fontweight="bold", fontsize=9)
        
    plt.tight_layout()
    chart_path = os.path.join(output_dir, "metrics_comparison_chart.png")
    plt.savefig(chart_path, bbox_inches="tight", dpi=180)
    plt.close()
    print(f" -> Saved metrics bar chart: {chart_path}")


if __name__ == "__main__":
    run_benchmark()
