import os
import pytest
from decimal import Decimal

from backend.services.evidence_service import EvidenceService
from backend.services.pdf_service import PDFIntelligenceService
from backend.services.spreadsheet_service import SpreadsheetIntelligenceService
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.services.completeness_service import CompletenessGateService
from backend.services.not_checked_service import NotCheckedRegisterService
from backend.models.evidence import DocumentType, ExtractionStatus
from backend.models.financial import TrialBalanceItem
from backend.models.completeness import GateStatus


@pytest.fixture
def synthetic_data_dir():
    return os.path.join("data", "synthetic")


def test_end_to_end_phase2_pipeline(synthetic_data_dir, tmp_path):
    # 1. Initialize services
    vault_dir = str(tmp_path / "vault")
    ev_svc = EvidenceService(storage_dir=vault_dir)
    pdf_svc = PDFIntelligenceService(evidence_service=ev_svc)
    sheet_svc = SpreadsheetIntelligenceService(evidence_service=ev_svc)
    fin_engine = DeterministicFinancialEngine()
    completeness_svc = CompletenessGateService()
    register_svc = NotCheckedRegisterService(persistence_file=str(tmp_path / "reg.json"))

    # 2. Ingest Synthetic Trial Balances (FY23, FY24, FY25)
    tb_fy24_path = os.path.join(synthetic_data_dir, "trial_balance_fy2024_25.csv")
    assert os.path.exists(tb_fy24_path)

    with open(tb_fy24_path, "rb") as f:
        tb_record, tb_data = sheet_svc.ingest_csv(f.read(), "trial_balance_fy2024_25.csv", hint_type=DocumentType.TRIAL_BALANCE)

    assert tb_record.extraction_status == ExtractionStatus.SUCCESS
    assert tb_record.document_type == DocumentType.TRIAL_BALANCE

    # Parse entries into TrialBalanceItems
    tb_items = []
    for r in tb_data["rows"]:
        tb_items.append(
            TrialBalanceItem(
                account_code=r["account_code"],
                account_name=r["account_name"],
                debit=Decimal(r["debit"]),
                credit=Decimal(r["credit"]),
            )
        )

    # 3. Deterministic Trial Balance Arithmetic
    tb_obj, calc_record = fin_engine.verify_trial_balance(tb_items, "FY2024-25", "Apex Industrial Dynamics")
    assert tb_obj.total_debits > Decimal("0")
    assert tb_obj.total_credits > Decimal("0")

    # 4. Ingest Invoices (PDF)
    inv_pdf_path = os.path.join(synthetic_data_dir, "invoices", "INV_2024_001.pdf")
    with open(inv_pdf_path, "rb") as f:
        inv_record, inv_data = pdf_svc.ingest_pdf(f.read(), "INV_2024_001.pdf", hint_type=DocumentType.INVOICE)
    assert inv_record.extraction_status == ExtractionStatus.SUCCESS
    assert inv_data["page_count"] == 1

    # 5. Detect Planted Anomaly #4 (Depreciation on AST-102: claimed $125k vs statutory $75k)
    far_path = os.path.join(synthetic_data_dir, "fixed_asset_register_fy2024_25.csv")
    with open(far_path, "rb") as f:
        far_rec, far_data = sheet_svc.ingest_csv(f.read(), "fixed_asset_register_fy2024_25.csv", hint_type=DocumentType.FIXED_ASSET_REGISTER)

    for row in far_data["rows"]:
        if row["asset_id"] == "AST-102":
            opening_wdv = Decimal(row["opening_wdv"])
            stat_rate = Decimal(row["statutory_rate"])
            claimed_dep = Decimal(row["depreciation_claimed"])
            correct_dep, _, _ = fin_engine.compute_depreciation(
                asset_cost=Decimal(row["cost"]),
                accumulated_depreciation=Decimal(row["cost"]) - opening_wdv,
                rate=stat_rate,
            )
            # Planted Anomaly #4 verified: Claimed 125,000 vs Correct 75,000 -> 50,000 variance
            variance = claimed_dep - correct_dep
            assert variance == Decimal("50000.00"), f"Expected 50000.00 depreciation variance, got {variance}"

    # 6. Detect Planted Anomaly #5 (Cross-Year Inventory Gap: FY23 closing $450k vs FY24 opening $485k)
    tb_fy23_path = os.path.join(synthetic_data_dir, "trial_balance_fy2023_24.csv")
    with open(tb_fy23_path, "rb") as f:
        _, tb23_data = sheet_svc.ingest_csv(f.read(), "trial_balance_fy2023_24.csv")

    fy23_inventory = Decimal([r["debit"] for r in tb23_data["rows"] if "Inventory" in r["account_name"]][0])
    fy24_opening_inventory = Decimal([r["debit"] for r in tb_data["rows"] if "Opening Inventory" in r["account_name"]][0])
    inv_gap = fy24_opening_inventory - fy23_inventory
    assert inv_gap == Decimal("35000.00"), f"Expected 35000.00 inventory gap, got {inv_gap}"

    # 7. Update Not-Checked Register based on completed empirical verification
    register_svc.complete_item("PROC-TB-01", evidence_id=tb_record.evidence_id, reviewer="Senior Auditor")
    summary = register_svc.get_summary()
    assert summary["status_breakdown"]["COMPLETED"] >= 1

    # 8. Evaluate Completeness Gate
    collected_evidence = [tb_record, inv_record, far_rec]
    gate_res = completeness_svc.evaluate_completeness("AUDIT-FY2024-25", collected_evidence)
    # Gate should be blocked because Balance Sheet, P&L, General Ledger are not yet uploaded
    assert gate_res.gate_status == GateStatus.BLOCKED
    assert gate_res.can_proceed_to_report is False
    assert len(gate_res.missing_documents) > 0
