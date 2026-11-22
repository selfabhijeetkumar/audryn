import pytest
from decimal import Decimal
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.models.financial import (
    CurrencyCode,
    ValidationStatus,
    TrialBalanceItem,
    GeneralLedger,
    GeneralLedgerEntry,
    DepreciationMethod,
)


@pytest.fixture
def engine():
    return DeterministicFinancialEngine()


def test_balanced_trial_balance(engine):
    items = [
        TrialBalanceItem(account_code="1001", account_name="Cash", debit=Decimal("15000.50"), credit=Decimal("0.00")),
        TrialBalanceItem(account_code="2001", account_name="Capital", debit=Decimal("0.00"), credit=Decimal("15000.50")),
    ]
    tb, calc = engine.verify_trial_balance(items, "FY2024-25", "Test Corp")
    assert tb.is_balanced is True
    assert tb.variance == Decimal("0.00")
    assert calc.validation_status == ValidationStatus.BALANCED


def test_unbalanced_trial_balance(engine):
    items = [
        TrialBalanceItem(account_code="1001", account_name="Cash", debit=Decimal("15000.00"), credit=Decimal("0.00")),
        TrialBalanceItem(account_code="2001", account_name="Capital", debit=Decimal("0.00"), credit=Decimal("14000.00")),
    ]
    tb, calc = engine.verify_trial_balance(items, "FY2024-25", "Test Corp")
    assert tb.is_balanced is False
    assert tb.variance == Decimal("1000.00")
    assert calc.validation_status == ValidationStatus.UNBALANCED


def test_balance_sheet_equation(engine):
    # Assets (100,000) = Liabilities (60,000) + Equity (40,000)
    bs, calc = engine.verify_balance_sheet(
        total_assets=Decimal("100000.00"),
        total_liabilities=Decimal("60000.00"),
        total_equity=Decimal("40000.00"),
        fiscal_year="FY2024-25",
        entity_name="Test Corp",
    )
    assert bs.is_balanced is True
    assert bs.variance == Decimal("0.00")

    # Unbalanced scenario
    bs_unbalanced, _ = engine.verify_balance_sheet(
        total_assets=Decimal("105000.00"),
        total_liabilities=Decimal("60000.00"),
        total_equity=Decimal("40000.00"),
        fiscal_year="FY2024-25",
        entity_name="Test Corp",
    )
    assert bs_unbalanced.is_balanced is False
    assert bs_unbalanced.variance == Decimal("5000.00")


def test_general_ledger_reconciliation(engine):
    entries = [
        GeneralLedgerEntry(entry_id="E1", date="2024-04-10", voucher_id="V1", account_code="4001", account_name="Revenue", description="Sale", debit=Decimal("0.00"), credit=Decimal("5000.00")),
        GeneralLedgerEntry(entry_id="E2", date="2024-05-15", voucher_id="V2", account_code="4001", account_name="Revenue", description="Sale", debit=Decimal("0.00"), credit=Decimal("7000.00")),
    ]
    gl = GeneralLedger(
        account_code="4001",
        account_name="Revenue",
        fiscal_year="FY2024-25",
        opening_balance=Decimal("0.00"),
        entries=entries,
        reported_closing_balance=Decimal("-12000.00"), # Net movement = 0 - 12000
    )
    reconciled_gl, calc = engine.reconcile_general_ledger(gl)
    assert reconciled_gl.is_reconciled is True
    assert reconciled_gl.reconciliation_variance == Decimal("0.00")


def test_decimal_precision_and_rounding(engine):
    # Verify no float IEEE 754 precision issues (0.1 + 0.2 == 0.3)
    val1 = Decimal("0.10")
    val2 = Decimal("0.20")
    summed = engine.round_currency(val1 + val2)
    assert summed == Decimal("0.30")

    # Half-up rounding test: 12.345 -> 12.35
    half_up = engine.round_currency(Decimal("12.345"))
    assert half_up == Decimal("12.35")


def test_cross_year_comparison_and_materiality(engine):
    metric = engine.compare_cross_year_metrics(
        metric_name="Inventory",
        fy1_val=Decimal("450000.00"),
        fy2_val=Decimal("485000.00"),
        fy3_val=Decimal("520000.00"),
        materiality_limit=Decimal("10000.00"),
    )
    assert metric.yoy_change_1_2 == Decimal("35000.00")
    assert metric.yoy_change_2_3 == Decimal("35000.00")
    assert metric.materiality_breached is True


def test_demonstration_corporate_tax(engine):
    # Gross Profit: 1,000,000, Allowable: 400,000, Disallowed: 100,000
    # Taxable = 700,000
    # Base Tax @ 25% = 175,000
    # Surcharge @ 7% = 12,250
    # Cess @ 4% of (175,000 + 12,250 = 187,250) = 7,490
    # Total = 194,740.00
    total_tax, calc = engine.compute_demonstration_corporate_tax(
        gross_profit=Decimal("1000000.00"),
        allowable_expenses=Decimal("400000.00"),
        disallowed_expenses=Decimal("100000.00"),
    )
    assert total_tax == Decimal("194740.00")
    assert calc.input_values["taxable_income"] == "700000.00"


def test_depreciation_wdv_and_slm(engine):
    # WDV: Cost 100,000, AccDep 20,000 -> Opening NBV 80,000. Rate 15% -> 12,000. Closing = 68,000
    dep_wdv, closing_wdv, _ = engine.compute_depreciation(
        asset_cost=Decimal("100000.00"),
        accumulated_depreciation=Decimal("20000.00"),
        rate=Decimal("0.15"),
        method=DepreciationMethod.WDV,
    )
    assert dep_wdv == Decimal("12000.00")
    assert closing_wdv == Decimal("68000.00")

    # SLM: Cost 100,000, AccDep 20,000. Rate 10% -> 10,000. Closing = 70,000
    dep_slm, closing_slm, _ = engine.compute_depreciation(
        asset_cost=Decimal("100000.00"),
        accumulated_depreciation=Decimal("20000.00"),
        rate=Decimal("0.10"),
        method=DepreciationMethod.SLM,
    )
    assert dep_slm == Decimal("10000.00")
    assert closing_slm == Decimal("70000.00")
