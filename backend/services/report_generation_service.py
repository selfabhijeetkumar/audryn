"""
AUDRYN Report Generation Service.

Assembles structured audit reports from persisted AUDRYN records.
Every figure, finding, and citation is derived from verifiable data.
No LLM-generated financial arithmetic. No fabricated evidence.
"""
import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional

from backend.models.report import (
    AuditReport,
    ReportSection,
    ReportSectionType,
    ReportManifest,
    ReportStatus,
)
from backend.services.release_gate_service import ReleaseGateService


class ReportGenerationService:
    """
    Generates versioned, reproducible audit reports from AUDRYN structured records.
    Persists report history to SQLite. Never silently overwrites finalized reports.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join("data", "reports", "audryn_reports.db")
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._conn = sqlite3.connect(
            self.db_path, timeout=10.0, check_same_thread=False, isolation_level=None,
        )
        self._configure_database()

    def _configure_database(self):
        with self._lock, self._conn:
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT NOT NULL,
                audit_id TEXT NOT NULL,
                report_version INTEGER NOT NULL,
                report_status TEXT NOT NULL,
                generated_at_utc TEXT NOT NULL,
                report_json TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                PRIMARY KEY (report_id, report_version)
            );
            """)

    def generate_report(
        self,
        audit_id: str,
        company_name: str,
        company_id: str,
        financial_periods: List[str],
        evidence_records: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        counter_evidence: List[Dict[str, Any]],
        gap_register: List[Dict[str, Any]],
        reconciliation_results: List[Dict[str, Any]],
        human_reviews: List[Dict[str, Any]],
        not_checked_items: List[Dict[str, Any]],
        completeness_status: str,
        human_review_status: str,
        risk_classification: str,
        rulebook_version: str = "Income-tax Act, 1961",
        is_synthetic: bool = True,
    ) -> AuditReport:
        """Assembles a complete audit report from structured records."""
        report_id = f"RPT-{audit_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        version = self._next_version(report_id)

        sections: List[ReportSection] = []

        # 1. COVER
        sections.append(ReportSection(
            section_id=f"{report_id}-S01",
            section_type=ReportSectionType.COVER,
            title="Report Identification",
            content={
                "report_id": report_id,
                "audit_id": audit_id,
                "report_version": version,
                "company_name": company_name,
                "company_id": company_id,
                "financial_periods": financial_periods,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "report_status": "DRAFT",
                "is_synthetic_data": is_synthetic,
            },
        ))

        # 2. EXECUTIVE SUMMARY
        total_findings = len(findings)
        material_findings = sum(1 for f in findings if f.get("severity") in ("HIGH", "CRITICAL"))
        approved_findings = sum(
            1 for r in human_reviews if r.get("decision") == "APPROVED"
        )
        rejected_findings = sum(
            1 for r in human_reviews if r.get("decision") == "REJECTED"
        )
        escalated_findings = sum(
            1 for r in human_reviews if r.get("decision") == "ESCALATED"
        )
        supported_ce = sum(1 for c in counter_evidence if c.get("reviewer_verdict") == "SUPPORTED")
        contradicted_ce = sum(1 for c in counter_evidence if c.get("reviewer_verdict") == "CONTRADICTED")
        unresolved_ce = sum(1 for c in counter_evidence if c.get("reviewer_verdict") in ("UNRESOLVED", "INSUFFICIENT_EVIDENCE"))

        sections.append(ReportSection(
            section_id=f"{report_id}-S02",
            section_type=ReportSectionType.EXECUTIVE_SUMMARY,
            title="Executive Summary",
            content={
                "audit_scope": f"Financial audit of {company_name} for periods {', '.join(financial_periods)}.",
                "total_evidence_documents": len(evidence_records),
                "processed_documents": sum(1 for e in evidence_records if e.get("extraction_status") == "SUCCESS"),
                "failed_documents": sum(1 for e in evidence_records if e.get("extraction_status") in ("FAILED", "CORRUPTED")),
                "total_findings": total_findings,
                "material_findings": material_findings,
                "approved_findings": approved_findings,
                "rejected_findings": rejected_findings,
                "escalated_findings": escalated_findings,
                "supported_findings": supported_ce,
                "contradicted_findings": contradicted_ce,
                "unresolved_findings": unresolved_ce,
                "open_gaps": sum(1 for g in gap_register if g.get("status") != "RESOLVED"),
                "not_checked_items": sum(1 for n in not_checked_items if n.get("status") != "COMPLETED"),
                "risk_classification": risk_classification,
            },
        ))

        # 3. SCOPE AND METHODOLOGY
        sections.append(ReportSection(
            section_id=f"{report_id}-S03",
            section_type=ReportSectionType.SCOPE_AND_METHODOLOGY,
            title="Audit Scope and Methodology",
            content={
                "documents_examined": len(evidence_records),
                "financial_periods": financial_periods,
                "deterministic_validation": "Python Decimal (ROUND_HALF_UP, 2dp)",
                "agent_frameworks": ["LangGraph Supervisor", "CrewAI Investigation", "MS Agent Framework Review"],
                "rulebook_version": rulebook_version,
                "limitations": ["AI-assisted analysis — professional auditor judgement required."],
            },
        ))

        # 4. EVIDENCE INVENTORY
        evidence_items = []
        evidence_hashes = []
        for ev in evidence_records:
            evidence_items.append({
                "evidence_id": ev.get("evidence_id", ""),
                "document_name": ev.get("original_filename", ""),
                "document_type": ev.get("document_type", "UNKNOWN"),
                "extraction_status": ev.get("extraction_status", "PENDING"),
                "sha256_short": ev.get("sha256_hash", "")[:16] + "..." if ev.get("sha256_hash") else "N/A",
            })
            if ev.get("sha256_hash"):
                evidence_hashes.append(ev["sha256_hash"])

        sections.append(ReportSection(
            section_id=f"{report_id}-S04",
            section_type=ReportSectionType.EVIDENCE_INVENTORY,
            title="Evidence Inventory",
            content={"evidence_documents": evidence_items},
            evidence_references=[e.get("evidence_id", "") for e in evidence_records],
            source_hash_references=evidence_hashes,
        ))

        # 5. FINANCIAL RECONCILIATION
        sections.append(ReportSection(
            section_id=f"{report_id}-S05",
            section_type=ReportSectionType.FINANCIAL_RECONCILIATION,
            title="Financial Reconciliation",
            content={"reconciliation_results": reconciliation_results},
        ))

        # 6. AUDIT FINDINGS
        finding_entries = []
        for f in findings:
            finding_entries.append({
                "finding_id": f.get("finding_id", ""),
                "title": f.get("title", ""),
                "description": f.get("description", ""),
                "severity": f.get("severity", "LOW"),
                "impact_amount": f.get("impact_amount", "0.00"),
                "currency": f.get("currency", "INR"),
                "status": f.get("status", "OPEN"),
                "source_evidence": f.get("source_evidence", []),
                "coordinates": f.get("coordinates", {}),
            })

        sections.append(ReportSection(
            section_id=f"{report_id}-S06",
            section_type=ReportSectionType.AUDIT_FINDINGS,
            title="Audit Findings",
            content={"findings": finding_entries},
            finding_references=[f.get("finding_id", "") for f in findings],
        ))

        # 7. COUNTER-EVIDENCE ANALYSIS
        ce_entries = []
        for c in counter_evidence:
            ce_entries.append({
                "challenge_id": c.get("challenge_id", ""),
                "finding_id": c.get("finding_id", ""),
                "verdict": c.get("reviewer_verdict", "UNRESOLVED"),
                "rationale": c.get("verdict_rationale", ""),
                "requires_escalation": c.get("requires_escalation", False),
            })

        sections.append(ReportSection(
            section_id=f"{report_id}-S07",
            section_type=ReportSectionType.COUNTER_EVIDENCE_ANALYSIS,
            title="Counter-Evidence Analysis",
            content={"counter_evidence_challenges": ce_entries},
        ))

        # 8. GAP RADAR & COMPLETENESS
        sections.append(ReportSection(
            section_id=f"{report_id}-S08",
            section_type=ReportSectionType.GAP_RADAR_COMPLETENESS,
            title="GAP RADAR and Audit Completeness",
            content={
                "completeness_status": completeness_status,
                "gaps": gap_register,
                "coverage_disclaimer": "A 100% GAP RADAR score does not prove absence of unknown blind spots.",
            },
        ))

        # 9. HUMAN REVIEW REGISTER
        sections.append(ReportSection(
            section_id=f"{report_id}-S09",
            section_type=ReportSectionType.HUMAN_REVIEW_REGISTER,
            title="Human Review Register",
            content={"review_decisions": human_reviews},
        ))

        # 10. NOT-CHECKED REGISTER
        sections.append(ReportSection(
            section_id=f"{report_id}-S10",
            section_type=ReportSectionType.NOT_CHECKED_REGISTER,
            title="Not-Checked Register",
            content={"not_checked_items": not_checked_items},
        ))

        # 11. RULEBOOK & TAX METHODOLOGY
        sections.append(ReportSection(
            section_id=f"{report_id}-S11",
            section_type=ReportSectionType.RULEBOOK_TAX_METHODOLOGY,
            title="Rulebook and Tax Methodology",
            content={
                "applicable_statute": rulebook_version,
                "financial_periods": financial_periods,
                "income_tax_act_2025_guard": "FY 2026-27 onwards blocked until statutory rules gazetted.",
            },
        ))

        # 12. LIMITATIONS & DISCLAIMERS
        limitations = [
            "AI-assisted analysis is advisory only. Professional auditor judgement is required.",
            "AUDRYN does not issue statutory audit opinions.",
        ]
        if is_synthetic:
            limitations.insert(0,
                "This report uses SYNTHETIC demonstration data. "
                "The entity, CIN, and financial records are entirely fictional."
            )

        sections.append(ReportSection(
            section_id=f"{report_id}-S12",
            section_type=ReportSectionType.LIMITATIONS_DISCLAIMERS,
            title="Limitations and Disclaimers",
            content={"limitations": limitations},
        ))

        # --- Evaluate Release Gate ---
        gate = ReleaseGateService()
        gate_result = gate.evaluate(
            completeness_status=completeness_status,
            findings=findings,
            counter_evidence=counter_evidence,
            gap_register=gap_register,
            human_review_status=human_review_status,
            not_checked_items=not_checked_items,
            evidence_records=evidence_records,
        )

        report_status = ReportStatus.DRAFT
        if gate_result.passed:
            report_status = ReportStatus.REVIEW_READY
        else:
            report_status = ReportStatus.BLOCKED

        # --- Build manifest ---
        manifest = ReportManifest(
            report_id=report_id,
            audit_id=audit_id,
            report_version=version,
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            evidence_document_count=len(evidence_records),
            evidence_sha256_manifest=evidence_hashes,
            finding_count=total_findings,
            finding_ids=[f.get("finding_id", "") for f in findings],
            rulebook_version=rulebook_version,
            financial_periods=financial_periods,
        )

        report = AuditReport(
            report_id=report_id,
            audit_id=audit_id,
            report_version=version,
            report_status=report_status,
            company_name=company_name,
            company_id=company_id,
            financial_periods=financial_periods,
            is_synthetic_data=is_synthetic,
            sections=sections,
            manifest=manifest,
            release_gate_result=gate_result.to_dict(),
        )
        report.report_content_hash = report.compute_content_hash()
        if manifest:
            manifest.report_content_hash = report.report_content_hash

        # Persist
        self._persist_report(report)

        return report

    def finalize_report(self, report_id: str, version: int) -> AuditReport:
        """
        Transitions a REVIEW_READY report to FINALIZED.
        Raises if the report is BLOCKED or already FINALIZED.
        """
        report = self.get_report(report_id, version)
        if not report:
            raise ValueError(f"Report {report_id} v{version} not found.")
        if report.report_status == ReportStatus.BLOCKED:
            raise ValueError("Cannot finalize a BLOCKED report. Resolve all blockers first.")
        if report.report_status == ReportStatus.FINALIZED:
            raise ValueError("Report is already FINALIZED and immutable.")
        if report.report_status == ReportStatus.DRAFT:
            raise ValueError("Report must be REVIEW_READY before finalization.")

        report.report_status = ReportStatus.FINALIZED
        report.report_content_hash = report.compute_content_hash()
        self._persist_report(report)
        return report

    def get_report(self, report_id: str, version: Optional[int] = None) -> Optional[AuditReport]:
        """Retrieve a report by ID and optional version (latest if None)."""
        with self._lock:
            if version is not None:
                cursor = self._conn.execute(
                    "SELECT report_json FROM reports WHERE report_id = ? AND report_version = ?;",
                    (report_id, version),
                )
            else:
                cursor = self._conn.execute(
                    "SELECT report_json FROM reports WHERE report_id = ? ORDER BY report_version DESC LIMIT 1;",
                    (report_id,),
                )
            row = cursor.fetchone()
            if not row:
                return None
            return AuditReport.model_validate_json(row[0])

    def list_report_versions(self, report_id: str) -> List[Dict[str, Any]]:
        """Lists all versions of a report."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT report_version, report_status, generated_at_utc, content_hash FROM reports WHERE report_id = ? ORDER BY report_version ASC;",
                (report_id,),
            )
            return [
                {"version": r[0], "status": r[1], "generated_at": r[2], "content_hash": r[3]}
                for r in cursor.fetchall()
            ]

    def _next_version(self, report_id: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT MAX(report_version) FROM reports WHERE report_id = ?;",
                (report_id,),
            )
            row = cursor.fetchone()
            return (row[0] or 0) + 1

    def _persist_report(self, report: AuditReport):
        with self._lock, self._conn:
            self._conn.execute("""
            INSERT OR REPLACE INTO reports (report_id, audit_id, report_version, report_status, generated_at_utc, report_json, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                report.report_id,
                report.audit_id,
                report.report_version,
                report.report_status.value,
                report.generated_at_utc,
                report.model_dump_json(),
                report.report_content_hash or "",
            ))

    def export_json(self, report: AuditReport) -> str:
        """Exports the report as a machine-readable JSON string."""
        return report.model_dump_json(indent=2)

    def close(self):
        with self._lock:
            if self._conn:
                self._conn.close()
