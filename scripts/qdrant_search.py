import argparse
import sys
from finshield.services.investigation import InvestigationContextService
from finshield.services.retrieval import FinancialMemoryService

def main():
    parser = argparse.ArgumentParser(description="Find the past customers most similar to a customer")
    parser.add_argument("--customer-id", type=str, required=True, help="e.g. FIN_000001")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    args = parser.parse_args()

    # Ensuring UTF-8 output to avoid powershell redirection issues
    sys.stdout.reconfigure(encoding='utf-8')

    context = InvestigationContextService.build_context(args.customer_id)
    service = FinancialMemoryService()
    results = service.search_similar_cases_for_customer(context, limit=args.limit)

    if not results:
        print("No results found.")
        sys.exit(0)

    defaults = sum(r["defaulted"] for r in results)
    print(f"{defaults} of {len(results)} similar past customers defaulted "
          f"(portfolio average {service.portfolio_default_rate():.1%})\n")
    print("="*60)
    for i, res in enumerate(results):
        print(f"Result {i+1} [Similarity: {res['similarity_score']:.4f}]")
        print(f"Case ID: {res['case_id']}  Outcome: {'DEFAULTED' if res['defaulted'] else 'REPAID'}")
        print(res['case_summary'].strip())
        print("="*60)

if __name__ == "__main__":
    main()
