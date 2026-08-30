import argparse
import sys
import uuid
from typing import List
from qdrant_client.http import models as rest
from finshield.qdrant.client import get_qdrant_client
from finshield.config.settings import settings
from finshield.database.connection import get_duckdb_connection
from finshield.services.investigation import InvestigationContextService
from finshield.services.memory_builder import MemoryDocumentBuilder
from finshield.services.embedding import MistralEmbeddingService
from finshield.models.domain import FinancialCase

def get_historical_cases(limit: int = None) -> List[FinancialCase]:
    with get_duckdb_connection() as con:
        query = "SELECT * FROM financial_cases"
        if limit:
            query += f" LIMIT {limit}"
        
        results = con.execute(query).fetchall()
        cols = [desc[0] for desc in con.description]
        return [FinancialCase(**dict(zip(cols, row))) for row in results]

def main():
    parser = argparse.ArgumentParser(description="Ingest Financial Cases into Qdrant Memory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases (dry-run/sample mode)")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for embeddings")
    args = parser.parse_args()
    
    print("Starting Qdrant Ingestion Pipeline")
    print(f"Collection: {settings.qdrant_collection_name}")
    
    # 1. Fetch Cases
    print("Fetching historical cases from DuckDB...")
    cases = get_historical_cases(limit=args.limit)
    print(f"Found {len(cases)} cases to process.")
    
    if not cases:
        print("No cases found. Exiting.")
        sys.exit(0)
        
    client = get_qdrant_client()
    embedder = MistralEmbeddingService()
    
    success_count = 0
    fail_count = 0
    
    # Process in batches
    for i in range(0, len(cases), args.batch_size):
        batch_cases = cases[i:i+args.batch_size]
        print(f"Processing batch {i//args.batch_size + 1} ({len(batch_cases)} cases)...")
        
        texts = []
        payloads = []
        point_ids = []
        
        for case in batch_cases:
            try:
                # Deterministic ID for idempotency
                point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"historical_financial_case_{case.case_id}"))
                point_ids.append(point_id)
                
                context = InvestigationContextService.build_context(case.finshield_customer_id)
                text, payload = MemoryDocumentBuilder.build_case_document(context, case)
                
                texts.append(text)
                payloads.append(payload)
            except Exception as e:
                print(f"Error building document for Case ID {case.case_id}: {e}")
                fail_count += 1
                
        if not texts:
            continue
            
        try:
            print("  Generating embeddings...")
            vectors = embedder.embed_batch(texts)
            
            print("  Upserting to Qdrant...")
            points = [
                rest.PointStruct(id=p_id, vector=vec, payload=pld)
                for p_id, vec, pld in zip(point_ids, vectors, payloads)
            ]
            
            client.upsert(
                collection_name=settings.qdrant_collection_name,
                points=points
            )
            success_count += len(points)
        except Exception as e:
            print(f"Failed to ingest batch: {e}")
            fail_count += len(texts)
            
    print("\nIngestion Complete!")
    print(f"Successfully upserted: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()
