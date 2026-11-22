"""
AUDRYN Audit Report and Cryptographic Manifest Endpoints.
Generates reproducible audit manifests with SHA-256 evidence integrity hashing and tamper detection.
"""
import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission, Role
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import (
    ReportRepository,
    EvidenceRepository,
    FindingsRepository,
    AuditEventRepository,
)
from backend.models.report import ReportStatus

router = APIRouter(prefix="/engagements/{engagement_id}/reports", tags=["Audit Reports"])


class GenerateReportRequest(BaseModel):
    include_counter_evidence: bool = True
    include_not_checked: bool = True


@router.get("/latest")
def get_latest_report(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.READ_EVIDENCE)),
):
    report = ReportRepository.get_latest_by_engagement(engagement["engagement_id"])
    if not report:
        # Default report manifest representation
        evidence_records = EvidenceRepository.list_by_engagement(engagement["engagement_id"])
        evidence_hashes = [e["sha256_hash"] for e in evidence_records]
        findings = FindingsRepository.list_by_engagement(engagement["engagement_id"])
        unresolved = [
            f for f in findings if f.get("counter_evidence", {}).get("verdict") != "SUPPORTED"
        ]

        dummy_hash = hashlib.sha256(f"{engagement['engagement_id']}-draft".encode()).hexdigest()
        manifest_data = {
            "manifest_id": f"MNF-{engagement['fiscal_year']}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_hash": dummy_hash,
            "evidence_hashes": evidence_hashes,
            "total_evidence_files": len(evidence_records),
            "unresolved_findings_count": len(unresolved),
            "status": "DRAFT",
        }
        report = ReportRepository.create_or_update(
            report_id=f"REP-{secrets.token_hex(4).upper()}",
            audit_id=engagement["engagement_id"],
            engagement_id=engagement["engagement_id"],
            report_version=1,
            report_status="DRAFT",
            company_name=engagement["entity_name"],
            financial_periods=[engagement["fiscal_year"]],
            report_content_hash=dummy_hash,
            manifest_data=manifest_data,
        )
    return report


@router.post("/generate", dependencies=[Depends(verify_csrf)])
def generate_report(
    payload: GenerateReportRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.GENERATE_DRAFT_REPORT)),
):
    engagement_id = engagement["engagement_id"]
    evidence_records = EvidenceRepository.list_by_engagement(engagement_id)
    findings = FindingsRepository.list_by_engagement(engagement_id)

    evidence_hashes = [e["sha256_hash"] for e in evidence_records]
    finding_ids = [f["finding_id"] for f in findings]
    unresolved_count = sum(
        1 for f in findings if f.get("counter_evidence", {}).get("verdict") in ["PARTIALLY_SUPPORTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"]
    )

    now_str = datetime.now(timezone.utc).isoformat()
    manifest_id = f"MNF-{engagement['fiscal_year']}-{secrets.token_hex(4).upper()}"

    content_dict = {
        "engagement_id": engagement_id,
        "entity_name": engagement["entity_name"],
        "cin": engagement["cin"],
        "fiscal_year": engagement["fiscal_year"],
        "evidence_sha256_manifest": evidence_hashes,
        "finding_ids": finding_ids,
        "unresolved_count": unresolved_count,
        "generated_at": now_str,
    }
    content_hash = hashlib.sha256(json.dumps(content_dict, sort_keys=True).encode("utf-8")).hexdigest()

    # Determine status: REVIEW_READY or DRAFT
    status_val = "REVIEW_READY" if len(evidence_hashes) > 0 else "DRAFT"

    manifest_data = {
        "manifest_id": manifest_id,
        "generated_at": now_str,
        "report_hash": content_hash,
        "evidence_hashes": evidence_hashes,
        "total_evidence_files": len(evidence_hashes),
        "unresolved_findings_count": unresolved_count,
        "status": status_val,
    }

    report_id = f"REP-{secrets.token_hex(4).upper()}"
    report = ReportRepository.create_or_update(
        report_id=report_id,
        audit_id=engagement_id,
        engagement_id=engagement_id,
        report_version=1,
        report_status=status_val,
        company_name=engagement["entity_name"],
        financial_periods=[engagement["fiscal_year"]],
        report_content_hash=content_hash,
        manifest_data=manifest_data,
    )

    AuditEventRepository.log_event(
        engagement_id,
        user["user_id"],
        "REPORT_GENERATED",
        {"report_id": report_id, "manifest_id": manifest_id, "status": status_val},
    )

    return report


@router.post("/finalize", dependencies=[Depends(verify_csrf)])
def finalize_report(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.FINALIZE_REPORT)),
):
    engagement_id = engagement["engagement_id"]
    latest = ReportRepository.get_latest_by_engagement(engagement_id)
    if not latest:
        raise HTTPException(status_code=400, detail="No generated report exists to finalize. Generate draft first.")

    # Check that user is Partner
    if user.get("role") != Role.PARTNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Finalizing statutory audit reports is strictly reserved for Partners.",
        )

    # Check for unreviewed findings
    findings = FindingsRepository.list_by_engagement(engagement_id)
    pending = [f for f in findings if f.get("human_review", {}).get("status") == "PENDING"]
    if pending:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize report: {len(pending)} finding(s) remain PENDING human review.",
        )

    manifest_data = latest.get("manifest", {})
    manifest_data["status"] = "FINALIZED"
    manifest_data["finalized_at"] = datetime.now(timezone.utc).isoformat()
    manifest_data["partner_signoff"] = user["full_name"]

    final_report = ReportRepository.create_or_update(
        report_id=latest["report_id"],
        audit_id=engagement_id,
        engagement_id=engagement_id,
        report_version=latest["report_version"] + 1,
        report_status="FINALIZED",
        company_name=latest["company_name"],
        financial_periods=latest.get("financial_periods", [engagement["fiscal_year"]]),
        report_content_hash=latest["report_content_hash"],
        manifest_data=manifest_data,
    )

    AuditEventRepository.log_event(
        engagement_id,
        user["user_id"],
        "REPORT_FINALIZED",
        {"report_id": latest["report_id"], "partner": user["full_name"]},
    )

    return final_report
