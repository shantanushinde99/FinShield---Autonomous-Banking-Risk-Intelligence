"""
Builds the Qdrant case memory: one point per past customer, holding a normalized
profile vector and the real loan outcome (Home Credit TARGET), so an investigation
can ask "how often did customers like this one default?".

Idempotent: point IDs are derived from case IDs, so re-running upserts in place.
"""
import argparse
import sys
import uuid
from pathlib import Path

from qdrant_client.http import models as rest

from finshield.qdrant.client import get_qdrant_client
from finshield.config.settings import settings
from finshield.database.connection import get_duckdb_connection
from finshield.models.domain import CustomerFinancialContext, CustomerProfile, TransactionProfile
from finshield.services.investigation import InvestigationContextService
from finshield.services.memory_builder import MemoryDocumentBuilder, PROFILE_FEATURES, profile_vector

TRAIN_CSV = Path(__file__).resolve().parent.parent / "finshield/data/raw/home_credit/application_train.csv"


def load_cases(limit=None):
    """Bulk-loads every case with its profile, transaction summary and real outcome."""
    with get_duckdb_connection() as con:
        def rows(sql):
            result = con.execute(sql).fetchall()
            cols = [desc[0] for desc in con.description]
            return [dict(zip(cols, r)) for r in result]

        profiles = {r["finshield_customer_id"]: CustomerProfile(**r)
                    for r in rows("SELECT * FROM finshield_customer_profiles")}
        transactions = {r.pop("finshield_customer_id"): TransactionProfile(**r)
                        for r in rows("""SELECT c.finshield_customer_id, t.* FROM finshield_customers c
                                         JOIN transaction_profiles t ON t.account_id = c.account_id""")}
        cases = rows(f"""SELECT fc.case_id, fc.finshield_customer_id, a.TARGET = 1 AS defaulted
                         FROM financial_cases fc
                         JOIN finshield_customers c USING (finshield_customer_id)
                         JOIN read_csv_auto('{TRAIN_CSV}') a ON a.SK_ID_CURR = c.SK_ID_CURR
                         ORDER BY fc.case_id {f'LIMIT {int(limit)}' if limit else ''}""")

    for case in cases:
        customer_id = case["finshield_customer_id"]
        if customer_id not in profiles:
            continue  # nothing to compare on
        t_summary = transactions.get(customer_id)
        fc = CustomerFinancialContext(
            customer_id=customer_id,
            profile=profiles[customer_id],
            transaction_summary=t_summary,
            has_prior_fraud_flags=InvestigationContextService.has_fraud_flags(t_summary),
        )
        yield case["case_id"], fc, bool(case["defaulted"])


def ensure_collection(client, name: str):
    size = len(PROFILE_FEATURES)
    if client.collection_exists(name):
        existing = client.get_collection(name).config.params.vectors.size
        if existing != size:
            sys.exit(f"Collection '{name}' has vector size {existing}, expected {size}. "
                     f"Delete it or set QDRANT_COLLECTION_NAME to a new name.")
        return
    print(f"Creating collection '{name}' ({size}-d, Euclidean)...")
    client.create_collection(name, vectors_config=rest.VectorParams(size=size, distance=rest.Distance.EUCLID))
    # Indexed because every search filters on these
    client.create_payload_index(name, field_name="customer_id", field_schema="keyword")
    client.create_payload_index(name, field_name="has_prior_fraud_flags", field_schema="bool")
    client.create_payload_index(name, field_name="defaulted", field_schema="bool")


def main():
    parser = argparse.ArgumentParser(description="Ingest past customers into the Qdrant case memory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases (sample mode)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Points per upsert request")
    args = parser.parse_args()

    name = settings.qdrant_collection_name
    print(f"Starting Qdrant ingestion into '{name}'")
    client = get_qdrant_client()
    ensure_collection(client, name)

    batch, total = [], 0
    for case_id, fc, defaulted in load_cases(args.limit):
        _, payload = MemoryDocumentBuilder.build_case_document(fc, case_id, defaulted)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"historical_financial_case_{case_id}"))
        batch.append(rest.PointStruct(id=point_id, vector=profile_vector(fc.profile), payload=payload))
        if len(batch) >= args.batch_size:
            client.upsert(collection_name=name, points=batch)
            total += len(batch)
            print(f"  upserted {total}")
            batch = []
    if batch:
        client.upsert(collection_name=name, points=batch)
        total += len(batch)

    print(f"\nIngestion complete: {total} points in '{name}' "
          f"(collection now holds {client.count(name, exact=True).count}).")


if __name__ == "__main__":
    main()
