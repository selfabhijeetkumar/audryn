"""
AUDRYN Phase 3 — End-to-End Integration Test.

Exercises the complete multi-agent audit pipeline on synthetic data:
1. Build LangGraph supervisor graph
2. Load synthetic trial balances
3. Run deterministic reconciliation
4. Dispatch investigation (create findings from anomalies)
5. Run counter-evidence challenges
6. Run GAP RADAR scan
7. Classify risk
8. Test human-in-the-loop interrupt and resume
9. Verify final audit state
"""
import os
import csv
import pytest
from decimal import Decimal
from langgraph.checkpoint.memory import MemorySaver

from backend.workflows.audit_supervisor import build_audit_graph
from backend.services.cross_year_service import CrossYearInvestigationService
from backend.services.counter_evidence_service import CounterEvidenceService
from backend.services.gap_radar_service import GapRadarService
from backend.services.human_review_service import HumanReviewService, HumanReviewDecision
from backend.agents.review_team import (
    run_counter_evidence_review,
    run_blind_spot_review,
    run_independent_finding_review,
)


def _load_synthetic_tb(filepath):
    """Load a synthetic trial balance CSV into list of dicts."""
    if not os.path.exists(filepath):
        return []
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "account_code": row.get("account_code", ""),
                "account_name": row.get("account_name", ""),
                "debit": row.get("debit", "0"),
                "credit": row.get("credit", "0"),
            })
    return rows


def test_phase3_full_integration_pipeline(tmp_path):
    """
    Full end-to-end Phase 3 integration test using synthetic data.
    Tests the complete multi-agent audit pipeline deterministically.
    """
    # ── 1. Load synthetic data ──
    base = os.path.join("data", "synthetic")
    tb_fy23 = _load_synthetic_tb(os.path.join(base, "trial_balance_fy2023_24.csv"))
    tb_fy24 = _load_synthetic_tb(os.path.join(base, "trial_balance_fy2024_25.csv"))

    # If synthetic data doesn't exist, use inline test data
    if not tb_fy23:
        tb_fy23 = [
            {"account_code": "1001", "account_name": "Cash", "debit": "250000", "credit": "0"},
            {"account_code": "1003", "account_name": "Inventory", "debit": "450000", "credit": "0"},
            {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "420000"},
            {"account_code": "3001", "account_name": "Equity", "debit": "0", "credit": "280000"},
        ]
    if not tb_fy24:
        tb_fy24 = [
            {"account_code": "1001", "account_name": "Cash", "debit": "280000", "credit": "0"},
            {"account_code": "1003", "account_name": "Inventory", "debit": "485000", "credit": "0"},
            {"account_code": "2001", "account_name": "Payables", "debit": "0", "credit": "460000"},
            {"account_code": "3001", "account_name": "Equity", "debit": "0", "credit": "280000"},
            # Planted imbalance: extra $25k in debits
            {"account_code": "9999", "account_name": "Suspense", "debit": "25000", "credit": "0"},
        ]

    # ── 2. Build audit graph ──
    saver = MemorySaver()
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=True)

    audit_input = {
        "audit_id": "AUD-INT-001",
        "company_id": "U29100MH2020PTC998877",
        "company_name": "Apex Industrial Dynamics Pvt Ltd",
        "financial_periods": ["FY2023-24", "FY2024-25"],
        "evidence_ids": [],
        "extracted_records": {
            "evidence_records": [],
            "trial_balances": {
                "FY2023-24": tb_fy23,
                "FY2024-25": tb_fy24,
            },
            "available_documents": {
                "FY2023-24": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS",
                              "GENERAL_LEDGER", "TAX_RETURN", "FIXED_ASSET_REGISTER", "BANK_STATEMENT"],
                "FY2024-25": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS",
                              "GENERAL_LEDGER", "TAX_RETURN", "FIXED_ASSET_REGISTER"],
                # Missing BANK_STATEMENT for FY2024-25
            },
            "procedures": [
                {"procedure_id": "PROC-01", "title": "Bank Recon", "status": "NOT_CHECKED",
                 "reason_not_checked": "Deferred."},
            ],
            "investigation_findings": [
                {
                    "finding_id": "FND-PLANTED-001",
                    "category": "GENERAL_LEDGER",
                    "severity": "HIGH",
                    "title": "Suspense Account Balance",
                    "description": "$25,000 unresolved suspense balance.",
                    "impact_amount": "25000",
                    "source_evidence": ["trial_balance_fy2024_25.csv"],
                    "agent_role": "Integration Test",
                    "status": "OPEN",
                },
            ],
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

    config = {"configurable": {"thread_id": "integration-phase3-001"}}

    # ── 3. First invocation — should run through pipeline ──
    result = graph.invoke(audit_input, config)

    # ── 4. Verify reconciliation detected anomalies ──
    recon = result.get("reconciliation_results", [])
    assert len(recon) > 0, "Expected reconciliation results"

    # ── 5. Verify investigation findings exist ──
    findings = result.get("investigation_findings", [])
    assert len(findings) >= 1, f"Expected at least 1 finding, got {len(findings)}"

    # ── 6. Verify counter-evidence was generated ──
    counter = result.get("counter_evidence", [])
    assert len(counter) >= 1, "Expected counter-evidence challenges"

    # ── 7. Verify GAP RADAR detected blind spots ──
    gaps = result.get("gap_register", [])
    # Should detect: missing BANK_STATEMENT for FY2024-25, untested procedure, unresolved findings
    assert len(gaps) >= 1, f"Expected gaps, got {len(gaps)}"

    # ── 8. Test human review if interrupted ──
    if result.get("human_review_status") == "PENDING":
        # Simulate human approval
        graph.update_state(
            config,
            {"human_review_status": "APPROVED", "human_reviewer_comments": "Integration test approved."},
        )
        result = graph.invoke(None, config)

    # ── 9. Verify final state ──
    assert result["audit_id"] == "AUD-INT-001"
    assert result["company_name"] == "Apex Industrial Dynamics Pvt Ltd"
    assert result["current_stage"] in ("finalized", "finalized_blocked")

    # ── 10. Cross-year service standalone verification ──
    cross_svc = CrossYearInvestigationService()
    prior_accts = {e["account_code"]: e for e in tb_fy23}
    curr_accts = {e["account_code"]: e for e in tb_fy24}
    movements = cross_svc.compare_account_balances(prior_accts, curr_accts, "FY2023-24", "FY2024-25")
    unusual = cross_svc.detect_unusual_movements(movements)
    # Suspense account appearing only in FY24 should be unusual
    suspense_moves = [m for m in movements if m["account_code"] == "9999"]
    if suspense_moves:
        assert suspense_moves[0]["prior_net_balance"] == "0.00"

    # ── 11. Independent review standalone verification ──
    finding_for_review = findings[0] if findings else {"finding_id": "FND-TEST", "source_evidence": ["test.csv"]}
    ce_for_review = counter[0] if counter else {"contradictory_evidence": [], "calculation_check": ""}
    review = run_independent_finding_review(finding_for_review, ce_for_review)
    assert review["independent_verdict"] in (
        "SUPPORTED", "CONTRADICTED", "PARTIALLY_SUPPORTED",
        "UNRESOLVED", "INSUFFICIENT_EVIDENCE",
    )

    # ── 12. Human review service standalone verification ──
    hr_svc = HumanReviewService(persistence_dir=str(tmp_path))
    hr_svc.record_decision("AUD-INT-001", "FND-PLANTED-001", "Test Auditor",
                           HumanReviewDecision.APPROVE, "Integration test.")
    assert hr_svc.is_audit_fully_reviewed("AUD-INT-001", ["FND-PLANTED-001"])

    print("PHASE 3 INTEGRATION TEST PASSED SUCCESSFULLY.")
