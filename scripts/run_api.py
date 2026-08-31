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
    
    # --- AZURE APP SERVICE FIX ---
    # DuckDB crashes with "Device or resource busy" if run directly from Azure's /home (SMB share).
    # We copy the database to the local container storage (/tmp) before starting the server.
    duckdb_path = os.environ.get("DUCKDB_PATH", "")
    if duckdb_path.startswith("/home/") and duckdb_path.endswith(".duckdb"):
        import shutil
        print(f"Detected DuckDB on Azure SMB share: {duckdb_path}")
        tmp_path = f"/tmp/{os.path.basename(duckdb_path)}"
        print(f"Copying to local container storage: {tmp_path} (to prevent file lock errors)")
        try:
            shutil.copy2(duckdb_path, tmp_path)
            os.environ["DUCKDB_PATH"] = tmp_path
            print("Database successfully copied to local storage!")
        except Exception as e:
            print(f"Warning: Failed to copy database to /tmp: {e}")
            print("DEBUG: Contents of /home/data:")
            try:
                print(os.listdir("/home/data"))
            except Exception as ls_e:
                print(f"Could not list /home/data: {ls_e}")
    # -----------------------------
    
    uvicorn.run("finshield.api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
