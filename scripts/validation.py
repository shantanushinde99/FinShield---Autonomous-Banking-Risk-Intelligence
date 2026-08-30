import json
import sys
from finshield.services.investigation import InvestigationContextService
from finshield.exceptions import CustomerNotFoundError

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    customer_id = "FIN_000001"
    print(f"Running Validation Scenario for Customer: {customer_id}")
    print("="*60)
    
    try:
        context = InvestigationContextService.build_context(customer_id)
        # Using Pydantic's json() to format it nicely
        output = context.model_dump_json(indent=2)
        print(output)
    except CustomerNotFoundError:
        print(f"Error: Customer {customer_id} not found in database.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    print("="*60)
    print("Validation Scenario Complete")

if __name__ == "__main__":
    main()
