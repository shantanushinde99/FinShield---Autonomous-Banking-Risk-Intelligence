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
    
    uvicorn.run("finshield.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
