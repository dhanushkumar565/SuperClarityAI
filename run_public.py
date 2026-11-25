"""
SupplierClarity AI - Public Deployment via Ngrok
Reference: SmartBridge / Skill Wallet Project Workflow - Milestone 5: Deployment
Activity 5.3: Public Deployment via Ngrok
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import app


def run_with_ngrok(port: int = 5050):
    """
    Sets up an ngrok public tunnel and starts the Flask server.
    Matches Milestone 5 requirements from project reference.
    """
    token = os.environ.get("NGROK_AUTHTOKEN", "").strip()
    
    print("\n======================================================")
    print("  SupplierClarity AI: Deployment Manager")
    print("======================================================")
    
    tunnel_started = False
    public_url = None
    
    try:
        from pyngrok import ngrok, conf
        
        if token and token != "your_ngrok_authtoken_here":
            ngrok.set_auth_token(token)
            print(" -> Configured Ngrok authtoken from environment.")
        else:
            print(" -> Note: No NGROK_AUTHTOKEN found in .env.")
            print(" -> If Ngrok requires authentication, configure it in .env:")
            print("    NGROK_AUTHTOKEN=your_token_here")
            
        print(f" -> Opening public HTTP tunnel on port {port}...")
        http_tunnel = ngrok.connect(port, "http")
        public_url = http_tunnel.public_url
        tunnel_started = True
        
        print("\n======================================================")
        print("  YOUR PUBLIC WEBSITE URL IS LIVE!")
        print(f"  URL: {public_url}")
        print("======================================================\n")
        
    except Exception as e:
        print(f" -> Ngrok Tunnel notice: {str(e)}")
        print(" -> Proceeding with local network deployment at http://127.0.0.1:5050\n")

    print(f"Serving SupplierClarity AI on http://127.0.0.1:{port} (debug=False)\n")
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    finally:
        if tunnel_started:
            try:
                ngrok.kill()
            except Exception:
                pass


if __name__ == "__main__":
    run_with_ngrok(port=5050)
