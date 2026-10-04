import logging
from functools import lru_cache
from typing import List, Dict, Any

from qdrant_client.http import models as rest

from finshield.qdrant.client import get_qdrant_client
from finshield.config.settings import settings
from finshield.models.domain import InvestigationContext
from finshield.services.memory_builder import profile_vector

logger = logging.getLogger(__name__)


def _match(key: str, value: Any) -> rest.FieldCondition:
    return rest.FieldCondition(key=key, match=rest.MatchValue(value=value))


class FinancialMemoryService:
    def __init__(self):
        self.qdrant = get_qdrant_client()
        self.collection_name = settings.qdrant_collection_name

    def search_similar_cases_for_customer(self, context: InvestigationContext, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves the past customers whose profiles are closest to this one, with their loan outcomes.
        """
        fc = context.financial_context
        if not fc.profile:
            return []

        # A customer is never their own precedent
        query_filter = rest.Filter(must_not=[_match("customer_id", fc.customer_id)])
        # If the current customer has fraud, compare only against past customers who ALSO had fraud
        if fc.has_prior_fraud_flags:
            query_filter.must = [_match("has_prior_fraud_flags", True)]

        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=profile_vector(fc.profile),
            query_filter=query_filter,
            limit=limit,
        )

        return [
            {
                "case_id": hit.payload.get("case_id"),
                # Euclidean distance -> (0, 1], higher is more similar
                "similarity_score": 1.0 / (1.0 + hit.score),
                "defaulted": bool(hit.payload.get("defaulted")),
                "metadata": hit.payload,
                "case_summary": hit.payload.get("text", ""),
            }
            for hit in response.points
        ]

    def portfolio_default_rate(self) -> float:
        return _portfolio_default_rate(self.collection_name)


@lru_cache(maxsize=4)
def _portfolio_default_rate(collection_name: str) -> float:
    client = get_qdrant_client()
    total = client.count(collection_name, exact=True).count
    defaulted = client.count(collection_name, count_filter=rest.Filter(must=[_match("defaulted", True)]), exact=True).count
    return defaulted / total if total else 0.0
