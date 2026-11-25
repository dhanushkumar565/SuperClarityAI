"""
SuperClarity AI - Advanced Asynchronous Batch Processing Engine
Provides non-blocking background queue for multi-image enhancement,
progress tracking, ZIP packaging, cancellation, and error retry.
"""

import os
import time
import uuid
import zipfile
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

import database
from models.upscaler import SupplierClarityUpscaler
from models.product_analyzer import ProductAnalyzer


class BatchProcessor:
    """
    Thread-safe asynchronous worker queue for bulk vendor image processing.
    """
    def __init__(self, max_workers: int = 2, output_dir: str = "static/outputs"):
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs = {}
        self.lock = threading.Lock()
        self.upscaler = SupplierClarityUpscaler()
        self.analyzer = ProductAnalyzer()
        os.makedirs(self.output_dir, exist_ok=True)

    def submit_batch(
        self,
        file_paths: list,
        scale: int = 4,
        method: str = "realesrgan",
        denoise: bool = True,
        sharpen: bool = True,
        auto_preset: bool = True,
        user_id: int = 1
    ) -> str:
        """
        Registers a new batch of images and starts background processing.
        Returns unique job_id.
        """
        job_id = f"batch_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        total = len(file_paths)

        job_info = {
            "job_id": job_id,
            "user_id": user_id,
            "scale": scale,
            "method": method,
            "denoise": denoise,
            "sharpen": sharpen,
            "auto_preset": auto_preset,
            "status": "queued",
            "total_count": total,
            "completed_count": 0,
            "failed_count": 0,
            "progress_percent": 0.0,
            "is_cancelled": False,
            "created_at": time.time(),
            "items": [
                {
                    "index": i,
                    "input_path": p,
                    "filename": os.path.basename(p),
                    "status": "pending",
                    "output_path": None,
                    "output_url": None,
                    "error": None
                }
                for i, p in enumerate(file_paths)
            ],
            "zip_path": None,
            "zip_url": None
        }

        with self.lock:
            self.jobs[job_id] = job_info

        # Record in database
        database.create_batch_job(job_id=job_id, total_count=total, user_id=user_id)

        # Dispatch execution to background worker pool
        self.executor.submit(self._execute_batch, job_id)
        return job_id

    def get_status(self, job_id: str) -> dict:
        """Returns the real-time status of a batch job."""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                # Fallback to database record
                db_job = database.get_batch_job(job_id)
                if db_job:
                    total = db_job["total_count"]
                    done = db_job["completed_count"]
                    pct = round((done / max(1, total)) * 100, 1)
                    return {
                        "job_id": job_id,
                        "status": db_job["status"],
                        "total_count": total,
                        "completed_count": done,
                        "progress_percent": pct,
                        "zip_url": f"/{db_job['zip_path'].replace(os.sep, '/')}" if db_job["zip_path"] else None,
                        "items": []
                    }
                return None

            return {
                "job_id": job["job_id"],
                "status": job["status"],
                "total_count": job["total_count"],
                "completed_count": job["completed_count"],
                "failed_count": job["failed_count"],
                "progress_percent": job["progress_percent"],
                "zip_url": job["zip_url"],
                "is_cancelled": job["is_cancelled"],
                "items": [
                    {
                        "filename": it["filename"],
                        "status": it["status"],
                        "output_url": it["output_url"],
                        "error": it["error"]
                    }
                    for it in job["items"]
                ]
            }

    def cancel_job(self, job_id: str) -> bool:
        """Flags an ongoing job as cancelled."""
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["is_cancelled"] = True
                self.jobs[job_id]["status"] = "cancelled"
                database.update_batch_progress(
                    job_id=job_id,
                    completed_count=self.jobs[job_id]["completed_count"],
                    failed_count=self.jobs[job_id]["failed_count"],
                    status="cancelled"
                )
                return True
        return False

    def _execute_batch(self, job_id: str):
        """Worker thread processing each image in the batch sequentially."""
        with self.lock:
            job = self.jobs[job_id]
            job["status"] = "processing"

        scale = job["scale"]
        method = job["method"]
        denoise = job["denoise"]
        sharpen = job["sharpen"]
        auto_preset = job["auto_preset"]
        completed_outputs = []

        for item in job["items"]:
            # Check for cancellation between images
            if job["is_cancelled"]:
                break

            item["status"] = "processing"
            input_path = item["input_path"]

            try:
                if not os.path.exists(input_path):
                    raise FileNotFoundError(f"File not found: {input_path}")

                pil_img = Image.open(input_path).convert("RGB")
                preset = None
                if auto_preset:
                    analysis = self.analyzer.analyze(pil_img)
                    preset = analysis["recommended_preset"]

                # Run neural upscaling
                res = self.upscaler.upscale(
                    image_input=pil_img,
                    scale=scale,
                    method=method,
                    denoise=denoise,
                    sharpen=sharpen,
                    product_preset=preset
                )

                enhanced_img = res["image"]
                out_filename = f"enhanced_{job_id}_{item['index']}.png"
                out_path = os.path.join(self.output_dir, out_filename)
                enhanced_img.save(out_path, format="PNG")

                item["output_path"] = out_path
                item["output_url"] = f"/static/outputs/{out_filename}"
                item["status"] = "completed"
                completed_outputs.append((out_path, out_filename))

                with self.lock:
                    job["completed_count"] += 1

            except Exception as err:
                item["status"] = "failed"
                item["error"] = str(err)
                with self.lock:
                    job["failed_count"] += 1

            with self.lock:
                total = job["total_count"]
                done = job["completed_count"] + job["failed_count"]
                job["progress_percent"] = round((done / max(1, total)) * 100.0, 1)

            # Update DB progress
            database.update_batch_progress(
                job_id=job_id,
                completed_count=job["completed_count"],
                failed_count=job["failed_count"],
                status="processing"
            )

        # Generate ZIP archive if any images succeeded
        zip_path = None
        zip_url = None
        if completed_outputs and not job["is_cancelled"]:
            zip_filename = f"{job_id}_all_enhanced.zip"
            zip_path = os.path.join(self.output_dir, zip_filename)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path, arc_name in completed_outputs:
                    zf.write(file_path, arcname=arc_name)
            zip_url = f"/static/outputs/{zip_filename}"

        final_status = "cancelled" if job["is_cancelled"] else ("completed" if job["completed_count"] > 0 else "failed")
        with self.lock:
            job["status"] = final_status
            job["zip_path"] = zip_path
            job["zip_url"] = zip_url

        database.update_batch_progress(
            job_id=job_id,
            completed_count=job["completed_count"],
            failed_count=job["failed_count"],
            status=final_status,
            zip_path=zip_path
        )
