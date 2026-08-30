import sys
import json
from finshield.services.investigation import InvestigationContextService
from finshield.agents.customer import CustomerProfileAgent
from finshield.agents.credit import CreditRiskAgent
from finshield.agents.transaction import TransactionAnalysisAgent
from finshield.agents.fraud import FraudDetectionAgent
from finshield.agents.historical import HistoricalCaseRetrievalAgent
from finshield.agents.decision import RiskDecisionAgent

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    customer_id = "FIN_000001"
    
    print("==================================================")
    print("FINSHIELD RISK INVESTIGATION DEMO")
    print("==================================================")
    
    print(f"\n[1/7] Building Investigation Context for {customer_id}...")
    context = InvestigationContextService.build_context(customer_id)
    print(f"      Investigation ID: {context.investigation_id}")
    
    print(f"\n[2/7] Running Customer Profile Agent...")
    customer_agent = CustomerProfileAgent()
    profile_assessment = customer_agent.analyze(context)
    
    print(f"\n[3/7] Running Credit Risk Agent...")
    credit_agent = CreditRiskAgent()
    credit_assessment = credit_agent.analyze(context)
    
    print(f"\n[4/7] Running Transaction Analysis Agent...")
    transaction_agent = TransactionAnalysisAgent()
    transaction_assessment = transaction_agent.analyze(context)
    
    print(f"\n[5/7] Running Fraud Detection Agent...")
    fraud_agent = FraudDetectionAgent()
    fraud_assessment = fraud_agent.analyze(context)
    
    print(f"\n[6/7] Running Historical Case Retrieval Agent...")
    historical_agent = HistoricalCaseRetrievalAgent()
    historical_assessment = historical_agent.analyze(context)
    
    print(f"\n[7/7] Running Risk Decision Agent (Mistral LLM Synthesis)...")
    decision_agent = RiskDecisionAgent()
    final_decision = decision_agent.analyze(
        context=context,
        profile=profile_assessment,
        credit=credit_assessment,
        transaction=transaction_assessment,
        fraud=fraud_assessment,
        historical=historical_assessment
    )
    
    print("\n\n==================================================")
    print("FINAL INVESTIGATION REPORT")
    print("==================================================")
    print(f"Customer: {customer_id}")
    print(f"Investigation: {context.investigation_id}")
    print("\nPROFILE")
    print(f"Age: {profile_assessment.age}")
    print(f"Income: ₹{profile_assessment.total_income:,.2f}")
    
    print("\nCREDIT")
    print(f"Risk: {credit_assessment.risk_level}")
    for kf in credit_assessment.key_factors:
        print(f"- {kf}")
        
    print("\nTRANSACTIONS")
    print(f"Risk: {transaction_assessment.risk_level}")
    for kf in transaction_assessment.anomalies:
        print(f"- {kf}")
        
    print("\nFRAUD")
    print(f"Risk: {fraud_assessment.risk_level}")
    for kf in fraud_assessment.suspicious_patterns:
        print(f"- {kf}")
        
    print("\nHISTORICAL MEMORY")
    for i, c in enumerate(historical_assessment.similar_cases):
        print(f"{i+1}. {c.case_id} - similarity {c.similarity_score:.2f}")
        
    print("\nFINAL ASSESSMENT")
    print(f"Risk Level: {final_decision.risk_level}")
    print(f"Confidence: {final_decision.confidence}")
    print(f"Recommendation: {final_decision.recommendation}")
    
    print(f"\nWhy:")
    print(final_decision.explanation)
    print("==================================================")

if __name__ == "__main__":
    main()
