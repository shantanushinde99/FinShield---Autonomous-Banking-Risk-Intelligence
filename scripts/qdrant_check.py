import sys
from finshield.qdrant.client import get_qdrant_client
from finshield.config.settings import settings

def main():
    print("Checking Qdrant Configuration...")
    try:
        client = get_qdrant_client()
        name = settings.qdrant_collection_name

        if not client.collection_exists(name):
            print(f"Collection '{name}' does not exist. Run scripts/qdrant_ingest.py to create and fill it.")
            sys.exit(1)

        info = client.get_collection(name)
        print(f"Collection '{name}': {client.count(name, exact=True).count} points")
        print(f"Vector configuration: {info.config.params.vectors}")
        print(f"Payload indexes: {sorted(info.payload_schema)}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
