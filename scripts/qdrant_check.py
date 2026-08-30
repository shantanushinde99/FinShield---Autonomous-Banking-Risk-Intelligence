import sys
from qdrant_client.http import models as rest
from finshield.qdrant.client import get_qdrant_client, QdrantConnectionError
from finshield.config.settings import settings

def main():
    print("Checking Qdrant Configuration...")
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        name = settings.qdrant_collection_name
        
        if name in collection_names:
            print(f"Collection '{name}' already exists.")
            info = client.get_collection(name)
            print(f"Vector configuration: {info.config.params.vectors}")
        else:
            print(f"Collection '{name}' does not exist. Creating it now...")
            # Mistral embeddings are 1024 dimensions, cosine distance
            client.create_collection(
                collection_name=name,
                vectors_config=rest.VectorParams(
                    size=1024, 
                    distance=rest.Distance.COSINE
                )
            )
            print(f"Created collection '{name}'.")
            
            # Create payload indexes
            print("Creating payload indexes...")
            client.create_payload_index(name, field_name="memory_type", field_schema="keyword")
            client.create_payload_index(name, field_name="risk_level", field_schema="keyword")
            client.create_payload_index(name, field_name="customer_id", field_schema="keyword")
            client.create_payload_index(name, field_name="case_id", field_schema="keyword")
            print("Payload indexes created successfully.")
            
        print("\nQdrant check complete. Ready for ingestion.")
            
    except QdrantConnectionError as e:
        print(f"Connection Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
