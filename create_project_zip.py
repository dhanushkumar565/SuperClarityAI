"""
Script to package the entire SupplierClarity AI project into a single, clean zip file.
Excludes __pycache__ and temporary files.
"""

import os
import zipfile
import time

SOURCE_DIR = os.path.abspath(".")
TARGET_ZIP = os.path.abspath(os.path.join("..", "SupplierClarity_AI_Complete_Project.zip"))

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo"}
EXCLUDE_FILES = {"test_chrome.png", "test.pdf"}

print(f"Creating zip file from: {SOURCE_DIR}")
print(f"Destination: {TARGET_ZIP}")

start_time = time.time()
file_count = 0
total_uncompressed_bytes = 0

with zipfile.ZipFile(TARGET_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            # Check exclusions
            if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
            if file.endswith(".zip"):
                continue

            full_path = os.path.join(root, file)
            # Create archive path with project folder root name 'SupplierClarity_AI'
            rel_path = os.path.relpath(full_path, SOURCE_DIR)
            arcname = os.path.join("SupplierClarity_AI", rel_path)

            file_size = os.path.getsize(full_path)
            total_uncompressed_bytes += file_size
            file_count += 1

            zipf.write(full_path, arcname)

elapsed = round(time.time() - start_time, 2)
zip_size_mb = round(os.path.getsize(TARGET_ZIP) / (1024 * 1024), 2)
uncompressed_mb = round(total_uncompressed_bytes / (1024 * 1024), 2)

print(f"\n[ZIP CREATION COMPLETE]")
print(f"Packaged {file_count} files in {elapsed} seconds.")
print(f"Uncompressed: {uncompressed_mb} MB -> Compressed: {zip_size_mb} MB")
print(f"Zip File Location: {TARGET_ZIP}")
