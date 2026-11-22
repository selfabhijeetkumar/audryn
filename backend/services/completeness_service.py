from typing import List, Dict, Optional
from datetime import datetime, timezone
from backend.models.evidence import EvidenceRecord, DocumentType, ExtractionStatus
from backend.models.completeness import (
    GateStatus,
    RequiredDocumentRule,
    CompletenessEvaluation,
    CompletenessGateResult,
)


class CompletenessGateService:
    """
    Audit Completeness Gate.
    Verifies that all statutory documentation is present, non-corrupted,
    and verified before an audit engagement can proceed to report generation.
    """

    def __init__(self, custom_rules: Optional[List[RequiredDocumentRule]] = None):
        self.rules: List[RequiredDocumentRule] = custom_rules or self._get_default_statutory_rules()

    @staticmethod
    def _get_default_statutory_rules() -> List[RequiredDocumentRule]:
        """Statutory Tax Audit minimum documentation checklist."""
        return [
            RequiredDocumentRule(
                rule_id="RULE-TB",
                document_type=DocumentType.TRIAL_BALANCE,
                display_name="Trial Balance",
                is_mandatory=True,
                minimum_count=1,
                description="Final signed trial balance for the audited fiscal period.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-BS",
                document_type=DocumentType.BALANCE_SHEET,
                display_name="Balance Sheet",
                is_mandatory=True,
                minimum_count=1,
                description="Balance sheet reflecting assets, liabilities, and equity balances.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-PL",
                document_type=DocumentType.PROFIT_AND_LOSS,
                display_name="Profit and Loss Statement",
                is_mandatory=True,
                minimum_count=1,
                description="Statement of operations, revenues, and expenses.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-GL",
                document_type=DocumentType.GENERAL_LEDGER,
                display_name="General Ledger",
                is_mandatory=True,
                minimum_count=1,
                description="Detailed journal account ledger records for audit sampling.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-FAR",
                document_type=DocumentType.FIXED_ASSET_REGISTER,
                display_name="Fixed Asset Register",
                is_mandatory=True,
                minimum_count=1,
                description="Asset register containing additions, deletions, and depreciation rates.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-TAX",
                document_type=DocumentType.TAX_RETURN,
                display_name="Tax Computation Schedule",
                is_mandatory=True,
                minimum_count=1,
                description="Detailed tax computation schedule and tax returns.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-BANK",
                document_type=DocumentType.BANK_STATEMENT,
                display_name="Bank Statements",
                is_mandatory=True,
                minimum_count=1,
                description="Bank reconciliation statements and year-end bank confirmations.",
            ),
            RequiredDocumentRule(
                rule_id="RULE-INV",
                document_type=DocumentType.INVOICE,
                display_name="Sample Invoices",
                is_mandatory=False,
                minimum_count=1,
                description="Sample vouchers/invoices supporting major revenue entries.",
            ),
        ]

    def evaluate_completeness(
        self,
        audit_id: str,
        evidence_records: List[EvidenceRecord],
    ) -> CompletenessGateResult:
        """
        Evaluates registered evidence against completeness rules.
        Blocks gate if mandatory documents are missing, corrupted, or unprocessed.
        """
        evaluations: List[CompletenessEvaluation] = []
        missing_docs: List[str] = []
        corrupted_docs: List[str] = []
        unprocessed_docs: List[str] = []
        requires_human_review: List[str] = []

        # Tally evidence records by type and status
        records_by_type: Dict[DocumentType, List[EvidenceRecord]] = {}
        for rec in evidence_records:
            records_by_type.setdefault(rec.document_type, []).append(rec)

            if rec.extraction_status == ExtractionStatus.CORRUPTED:
                corrupted_docs.append(f"{rec.original_filename} ({rec.evidence_id})")
            elif rec.extraction_status == ExtractionStatus.PENDING:
                unprocessed_docs.append(f"{rec.original_filename} ({rec.evidence_id})")
            elif rec.extraction_status == ExtractionStatus.REQUIRES_OCR:
                requires_human_review.append(
                    f"{rec.original_filename} ({rec.evidence_id}): Scanned document requiring OCR."
                )

        total_required_rules = 0
        total_satisfied_rules = 0

        for rule in self.rules:
            if rule.is_mandatory:
                total_required_rules += 1

            matched_records = records_by_type.get(rule.document_type, [])
            # Filter out corrupted or empty records
            valid_matched = [
                r for r in matched_records
                if r.extraction_status not in (ExtractionStatus.CORRUPTED, ExtractionStatus.EMPTY)
            ]
            matched_count = len(valid_matched)
            is_satisfied = matched_count >= rule.minimum_count

            if is_satisfied and rule.is_mandatory:
                total_satisfied_rules += 1
            elif not is_satisfied and rule.is_mandatory:
                missing_docs.append(
                    f"{rule.display_name}: Expected at least {rule.minimum_count}, found {matched_count}."
                )

            evaluations.append(
                CompletenessEvaluation(
                    rule=rule,
                    matched_count=matched_count,
                    matched_evidence_ids=[r.evidence_id for r in valid_matched],
                    is_satisfied=is_satisfied,
                    missing_count=max(0, rule.minimum_count - matched_count),
                    remarks="Requirement met." if is_satisfied else f"Missing {rule.minimum_count - matched_count} document(s).",
                )
            )

        # Gate passes ONLY if ALL mandatory rules are satisfied AND no corrupted documents exist
        can_proceed = (total_satisfied_rules == total_required_rules) and (len(corrupted_docs) == 0)
        gate_status = GateStatus.PASSED if can_proceed else GateStatus.BLOCKED

        return CompletenessGateResult(
            audit_id=audit_id,
            gate_status=gate_status,
            total_required=total_required_rules,
            total_satisfied=total_satisfied_rules,
            evaluations=evaluations,
            missing_documents=missing_docs,
            corrupted_documents=corrupted_docs,
            unprocessed_documents=unprocessed_docs,
            requires_human_review=requires_human_review,
            can_proceed_to_report=can_proceed,
            evaluated_at=datetime.now(timezone.utc),
        )
