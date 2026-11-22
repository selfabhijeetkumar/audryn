"""
AUDRYN Phase 4 — INR Formatting & Currency Tests.

Covers:
- Indian numbering system grouping (Lakhs and Crores)
- ₹ symbol handling and Decimal preservation
- format_inr and format_inr_lakhs_crores functions
- Negative amount formatting in Indian notation
- Spreadsheet currency parsing with ₹ and INR
"""
import pytest
from decimal import Decimal
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.services.spreadsheet_service import SpreadsheetIntelligenceService


def test_format_inr_basic():
    """Verify Indian comma placement: 12,34,567.89."""
    engine = DeterministicFinancialEngine()
    val = Decimal("1234567.89")
    formatted = engine.format_inr(val, include_symbol=True)
    assert formatted == "₹ 12,34,567.89"


def test_format_inr_thousands():
    """Verify thousands formatting: 18,500.00."""
    engine = DeterministicFinancialEngine()
    val = Decimal("18500.00")
    formatted = engine.format_inr(val, include_symbol=True)
    assert formatted == "₹ 18,500.00"


def test_format_inr_negative():
    """Verify negative formatting with Indian grouping."""
    engine = DeterministicFinancialEngine()
    val = Decimal("-50000.00")
    formatted = engine.format_inr(val, include_symbol=True)
    assert formatted == "-₹ 50,000.00"


def test_format_inr_lakhs_crores_expression():
    """Verify word expressions for Lakhs (10^5) and Crores (10^7)."""
    engine = DeterministicFinancialEngine()
    
    # 1.5 Crore
    val_cr = Decimal("15000000.00")
    assert engine.format_inr_lakhs_crores(val_cr) == "₹ 1.50 Crore"
    
    # 45 Lakh
    val_lakh = Decimal("4500000.00")
    assert engine.format_inr_lakhs_crores(val_lakh) == "₹ 45.00 Lakh"
    
    # Below Lakh
    val_small = Decimal("18500.00")
    assert engine.format_inr_lakhs_crores(val_small) == "₹ 18,500.00"


def test_to_decimal_with_inr_and_rupee_symbol():
    """Verify to_decimal parses strings with ₹ and INR cleanly."""
    engine = DeterministicFinancialEngine()
    assert engine.to_decimal("₹ 18,500.00") == Decimal("18500.00")
    assert engine.to_decimal("INR 25,00,000.00") == Decimal("2500000.00")
    assert engine.to_decimal("₹ 1,20,500.50") == Decimal("120500.50")


def test_spreadsheet_currency_normalization_inr():
    """Verify SpreadsheetIntelligenceService normalizes ₹ values without float loss."""
    dec = SpreadsheetIntelligenceService.normalize_currency_decimal("₹ 42,000.00")
    assert dec == Decimal("42000.00")
    assert isinstance(dec, Decimal)
