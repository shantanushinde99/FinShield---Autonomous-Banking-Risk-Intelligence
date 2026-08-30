import logging
from finshield.models.domain import InvestigationContext
from finshield.models.agents import HistoricalCaseAssessment, HistoricalCaseItem
from finshield.services.retrieval import FinancialMemoryService

logger = logging.getLogger(__name__)

class HistoricalCaseRetrievalAgent:
    """
    Wraps the Phase 3 Qdrant Retrieval Service to format semantic historical similarities into evidence.
    """
    
    def __init__(self):
        # We instantiate the service once per agent, which handles Qdrant connectivity.
        self.memory_service = FinancialMemoryService()
        
    def analyze(self, context: InvestigationContext) -> HistoricalCaseAssessment:
        similar_cases = []
        explanation = "Semantic retrieval complete."
        
        try:
            # Query top 5 similar cases based on the customer's financial profile
            results = self.memory_service.search_similar_cases_for_customer(context, limit=5)
            
            for res in results:
                similar_cases.append(HistoricalCaseItem(
                    case_id=res["case_id"],
                    similarity_score=res["similarity_score"],
                    risk_level=res["risk_level"],
                    case_summary=res["case_summary"].strip()
                ))
                
            if not similar_cases:
                explanation = "No sufficiently similar historical cases were found in the memory cluster."
                
        except Exception as e:
            logger.error(f"Failed to retrieve historical cases: {e}")
            explanation = f"Failed to connect to Qdrant memory cluster: {e}"
            
        return HistoricalCaseAssessment(
            investigation_id=context.investigation_id,
            customer_id=context.financial_context.customer_id,
            query_summary="Financial similarity search based on profile and transaction behavior",
            similar_cases=similar_cases,
            explanation=explanation
        )
