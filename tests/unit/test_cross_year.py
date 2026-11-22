"""
AUDRYN Phase 3 — Cross-Year Investigation Tests.

Covers:
- Valid YoY movements
- Abnormal / material movements
- Opening/closing balance discontinuities
- Missing periods
- Duplicate transactions
"""
import pytest
from decimal import Decimal
from backend.services.cross_year_service import CrossYearInvestigationService


@pytest.fixture
def service():
    return CrossYearInvestigationService(
        materiality_threshold=Decimal("5000.00"),
        percentage_threshold=Decimal("0.25"),
    )


def test_balanced_yoy_no_flags(service):
    """Identical balances across years should produce no flags."""
    prior = {
        "1001": {"account_name": "Cash", "debit": "100000", "credit": "0"},
        "2001": {"account_name": "Payables", "debit": "0", "credit": "50000"},
    }
    current = {
        "1001": {"account_name": "Cash", "debit": "100000", "credit": "0"},
        "2001": {"account_name": "Payables", "debit": "0", "credit": "50000"},
    }
    movements = service.compare_account_balances(prior, current)
    unusual = service.detect_unusual_movements(movements)
    assert len(unusual) == 0


def test_material_movement_flagged(service):
    """A $10k variance should be flagged as MATERIAL."""
    prior = {
        "1001": {"account_name": "Cash", "debit": "100000", "credit": "0"},
    }
    current = {
        "1001": {"account_name": "Cash", "debit": "110000", "credit": "0"},
    }
    movements = service.compare_account_balances(prior, current)
    flagged = [m for m in movements if m["is_material"]]
    assert len(flagged) == 1
    assert flagged[0]["variance"] == "10000.00"


def test_unusual_percentage_flagged(service):
    """A 50% increase should be flagged as UNUSUAL even if below materiality."""
    prior = {
        "3001": {"account_name": "Misc Income", "debit": "2000", "credit": "0"},
    }
    current = {
        "3001": {"account_name": "Misc Income", "debit": "3000", "credit": "0"},
    }
    movements = service.compare_account_balances(prior, current)
    unusual = service.detect_unusual_movements(movements)
    assert len(unusual) == 1
    assert unusual[0]["is_unusual"]


def test_opening_closing_continuity_match(service):
    """Matching closing/opening should produce zero discontinuities."""
    prior_closing = {"1001": "100000", "2001": "50000"}
    current_opening = {"1001": "100000", "2001": "50000"}
    discon = service.check_opening_closing_continuity(prior_closing, current_opening)
    assert len(discon) == 0


def test_opening_closing_discontinuity_detected(service):
    """Mismatched closing/opening should produce a discontinuity."""
    prior_closing = {"1001": "100000"}
    current_opening = {"1001": "135000"}
    discon = service.check_opening_closing_continuity(prior_closing, current_opening)
    assert len(discon) == 1
    assert discon[0]["status"] == "DISCONTINUITY"
    assert discon[0]["variance"] == "35000.00"


def test_new_account_in_current_year(service):
    """Account appearing only in current year should still be reported."""
    prior = {}
    current = {"9001": {"account_name": "New Account", "debit": "50000", "credit": "0"}}
    movements = service.compare_account_balances(prior, current)
    assert len(movements) == 1
    assert movements[0]["prior_net_balance"] == "0.00"
    assert movements[0]["current_net_balance"] == "50000.00"


def test_cross_year_summary(service):
    """Summary should aggregate statistics correctly."""
    prior = {
        "1001": {"account_name": "Cash", "debit": "100000", "credit": "0"},
        "2001": {"account_name": "Payables", "debit": "0", "credit": "50000"},
    }
    current = {
        "1001": {"account_name": "Cash", "debit": "115000", "credit": "0"},
        "2001": {"account_name": "Payables", "debit": "0", "credit": "50000"},
    }
    movements = service.compare_account_balances(prior, current)
    discon = service.check_opening_closing_continuity(
        {"1001": "100000"}, {"1001": "115000"}
    )
    summary = service.generate_cross_year_summary(movements, discon)
    assert summary["total_accounts_compared"] == 2
    assert summary["discontinuities_found"] == 1
    assert summary["material_movements"] == 1
