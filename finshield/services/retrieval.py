import logging
from typing import List, Dict, Any
from finshield.qdrant.client import get_qdrant_client
from finshield.services.embedding import MistralEmbeddingService
from finshield.config.settings import settings
from finshield.models.domain import InvestigationContext
from finshield.services.memory_builder import MemoryDocumentBuilder

logger = logging.getLogger(__name__)

class FinancialMemoryService:
    def __init__(self):
        self.qdrant = get_qdrant_client()
        self.embedder = MistralEmbeddingService()
        self.collection_name = settings.qdrant_collection_name
        
    def search_similar_cases(self, query_text: str, limit: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Searches Qdrant for similar historical financial cases based on arbitrary text.
        """
        try:
            vector = self.embedder.embed_text(query_text)
            
            # Construct Qdrant filter if provided
            query_filter = None
            if filters:
                from qdrant_client.http import models as rest
                must_conditions = []
                for k, v in filters.items():
                    must_conditions.append(rest.FieldCondition(
                        key=k, 
                        match=rest.MatchValue(value=v)
                    ))
                query_filter = rest.Filter(must=must_conditions)
                
            response = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=vector,
                query_filter=query_filter,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for hit in response.points:
                formatted_results.append({
                    "case_id": hit.payload.get("case_id"),
                    "similarity_score": hit.score,
                    "risk_level": hit.payload.get("risk_level"),
                    "metadata": hit.payload,
                    "case_summary": hit.payload.get("text", "")[:500] + "..." # return prefix
                })
                
            return formatted_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def search_similar_cases_for_customer(self, context: InvestigationContext, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Builds a semantic query from the investigation context and retrieves similar historical cases.
        """
        query_text = MemoryDocumentBuilder.build_query_document(context)
        
        # Base filter to only search financial cases
        filters = {"memory_type": "historical_financial_case"}
        
        # If the current customer has fraud, force Qdrant to ONLY fetch historical cases that ALSO have fraud.
        if context.financial_context.has_prior_fraud_flags:
            filters["has_prior_fraud_flags"] = True
            
        return self.search_similar_cases(query_text, limit=limit, filters=filters)
