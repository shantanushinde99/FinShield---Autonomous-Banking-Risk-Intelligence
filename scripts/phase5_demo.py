import argparse
import logging
import sys
import os

# Ensure the root of the project is in the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure python-dotenv
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Suppress noisy logs from httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from finshield.services.investigation import InvestigationWorkflowService

def main():
    parser = argparse.ArgumentParser(description="FinShield Lyzr Multi-Agent Orchestration Demo")
    parser.add_argument("--customer", type=str, default="FIN_000001", help="Customer ID to investigate")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"FINSHIELD - PHASE 5: LYZR ORCHESTRATION DEMO")
    print(f"Investigating Customer: {args.customer}")
    print(f"{'='*60}\n")
    
    workflow_service = InvestigationWorkflowService()
    
    # 1. Run investigation
    print("[*] Starting multi-agent investigation orchestrated by Lyzr...")
    try:
        final_state = workflow_service.run_investigation(args.customer)
    except Exception as e:
        print(f"\n[!] Investigation failed: {e}")
        return

    # 2. Print Execution Trace
    print(f"\n{'-'*60}")
    print(f"EXECUTION TRACE")
    print(f"{'-'*60}")
    
    for step in final_state.trace:
        duration = f"{step.duration_ms:.2f}ms" if step.duration_ms else "N/A"
        print(f"[{step.status.value}] {step.tool_name:<30} | Time: {duration}")
        if step.error:
            print(f"    Error: {step.error}")
            
    # 3. Final Result
    print(f"\n{'-'*60}")
    print(f"FINAL RISK SYNTHESIS")
    print(f"{'-'*60}")
    
    if final_state.final_decision:
        print(f"Customer ID    : {final_state.final_decision.customer_id}")
        print(f"Risk Score     : {final_state.final_decision.risk_score:.2f}")
        print(f"Risk Level     : {final_state.final_decision.risk_level}")
        print(f"Confidence     : {final_state.final_decision.confidence}")
        print(f"Recommendation : {final_state.final_decision.recommendation}")
        print(f"\nExplanation:\n{final_state.final_decision.explanation}")
    else:
        print("No final decision was synthesized due to workflow failure.")
        
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
