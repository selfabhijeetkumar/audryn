import pytest
from backend.services.not_checked_service import NotCheckedRegisterService
from backend.models.not_checked import ProcedureStatus, AuditArea, NotCheckedItem


@pytest.fixture
def register_service(tmp_path):
    f = str(tmp_path / "not_checked.json")
    return NotCheckedRegisterService(persistence_file=f)


def test_initial_register_population(register_service):
    items = register_service.list_items()
    assert len(items) >= 8
    summary = register_service.get_summary()
    assert summary["unresolved_count"] == summary["total_procedures"]
    assert summary["completion_percentage"] == 0.0


def test_create_and_retrieve_procedure(register_service):
    item = NotCheckedItem(
        procedure_id="PROC-CUSTOM-01",
        audit_area=AuditArea.TAX_COMPLIANCE,
        title="Custom Transfer Pricing Review",
        description="Review international related-party transactions.",
        status=ProcedureStatus.NOT_CHECKED,
        required_evidence=["TRANSFER_PRICING_STUDY"],
    )
    register_service.create_item(item)
    retrieved = register_service.get_item("PROC-CUSTOM-01")
    assert retrieved is not None
    assert retrieved.title == "Custom Transfer Pricing Review"


def test_block_procedure(register_service):
    register_service.block_item("PROC-DEP-01", reason="Fixed Asset Register not provided by client.")
    item = register_service.get_item("PROC-DEP-01")
    assert item.status == ProcedureStatus.BLOCKED
    assert "not provided" in item.reason_not_checked


def test_complete_procedure(register_service):
    register_service.complete_item("PROC-TB-01", evidence_id="EV-TB-2024", reviewer="Senior Auditor A")
    item = register_service.get_item("PROC-TB-01")
    assert item.status == ProcedureStatus.COMPLETED
    assert item.responsible_reviewer == "Senior Auditor A"
    assert "EV-TB-2024" in item.associated_evidence_ids
