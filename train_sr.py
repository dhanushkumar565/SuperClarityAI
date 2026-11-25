"""
SupplierClarity AI - Model Training & Fine-Tuning Pipeline
Supports training SRCNN and EDSR on E-Commerce Product Image Pairs.
"""

import os
import time
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.transforms import functional as TF
from skimage.metrics import peak_signal_noise_ratio as compute_psnr
from skimage.metrics import structural_similarity as compute_ssim

from dataset_pipeline import SupplierProductSRDataset, setup_demo_and_eval_datasets
from models.srcnn import SRCNN
from models.edsr import EDSR


class CharbonnierLoss(nn.Module):
    """Robust L1 variant that prevents gradient explosion around zero."""
    def __init__(self, eps: float = 1e-6):
        super(CharbonnierLoss, self).__init__()
        self.eps = eps

    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        diff = x - y
        loss = torch.mean(torch.sqrt((diff * diff) + (self.eps * self.eps)))
        return loss


def evaluate_model(model: nn.Module, val_loader: DataLoader, device: torch.device, scale: int, is_srcnn: bool = False):
    """Compute validation PSNR and SSIM over paired images."""
    model.eval()
    psnr_scores = []
    ssim_scores = []
    
    with torch.no_grad():
        for batch in val_loader:
            lr = batch["lr"].to(device)
            hr = batch["hr"].to(device)
            
            if is_srcnn:
                # SRCNN takes bicubic interpolated image as input
                lr_up = TF.resize(lr, [hr.shape[2], hr.shape[3]], interpolation=TF.InterpolationMode.BICUBIC)
                preds = model(lr_up)
            else:
                preds = model(lr)
                
            preds = torch.clamp(preds, 0.0, 1.0)
            
            for i in range(preds.shape[0]):
                p_np = preds[i].permute(1, 2, 0).cpu().numpy()
                h_np = hr[i].permute(1, 2, 0).cpu().numpy()
                
                # Metrics
                p_val = compute_psnr(h_np, p_np, data_range=1.0)
                s_val = compute_ssim(h_np, p_np, data_range=1.0, channel_axis=2)
                psnr_scores.append(p_val)
                ssim_scores.append(s_val)
                
    return np.mean(psnr_scores), np.mean(ssim_scores)


def train_super_resolution(
    model_type: str = "srcnn",
    scale: int = 4,
    epochs: int = 15,
    batch_size: int = 4,
    lr: float = 5e-4,
    data_dir: str = "data",
    save_dir: str = "models/weights"
):
    """
    Train or fine-tune super-resolution model on supplier product dataset.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n========================================================")
    print(f"SupplierClarity AI - Model Training Pipeline")
    print(f"Model: {model_type.upper()} | Scale: {scale}x | Device: {device}")
    print(f"Epochs: {epochs} | Batch Size: {batch_size} | Learning Rate: {lr}")
    print(f"========================================================\n")
    
    hr_dir = os.path.join(data_dir, "eval_dataset", "hr")
    lr_dir = os.path.join(data_dir, "eval_dataset", "lr")
    
    if not os.path.exists(hr_dir):
        setup_demo_and_eval_datasets(base_dir=data_dir)
        
    os.makedirs(save_dir, exist_ok=True)
    
    # Dataset and DataLoaders
    train_dataset = SupplierProductSRDataset(hr_dir=hr_dir, lr_dir=lr_dir, scale=scale, crop_size=256, is_train=True)
    val_dataset = SupplierProductSRDataset(hr_dir=hr_dir, lr_dir=lr_dir, scale=scale, crop_size=256, is_train=False)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)
    
    # Instantiate Model
    is_srcnn = (model_type.lower() == "srcnn")
    if is_srcnn:
        model = SRCNN(num_channels=3).to(device)
        save_path = os.path.join(save_dir, "srcnn.pth")
    else:
        model = EDSR(n_resblocks=8, n_feats=64, scale=scale, num_channels=3).to(device)
        save_path = os.path.join(save_dir, f"edsr_{scale}x.pth")
        
    criterion = CharbonnierLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    best_psnr = -1.0
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        
        for batch in train_loader:
            lr_imgs = batch["lr"].to(device)
            hr_imgs = batch["hr"].to(device)
            
            optimizer.zero_grad()
            
            if is_srcnn:
                lr_input = TF.resize(lr_imgs, [hr_imgs.shape[2], hr_imgs.shape[3]], interpolation=TF.InterpolationMode.BICUBIC)
                preds = model(lr_input)
            else:
                preds = model(lr_imgs)
                
            loss = criterion(preds, hr_imgs)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * lr_imgs.size(0)
            
        epoch_loss = running_loss / len(train_dataset)
        scheduler.step()
        
        # Validation
        if epoch % 5 == 0 or epoch == epochs:
            val_psnr, val_ssim = evaluate_model(model, val_loader, device, scale=scale, is_srcnn=is_srcnn)
            print(f"Epoch [{epoch:02d}/{epochs:02d}] - Loss: {epoch_loss:.5f} | Val PSNR: {val_psnr:.2f} dB | Val SSIM: {val_ssim:.4f}")
            
            if val_psnr > best_psnr:
                best_psnr = val_psnr
                torch.save(model.state_dict(), save_path)
                print(f" -> Best checkpoint saved to '{save_path}' (PSNR: {best_psnr:.2f} dB)")
        else:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] - Loss: {epoch_loss:.5f}")

    total_time = time.time() - start_time
    print(f"\n[Training Complete] Elapsed Time: {total_time:.2f}s | Best Val PSNR: {best_psnr:.2f} dB")
    print(f"Saved weights to: {save_path}\n")


def main():
    parser = argparse.ArgumentParser(description="SupplierClarity AI - Model Training")
    parser.add_argument("--model", "-m", type=str, default="srcnn", choices=["srcnn", "edsr"], help="Model architecture")
    parser.add_argument("--scale", "-s", type=int, default=4, choices=[2, 4], help="Upscaling scale factor")
    parser.add_argument("--epochs", "-e", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", "-b", type=int, default=2, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    
    args = parser.parse_args()
    train_super_resolution(
        model_type=args.model,
        scale=args.scale,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )


if __name__ == "__main__":
    main()
