"""
AUDRYN Phase 4 — Indian Tax Rulebook Tests.

Covers:
- Section 115BAA domestic company eligibility
- Prohibited deduction disallowance (Section 10AA, 35AD, additional depreciation)
- Base tax (22%), flat surcharge (10%), Health & Education Cess (4%)
- Effective tax rate (25.168%)
- Section 32 depreciation blocks & rates
- Section 32 180-day usage restriction (50% statutory rate)
- Pool exhaustion and Section 50 capital gains
- Book vs tax depreciation timing difference reconciliation
- Forward-compatibility guard for Income-tax Act, 2025 (FY 2026-27)
"""
import pytest
from decimal import Decimal
from backend.services.indian_tax_rulebook import IndianTaxRulebookService
from backend.models.tax_rule import (
    TaxpayerCategory,
    TaxRegime,
    VerificationStatus,
)


@pytest.fixture
def rulebook():
    return IndianTaxRulebookService()


class TestSection115BAAEligibility:
    def test_eligible_domestic_company(self, rulebook):
        """Domestic company with Form 10-IC and no prohibited deductions is eligible."""
        is_eligible, notes, disallowed = rulebook.verify_section_115baa_eligibility(
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=True,
            deductions_claimed=[],
        )
        assert is_eligible is True
        assert len(disallowed) == 0
        assert "ELIGIBLE" in notes[0]

    def test_ineligible_foreign_company(self, rulebook):
        """Foreign company cannot opt for Section 115BAA."""
        is_eligible, notes, disallowed = rulebook.verify_section_115baa_eligibility(
            taxpayer_category=TaxpayerCategory.FOREIGN_COMPANY,
            has_exercised_form_10ic=True,
            deductions_claimed=[],
        )
        assert is_eligible is False
        assert "INELIGIBLE" in notes[0]

    def test_ineligible_without_form_10ic(self, rulebook):
        """Company without Form 10-IC cannot opt for Section 115BAA."""
        is_eligible, notes, disallowed = rulebook.verify_section_115baa_eligibility(
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=False,
            deductions_claimed=[],
        )
        assert is_eligible is False
        assert "Form 10-IC" in notes[0]

    def test_ineligible_with_prohibited_section_10aa(self, rulebook):
        """Claiming Section 10AA SEZ deduction violates Section 115BAA(2)."""
        is_eligible, notes, disallowed = rulebook.verify_section_115baa_eligibility(
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=True,
            deductions_claimed=["Section 10AA (SEZ profit)"],
        )
        assert is_eligible is False
        assert len(disallowed) == 1
        assert "Section 10AA" in disallowed[0]

    def test_ineligible_with_prohibited_additional_depreciation(self, rulebook):
        """Claiming additional depreciation under Section 32(1)(iia) is prohibited."""
        is_eligible, notes, disallowed = rulebook.verify_section_115baa_eligibility(
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=True,
            deductions_claimed=["Section 32(1)(iia) additional depreciation"],
        )
        assert is_eligible is False
        assert len(disallowed) == 1


class TestCorporateTaxCalculations:
    def test_section_115baa_exact_effective_rate(self, rulebook):
        """
        Gross Total Income: INR 1,00,00,000 (1 Crore).
        Base Tax (22%): INR 22,00,000.
        Surcharge (10% of base tax): INR 2,20,000.
        Tax + Surcharge: INR 24,20,000.
        Cess (4% of 24,20,000): INR 96,800.
        Total Tax: INR 25,16,800 (Effective rate: 25.168% / 25.17%).
        """
        gti = Decimal("10000000.00")
        result = rulebook.calculate_corporate_tax(
            financial_year="FY 2024-25",
            gross_total_income=gti,
            regime=TaxRegime.SECTION_115BAA_CONCESSIONAL,
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=True,
        )
        assert result.is_eligible is True
        assert result.base_tax == "2200000.00"
        assert result.surcharge == "220000.00"
        assert result.cess == "96800.00"
        assert result.total_tax_liability == "2516800.00"
        assert result.effective_tax_rate_percent == "25.17"
        assert result.verification_status == VerificationStatus.VERIFIED_STATUTORY

    def test_section_115baa_with_allowable_80jjaa(self, rulebook):
        """Section 80JJAA employment deduction is permissible under 115BAA."""
        gti = Decimal("10000000.00")
        result = rulebook.calculate_corporate_tax(
            financial_year="FY 2024-25",
            gross_total_income=gti,
            regime=TaxRegime.SECTION_115BAA_CONCESSIONAL,
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            has_exercised_form_10ic=True,
            deduction_amounts={"Section 80JJAA": Decimal("1000000.00")},
        )
        assert result.is_eligible is True
        assert result.allowable_deductions == "1000000.00"
        assert result.taxable_income == "9000000.00"
        # 9,000,000 * 25.168% = 2,265,120.00
        assert result.total_tax_liability == "2265120.00"

    def test_forward_compatibility_blocks_fy26_27_act_2025(self, rulebook):
        """Income-tax Act, 2025 applies from 1 April 2026. Old 115BAA references are blocked."""
        result = rulebook.calculate_corporate_tax(
            financial_year="FY 2026-27",
            gross_total_income=Decimal("5000000.00"),
            regime=TaxRegime.SECTION_115BAA_CONCESSIONAL,
        )
        assert result.is_eligible is False
        assert "BLOCKED" in result.eligibility_notes[0]
        assert "Income-tax Act, 2025" in result.eligibility_notes[0]


class TestSection32Depreciation:
    def test_plant_machinery_full_year_15_percent(self, rulebook):
        """Opening WDV 10,00,000 + additions > 180 days 2,00,000 @ 15%."""
        res = rulebook.calculate_section_32_depreciation(
            block_id="IN-SEC32-PLANT-MACHINERY-GENERAL",
            opening_wdv=Decimal("1000000.00"),
            additions_used_gte_180_days=Decimal("200000.00"),
        )
        # Pool = 12,00,000. Depreciation @ 15% = 1,80,000. Closing WDV = 10,20,000.
        assert res["total_tax_depreciation"] == "180000.00"
        assert res["closing_wdv"] == "1020000.00"
        assert res["status"] == "DEPRECIATION_ALLOWABLE"

    def test_plant_machinery_less_than_180_days_half_rate(self, rulebook):
        """Additions < 180 days are restricted to 50% rate (7.5%)."""
        res = rulebook.calculate_section_32_depreciation(
            block_id="IN-SEC32-PLANT-MACHINERY-GENERAL",
            opening_wdv=Decimal("1000000.00"),
            additions_used_lt_180_days=Decimal("400000.00"),
        )
        # Pool = 14,00,000.
        # Dep on lt_180 (4,00,000 @ 7.5%) = 30,000.
        # Dep on balance pool (10,00,000 @ 15%) = 1,50,000.
        # Total Dep = 1,80,000. Closing WDV = 12,20,000.
        assert res["depreciation_on_lt_180"] == "30000.00"
        assert res["depreciation_on_balance_pool"] == "150000.00"
        assert res["total_tax_depreciation"] == "180000.00"
        assert res["closing_wdv"] == "1220000.00"

    def test_computers_and_software_40_percent(self, rulebook):
        """Computer hardware and software block @ 40%."""
        res = rulebook.calculate_section_32_depreciation(
            block_id="IN-SEC32-COMPUTERS-SOFTWARE",
            opening_wdv=Decimal("500000.00"),
        )
        # 5,00,000 @ 40% = 2,00,000. Closing = 3,00,000.
        assert res["total_tax_depreciation"] == "200000.00"
        assert res["closing_wdv"] == "300000.00"

    def test_pool_exhaustion_nil_depreciation_capital_gain(self, rulebook):
        """When sales realized exceed pool, depreciation is NIL and capital gain arises."""
        res = rulebook.calculate_section_32_depreciation(
            block_id="IN-SEC32-PLANT-MACHINERY-GENERAL",
            opening_wdv=Decimal("500000.00"),
            sales_realized=Decimal("700000.00"),
        )
        assert res["total_tax_depreciation"] == "0.00"
        assert res["closing_wdv"] == "0.00"
        assert res["status"] == "POOL_EXHAUSTED_NIL_DEPRECIATION"
        assert res["section_50_capital_gain"] == "200000.00"


class TestAccountingVsTaxReconciliation:
    def test_book_depreciation_exceeds_tax_depreciation(self, rulebook):
        """When book dep > tax dep, variance is added back to accounting profit."""
        recon = rulebook.reconcile_accounting_vs_tax_depreciation(
            book_depreciation=Decimal("250000.00"),
            tax_depreciation=Decimal("180000.00"),
        )
        assert recon["timing_difference_inr"] == "70000.00"
        assert "Add back to profit" in recon["tax_impact_description"]
        assert "Clause 17" in recon["statutory_form_3cd_clause"]
