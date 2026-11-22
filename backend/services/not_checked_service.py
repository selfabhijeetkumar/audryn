import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from backend.models.not_checked import ProcedureStatus, AuditArea, NotCheckedItem


class NotCheckedRegisterService:
    """
    Persistent Not-Checked Register.
    Tracks audit procedures, areas not yet examined, blocked items,
    and prevents silent assumptions that untested procedures have passed.
    """

    def __init__(self, persistence_file: Optional[str] = None):
        self.persistence_file = persistence_file or os.path.join("data", "not_checked_register.json")
        self._items: Dict[str, NotCheckedItem] = {}
        self._load_or_initialize()

    def _get_default_procedures(self) -> List[NotCheckedItem]:
        """Pre-populates baseline statutory tax audit procedures."""
        return [
            NotCheckedItem(
                procedure_id="PROC-TB-01",
                audit_area=AuditArea.STATUTORY_RECONCILIATION,
                title="Trial Balance Arithmetic Balance",
                description="Verify that total debits equal total credits across all account codes.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Scheduled for initial ingestion phase.",
                required_evidence=["TRIAL_BALANCE"],
            ),
            NotCheckedItem(
                procedure_id="PROC-BS-01",
                audit_area=AuditArea.STATUTORY_RECONCILIATION,
                title="Balance Sheet Equation Verification",
                description="Verify that Assets equal Total Liabilities plus Equity.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending balance sheet ingestion.",
                required_evidence=["BALANCE_SHEET"],
            ),
            NotCheckedItem(
                procedure_id="PROC-CY-01",
                audit_area=AuditArea.STATUTORY_RECONCILIATION,
                title="Cross-Year Opening vs Prior Year Closing Tie-Out",
                description="Verify that Prior Year closing balances match Current Year opening balances exactly.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending multi-year schedule ingestion.",
                required_evidence=["TRIAL_BALANCE_PY", "TRIAL_BALANCE_CY"],
            ),
            NotCheckedItem(
                procedure_id="PROC-DEP-01",
                audit_area=AuditArea.FIXED_ASSETS_AND_DEPRECIATION,
                title="Fixed Asset Depreciation Schedule Recalculation",
                description="Recalculate statutory depreciation using WDV method for machinery and computers.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending Fixed Asset Register.",
                required_evidence=["FIXED_ASSET_REGISTER"],
            ),
            NotCheckedItem(
                procedure_id="PROC-TAX-01",
                audit_area=AuditArea.TAX_COMPLIANCE,
                title="Section 40(a)(ia) TDS Disallowance Check",
                description="Verify compliance with TDS withholding on contract and professional payments.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending ledger sampling.",
                required_evidence=["GENERAL_LEDGER", "TAX_RETURN"],
            ),
            NotCheckedItem(
                procedure_id="PROC-TAX-02",
                audit_area=AuditArea.TAX_COMPLIANCE,
                title="Section 40A(3) Cash Payment Limit Check",
                description="Identify single cash payments exceeding statutory threshold of $10,000.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending cash book ledger analysis.",
                required_evidence=["GENERAL_LEDGER"],
            ),
            NotCheckedItem(
                procedure_id="PROC-BNK-01",
                audit_area=AuditArea.CASH_AND_BANK,
                title="Bank Reconciliation Statement Verification",
                description="Reconcile bank ledger balance with external bank statements and clearing vouchers.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending bank statement receipt.",
                required_evidence=["BANK_STATEMENT", "GENERAL_LEDGER"],
            ),
            NotCheckedItem(
                procedure_id="PROC-REV-01",
                audit_area=AuditArea.REVENUE_AND_SALES,
                title="Sales Register to Trial Balance Reconciliation",
                description="Reconcile total sales register revenue against the trial balance revenue code.",
                status=ProcedureStatus.NOT_CHECKED,
                reason_not_checked="Pending sales register ingestion.",
                required_evidence=["SALES_REGISTER", "TRIAL_BALANCE"],
            ),
        ]

    def _load_or_initialize(self) -> None:
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_data in data:
                        item = NotCheckedItem(**item_data)
                        self._items[item.procedure_id] = item
                return
            except Exception:
                pass  # Fall back to defaults if corrupted

        # Initialize with standard statutory procedures
        for p in self._get_default_procedures():
            self._items[p.procedure_id] = p
        self._save()

    def _save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.persistence_file)), exist_ok=True)
        with open(self.persistence_file, "w", encoding="utf-8") as f:
            json.dump([item.model_dump(mode="json") for item in self._items.values()], f, indent=2)

    def create_item(self, item: NotCheckedItem) -> NotCheckedItem:
        self._items[item.procedure_id] = item
        self._save()
        return item

    def get_item(self, procedure_id: str) -> Optional[NotCheckedItem]:
        return self._items.get(procedure_id)

    def update_item_status(
        self,
        procedure_id: str,
        status: ProcedureStatus,
        reason: Optional[str] = None,
        reviewer: Optional[str] = None,
        associated_evidence_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[NotCheckedItem]:
        item = self._items.get(procedure_id)
        if not item:
            return None

        item.status = status
        item.last_updated = datetime.now(timezone.utc)
        if reason:
            item.reason_not_checked = reason
        if reviewer:
            item.responsible_reviewer = reviewer
        if associated_evidence_id and associated_evidence_id not in item.associated_evidence_ids:
            item.associated_evidence_ids.append(associated_evidence_id)
        if notes:
            item.notes = notes

        self._save()
        return item

    def block_item(self, procedure_id: str, reason: str, reviewer: Optional[str] = None) -> Optional[NotCheckedItem]:
        return self.update_item_status(
            procedure_id=procedure_id,
            status=ProcedureStatus.BLOCKED,
            reason=reason,
            reviewer=reviewer,
        )

    def complete_item(self, procedure_id: str, evidence_id: str, reviewer: Optional[str] = None) -> Optional[NotCheckedItem]:
        return self.update_item_status(
            procedure_id=procedure_id,
            status=ProcedureStatus.COMPLETED,
            reviewer=reviewer,
            associated_evidence_id=evidence_id,
            reason="Procedure empirically verified by evidence.",
        )

    def list_items(
        self,
        status: Optional[ProcedureStatus] = None,
        audit_area: Optional[AuditArea] = None,
    ) -> List[NotCheckedItem]:
        items = list(self._items.values())
        if status:
            items = [i for i in items if i.status == status]
        if audit_area:
            items = [i for i in items if i.audit_area == audit_area]
        return items

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._items)
        by_status = {}
        for s in ProcedureStatus:
            by_status[s.value] = sum(1 for i in self._items.values() if i.status == s)
        return {
            "total_procedures": total,
            "status_breakdown": by_status,
            "completion_percentage": round((by_status[ProcedureStatus.COMPLETED.value] / total) * 100, 2) if total else 0.0,
            "unresolved_count": total - by_status[ProcedureStatus.COMPLETED.value],
        }
