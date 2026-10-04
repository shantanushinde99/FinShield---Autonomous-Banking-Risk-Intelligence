import logging
from finshield.models.domain import InvestigationContext
from finshield.models.agents import HistoricalCaseAssessment, HistoricalCaseItem
from finshield.services.retrieval import FinancialMemoryService

logger = logging.getLogger(__name__)

class HistoricalCaseRetrievalAgent:
    """
    Retrieves the most similar past customers from Qdrant and reports how often they defaulted.
    """
    # Neighbours used for the default rate; 5 alone is too few against an ~8% base rate
    NEIGHBOURS = 50
    SHOWN_CASES = 5

    def analyze(self, context: InvestigationContext) -> HistoricalCaseAssessment:
        similar_cases = []
        common_patterns = []
        similar_rate = portfolio_rate = None
        explanation = "No sufficiently similar historical cases were found in the memory cluster."

        try:
            # Inside the try so missing Qdrant config degrades to an empty result
            service = FinancialMemoryService()
            results = service.search_similar_cases_for_customer(context, limit=self.NEIGHBOURS)

            similar_cases = [
                HistoricalCaseItem(
                    case_id=res["case_id"],
                    similarity_score=res["similarity_score"],
                    outcome="DEFAULTED" if res["defaulted"] else "REPAID",
                    case_summary=res["case_summary"].strip(),
                )
                for res in results[:self.SHOWN_CASES]
            ]

            if results:
                defaults = sum(res["defaulted"] for res in results)
                similar_rate = defaults / len(results)
                portfolio_rate = service.portfolio_default_rate()
                common_patterns.append(
                    f"{defaults} of the {len(results)} most similar past customers defaulted "
                    f"({similar_rate:.0%} vs {portfolio_rate:.0%} portfolio average)"
                )
                explanation = "Similarity search over past customers' profiles with known loan outcomes."

        except Exception as e:
            logger.error(f"Failed to retrieve historical cases: {e}")
            explanation = f"Failed to connect to Qdrant memory cluster: {e}"

        return HistoricalCaseAssessment(
            investigation_id=context.investigation_id,
            customer_id=context.financial_context.customer_id,
            query_summary="Nearest past customers by credit, repayment and income profile",
            similar_cases=similar_cases,
            similar_default_rate=similar_rate,
            portfolio_default_rate=portfolio_rate,
            common_patterns=common_patterns,
            explanation=explanation,
        )
