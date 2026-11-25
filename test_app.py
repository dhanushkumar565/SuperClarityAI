"""
SupplierClarity AI - End-to-End System & API Verification Tests
"""

import os
import json
import io
import unittest
from PIL import Image
from app import app


class SupplierClarityTestSuite(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_index_page(self):
        """Verify home page loads successfully with 200 OK and expected DOM strings."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("SupplierClarity", html)
        self.assertIn("Vendor Product Image Upscaler", html)
        self.assertIn("split-slider-wrapper", html)
        print("[TEST PASSED] Home page renders cleanly with 200 OK.")

    def test_02_samples_list_api(self):
        """Verify /api/samples returns sample products manifest."""
        response = self.client.get("/api/samples")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["samples"]), 5)
        print(f"[TEST PASSED] /api/samples returns {len(data['samples'])} products.")

    def test_03_sample_image_api(self):
        """Verify /api/sample/<id> returns image base64 and dimension metadata."""
        response = self.client.get("/api/sample/luxury_watch")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertIn("data:image/jpeg;base64,", data["image_base64"])
        self.assertEqual(data["resolution"], "128x128")
        print("[TEST PASSED] /api/sample/luxury_watch returns valid metadata & base64.")

    def test_04_upscale_with_sample_4x(self):
        """Verify 4x enhancement on sample image."""
        response = self.client.post("/api/upscale", data={
            "sample_id": "luxury_watch",
            "scale": 4,
            "method": "realesrgan",
            "denoise": "true",
            "sharpen": "true"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["original_resolution"], "128x128")
        self.assertEqual(data["enhanced_resolution"], "512x512")
        self.assertEqual(data["scale"], 4)
        self.assertIn("download_png_url", data)
        self.assertIn("download_jpg_url", data)
        self.assertTrue(data["metrics"]["has_ground_truth"])
        self.assertIn("ssim", data["metrics"])
        self.assertIn("psnr_db", data["metrics"])
        print(f"[TEST PASSED] 4x AI Upscale: 128x128 -> 512x512 in {data['latency_ms']}ms.")

    def test_05_upscale_with_sample_2x(self):
        """Verify 2x enhancement on sample image."""
        response = self.client.post("/api/upscale", data={
            "sample_id": "sneaker_shoe",
            "scale": 2,
            "method": "realesrgan",
            "denoise": "true",
            "sharpen": "true"
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["original_resolution"], "128x128")
        self.assertEqual(data["enhanced_resolution"], "256x256")
        self.assertEqual(data["scale"], 2)
        print(f"[TEST PASSED] 2x AI Upscale: 128x128 -> 256x256 in {data['latency_ms']}ms.")

    def test_06_upscale_with_custom_file_upload(self):
        """Verify file upload enhancement with synthetic test image."""
        # Create a small in-memory 64x64 test image
        img = Image.new("RGB", (64, 64), color=(40, 90, 160))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        response = self.client.post("/api/upscale", data={
            "file": (img_bytes, "vendor_upload_test.png"),
            "scale": 4,
            "method": "realesrgan",
            "denoise": "false",
            "sharpen": "false"
        }, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["original_resolution"], "64x64")
        self.assertEqual(data["enhanced_resolution"], "256x256")
        print(f"[TEST PASSED] Custom image file upload upscaled successfully: 64x64 -> 256x256.")

    def test_07_download_enhanced_file(self):
        """Verify downloaded enhanced image exists and is valid."""
        # Upscale first
        res = self.client.post("/api/upscale", data={
            "sample_id": "wireless_earbuds",
            "scale": 4,
            "method": "realesrgan"
        })
        data = json.loads(res.data.decode("utf-8"))
        dl_url = data["download_png_url"]
        
        # Download
        dl_res = self.client.get(dl_url)
        self.assertEqual(dl_res.status_code, 200)
        self.assertGreater(len(dl_res.data), 1000)
        # Check valid image by loading PIL
        dl_img = Image.open(io.BytesIO(dl_res.data))
        self.assertEqual(dl_img.size, (512, 512))
        print(f"[TEST PASSED] Download endpoint verified. Valid PNG: {dl_img.size}, {len(dl_res.data)} bytes.")

    def test_08_benchmark_api(self):
        """Verify /api/benchmark returns evaluation metrics."""
        response = self.client.get("/api/benchmark")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertIn("averages", data["data"])
        print("[TEST PASSED] /api/benchmark returned verified experimental data.")

    def test_09_input_validation(self):
        """Verify invalid requests return proper 400 Bad Request error."""
        # No file or sample provided
        res = self.client.post("/api/upscale", data={})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data.decode("utf-8"))
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        print("[TEST PASSED] Input validation cleanly blocks empty requests with 400.")

    def test_10_chat_languages_api(self):
        """Verify /api/chat/languages returns supported languages (English, Telugu, Hindi)."""
        response = self.client.get("/api/chat/languages")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        lang_codes = [l["code"] for l in data["languages"]]
        self.assertIn("en", lang_codes)
        self.assertIn("te", lang_codes)
        self.assertIn("hi", lang_codes)
        print(f"[TEST PASSED] /api/chat/languages returned {len(lang_codes)} supported locales.")

    def test_11_chat_english_query_with_context(self):
        """Verify English chat query with active ML telemetry context."""
        payload = {
            "message": "Explain this upscaled product image result",
            "language": "en",
            "context": {
                "scale": 4,
                "original_resolution": "128x128",
                "enhanced_resolution": "512x512",
                "latency_ms": 251.5,
                "metrics": {
                    "ssim": 0.9206,
                    "psnr_db": 24.22,
                    "sharpness_boost": "53.5x"
                }
            }
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["intent"], "explain_result")
        self.assertEqual(data["active_language"], "en")
        self.assertIn("512x512", data["response_markdown"])
        self.assertIn("0.9206", data["response_markdown"])
        print(f"[TEST PASSED] Chatbot English context query responded in {data['latency_ms']}ms.")

    def test_12_chat_telugu_query(self):
        """Verify Telugu chat query auto-detection and response."""
        payload = {
            "message": "ఈ ఫలితాన్ని వివరించండి",
            "language": "auto"
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_language"], "te")
        self.assertEqual(data["active_language"], "te")
        self.assertIn("తెలుగు", data["response_markdown"])
        print(f"[TEST PASSED] Chatbot Telugu query verified (Lang: {data['active_language']}, Latency: {data['latency_ms']}ms).")

    def test_13_chat_hindi_query(self):
        """Verify Hindi chat query auto-detection and response."""
        payload = {
            "message": "अमेज़न कैटलॉग नियम क्या हैं?",
            "language": "auto"
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["detected_language"], "hi")
        self.assertEqual(data["intent"], "catalog_standards")
        self.assertIn("अमेज़न", data["response_markdown"])
        print(f"[TEST PASSED] Chatbot Hindi query verified (Intent: {data['intent']}, Latency: {data['latency_ms']}ms).")

    def test_14_chat_empty_query_validation(self):
        """Verify empty chat message returns 400 Bad Request."""
        response = self.client.post("/api/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode("utf-8"))
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        print("[TEST PASSED] Chatbot rejected empty message with HTTP 400.")


if __name__ == "__main__":
    unittest.main()
