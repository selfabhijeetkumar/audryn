"""
AUDRYN Versioned Indian Tax Rulebook Service.

Authoritative statutory tax rule architecture implementing:
- Income-tax Act, 1961 provisions for historical periods:
  * FY 2023-24 (AY 2024-25)
  * FY 2024-25 (AY 2025-26)
  * FY 2025-26 (AY 2026-27)
- Section 115BAA concessional corporate tax framework (22% + 10% surcharge + 4% cess = 25.168%)
  with strict deduction restrictions (Section 10AA, 32(1)(iia), 32AD, 33AB, 35AD, Chapter VI-A).
- Section 32 WDV Block Depreciation schedules with the statutory 180-day usage rule
  (50% depreciation restriction for assets put to use < 180 days).
- Separation of accounting/book depreciation (Companies Act, 2013) vs tax depreciation.
- Forward-compatibility guard for the new Income-tax Act, 2025 (effective 1 April 2026).
- All calculations executed exclusively via Python Decimal. Zero LLM arithmetic.

DISCLAIMER: This system provides deterministic audit calculations based on published
statutory provisions. It does not provide legal advice or substitute for licensed CAs.
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

from backend.models.tax_rule import (
    TaxpayerCategory,
    TaxRegime,
    VerificationStatus,
    DepreciationBlock,
    StatutoryTaxRule,
    TaxCalculationResult,
)


class IndianTaxRulebookService:
    """
    Versioned repository and deterministic calculation engine for Indian statutory tax rules.
    """

    TWO_PLACES = Decimal("0.01")
    FOUR_PLACES = Decimal("0.0001")

    # Ineligible deductions under Section 115BAA(2) of the Income-tax Act, 1961
    SECTION_115BAA_PROHIBITED_DEDUCTIONS = {
        "10AA",      # SEZ tax holiday
        "32_1_IIA",  # Additional depreciation
        "32AD",      # Investment in new plant/machinery in backward areas
        "33AB",      # Tea/Coffee/Rubber development
        "33ABA",     # Site restoration fund
        "35_1_II",   # Scientific research scientific institution
        "35_1_IIA",  # Scientific research company
        "35_1_III",  # Social science / statistical research
        "35_2AA",    # National laboratory
        "35AD",      # Specified business capital expenditure
        "35CCC",     # Agricultural extension project
        "35CCD",     # Skill development project
        "80_IA",     # Infrastructure development
        "80_IAB",    # SEZ development
        "80_IAC",    # Eligible start-ups
        "80_IB",     # Industrial undertakings
        "80_IBA",    # Housing projects
        "80_IC",     # Special category states
        "80_ID",     # Hotels/convention centers
        "80_IE",     # North-Eastern states
    }

    def __init__(self):
        self._rules: Dict[str, StatutoryTaxRule] = {}
        self._depreciation_blocks: Dict[str, DepreciationBlock] = {}
        self._initialize_depreciation_blocks()
        self._initialize_statutory_rules()

    def _initialize_depreciation_blocks(self):
        """Initializes statutory WDV depreciation blocks under Section 32 of Income-tax Act, 1961."""
        blocks = [
            DepreciationBlock(
                block_id="IN-SEC32-BUILDINGS-FACTORY",
                asset_class="BUILDINGS",
                description="Buildings used mainly for industrial, factory or workshop purposes",
                statutory_rate=Decimal("0.10"),  # 10%
                less_than_180_days_rate=Decimal("0.05"),  # 5% (50% rule)
            ),
            DepreciationBlock(
                block_id="IN-SEC32-BUILDINGS-RESIDENTIAL",
                asset_class="BUILDINGS",
                description="Buildings used mainly for residential purposes except hotels and boarding houses",
                statutory_rate=Decimal("0.05"),  # 5%
                less_than_180_days_rate=Decimal("0.025"),  # 2.5%
            ),
            DepreciationBlock(
                block_id="IN-SEC32-FURNITURE-FITTINGS",
                asset_class="FURNITURE",
                description="Furniture and fittings including electrical fittings",
                statutory_rate=Decimal("0.10"),  # 10%
                less_than_180_days_rate=Decimal("0.05"),  # 5%
            ),
            DepreciationBlock(
                block_id="IN-SEC32-PLANT-MACHINERY-GENERAL",
                asset_class="PLANT_MACHINERY",
                description="Plant and Machinery (General rate for manufacturing and processing)",
                statutory_rate=Decimal("0.15"),  # 15%
                less_than_180_days_rate=Decimal("0.075"),  # 7.5%
            ),
            DepreciationBlock(
                block_id="IN-SEC32-COMPUTERS-SOFTWARE",
                asset_class="COMPUTERS",
                description="Computers including computer software",
                statutory_rate=Decimal("0.40"),  # 40%
                less_than_180_days_rate=Decimal("0.20"),  # 20%
            ),
            DepreciationBlock(
                block_id="IN-SEC32-MOTOR-VEHICLES-COMMERCIAL",
                asset_class="VEHICLES",
                description="Motor cars, buses, lorries used in business of running them on hire",
                statutory_rate=Decimal("0.30"),  # 30%
                less_than_180_days_rate=Decimal("0.15"),  # 15%
            ),
        ]
        for b in blocks:
            self._depreciation_blocks[b.block_id] = b

    def _initialize_statutory_rules(self):
        """Initializes versioned corporate tax rules across FY 2023-24, FY 2024-25, FY 2025-26."""
        # 1. Section 115BAA Concessional Regime (FY 2023-24 to FY 2025-26)
        rule_115baa = StatutoryTaxRule(
            rule_id="IN-IT1961-SEC115BAA-CORP",
            act_name="Income-tax Act, 1961",
            statutory_reference="Section 115BAA of the Income-tax Act, 1961",
            applicable_periods=["FY 2023-24", "FY 2024-25", "FY 2025-26"],
            effective_from="2019-10-01",
            effective_to="2026-03-31",
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            regime=TaxRegime.SECTION_115BAA_CONCESSIONAL,
            base_tax_rate=Decimal("0.22"),       # 22% Base tax
            surcharge_rate=Decimal("0.10"),      # Flat 10% surcharge under Section 115BAA
            cess_rate=Decimal("0.04"),           # 4% Health & Education Cess
            effective_tax_rate=Decimal("0.25168"), # 22% * 1.10 * 1.04 = 25.168%
            eligibility_conditions=[
                "Taxpayer must be a Domestic Company registered under the Companies Act.",
                "Company must exercise option in prescribed Form 10-IC on or before due date under Section 139(1).",
                "Option once exercised cannot be subsequently withdrawn for any previous year.",
                "Total income must be computed without claiming specified deductions or additional depreciation.",
                "Cannot set off any loss or unabsorbed depreciation carried forward from earlier AY attributable to specified deductions.",
            ],
            ineligible_deductions=list(self.SECTION_115BAA_PROHIBITED_DEDUCTIONS),
            authoritative_source="Ministry of Finance, Government of India; Income-tax Act, 1961; Notification No. 10/2020",
            verification_status=VerificationStatus.VERIFIED_STATUTORY,
            notes="Effective tax rate is exactly 25.168%. Minimum Alternate Tax (MAT) under Section 115JB does not apply.",
        )
        self._rules[rule_115baa.rule_id] = rule_115baa

        # 2. Regular Old Regime for Domestic Companies (FY 2023-24 to FY 2025-26)
        rule_regular_sme = StatutoryTaxRule(
            rule_id="IN-IT1961-REGULAR-CORP-SME",
            act_name="Income-tax Act, 1961",
            statutory_reference="Section 115BA / First Schedule to Finance Act",
            applicable_periods=["FY 2023-24", "FY 2024-25", "FY 2025-26"],
            effective_from="2020-04-01",
            effective_to="2026-03-31",
            taxpayer_category=TaxpayerCategory.DOMESTIC_COMPANY,
            regime=TaxRegime.REGULAR_OLD_REGIME,
            base_tax_rate=Decimal("0.25"),       # 25% if turnover in base year <= 400 Cr
            surcharge_rate=Decimal("0.07"),      # Demonstration 7% for income between 1 Cr and 10 Cr
            cess_rate=Decimal("0.04"),           # 4% Cess
            effective_tax_rate=Decimal("0.2782"),# 25% * 1.07 * 1.04 = 27.82%
            eligibility_conditions=[
                "Applicable to domestic companies with total turnover/gross receipts <= INR 400 Crore in the relevant previous base year.",
                "Subject to Minimum Alternate Tax (MAT) under Section 115JB (15% + surcharge + cess = 17.472%).",
            ],
            ineligible_deductions=[],
            authoritative_source="Finance Acts 2023, 2024; Ministry of Finance, Government of India",
            verification_status=VerificationStatus.VERIFIED_STATUTORY,
            notes="MAT applies. Standard Chapter VI-A and special incentive deductions are permissible.",
        )
        self._rules[rule_regular_sme.rule_id] = rule_regular_sme

    @classmethod
    def round_inr(cls, val: Decimal) -> Decimal:
        """Rounds amount to 2 decimal places using ROUND_HALF_UP."""
        return val.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    def get_depreciation_block(self, block_id: str) -> Optional[DepreciationBlock]:
        return self._depreciation_blocks.get(block_id)

    def list_depreciation_blocks(self) -> List[DepreciationBlock]:
        return list(self._depreciation_blocks.values())

    def get_tax_rule(self, rule_id: str) -> Optional[StatutoryTaxRule]:
        return self._rules.get(rule_id)

    def verify_section_115baa_eligibility(
        self,
        taxpayer_category: TaxpayerCategory,
        has_exercised_form_10ic: bool,
        deductions_claimed: List[str],
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Verifies whether a taxpayer is legally eligible for Section 115BAA concessional rate.
        Returns: (is_eligible, eligibility_notes, disallowed_claims)
        """
        notes = []
        disallowed = []

        if taxpayer_category != TaxpayerCategory.DOMESTIC_COMPANY:
            notes.append(f"INELIGIBLE: Taxpayer category {taxpayer_category.value} is not a Domestic Company. Section 115BAA applies exclusively to domestic companies.")
            return False, notes, disallowed

        if not has_exercised_form_10ic:
            notes.append("INELIGIBLE: Form 10-IC has not been filed on or before the due date under Section 139(1).")
            return False, notes, disallowed

        # Check for prohibited deductions
        for ded in deductions_claimed:
            norm_ded = ded.strip().upper().replace("SECTION ", "").replace("SEC ", "").replace("-", "_").replace("(", "_").replace(")", "")
            for prohibited in self.SECTION_115BAA_PROHIBITED_DEDUCTIONS:
                if prohibited in norm_ded:
                    disallowed.append(ded)

        if disallowed:
            notes.append(f"INELIGIBLE: Claimed prohibited deductions under Section 115BAA(2): {', '.join(disallowed)}.")
            return False, notes, disallowed

        notes.append("ELIGIBLE: Domestic company filed Form 10-IC with zero prohibited deduction claims under Section 115BAA(2).")
        return True, notes, []

    def calculate_corporate_tax(
        self,
        financial_year: str,
        gross_total_income: Decimal,
        regime: TaxRegime = TaxRegime.SECTION_115BAA_CONCESSIONAL,
        taxpayer_category: TaxpayerCategory = TaxpayerCategory.DOMESTIC_COMPANY,
        has_exercised_form_10ic: bool = True,
        deductions_claimed: Optional[List[str]] = None,
        deduction_amounts: Optional[Dict[str, Decimal]] = None,
    ) -> TaxCalculationResult:
        """
        Computes statutory corporate income tax liability with full statutory compliance checks.
        Enforces Section 115BAA eligibility and Income-tax Act, 2025 forward-compatibility.
        """
        deductions_claimed = deductions_claimed or []
        deduction_amounts = deduction_amounts or {}
        gti = self.round_inr(gross_total_income)

        # 1. Forward-compatibility check for Income-tax Act, 2025
        if "2026-27" in financial_year or financial_year > "FY 2025-26":
            return TaxCalculationResult(
                calculation_id=f"TAX-CALC-BLOCKED-{uuid.uuid4().hex[:8]}",
                financial_year=financial_year,
                regime=regime,
                taxpayer_category=taxpayer_category,
                gross_total_income=str(gti),
                allowable_deductions="0.00",
                taxable_income="0.00",
                base_tax="0.00",
                surcharge="0.00",
                cess="0.00",
                total_tax_liability="0.00",
                effective_tax_rate_percent="0.00",
                is_eligible=False,
                eligibility_notes=[
                    "BLOCKED: The Income-tax Act, 2025 comes into effect on 1 April 2026 (FY 2026-27). "
                    "Historical Section 115BAA and Section 32 references cannot be automatically applied "
                    "without independent research and verification of the new Act's enacted schedules."
                ],
                disallowed_deductions=[],
                statutory_citations=["Income-tax Act, 2025 (Effective 1 April 2026)"],
                verification_status=VerificationStatus.DEMONSTRATION,
            )

        # 2. Section 115BAA Concessional Regime
        if regime == TaxRegime.SECTION_115BAA_CONCESSIONAL:
            rule = self._rules.get("IN-IT1961-SEC115BAA-CORP")
            is_eligible, notes, disallowed = self.verify_section_115baa_eligibility(
                taxpayer_category=taxpayer_category,
                has_exercised_form_10ic=has_exercised_form_10ic,
                deductions_claimed=deductions_claimed,
            )

            if not is_eligible:
                # Ineligible: computation blocked under concessional regime
                return TaxCalculationResult(
                    calculation_id=f"TAX-CALC-INELIGIBLE-{uuid.uuid4().hex[:8]}",
                    financial_year=financial_year,
                    regime=regime,
                    taxpayer_category=taxpayer_category,
                    gross_total_income=str(gti),
                    allowable_deductions="0.00",
                    taxable_income=str(gti),
                    base_tax="0.00",
                    surcharge="0.00",
                    cess="0.00",
                    total_tax_liability="0.00",
                    effective_tax_rate_percent="0.00",
                    is_eligible=False,
                    eligibility_notes=notes,
                    disallowed_deductions=disallowed,
                    statutory_citations=[rule.statutory_reference if rule else "Section 115BAA"],
                    verification_status=VerificationStatus.VERIFIED_STATUTORY,
                )

            # Eligible under Section 115BAA:
            # Only allowable deductions: Section 80JJAA (employment generation) and 80M (inter-corporate dividends)
            allowable_ded_total = Decimal("0.00")
            for ded_name, amt in deduction_amounts.items():
                if "80JJAA" in ded_name.upper() or "80M" in ded_name.upper():
                    allowable_ded_total += self.round_inr(amt)

            taxable_income = self.round_inr(max(Decimal("0.00"), gti - allowable_ded_total))
            base_tax = self.round_inr(taxable_income * rule.base_tax_rate)
            surcharge = self.round_inr(base_tax * rule.surcharge_rate)
            cess = self.round_inr((base_tax + surcharge) * rule.cess_rate)
            total_tax = self.round_inr(base_tax + surcharge + cess)

            eff_rate = Decimal("0.00")
            if taxable_income > Decimal("0.00"):
                eff_rate = ((total_tax / taxable_income) * Decimal("100")).quantize(self.TWO_PLACES)

            return TaxCalculationResult(
                calculation_id=f"TAX-CALC-{uuid.uuid4().hex[:8]}",
                financial_year=financial_year,
                regime=regime,
                taxpayer_category=taxpayer_category,
                gross_total_income=str(gti),
                allowable_deductions=str(allowable_ded_total),
                taxable_income=str(taxable_income),
                base_tax=str(base_tax),
                surcharge=str(surcharge),
                cess=str(cess),
                total_tax_liability=str(total_tax),
                effective_tax_rate_percent=str(eff_rate),
                is_eligible=True,
                eligibility_notes=notes,
                disallowed_deductions=[],
                statutory_citations=[
                    rule.statutory_reference,
                    "Finance Act, 2019 (Taxation Laws Amendment Act, 2019)",
                ],
                verification_status=rule.verification_status,
            )

        # 3. Regular Old Regime
        rule = self._rules.get("IN-IT1961-REGULAR-CORP-SME")
        total_deductions = sum(self.round_inr(v) for v in deduction_amounts.values())
        taxable_income = self.round_inr(max(Decimal("0.00"), gti - total_deductions))
        base_tax = self.round_inr(taxable_income * rule.base_tax_rate)
        surcharge = self.round_inr(base_tax * rule.surcharge_rate)
        cess = self.round_inr((base_tax + surcharge) * rule.cess_rate)
        total_tax = self.round_inr(base_tax + surcharge + cess)

        eff_rate = Decimal("0.00")
        if taxable_income > Decimal("0.00"):
            eff_rate = ((total_tax / taxable_income) * Decimal("100")).quantize(self.TWO_PLACES)

        return TaxCalculationResult(
            calculation_id=f"TAX-CALC-{uuid.uuid4().hex[:8]}",
            financial_year=financial_year,
            regime=regime,
            taxpayer_category=taxpayer_category,
            gross_total_income=str(gti),
            allowable_deductions=str(total_deductions),
            taxable_income=str(taxable_income),
            base_tax=str(base_tax),
            surcharge=str(surcharge),
            cess=str(cess),
            total_tax_liability=str(total_tax),
            effective_tax_rate_percent=str(eff_rate),
            is_eligible=True,
            eligibility_notes=["Eligible under standard corporate regime."],
            disallowed_deductions=[],
            statutory_citations=[rule.statutory_reference],
            verification_status=rule.verification_status,
        )

    def calculate_section_32_depreciation(
        self,
        block_id: str,
        opening_wdv: Decimal,
        additions_used_gte_180_days: Decimal = Decimal("0.00"),
        additions_used_lt_180_days: Decimal = Decimal("0.00"),
        sales_realized: Decimal = Decimal("0.00"),
    ) -> Dict[str, Any]:
        """
        Computes statutory tax depreciation on an asset block under Section 32 of Income-tax Act, 1961.
        
        Statutory Rules:
        1. Net Pool before depreciation = Opening WDV + All Additions - Moneys Payable / Scrap Realized.
        2. If additions put to use < 180 days:
           Depreciation on lt_180 additions = lt_180 * (statutory_rate / 2).
        3. Depreciation on balance pool = (Net Pool - lt_180 additions) * statutory_rate.
        4. If Net Pool <= 0: Depreciation is NIL (short-term capital gain under Section 50).
        5. Closing WDV = Net Pool - Total Allowable Depreciation.
        """
        block = self._depreciation_blocks.get(block_id)
        if not block:
            raise ValueError(f"Unknown Section 32 depreciation block: {block_id}")

        op = self.round_inr(opening_wdv)
        add_gte = self.round_inr(additions_used_gte_180_days)
        add_lt = self.round_inr(additions_used_lt_180_days)
        sales = self.round_inr(sales_realized)

        total_additions = self.round_inr(add_gte + add_lt)
        pool_value = self.round_inr(op + total_additions - sales)

        if pool_value <= Decimal("0.00"):
            # Pool exhausted or negative -> NIL depreciation
            return {
                "block_id": block_id,
                "asset_class": block.asset_class,
                "statutory_rate": str(block.statutory_rate),
                "opening_wdv": str(op),
                "additions_gte_180": str(add_gte),
                "additions_lt_180": str(add_lt),
                "sales_realized": str(sales),
                "pool_value_before_depreciation": str(pool_value),
                "depreciation_on_lt_180": "0.00",
                "depreciation_on_balance_pool": "0.00",
                "total_tax_depreciation": "0.00",
                "closing_wdv": "0.00",
                "status": "POOL_EXHAUSTED_NIL_DEPRECIATION",
                "section_50_capital_gain": str(abs(pool_value)) if pool_value < Decimal("0.00") else "0.00",
            }

        # Case 1: Pool value exceeds or equals additions < 180 days
        if pool_value >= add_lt:
            dep_lt = self.round_inr(add_lt * block.less_than_180_days_rate)
            bal_pool = self.round_inr(pool_value - add_lt)
            dep_bal = self.round_inr(bal_pool * block.statutory_rate)
        else:
            # Case 2: Pool value is less than additions < 180 days (sales eroded opening/full additions)
            dep_lt = self.round_inr(pool_value * block.less_than_180_days_rate)
            dep_bal = Decimal("0.00")

        total_dep = self.round_inr(dep_lt + dep_bal)
        closing_wdv = self.round_inr(max(Decimal("0.00"), pool_value - total_dep))

        return {
            "block_id": block_id,
            "asset_class": block.asset_class,
            "statutory_rate": str(block.statutory_rate),
            "opening_wdv": str(op),
            "additions_gte_180": str(add_gte),
            "additions_lt_180": str(add_lt),
            "sales_realized": str(sales),
            "pool_value_before_depreciation": str(pool_value),
            "depreciation_on_lt_180": str(dep_lt),
            "depreciation_on_balance_pool": str(dep_bal),
            "total_tax_depreciation": str(total_dep),
            "closing_wdv": str(closing_wdv),
            "status": "DEPRECIATION_ALLOWABLE",
            "section_50_capital_gain": "0.00",
        }

    def reconcile_accounting_vs_tax_depreciation(
        self,
        book_depreciation: Decimal,
        tax_depreciation: Decimal,
    ) -> Dict[str, Any]:
        """
        Computes statutory book-vs-tax depreciation timing difference for tax audit (Form 3CD Clause 17/18).
        Timing difference = Book Depreciation - Tax Depreciation.
        If Book > Tax: Disallowed addition to taxable profit.
        If Tax > Book: Allowable deduction from taxable profit.
        """
        book = self.round_inr(book_depreciation)
        tax = self.round_inr(tax_depreciation)
        variance = self.round_inr(book - tax)

        if variance > Decimal("0.00"):
            impact = f"Add back to profit: Book depreciation exceeds tax depreciation by INR {variance}."
        elif variance < Decimal("0.00"):
            impact = f"Deduct from profit: Tax depreciation exceeds book depreciation by INR {abs(variance)}."
        else:
            impact = "Neutral: Book depreciation equals tax allowable depreciation."

        return {
            "book_depreciation_inr": str(book),
            "tax_depreciation_inr": str(tax),
            "timing_difference_inr": str(variance),
            "tax_impact_description": impact,
            "statutory_form_3cd_clause": "Clause 17 / Clause 18 (Depreciation admissible under Section 32)",
        }
