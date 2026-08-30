import pytest
import uuid
from unittest.mock import MagicMock, patch

from finshield.models.domain import InvestigationContext, CustomerFinancialContext
from finshield.models.workflow import InvestigationState, ExecutionStatus
from finshield.orchestration.lyzr_workflow import (
    _ACTIVE_STATES,
    _analyze_profile,
    _analyze_credit,
    _analyze_transactions,
    _analyze_fraud,
    _retrieve_historical_cases,
    _synthesize_risk_decision,
    FinShieldOrchestrator
)

@pytest.fixture
def mock_investigation_state():
    context = InvestigationContext(
        investigation_id="TEST-INV-001",
        financial_context=CustomerFinancialContext(
            customer_id="FIN_TEST_1",
            total_exposure=50000,
            has_prior_fraud_flags=False
        )
    )
    state = InvestigationState(investigation_id=context.investigation_id, context=context)
    # Register the state globally for tests
    _ACTIVE_STATES[state.investigation_id] = state
    yield state
    # Cleanup
    if state.investigation_id in _ACTIVE_STATES:
        del _ACTIVE_STATES[state.investigation_id]

@patch("finshield.agents.customer.CustomerProfileAgent.analyze")
def test_analyze_profile_tool(mock_analyze, mock_investigation_state):
    mock_analyze.return_value = MagicMock()
    
    result = _analyze_profile(investigation_id=mock_investigation_state.investigation_id)
    
    assert "COMPLETED" in result
    assert mock_investigation_state.profile is not None
    assert mock_investigation_state.trace[-1].status == ExecutionStatus.COMPLETED
    assert mock_investigation_state.trace[-1].tool_name == "analyze_profile"

@patch("finshield.agents.credit.CreditRiskAgent.analyze")
def test_analyze_credit_tool_fails_without_profile(mock_analyze, mock_investigation_state):
    # Ensure profile is missing
    mock_investigation_state.profile = None
    
    result = _analyze_credit(investigation_id=mock_investigation_state.investigation_id)
    
    assert "FAILED" in result
    assert mock_investigation_state.credit is None
    assert mock_investigation_state.trace[-1].status == ExecutionStatus.FAILED
    assert mock_investigation_state.trace[-1].tool_name == "analyze_credit"

@patch("lyzr.Studio")
def test_orchestrator_initialization(mock_studio):
    orchestrator = FinShieldOrchestrator()
    assert len(orchestrator.tools) == 6
    assert mock_studio.called

@patch("lyzr.Studio")
@patch("finshield.orchestration.lyzr_workflow.asyncio")
def test_run_investigation_workflow(mock_asyncio, mock_studio, mock_investigation_state):
    # Setup mock agent
    mock_agent = MagicMock()
    mock_studio.return_value.agents.create.return_value = mock_agent
    mock_asyncio.run.return_value = MagicMock(response="Agent completed workflow")
    
    orchestrator = FinShieldOrchestrator()
    orchestrator.studio = mock_studio.return_value
    
    final_state = orchestrator.run_investigation_workflow(mock_investigation_state)
    
    # Verify that the agent was created with the correct instructions
    mock_studio.return_value.agents.create.assert_called_once()
    # add_tool is called once per tool (6 times)
    assert mock_agent.add_tool.call_count == 6
    mock_asyncio.run.assert_called_once()
    
    # State should still be accessible
    assert final_state.investigation_id == "TEST-INV-001"

