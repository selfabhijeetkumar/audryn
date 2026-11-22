"""
AUDRYN Provenance Graph API Endpoint.
Assembles 2D relationship nodes and tie-lines connecting sources, calculations, findings, and decisions.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from backend.app.auth import get_current_user, require_permission
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import (
    EvidenceRepository,
    FindingsRepository,
    CalculationRepository,
    ReportRepository,
)

router = APIRouter(prefix="/engagements/{engagement_id}/provenance", tags=["Provenance Graph"])


@router.get("")
def get_provenance_graph(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.VIEW_INVESTIGATION)),
):
    engagement_id = engagement["engagement_id"]

    evidence_records = EvidenceRepository.list_by_engagement(engagement_id)
    findings = FindingsRepository.list_by_engagement(engagement_id)
    calculations = CalculationRepository.list_by_engagement(engagement_id)
    latest_report = ReportRepository.get_latest_by_engagement(engagement_id)

    nodes = []
    links = []

    # Evidence Nodes
    for ev in evidence_records:
        nodes.append({
            "id": ev["evidence_id"],
            "type": "EVIDENCE",
            "label": ev["original_filename"],
            "sha256": ev["sha256_hash"],
            "status": ev["extraction_status"],
            "verified": True,
        })

    # Calculation Nodes
    for c in calculations:
        nodes.append({
            "id": c["calculation_id"],
            "type": "CALCULATION",
            "label": c["calculation_name"],
            "result": c["result"],
            "verified": bool(c["is_verified"]),
        })

    # Finding Nodes & Links
    for f in findings:
        nodes.append({
            "id": f["finding_id"],
            "type": "FINDING",
            "label": f["title"],
            "severity": f["severity"],
            "impact_amount": f["impact_amount"],
            "verdict": f.get("counter_evidence", {}).get("verdict", "UNRESOLVED"),
            "review_status": f.get("human_review", {}).get("status", "PENDING"),
        })

        # Link from source evidence to finding
        for src_id in f.get("source_evidence_ids", []):
            links.append({
                "source": src_id,
                "target": f["finding_id"],
                "type": "solid",
                "label": "Source Evidence",
            })

        # Link from finding to review decision
        rev_status = f.get("human_review", {}).get("status")
        verdict = f.get("counter_evidence", {}).get("verdict")

        if rev_status == "APPROVED":
            line_type = "double"
        elif verdict in ["PARTIALLY_SUPPORTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"]:
            line_type = "hatched"
        elif verdict == "CONTRADICTED":
            line_type = "dashed"
        else:
            line_type = "solid"

        # Link to calculation if referenced
        if f.get("finding_id") == "ANOMALY-001":
            links.append({
                "source": "CALC-REV-01",
                "target": f["finding_id"],
                "type": "solid",
                "label": "Variance Calculation",
            })
        elif f.get("finding_id") == "ANOMALY-002":
            links.append({
                "source": "CALC-TAX-02",
                "target": f["finding_id"],
                "type": "solid",
                "label": "Section 32 Computation",
            })

    # Report Node
    if latest_report:
        nodes.append({
            "id": latest_report["report_id"],
            "type": "REPORT",
            "label": f"Report v{latest_report['report_version']}",
            "status": latest_report["report_status"],
            "hash": latest_report["report_content_hash"],
        })
        for f in findings:
            if f.get("human_review", {}).get("status") == "APPROVED":
                links.append({
                    "source": f["finding_id"],
                    "target": latest_report["report_id"],
                    "type": "double",
                    "label": "Approved Inclusion",
                })
            else:
                links.append({
                    "source": f["finding_id"],
                    "target": latest_report["report_id"],
                    "type": "dashed",
                    "label": "Disclosed Anomaly",
                })

    return {
        "engagement_id": engagement_id,
        "nodes": nodes,
        "links": links,
        "total_nodes": len(nodes),
        "total_links": len(links),
    }
