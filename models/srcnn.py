"""
SupplierClarity AI - SRCNN (Super-Resolution Convolutional Neural Network)
Reference: Dong et al., "Image Super-Resolution Using Deep Convolutional Networks", TPAMI 2016.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SRCNN(nn.Module):
    """
    3-layer Convolutional Neural Network for Super-Resolution:
    1. Patch extraction & representation: Conv(9x9, 64) + ReLU
    2. Non-linear mapping: Conv(5x5, 32) + ReLU
    3. High-resolution reconstruction: Conv(5x5, 3)
    """
    def __init__(self, num_channels: int = 3):
        super(SRCNN, self).__init__()
        # Layer 1: Patch extraction
        self.conv1 = nn.Conv2d(num_channels, 64, kernel_size=9, padding=4)
        self.relu1 = nn.ReLU(inplace=True)
        # Layer 2: Non-linear mapping
        self.conv2 = nn.Conv2d(64, 32, kernel_size=5, padding=2)
        self.relu2 = nn.ReLU(inplace=True)
        # Layer 3: Reconstruction
        self.conv3 = nn.Conv2d(32, num_channels, kernel_size=5, padding=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.relu1(self.conv1(x))
        out = self.relu2(self.conv2(out))
        out = self.conv3(out)
        return out


def create_srcnn_model(pretrained_weights: str = None, device: str = "cpu") -> SRCNN:
    """Instantiate and optionally load weights for SRCNN."""
    model = SRCNN(num_channels=3)
    if pretrained_weights:
        state_dict = torch.load(pretrained_weights, map_location=device)
        model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model
