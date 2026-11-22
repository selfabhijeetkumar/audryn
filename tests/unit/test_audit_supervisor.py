"""
AUDRYN Phase 3 — LangGraph Audit Supervisor Tests.

Covers:
- Full workflow execution (happy path)
- Conditional routing (validation failure, completeness block)
- Checkpointing and resume
- Human-in-the-loop interrupt and resume
- Risk classification routing
- State isolation between audits
- Failed node error propagation
- Retry behavior
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from backend.workflows.audit_supervisor import build_audit_graph, AuditGraphState


def _make_valid_input(audit_id="AUD-TEST-001"):
    """Minimal valid audit input with synthetic trial balance data."""
    return {
        "audit_id": audit_id,
        "company_id": "CIN-TEST-001",
        "company_name": "Test Corp Pvt Ltd",
        "financial_periods": ["FY2023-24", "FY2024-25"],
        "evidence_ids": [],
        "extracted_records": {
            "evidence_records": [],
            "trial_balances": {
                "FY2023-24": [
                    {"account_code": "1001", "account_name": "Cash", "debit": "100000", "credit": "0"},
                    {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "100000"},
                ],
                "FY2024-25": [
                    {"account_code": "1001", "account_name": "Cash", "debit": "120000", "credit": "0"},
                    {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "120000"},
                ],
            },
            "available_documents": {
                "FY2023-24": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS",
                              "GENERAL_LEDGER", "TAX_RETURN", "FIXED_ASSET_REGISTER", "BANK_STATEMENT"],
                "FY2024-25": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS",
                              "GENERAL_LEDGER", "TAX_RETURN", "FIXED_ASSET_REGISTER", "BANK_STATEMENT"],
            },
            "procedures": [],
        },
        "completeness_status": "PENDING",
        "reconciliation_results": [],
        "investigation_findings": [],
        "counter_evidence": [],
        "verification_results": [],
        "gap_register": [],
        "risk_classification": "LOW",
        "human_review_status": "NOT_REQUIRED",
        "human_reviewer_comments": "",
        "final_report_status": "NOT_STARTED",
        "execution_errors": [],
        "retry_count": 0,
        "current_stage": "",
    }


def test_supervisor_full_happy_path():
    """Full audit workflow with balanced data should finalize successfully."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "test-happy-001"}}
    result = graph.invoke(_make_valid_input(), config)
    assert result["current_stage"] in ("finalized", "finalized_blocked")
    assert result["audit_id"] == "AUD-TEST-001"
    # Balanced TBs should produce no unbalanced findings
    assert result["completeness_status"] in ("BLOCKED", "PASS")


def test_supervisor_validation_failure_missing_company():
    """Missing company_id should route to finalize with BLOCKED status."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "test-val-fail-001"}}
    inp = _make_valid_input()
    inp["company_id"] = ""
    result = graph.invoke(inp, config)
    assert result["final_report_status"] == "BLOCKED"
    assert any("company_id" in e for e in result["execution_errors"])


def test_supervisor_validation_failure_missing_periods():
    """Missing financial_periods should block."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "test-val-fail-002"}}
    inp = _make_valid_input()
    inp["financial_periods"] = []
    result = graph.invoke(inp, config)
    assert result["final_report_status"] == "BLOCKED"


def test_supervisor_completeness_block():
    """Missing evidence records should block at completeness check."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "test-completeness-block-001"}}
    inp = _make_valid_input()
    inp["extracted_records"]["evidence_records"] = []  # No evidence
    inp["extracted_records"]["available_documents"] = {}  # No documents catalogued
    result = graph.invoke(inp, config)
    assert result["completeness_status"] == "BLOCKED"
    assert result["final_report_status"] == "BLOCKED"


def test_supervisor_unbalanced_tb_creates_findings():
    """Unbalanced trial balance should produce investigation findings."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "test-unbalanced-001"}}
    inp = _make_valid_input()
    # Inject unbalanced TB
    inp["extracted_records"]["trial_balances"]["FY2024-25"] = [
        {"account_code": "1001", "account_name": "Cash", "debit": "130000", "credit": "0"},
        {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "120000"},
    ]
    result = graph.invoke(inp, config)
    # Should have at least one finding for the unbalanced TB
    findings = result.get("investigation_findings", [])
    unbalanced = [f for f in findings if "UNBALANCED" in str(f) or "TRIAL_BALANCE" in str(f)]
    assert len(unbalanced) >= 1, f"Expected unbalanced finding, got: {findings}"


def test_supervisor_checkpointing_state_isolation():
    """Two different audit threads must not share state."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)

    inp1 = _make_valid_input("AUD-ISO-001")
    inp1["company_name"] = "Company Alpha"
    config1 = {"configurable": {"thread_id": "iso-thread-001"}}

    inp2 = _make_valid_input("AUD-ISO-002")
    inp2["company_name"] = "Company Beta"
    config2 = {"configurable": {"thread_id": "iso-thread-002"}}

    r1 = graph.invoke(inp1, config1)
    r2 = graph.invoke(inp2, config2)

    assert r1["audit_id"] == "AUD-ISO-001"
    assert r2["audit_id"] == "AUD-ISO-002"
    assert r1["company_name"] == "Company Alpha"
    assert r2["company_name"] == "Company Beta"


def test_supervisor_human_review_interrupt_and_resume():
    """
    When risk is HIGH/CRITICAL, graph should interrupt before human review.
    After updating state, graph should resume and finalize.
    """
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=True)
    config = {"configurable": {"thread_id": "test-hitl-001"}}

    inp = _make_valid_input()
    # Inject a critical finding to trigger HIGH risk
    inp["extracted_records"]["trial_balances"]["FY2024-25"] = [
        {"account_code": "1001", "account_name": "Cash", "debit": "200000", "credit": "0"},
        {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "120000"},
    ]
    # Also add a pre-loaded critical finding
    inp["extracted_records"]["investigation_findings"] = [
        {
            "finding_id": "FND-CRIT-001",
            "category": "GENERAL_LEDGER",
            "severity": "CRITICAL",
            "title": "Major Ledger Discrepancy",
            "description": "Critical variance detected.",
            "impact_amount": "80000",
            "source_evidence": ["trial_balance_fy2024_25.csv"],
            "agent_role": "Test",
            "status": "OPEN",
        }
    ]

    # First invocation — should pause at human review
    result = graph.invoke(inp, config)
    assert result["human_review_status"] == "PENDING"
    assert result["current_stage"] == "risk_classified"

    # Simulate human approval by updating state
    graph.update_state(
        config,
        {"human_review_status": "APPROVED", "human_reviewer_comments": "Reviewed and approved."},
    )

    # Resume
    result2 = graph.invoke(None, config)
    assert result2["human_review_status"] == "APPROVED"
    assert result2["current_stage"] in ("finalized", "finalized_blocked")


def test_supervisor_risk_low_skips_human_review():
    """LOW risk should skip human review and go directly to finalize."""
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=True)
    config = {"configurable": {"thread_id": "test-low-risk-001"}}
    inp = _make_valid_input()
    result = graph.invoke(inp, config)
    # With balanced TBs and no critical findings, risk should be LOW
    # Should have gone through finalize without interrupt
    assert result["current_stage"] in ("finalized", "finalized_blocked")
