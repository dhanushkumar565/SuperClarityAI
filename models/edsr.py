"""
SupplierClarity AI - EDSR (Enhanced Deep Residual Networks for Super-Resolution)
Reference: Lim et al., "Enhanced Deep Residual Networks for Single Image Super-Resolution", CVPRW 2017.
"""

import math
import torch
import torch.nn as nn


class ResBlock(nn.Module):
    """Residual Block without Batch Normalization for stable SR training."""
    def __init__(self, n_feats: int, kernel_size: int = 3, res_scale: float = 0.1):
        super(ResBlock, self).__init__()
        self.res_scale = res_scale
        self.body = nn.Sequential(
            nn.Conv2d(n_feats, n_feats, kernel_size, padding=kernel_size // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(n_feats, n_feats, kernel_size, padding=kernel_size // 2)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.body(x).mul(self.res_scale)
        return x + res


class Upsampler(nn.Sequential):
    """Sub-pixel Convolution (PixelShuffle) Upsampler module."""
    def __init__(self, scale: int, n_feats: int):
        m = []
        if (scale & (scale - 1)) == 0:  # Scale is power of 2 (2x, 4x, 8x)
            for _ in range(int(math.log2(scale))):
                m.append(nn.Conv2d(n_feats, 4 * n_feats, 3, padding=1))
                m.append(nn.PixelShuffle(2))
                m.append(nn.ReLU(inplace=True))
        elif scale == 3:
            m.append(nn.Conv2d(n_feats, 9 * n_feats, 3, padding=1))
            m.append(nn.PixelShuffle(3))
            m.append(nn.ReLU(inplace=True))
        else:
            raise NotImplementedError(f"Scale {scale} is not supported.")
        super(Upsampler, self).__init__(*m)


class EDSR(nn.Module):
    """
    Enhanced Deep Residual Networks for Single Image Super-Resolution.
    Removes Batch Normalization layers to preserve range flexibility and reduce memory footprint.
    """
    def __init__(self, n_resblocks: int = 8, n_feats: int = 64, scale: int = 4, num_channels: int = 3):
        super(EDSR, self).__init__()
        self.scale = scale
        
        # 1. Head
        self.head = nn.Conv2d(num_channels, n_feats, kernel_size=3, padding=1)
        
        # 2. Body (Residual blocks)
        blocks = [ResBlock(n_feats, kernel_size=3, res_scale=0.1) for _ in range(n_resblocks)]
        blocks.append(nn.Conv2d(n_feats, n_feats, kernel_size=3, padding=1))
        self.body = nn.Sequential(*blocks)
        
        # 3. Tail (Upsampling + output projection)
        self.upsample = Upsampler(scale, n_feats)
        self.tail = nn.Conv2d(n_feats, num_channels, kernel_size=3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.head(x)
        res = self.body(feat)
        res = res + feat
        up = self.upsample(res)
        out = self.tail(up)
        return out


def create_edsr_model(scale: int = 4, pretrained_weights: str = None, device: str = "cpu") -> EDSR:
    """Instantiate and optionally load weights for EDSR."""
    model = EDSR(n_resblocks=8, n_feats=64, scale=scale, num_channels=3)
    if pretrained_weights:
        state_dict = torch.load(pretrained_weights, map_location=device)
        model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
