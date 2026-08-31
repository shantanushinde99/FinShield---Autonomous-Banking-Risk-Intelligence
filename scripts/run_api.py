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
    
    # --- AZURE BLOB STORAGE FIX ---
    # We download the database directly from Azure Blob Storage into the container's local memory (/tmp).
    # This prevents any SMB locking issues and ensures lightning-fast performance.
    download_url = os.environ.get("DUCKDB_DOWNLOAD_URL", "")
    if download_url:
        import urllib.request
        print("Detected DUCKDB_DOWNLOAD_URL! Downloading database from Azure Blob Storage...")
        tmp_path = "/tmp/finshield.duckdb"
        try:
            # We use urlretrieve for an efficient streaming download
            urllib.request.urlretrieve(download_url, tmp_path)
            os.environ["DUCKDB_PATH"] = tmp_path
            print(f"✅ Database successfully downloaded to {tmp_path}!")
        except Exception as e:
            print(f"❌ Error downloading database: {e}")
    # -----------------------------
    
    uvicorn.run("finshield.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
