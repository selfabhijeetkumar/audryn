"""
LangGraph Smoke Test for AUDRYN
Verifies StateGraph creation, state passing, deterministic execution, and state return.
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class AuditState(TypedDict):
    audit_id: str
    stage: str
    reconciliation_balance: float
    verified: bool


def deterministic_audit_node(state: AuditState) -> AuditState:
    """Deterministic node verifying math without LLM hallucination."""
    balance = state.get("reconciliation_balance", 0.0)
    # Perform exact calculation
    is_balanced = abs(balance) < 0.001
    return {
        "audit_id": state["audit_id"],
        "stage": "deterministic_math_passed",
        "reconciliation_balance": balance,
        "verified": is_balanced
    }


def run_smoke_test():
    print("Testing LangGraph StateGraph initialization...")
    workflow = StateGraph(AuditState)
    workflow.add_node("verify_math", deterministic_audit_node)
    workflow.add_edge(START, "verify_math")
    workflow.add_edge("verify_math", END)

    app = workflow.compile()

    initial_state: AuditState = {
        "audit_id": "AUD-2026-TEST",
        "stage": "init",
        "reconciliation_balance": 0.0,
        "verified": False
    }

    result = app.invoke(initial_state)
    print(f"Execution result: {result}")
    assert result["verified"] is True, "Reconciliation verification failed!"
    assert result["stage"] == "deterministic_math_passed", "Unexpected stage transition!"
    print("SUCCESS: LangGraph StateGraph smoke test passed!")


if __name__ == "__main__":
    run_smoke_test()
