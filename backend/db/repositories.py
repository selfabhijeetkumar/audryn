"""
AUDRYN Persistent Repositories and Data Access Layer.
Maps SQLite rows to domain Pydantic schemas with transaction boundaries.
"""
import json
import secrets
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.db.connection import db_manager
from backend.models.evidence import EvidenceRecord, DocumentType, ExtractionStatus
from backend.models.counter_evidence import ReviewVerdict, CounterEvidenceChallenge
from backend.models.investigation import InvestigationFinding, FindingCategory, FindingSeverity
from backend.models.not_checked import NotCheckedItem, ProcedureStatus, AuditArea
from backend.models.report import ReportStatus, ReportManifest


class EvidenceRepository:

    @staticmethod
    def create(
        evidence_id: str,
        engagement_id: str,
        original_filename: str,
        sha256_hash: str,
        file_size_bytes: int,
        document_type: str,
        extraction_status: str,
        raw_storage_path: str,
        uploaded_by: str,
        page_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO evidence_records (
                    evidence_id, engagement_id, original_filename, sha256_hash,
                    file_size_bytes, document_type, extraction_status, page_count,
                    raw_storage_path, uploaded_by, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    evidence_id,
                    engagement_id,
                    original_filename,
                    sha256_hash,
                    file_size_bytes,
                    document_type,
                    extraction_status,
                    page_count,
                    raw_storage_path,
                    uploaded_by,
                    json.dumps(metadata or {}),
                ),
            )
        return EvidenceRepository.get_by_id(engagement_id, evidence_id)

    @staticmethod
    def get_by_id(engagement_id: str, evidence_id: str) -> Optional[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM evidence_records
                WHERE engagement_id = ? AND evidence_id = ?;
                """,
                (engagement_id, evidence_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            data["metadata"] = json.loads(data["metadata_json"] or "{}")
            return data
        finally:
            conn.close()

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM evidence_records
                WHERE engagement_id = ?
                ORDER BY uploaded_at DESC;
                """,
                (engagement_id,),
            )
            records = []
            for row in cur.fetchall():
                d = dict(row)
                d["metadata"] = json.loads(d["metadata_json"] or "{}")
                records.append(d)
            return records
        finally:
            conn.close()


class EvidenceValidityRepository:

    @staticmethod
    def record_decision(
        decision_id: str,
        evidence_id: str,
        engagement_id: str,
        reviewer_id: str,
        reviewer_role: str,
        status: str,
        purpose_scope: str,
        rationale: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO evidence_validity_decisions (
                    decision_id, evidence_id, engagement_id, reviewer_id,
                    reviewer_role, status, purpose_scope, rationale, decided_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    decision_id,
                    evidence_id,
                    engagement_id,
                    reviewer_id,
                    reviewer_role,
                    status,
                    purpose_scope,
                    rationale,
                    now,
                ),
            )
        return {
            "decision_id": decision_id,
            "evidence_id": evidence_id,
            "engagement_id": engagement_id,
            "reviewer_id": reviewer_id,
            "reviewer_role": reviewer_role,
            "status": status,
            "purpose_scope": purpose_scope,
            "rationale": rationale,
            "decided_at": now,
        }

    @staticmethod
    def list_decisions(engagement_id: str, evidence_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            if evidence_id:
                cur.execute(
                    """
                    SELECT evd.*, u.full_name as reviewer_name
                    FROM evidence_validity_decisions evd
                    JOIN users u ON evd.reviewer_id = u.user_id
                    WHERE evd.engagement_id = ? AND evd.evidence_id = ?
                    ORDER BY evd.decided_at DESC;
                    """,
                    (engagement_id, evidence_id),
                )
            else:
                cur.execute(
                    """
                    SELECT evd.*, u.full_name as reviewer_name
                    FROM evidence_validity_decisions evd
                    JOIN users u ON evd.reviewer_id = u.user_id
                    WHERE evd.engagement_id = ?
                    ORDER BY evd.decided_at DESC;
                    """,
                    (engagement_id,),
                )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


class NotCheckedRepository:

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM not_checked_items WHERE engagement_id = ? ORDER BY procedure_id;",
                (engagement_id,),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def create_or_update(
        procedure_id: str,
        engagement_id: str,
        audit_area: str,
        title: str,
        description: str,
        status: str = "NOT_CHECKED",
        reason_not_checked: Optional[str] = None,
        mitigating_notes: Optional[str] = None,
        assigned_reviewer: str = "Unassigned",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO not_checked_items (
                    procedure_id, engagement_id, audit_area, title, description,
                    status, reason_not_checked, mitigating_notes, assigned_reviewer,
                    created_at, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(procedure_id) DO UPDATE SET
                    audit_area = excluded.audit_area,
                    title = excluded.title,
                    description = excluded.description,
                    status = excluded.status,
                    reason_not_checked = excluded.reason_not_checked,
                    mitigating_notes = excluded.mitigating_notes,
                    assigned_reviewer = excluded.assigned_reviewer,
                    last_updated = excluded.last_updated;
                """,
                (
                    procedure_id,
                    engagement_id,
                    audit_area,
                    title,
                    description,
                    status,
                    reason_not_checked,
                    mitigating_notes,
                    assigned_reviewer,
                    now,
                    now,
                ),
            )
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM not_checked_items WHERE procedure_id = ?;", (procedure_id,))
            return dict(cur.fetchone())
        finally:
            conn.close()


class FindingsRepository:

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT f.*,
                    (SELECT hr.decision FROM human_reviews hr WHERE hr.finding_id = f.finding_id ORDER BY hr.decided_at DESC LIMIT 1) as latest_decision,
                    (SELECT hr.reviewer_name FROM human_reviews hr WHERE hr.finding_id = f.finding_id ORDER BY hr.decided_at DESC LIMIT 1) as latest_reviewer_name,
                    (SELECT hr.reviewer_membership_no FROM human_reviews hr WHERE hr.finding_id = f.finding_id ORDER BY hr.decided_at DESC LIMIT 1) as latest_membership_no,
                    (SELECT hr.decided_at FROM human_reviews hr WHERE hr.finding_id = f.finding_id ORDER BY hr.decided_at DESC LIMIT 1) as latest_decided_at,
                    (SELECT hr.comments FROM human_reviews hr WHERE hr.finding_id = f.finding_id ORDER BY hr.decided_at DESC LIMIT 1) as latest_comments
                FROM findings f
                WHERE f.engagement_id = ?
                ORDER BY f.finding_id;
                """,
                (engagement_id,),
            )
            findings = []
            for row in cur.fetchall():
                d = dict(row)
                d["source_evidence_ids"] = json.loads(d["source_evidence_ids_json"] or "[]")
                d["coordinates"] = json.loads(d["coordinates_json"] or "{}")

                # Get counter-evidence challenge for finding
                cur2 = conn.cursor()
                cur2.execute(
                    "SELECT * FROM counter_evidence_challenges WHERE finding_id = ?;",
                    (d["finding_id"],),
                )
                ce_row = cur2.fetchone()
                if ce_row:
                    ce_dict = dict(ce_row)
                    d["counter_evidence"] = {
                        "challenge_id": ce_dict["challenge_id"],
                        "verdict": ce_dict["reviewer_verdict"],
                        "original_hypothesis": ce_dict["original_hypothesis"],
                        "supporting_points": json.loads(ce_dict["supporting_evidence_json"] or "[]"),
                        "contradicting_points": json.loads(ce_dict["contradictory_evidence_json"] or "[]"),
                        "alternative_explanation": (json.loads(ce_dict["alternative_explanations_json"] or "[]") or [""])[0],
                        "calculation_verification": ce_dict["calculation_verification"],
                        "remaining_unknowns": [ce_dict["notes"]] if ce_dict["notes"] else [],
                    }
                else:
                    d["counter_evidence"] = {
                        "verdict": "UNRESOLVED",
                        "supporting_points": [],
                        "contradicting_points": [],
                        "alternative_explanation": "",
                        "calculation_verification": "No verification recorded.",
                        "remaining_unknowns": [],
                    }

                # Human review payload
                if d["latest_decision"]:
                    d["human_review"] = {
                        "status": d["latest_decision"],
                        "reviewer_name": d["latest_reviewer_name"],
                        "reviewer_membership_no": d["latest_membership_no"],
                        "decided_at": d["latest_decided_at"],
                        "reason": d["latest_comments"],
                    }
                else:
                    d["human_review"] = {"status": "PENDING"}

                findings.append(d)
            return findings
        finally:
            conn.close()

    @staticmethod
    def get_by_id(engagement_id: str, finding_id: str) -> Optional[Dict[str, Any]]:
        all_findings = FindingsRepository.list_by_engagement(engagement_id)
        for f in all_findings:
            if f["finding_id"] == finding_id:
                return f
        return None

    @staticmethod
    def create(
        finding_id: str,
        engagement_id: str,
        title: str,
        category: str,
        severity: str,
        impact_amount: str,
        currency: str,
        source_evidence_ids: List[str],
        agent_role: str,
        coordinates: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO findings (
                    finding_id, engagement_id, title, category, severity,
                    impact_amount, currency, source_evidence_ids_json, coordinates_json, agent_role
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(finding_id) DO UPDATE SET
                    title = excluded.title,
                    severity = excluded.severity,
                    impact_amount = excluded.impact_amount;
                """,
                (
                    finding_id,
                    engagement_id,
                    title,
                    category,
                    severity,
                    impact_amount,
                    currency,
                    json.dumps(source_evidence_ids),
                    json.dumps(coordinates or {}),
                    agent_role,
                ),
            )
        return FindingsRepository.get_by_id(engagement_id, finding_id)


class CounterEvidenceRepository:

    @staticmethod
    def create_or_update(
        challenge_id: str,
        finding_id: str,
        engagement_id: str,
        original_hypothesis: str,
        supporting_evidence: List[str],
        contradictory_evidence: List[str],
        alternative_explanations: List[str],
        calculation_verification: str,
        reviewer_role: str,
        reviewer_verdict: str,
        verdict_rationale: str,
        requires_escalation: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO counter_evidence_challenges (
                    challenge_id, finding_id, engagement_id, original_hypothesis,
                    supporting_evidence_json, contradictory_evidence_json, alternative_explanations_json,
                    calculation_verification, reviewer_role, reviewer_verdict, verdict_rationale,
                    requires_escalation, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(challenge_id) DO UPDATE SET
                    reviewer_verdict = excluded.reviewer_verdict,
                    verdict_rationale = excluded.verdict_rationale,
                    notes = excluded.notes;
                """,
                (
                    challenge_id,
                    finding_id,
                    engagement_id,
                    original_hypothesis,
                    json.dumps(supporting_evidence),
                    json.dumps(contradictory_evidence),
                    json.dumps(alternative_explanations),
                    calculation_verification,
                    reviewer_role,
                    reviewer_verdict,
                    verdict_rationale,
                    1 if requires_escalation else 0,
                    notes,
                ),
            )
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM counter_evidence_challenges WHERE challenge_id = ?;", (challenge_id,))
            return dict(cur.fetchone())
        finally:
            conn.close()


class HumanReviewRepository:

    @staticmethod
    def record_decision(
        review_id: str,
        audit_id: str,
        finding_id: str,
        engagement_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_role: str,
        reviewer_membership_no: str,
        decision: str,
        comments: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO human_reviews (
                    review_id, audit_id, finding_id, engagement_id, reviewer_id,
                    reviewer_name, reviewer_role, reviewer_membership_no, decision, comments, decided_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    review_id,
                    audit_id,
                    finding_id,
                    engagement_id,
                    reviewer_id,
                    reviewer_name,
                    reviewer_role,
                    reviewer_membership_no,
                    decision,
                    comments,
                    now,
                ),
            )
        return {
            "review_id": review_id,
            "audit_id": audit_id,
            "finding_id": finding_id,
            "engagement_id": engagement_id,
            "reviewer_name": reviewer_name,
            "reviewer_role": reviewer_role,
            "reviewer_membership_no": reviewer_membership_no,
            "decision": decision,
            "comments": comments,
            "decided_at": now,
        }

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM human_reviews WHERE engagement_id = ? ORDER BY decided_at DESC;",
                (engagement_id,),
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()


class CalculationRepository:

    @staticmethod
    def create(
        calculation_id: str,
        engagement_id: str,
        calculation_name: str,
        statutory_section: Optional[str],
        method: str,
        input_values: Dict[str, str],
        result: str,
        variance: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO calculation_records (
                    calculation_id, engagement_id, calculation_name, statutory_section,
                    method, input_values_json, result, variance, is_verified, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(calculation_id) DO UPDATE SET
                    input_values_json = excluded.input_values_json,
                    result = excluded.result,
                    variance = excluded.variance,
                    notes = excluded.notes;
                """,
                (
                    calculation_id,
                    engagement_id,
                    calculation_name,
                    statutory_section,
                    method,
                    json.dumps(input_values),
                    result,
                    variance,
                    notes,
                ),
            )
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM calculation_records WHERE calculation_id = ?;", (calculation_id,))
            row = cur.fetchone()
            d = dict(row)
            d["input_values"] = json.loads(d["input_values_json"] or "{}")
            return d
        finally:
            conn.close()

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM calculation_records WHERE engagement_id = ? ORDER BY calculation_id;",
                (engagement_id,),
            )
            items = []
            for row in cur.fetchall():
                d = dict(row)
                d["input_values"] = json.loads(d["input_values_json"] or "{}")
                items.append(d)
            return items
        finally:
            conn.close()


class ReportRepository:

    @staticmethod
    def create_or_update(
        report_id: str,
        audit_id: str,
        engagement_id: str,
        report_version: int,
        report_status: str,
        company_name: str,
        financial_periods: List[str],
        report_content_hash: str,
        manifest_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO audit_reports (
                    report_id, audit_id, engagement_id, report_version, report_status,
                    company_name, financial_periods_json, report_content_hash, manifest_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(report_id) DO UPDATE SET
                    report_status = excluded.report_status,
                    report_content_hash = excluded.report_content_hash,
                    manifest_json = excluded.manifest_json;
                """,
                (
                    report_id,
                    audit_id,
                    engagement_id,
                    report_version,
                    report_status,
                    company_name,
                    json.dumps(financial_periods),
                    report_content_hash,
                    json.dumps(manifest_data),
                ),
            )
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM audit_reports WHERE report_id = ?;", (report_id,))
            row = cur.fetchone()
            d = dict(row)
            d["manifest"] = json.loads(d["manifest_json"] or "{}")
            d["financial_periods"] = json.loads(d["financial_periods_json"] or "[]")
            return d
        finally:
            conn.close()

    @staticmethod
    def get_latest_by_engagement(engagement_id: str) -> Optional[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM audit_reports WHERE engagement_id = ? ORDER BY created_at DESC LIMIT 1;",
                (engagement_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["manifest"] = json.loads(d["manifest_json"] or "{}")
            d["financial_periods"] = json.loads(d["financial_periods_json"] or "[]")
            return d
        finally:
            conn.close()


class AuditEventRepository:

    @staticmethod
    def log_event(
        engagement_id: str,
        user_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event_id = f"EVT-{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (event_id, engagement_id, user_id, event_type, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (event_id, engagement_id, user_id, event_type, json.dumps(details or {}), now),
            )
        return {
            "event_id": event_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "event_type": event_type,
            "details": details or {},
            "created_at": now,
        }

    @staticmethod
    def list_by_engagement(engagement_id: str) -> List[Dict[str, Any]]:
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ae.*, u.full_name as user_name, u.role as user_role
                FROM audit_events ae
                JOIN users u ON ae.user_id = u.user_id
                WHERE ae.engagement_id = ?
                ORDER BY ae.created_at DESC;
                """,
                (engagement_id,),
            )
            events = []
            for r in cur.fetchall():
                d = dict(r)
                d["details"] = json.loads(d["details_json"] or "{}")
                events.append(d)
            return events
        finally:
            conn.close()
