import uvicorn
import sys
import os

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    print("Starting FinShield API Server...")
    
    # Auto-reload is a dev convenience; it doubles processes and watches files in production
    reload = os.environ.get("APP_ENV", "development") != "production"
    uvicorn.run("finshield.api.main:app", host="0.0.0.0", port=8000, reload=reload)

if __name__ == "__main__":
    main()
