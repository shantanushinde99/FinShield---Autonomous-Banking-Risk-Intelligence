import logging
import asyncio
from typing import Dict
import lyzr
from lyzr import Tool

from finshield.models.workflow import InvestigationState, ExecutionStatus
from finshield.agents.customer import CustomerProfileAgent
from finshield.agents.credit import CreditRiskAgent
from finshield.agents.transaction import TransactionAnalysisAgent
from finshield.agents.fraud import FraudDetectionAgent
from finshield.agents.historical import HistoricalCaseRetrievalAgent
from finshield.agents.decision import RiskDecisionAgent

logger = logging.getLogger(__name__)

# Global registry for active workflows to allow tool wrappers to access state
_ACTIVE_STATES: Dict[str, InvestigationState] = {}

def get_state(investigation_id: str) -> InvestigationState:
    if investigation_id not in _ACTIVE_STATES:
        raise ValueError(f"Unknown investigation ID: {investigation_id}")
    return _ACTIVE_STATES[investigation_id]

def _analyze_profile(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("analyze_profile")
    try:
        agent = CustomerProfileAgent()
        state.profile = agent.analyze(state.context)
        state.log_tool_end("analyze_profile", ExecutionStatus.COMPLETED)
        return "Customer Profile Analysis COMPLETED successfully. Proceed to Credit and Transaction analysis."
    except Exception as e:
        state.log_tool_end("analyze_profile", ExecutionStatus.FAILED, str(e))
        return f"Customer Profile Analysis FAILED: {str(e)}"

def _analyze_credit(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("analyze_credit")
    try:
        if state.profile is None:
            state.log_tool_end("analyze_credit", ExecutionStatus.FAILED, "Missing Profile analysis")
            return "FAILED: Profile analysis must be completed before Credit analysis."
        agent = CreditRiskAgent()
        state.credit = agent.analyze(state.context)
        state.log_tool_end("analyze_credit", ExecutionStatus.COMPLETED)
        return "Credit Risk Analysis COMPLETED successfully."
    except Exception as e:
        state.log_tool_end("analyze_credit", ExecutionStatus.FAILED, str(e))
        return f"Credit Risk Analysis FAILED: {str(e)}"

def _analyze_transactions(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("analyze_transactions")
    try:
        if state.profile is None:
            state.log_tool_end("analyze_transactions", ExecutionStatus.FAILED, "Missing Profile analysis")
            return "FAILED: Profile analysis must be completed before Transaction analysis."
        agent = TransactionAnalysisAgent()
        state.transactions = agent.analyze(state.context)
        state.log_tool_end("analyze_transactions", ExecutionStatus.COMPLETED)
        return "Transaction Analysis COMPLETED successfully."
    except Exception as e:
        state.log_tool_end("analyze_transactions", ExecutionStatus.FAILED, str(e))
        return f"Transaction Analysis FAILED: {str(e)}"

def _analyze_fraud(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("analyze_fraud")
    try:
        if not (state.profile and state.credit and state.transactions):
            state.log_tool_end("analyze_fraud", ExecutionStatus.FAILED, "Missing dependencies")
            return "FAILED: Profile, Credit, and Transaction analysis must be completed before Fraud analysis."
        agent = FraudDetectionAgent()
        state.fraud = agent.analyze(state.context)
        state.log_tool_end("analyze_fraud", ExecutionStatus.COMPLETED)
        return "Fraud Detection Analysis COMPLETED successfully."
    except Exception as e:
        state.log_tool_end("analyze_fraud", ExecutionStatus.FAILED, str(e))
        return f"Fraud Detection Analysis FAILED: {str(e)}"

def _retrieve_historical_cases(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("retrieve_historical_cases")
    try:
        agent = HistoricalCaseRetrievalAgent()
        state.historical = agent.analyze(state.context)
        state.log_tool_end("retrieve_historical_cases", ExecutionStatus.COMPLETED)
        return "Historical Cases Retrieval COMPLETED successfully."
    except Exception as e:
        state.log_tool_end("retrieve_historical_cases", ExecutionStatus.FAILED, str(e))
        return f"Historical Cases Retrieval FAILED: {str(e)}"

def _synthesize_risk_decision(investigation_id: str) -> str:
    state = get_state(investigation_id)
    state.log_tool_start("synthesize_risk_decision")
    try:
        if not (state.profile and state.credit and state.transactions and state.fraud and state.historical):
            state.log_tool_end("synthesize_risk_decision", ExecutionStatus.FAILED, "Missing dependencies")
            return "FAILED: All previous analysis steps (profile, credit, transactions, fraud, historical) must be completed."
        agent = RiskDecisionAgent()
        state.final_decision = agent.analyze(
            state.context,
            state.profile,
            state.credit,
            state.transactions,
            state.fraud,
            state.historical
        )
        state.log_tool_end("synthesize_risk_decision", ExecutionStatus.COMPLETED)
        return "Final Risk Decision Synthesized successfully. The investigation is complete."
    except Exception as e:
        state.log_tool_end("synthesize_risk_decision", ExecutionStatus.FAILED, str(e))
        return f"Final Risk Decision FAILED: {str(e)}"


# Define parameters schema for all tools
ID_PARAMS = {
    "type": "object",
    "properties": {
        "investigation_id": {
            "type": "string",
            "description": "The investigation ID to process."
        }
    },
    "required": ["investigation_id"]
}

# Create Tool objects manually
analyze_profile = Tool(
    name="analyze_profile",
    description="Analyze customer profile for basic eligibility and stability. Must run first.",
    parameters=ID_PARAMS,
    function=_analyze_profile
)

analyze_credit = Tool(
    name="analyze_credit",
    description="Analyze credit risk, debt-to-income, and repayment history.",
    parameters=ID_PARAMS,
    function=_analyze_credit
)

analyze_transactions = Tool(
    name="analyze_transactions",
    description="Analyze recent transactions for volume, frequency, and patterns.",
    parameters=ID_PARAMS,
    function=_analyze_transactions
)

analyze_fraud = Tool(
    name="analyze_fraud",
    description="Analyze for fraud indicators. Requires Profile, Credit, and Transaction analysis to be completed first.",
    parameters=ID_PARAMS,
    function=_analyze_fraud
)

retrieve_historical_cases = Tool(
    name="retrieve_historical_cases",
    description="Retrieve similar historical financial cases from Qdrant memory.",
    parameters=ID_PARAMS,
    function=_retrieve_historical_cases
)

synthesize_risk_decision = Tool(
    name="synthesize_risk_decision",
    description="Synthesize all evidence into a final risk decision. Must run LAST.",
    parameters=ID_PARAMS,
    function=_synthesize_risk_decision
)

class FinShieldOrchestrator:
    """
    Manages the multi-agent orchestration layer using Lyzr ADK.
    """
    def __init__(self):
        # Assumes LYZR_API_KEY is loaded in environment
        self.studio = lyzr.Studio()
        self.tools = [
            analyze_profile,
            analyze_credit,
            analyze_transactions,
            analyze_fraud,
            retrieve_historical_cases,
            synthesize_risk_decision
        ]
        
    def run_investigation_workflow(self, state: InvestigationState) -> InvestigationState:
        # Register the state for tool access
        _ACTIVE_STATES[state.investigation_id] = state
        
        system_prompt = (
            "You are the FinShield Autonomous Orchestrator Agent.\n"
            "Your task is to execute a strict banking risk investigation DAG.\n"
            "You MUST call the following tools sequentially in this exact order:\n"
            "1. analyze_profile\n"
            "2. analyze_credit\n"
            "3. analyze_transactions\n"
            "4. analyze_fraud\n"
            "5. retrieve_historical_cases\n"
            "6. synthesize_risk_decision\n\n"
            "Pass the provided investigation_id to each tool.\n"
            "Do NOT skip any tools. Wait for each tool to finish and return a success message before running the next.\n"
            "If any tool fails, STOP the investigation and report the failure.\n"
        )
        
        try:
            agent = self.studio.agents.create(
                name="FinShield_Orchestrator",
                provider="openai/gpt-4o",
                role="Autonomous Banking Risk Orchestrator",
                goal="Execute the banking risk investigation DAG strictly in order.",
                instructions=system_prompt,
            )
            
            for t in self.tools:
                agent.add_tool(t)
            
            prompt = f"Please run the full investigation workflow for investigation_id: {state.investigation_id}"
            logger.info(f"Starting Lyzr Orchestrator Agent Workflow for {state.investigation_id}...")
            
            response = asyncio.run(agent.run_with_local_tools(prompt))
            logger.info(f"Orchestrator finished: {response.response}")
            
        except Exception as e:
            logger.error(f"Orchestrator workflow failed: {e}")
        finally:
            # Clean up the state registry
            if state.investigation_id in _ACTIVE_STATES:
                del _ACTIVE_STATES[state.investigation_id]
                
        return state
