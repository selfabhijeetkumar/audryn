"""
AUDRYN Financial Linkage Service.

Connects financial transactions, general ledger entries, vendor invoices,
bank movements, fixed assets, and tax calculations into the Evidence Graph
through deterministic matching logic. Strictly zero LLM arithmetic.
"""
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from backend.models.evidence_graph import (
    NodeType,
    RelationshipType,
    GraphNode,
    GraphRelationship,
)
from backend.services.evidence_graph_service import EvidenceGraphService
from backend.services.financial_engine import DeterministicFinancialEngine


class FinancialLinkageService:
    """
    Performs deterministic tie-outs and establishes verified relationships
    in the AUDRYN Evidence Graph across transactions, ledgers, and documents.
    """

    def __init__(self, graph_service: EvidenceGraphService):
        self.graph = graph_service
        self.engine = DeterministicFinancialEngine()

    def link_invoice_to_ledger(
        self,
        audit_id: str,
        invoice_node_id: str,
        invoice_number: str,
        invoice_amount: Decimal,
        ledger_entry_id: str,
        ledger_voucher_id: str,
        ledger_amount: Decimal,
        ledger_type: str = "PURCHASE",  # PURCHASE or SALES
    ) -> GraphRelationship:
        """
        Deterministically matches an invoice to a general ledger entry.
        Verifies voucher number and amount equality.
        """
        inv_amt = self.engine.round_currency(invoice_amount)
        led_amt = self.engine.round_currency(ledger_amount)
        variance = abs(inv_amt - led_amt)

        rel_id = f"REL-INV-GL-{invoice_number}-{ledger_voucher_id}"
        is_match = (variance == Decimal("0.00")) and (invoice_number.strip().upper() == ledger_voucher_id.strip().upper())

        rel_type = (
            RelationshipType.TRANSACTION_MATCHES_TRANSACTION
            if is_match
            else RelationshipType.TRANSACTION_CONTRADICTS_TRANSACTION
        )

        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=invoice_node_id,
            target_id=ledger_entry_id,
            relationship_type=rel_type,
            provenance="Deterministic Voucher & Amount Tie-Out",
            properties={
                "invoice_number": invoice_number,
                "voucher_id": ledger_voucher_id,
                "invoice_amount": str(inv_amt),
                "ledger_amount": str(led_amt),
                "variance": str(variance),
                "ledger_type": ledger_type,
                "is_exact_match": is_match,
            },
            validation_status="VALIDATED" if is_match else "DISCREPANCY_FLAGGED",
        )
        return self.graph.add_relationship(rel)

    def link_credit_note_reversal(
        self,
        audit_id: str,
        credit_note_node_id: str,
        credit_note_num: str,
        original_invoice_node_id: str,
        original_invoice_num: str,
        reversal_amount: Decimal,
        invoice_amount: Decimal,
    ) -> GraphRelationship:
        """
        Links a credit note reversal to an original sales/purchase invoice.
        Establishes valid commercial counter-evidence for apparent discrepancies.
        """
        rev_amt = self.engine.round_currency(reversal_amount)
        inv_amt = self.engine.round_currency(invoice_amount)
        rel_id = f"REL-CN-INV-{credit_note_num}-{original_invoice_num}"

        is_valid_reversal = rev_amt <= inv_amt

        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=credit_note_node_id,
            target_id=original_invoice_node_id,
            relationship_type=RelationshipType.TRANSACTION_MATCHES_TRANSACTION,
            provenance="Commercial Credit Note Reversal Link",
            properties={
                "credit_note_number": credit_note_num,
                "original_invoice_number": original_invoice_num,
                "reversal_amount": str(rev_amt),
                "original_invoice_amount": str(inv_amt),
                "is_full_reversal": (rev_amt == inv_amt),
                "is_valid_reversal": is_valid_reversal,
            },
            validation_status="VALIDATED",
        )
        return self.graph.add_relationship(rel)

    def link_bank_transaction_to_ledger(
        self,
        audit_id: str,
        bank_tx_node_id: str,
        bank_ref: str,
        bank_date: str,
        bank_amount: Decimal,
        ledger_tx_node_id: str,
        ledger_ref: str,
        ledger_date: str,
        ledger_amount: Decimal,
    ) -> GraphRelationship:
        """
        Links a bank statement movement to a general ledger payment/receipt.
        Detects timing differences within standard clearing windows (e.g. <= 5 days).
        """
        b_amt = self.engine.round_currency(bank_amount)
        l_amt = self.engine.round_currency(ledger_amount)
        variance = abs(b_amt - l_amt)

        # Check date difference for timing difference classification
        is_timing_difference = False
        try:
            d_bank = datetime.fromisoformat(bank_date)
            d_led = datetime.fromisoformat(ledger_date)
            day_diff = abs((d_bank - d_led).days)
            if day_diff <= 5 and variance == Decimal("0.00"):
                is_timing_difference = True
        except Exception:
            day_diff = None

        is_match = (variance == Decimal("0.00"))
        rel_id = f"REL-BANK-LED-{bank_ref}-{ledger_ref}"

        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=bank_tx_node_id,
            target_id=ledger_tx_node_id,
            relationship_type=RelationshipType.TRANSACTION_MATCHES_TRANSACTION if is_match else RelationshipType.TRANSACTION_CONTRADICTS_TRANSACTION,
            provenance="Bank Reconciliation Statement Tie-Out",
            properties={
                "bank_ref": bank_ref,
                "ledger_ref": ledger_ref,
                "bank_amount": str(b_amt),
                "ledger_amount": str(l_amt),
                "variance": str(variance),
                "day_difference": day_diff,
                "is_timing_difference": is_timing_difference,
            },
            validation_status="VALIDATED" if is_match else "DISCREPANCY_FLAGGED",
        )
        return self.graph.add_relationship(rel)

    def link_calculation_to_tax_rule(
        self,
        audit_id: str,
        calc_node_id: str,
        tax_rule_node_id: str,
        section_reference: str,
        effective_rate: str,
        rulebook_version: str,
    ) -> GraphRelationship:
        """Links a corporate tax or statutory depreciation calculation to a versioned tax rule."""
        rel_id = f"REL-CALC-RULE-{calc_node_id}-{section_reference}"
        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=calc_node_id,
            target_id=tax_rule_node_id,
            relationship_type=RelationshipType.CALCULATION_USES_RULE,
            provenance="Statutory Tax Rulebook Mapping",
            properties={
                "section": section_reference,
                "effective_rate": effective_rate,
                "rulebook_version": rulebook_version,
            },
            validation_status="VALIDATED",
        )
        return self.graph.add_relationship(rel)

    def link_finding_to_counter_evidence(
        self,
        audit_id: str,
        finding_node_id: str,
        counter_evidence_node_id: str,
        challenge_id: str,
        verdict: str,
        rationale: str,
    ) -> GraphRelationship:
        """Links an audit finding to an independent counter-evidence challenge verdict."""
        rel_id = f"REL-FIND-CE-{finding_node_id}-{challenge_id}"
        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=finding_node_id,
            target_id=counter_evidence_node_id,
            relationship_type=RelationshipType.FINDING_HAS_COUNTER_EVIDENCE,
            provenance="Independent Review Challenger Engine",
            properties={
                "challenge_id": challenge_id,
                "verdict": verdict,
                "rationale": rationale,
            },
            validation_status="VALIDATED",
        )
        return self.graph.add_relationship(rel)

    def link_finding_to_human_review(
        self,
        audit_id: str,
        finding_node_id: str,
        review_decision_node_id: str,
        decision: str,
        reviewer_name: str,
        comments: str,
    ) -> GraphRelationship:
        """Links an audit finding to a human auditor review decision."""
        rel_id = f"REL-FIND-REV-{finding_node_id}-{review_decision_node_id}"
        rel = GraphRelationship(
            relationship_id=rel_id,
            audit_id=audit_id,
            source_id=finding_node_id,
            target_id=review_decision_node_id,
            relationship_type=RelationshipType.FINDING_HAS_REVIEW_DECISION,
            provenance="Auditor Human-in-the-Loop Signoff",
            properties={
                "decision": decision,
                "reviewer": reviewer_name,
                "comments": comments,
            },
            validation_status="VALIDATED",
        )
        return self.graph.add_relationship(rel)
