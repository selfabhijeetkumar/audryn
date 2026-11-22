"""
LangGraph Comprehensive Deterministic Execution Test for AUDRYN
Verifies:
1. State Initialization
2. Node Execution
3. Conditional Routing
4. Final State
5. Error Handling
"""
import sys
from decimal import Decimal
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class AuditWorkflowState(TypedDict):
    voucher_id: str
    reported_debit: str
    reported_credit: str
    variance: str
    stage: str
    status: Literal["PENDING", "RECONCILED", "DISCREPANCY_FLAGGED", "INPUT_ERROR"]
    audit_log: list[str]
    error_details: str | None


def ingest_and_validate_node(state: AuditWorkflowState) -> dict:
    """Step 1: Ingest voucher and validate numeric inputs with Python Decimal."""
    log = list(state.get("audit_log", []))
    log.append("Node 'ingest_and_validate': Validating raw voucher inputs.")
    try:
        debit = Decimal(state["reported_debit"])
        credit = Decimal(state["reported_credit"])
        if debit < Decimal("0") or credit < Decimal("0"):
            raise ValueError("Debit and credit amounts cannot be negative.")
        return {
            "stage": "validated",
            "audit_log": log,
            "error_details": None
        }
    except Exception as e:
        log.append(f"Node 'ingest_and_validate': Validation error caught - {str(e)}")
        return {
            "stage": "input_error",
            "status": "INPUT_ERROR",
            "audit_log": log,
            "error_details": f"Validation failed: {str(e)}"
        }


def calculate_variance_node(state: AuditWorkflowState) -> dict:
    """Step 2: Deterministic calculation using Python Decimal (Zero LLM math)."""
    log = list(state.get("audit_log", []))
    debit = Decimal(state["reported_debit"])
    credit = Decimal(state["reported_credit"])
    variance = abs(debit - credit)
    log.append(f"Node 'calculate_variance': Computed variance = {variance} using Decimal precision.")
    return {
        "variance": str(variance),
        "stage": "variance_computed",
        "audit_log": log
    }


def route_reconciliation(state: AuditWorkflowState) -> str:
    """Conditional Routing logic based on deterministic variance threshold."""
    if state.get("status") == "INPUT_ERROR":
        return "handle_error"
    variance = Decimal(state.get("variance", "0"))
    if variance == Decimal("0.00"):
        return "reconciliation_pass"
    else:
        return "reconciliation_flag"


def reconciliation_pass_node(state: AuditWorkflowState) -> dict:
    """Step 3A: Pass reconciliation when variance is zero."""
    log = list(state.get("audit_log", []))
    log.append("Node 'reconciliation_pass': Balanced voucher verified.")
    return {
        "status": "RECONCILED",
        "stage": "complete",
        "audit_log": log
    }


def reconciliation_flag_node(state: AuditWorkflowState) -> dict:
    """Step 3B: Flag anomaly when variance is detected."""
    log = list(state.get("audit_log", []))
    log.append(f"Node 'reconciliation_flag': Discrepancy of {state['variance']} detected! Dispatched to Not-Checked / Investigation.")
    return {
        "status": "DISCREPANCY_FLAGGED",
        "stage": "complete",
        "audit_log": log
    }


def error_handler_node(state: AuditWorkflowState) -> dict:
    """Step 3C: Dedicated error handling node."""
    log = list(state.get("audit_log", []))
    log.append(f"Node 'error_handler': Processed workflow error: {state.get('error_details')}")
    return {
        "stage": "terminated_on_error",
        "audit_log": log
    }


def build_audit_graph():
    workflow = StateGraph(AuditWorkflowState)
    
    # Register Nodes
    workflow.add_node("ingest_and_validate", ingest_and_validate_node)
    workflow.add_node("calculate_variance", calculate_variance_node)
    workflow.add_node("reconciliation_pass", reconciliation_pass_node)
    workflow.add_node("reconciliation_flag", reconciliation_flag_node)
    workflow.add_node("handle_error", error_handler_node)

    # Add Edges
    workflow.add_edge(START, "ingest_and_validate")

    def route_after_validation(state: AuditWorkflowState) -> str:
        if state.get("status") == "INPUT_ERROR":
            return "handle_error"
        return "calculate_variance"

    workflow.add_conditional_edges(
        "ingest_and_validate",
        route_after_validation,
        {
            "calculate_variance": "calculate_variance",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "calculate_variance",
        route_reconciliation,
        {
            "reconciliation_pass": "reconciliation_pass",
            "reconciliation_flag": "reconciliation_flag",
            "handle_error": "handle_error"
        }
    )

    workflow.add_edge("reconciliation_pass", END)
    workflow.add_edge("reconciliation_flag", END)
    workflow.add_edge("handle_error", END)

    return workflow.compile()


def test_langgraph_execution():
    app = build_audit_graph()

    print("--- SCENARIO 1: Balanced Trial Balance (Pass Route) ---")
    state_pass: AuditWorkflowState = {
        "voucher_id": "VOUCH-BALANCED-01",
        "reported_debit": "154200.50",
        "reported_credit": "154200.50",
        "variance": "0.00",
        "stage": "init",
        "status": "PENDING",
        "audit_log": [],
        "error_details": None
    }
    result_pass = app.invoke(state_pass)
    print(f"Status: {result_pass['status']}, Stage: {result_pass['stage']}, Variance: {result_pass['variance']}")
    assert result_pass["status"] == "RECONCILED", "Expected RECONCILED status"
    assert result_pass["stage"] == "complete"
    assert len(result_pass["audit_log"]) >= 3
    print("PASS: Scenario 1 succeeded.")

    print("\n--- SCENARIO 2: Discrepancy Detected (Flag Route) ---")
    state_flag: AuditWorkflowState = {
        "voucher_id": "VOUCH-DISCREPANT-02",
        "reported_debit": "500000.00",
        "reported_credit": "495000.00",
        "variance": "0.00",
        "stage": "init",
        "status": "PENDING",
        "audit_log": [],
        "error_details": None
    }
    result_flag = app.invoke(state_flag)
    print(f"Status: {result_flag['status']}, Stage: {result_flag['stage']}, Variance: {result_flag['variance']}")
    assert result_flag["status"] == "DISCREPANCY_FLAGGED"
    assert result_flag["variance"] == "5000.00"
    print("PASS: Scenario 2 succeeded.")

    print("\n--- SCENARIO 3: Invalid Input (Error Handling Route) ---")
    state_err: AuditWorkflowState = {
        "voucher_id": "VOUCH-INVALID-03",
        "reported_debit": "-1000.00",
        "reported_credit": "1000.00",
        "variance": "0.00",
        "stage": "init",
        "status": "PENDING",
        "audit_log": [],
        "error_details": None
    }
    result_err = app.invoke(state_err)
    print(f"Status: {result_err['status']}, Stage: {result_err['stage']}, Error: {result_err['error_details']}")
    assert result_err["status"] == "INPUT_ERROR"
    assert result_err["stage"] == "terminated_on_error"
    print("PASS: Scenario 3 error handling succeeded.")

    print("\nALL LANGGRAPH EXECUTION TESTS VERIFIED SUCCESSFULLY.")


if __name__ == "__main__":
    test_langgraph_execution()
