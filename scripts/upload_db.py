import ftplib
import os
import sys

def main():
    print("========================================")
    print(" Azure FTPS Database Uploader")
    print("========================================")
    print("1. Go to Azure Portal -> Your Web App -> Deployment Center")
    print("2. Click the 'FTPS credentials' tab")
    print("========================================\n")
    
    import urllib.parse
    
    host_input = input("Enter FTPS Endpoint (e.g., ftps://waws-prod-...). Paste the full link: ").strip()
    
    # Parse the host safely regardless of what the user pastes
    if not host_input.startswith("ftps://") and not host_input.startswith("ftp://"):
        host_input = "ftps://" + host_input
        
    parsed_url = urllib.parse.urlparse(host_input)
    host = parsed_url.hostname or parsed_url.path.split('/')[0]
        
    user = input("Enter FTPS Username: ").strip()
    password = input("Enter FTPS Password: ").strip()
    
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'finshield', 'database', 'finshield.duckdb'))
    
    if not os.path.exists(db_path):
        print(f"\nERROR: Could not find database at {db_path}")
        print("Please make sure you are running this from the project root.")
        return

    file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"\nFound database: {file_size_mb:.2f} MB")
    print("Connecting to Azure FTPS server...\n")
    
    try:
        with ftplib.FTP_TLS(host) as ftp:
            ftp.login(user, password)
            # Secure data connection
            ftp.prot_p()
            
            # Navigate to the persistent data directory
            print("Connected! Navigating to /data ...")
            try:
                ftp.cwd("/data")
            except:
                ftp.mkd("/data")
                ftp.cwd("/data")

            print("Uploading finshield.duckdb (This may take 5-15 minutes depending on your internet upload speed)...")

            file_size_bytes = os.path.getsize(db_path)
            uploaded_bytes = 0

            def handle_block(block):
                nonlocal uploaded_bytes
                uploaded_bytes += len(block)
                percent = (uploaded_bytes / file_size_bytes) * 100
                sys.stdout.write(f"\rUpload Progress: {percent:.1f}%  ({uploaded_bytes // (1024*1024)} MB / {file_size_bytes // (1024*1024)} MB)")
                sys.stdout.flush()

            with open(db_path, "rb") as f:
                # Use a block size of 8192 for efficient uploading and pass our progress callback
                ftp.storbinary("STOR finshield.duckdb", f, blocksize=8192, callback=handle_block)
                
        print("\n\n✅ UPLOAD COMPLETE! The database is now safely on Azure!")
        print("Go to your Azure Configuration, ensure DUCKDB_PATH is set to '/home/data/finshield.duckdb', and you're done!")
        
    except Exception as e:
        print(f"\n❌ Error during upload: {e}")
        print("Please double check your credentials and make sure you copied them exactly without spaces.")

if __name__ == "__main__":
    main()
