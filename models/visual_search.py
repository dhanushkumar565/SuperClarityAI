"""
SuperClarity AI - Visual Vector Search & Perceptual Duplicate Engine
Computes deep feature embeddings, cosine similarity matching, and
dHash perceptual hashing for near-duplicate vendor image detection.
"""

import numpy as np
import cv2
from PIL import Image

try:
    import torch
    import torchvision.transforms as T
    HAS_TORCH = True
except ImportError:
    torch = None
    T = None
    HAS_TORCH = False


class VisualSearchEngine:
    """
    Vector search engine for catalog similarity and duplicate detection.
    """

    def __init__(self):
        if HAS_TORCH:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self._transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.device = "cpu"
            self._transform = None
        self._model = None

    def _get_embedding_model(self):
        """Loads lightweight MobileNetV3 feature extractor or returns fallback."""
        if not HAS_TORCH:
            return "fallback"
        if self._model is None:
            try:
                import torchvision.models as models
                weights = models.MobileNet_V3_Small_Weights.DEFAULT
                base_model = models.mobilenet_v3_small(weights=weights)
                # Remove classification head to get latent feature pooling
                base_model.classifier = torch.nn.Identity()
                base_model.to(self.device)
                base_model.eval()
                self._model = base_model
            except Exception:
                # If network is unavailable for weights download, use spatial color descriptor fallback
                self._model = "fallback"
        return self._model

    def extract_embedding(self, img_pil: Image.Image) -> np.ndarray:
        """
        Extracts a normalized visual feature vector for an image.
        Returns 1D numpy float32 array.
        """
        model = self._get_embedding_model()

        if model != "fallback":
            try:
                tensor = self._transform(img_pil.convert("RGB")).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    feat = model(tensor).squeeze().cpu().numpy()
                norm = np.linalg.norm(feat)
                return feat / (norm + 1e-7)
            except Exception:
                pass

        # Robust color & texture fallback descriptor (512 dimensions)
        img_np = np.array(img_pil.convert("RGB").resize((64, 64)))
        hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [64], [0, 180]).flatten()
        hist_s = cv2.calcHist([hsv], [1], None, [64], [0, 256]).flatten()
        hist_v = cv2.calcHist([hsv], [2], None, [64], [0, 256]).flatten()
        
        # Spatial thumbnail features
        thumb = cv2.resize(img_np, (16, 16)).flatten().astype(np.float32) / 255.0
        combined = np.concatenate([hist_h, hist_s, hist_v, thumb[:320]])
        norm = np.linalg.norm(combined)
        return combined / (norm + 1e-7)

    @staticmethod
    def compute_dhash(img_pil: Image.Image, hash_size: int = 8) -> str:
        """
        Computes 64-bit difference hash (dHash) for fast duplicate detection.
        """
        # Resize to (width + 1, height) grayscale
        resized = img_pil.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        arr = np.array(resized)

        # Compare adjacent pixels: arr[:, 1:] > arr[:, :-1]
        diff = arr[:, 1:] > arr[:, :-1]
        # Convert boolean matrix to hex string
        decimal_val = 0
        hex_str = []
        for index, val in enumerate(diff.flatten()):
            if val:
                decimal_val += 2 ** (index % 8)
            if (index % 8) == 7:
                hex_str.append(hex(decimal_val)[2:].rjust(2, '0'))
                decimal_val = 0
        return "".join(hex_str)

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """Computes bitwise Hamming distance between two hex hashes."""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 999
        try:
            return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
        except ValueError:
            return 999

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculates normalized cosine similarity between two feature vectors."""
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        return float(dot / (norm1 * norm2 + 1e-7))

    def find_similar_items(self, query_img: Image.Image, catalog_items: list, top_k: int = 8) -> list:
        """
        Ranks catalog items by visual cosine similarity to the query image.
        """
        query_vec = self.extract_embedding(query_img)
        query_hash = self.compute_dhash(query_img)
        results = []

        for item in catalog_items:
            # Check cached or stored embedding
            item_path = item.get("enhanced_path") or item.get("original_path")
            if not item_path or not os.path.exists(item_path):
                continue

            try:
                item_img = Image.open(item_path).convert("RGB")
                item_vec = self.extract_embedding(item_img)
                similarity = self.cosine_similarity(query_vec, item_vec)
                
                # Check for duplicate
                item_hash = item.get("phash") or self.compute_dhash(item_img)
                dist = self.hamming_distance(query_hash, item_hash)
                is_duplicate = dist <= 4
                is_near_duplicate = 4 < dist <= 10

                results.append({
                    "item": item,
                    "similarity_score": round(similarity * 100, 1),
                    "hamming_distance": dist,
                    "is_duplicate": is_duplicate,
                    "is_near_duplicate": is_near_duplicate
                })
            except Exception:
                continue

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
