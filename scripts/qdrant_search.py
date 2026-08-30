import argparse
import sys
import json
from finshield.services.retrieval import FinancialMemoryService

def main():
    parser = argparse.ArgumentParser(description="Search Qdrant Semantic Memory")
    parser.add_argument("--query", type=str, required=True, help="Text to search for")
    parser.add_argument("--limit", type=int, default=5, help="Number of results")
    args = parser.parse_args()
    
    # Ensuring UTF-8 output to avoid powershell redirection issues
    sys.stdout.reconfigure(encoding='utf-8')
    
    print(f"Executing semantic search...\nQuery: '{args.query}'\n")
    
    service = FinancialMemoryService()
    results = service.search_similar_cases(query_text=args.query, limit=args.limit)
    
    if not results:
        print("No results found or error occurred.")
        sys.exit(0)
        
    print(f"Found {len(results)} relevant historical cases:\n")
    print("="*60)
    for i, res in enumerate(results):
        print(f"Result {i+1} [Similarity Score: {res['similarity_score']:.4f}]")
        print(f"Case ID: {res['case_id']}")
        print(f"Risk Level: {res['risk_level']}")
        print(f"Transaction Count: {res['metadata'].get('transaction_count')}")
        print(f"Outstanding Debt: ₹{res['metadata'].get('outstanding_debt', 0.0):,.2f}")
        print("\nCase Summary Snippet:")
        print(res['case_summary'].strip())
        print("="*60)

if __name__ == "__main__":
    main()
