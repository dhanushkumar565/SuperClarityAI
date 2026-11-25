"""
Test and capture headless Chrome screenshots of the Multilingual Voice-Enabled Chatbot
"""
import subprocess
import time
import os

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

os.makedirs("static/assets", exist_ok=True)
screenshot_path = os.path.abspath("static/assets/chatbot_live_preview.png")

# Use a small demo flag or execute script
print("Launching Chrome headless capture for Chatbot...")
cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--window-size=1600,1050",
    f"--screenshot={screenshot_path}",
    "http://127.0.0.1:5050"
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("Chrome return code:", res.returncode)
if os.path.exists(screenshot_path):
    print(f"Captured: {screenshot_path} ({os.path.getsize(screenshot_path)} bytes)")
else:
    print("Screenshot failed:", res.stderr)
