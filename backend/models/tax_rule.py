from enum import Enum
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaxpayerCategory(str, Enum):
    DOMESTIC_COMPANY = "DOMESTIC_COMPANY"
    FOREIGN_COMPANY = "FOREIGN_COMPANY"
    PARTNERSHIP_FIRM_LLP = "PARTNERSHIP_FIRM_LLP"
    INDIVIDUAL_HUF = "INDIVIDUAL_HUF"


class TaxRegime(str, Enum):
    SECTION_115BAA_CONCESSIONAL = "SECTION_115BAA_CONCESSIONAL"
    REGULAR_OLD_REGIME = "REGULAR_OLD_REGIME"


class VerificationStatus(str, Enum):
    VERIFIED_STATUTORY = "VERIFIED_STATUTORY"
    DEMONSTRATION = "DEMONSTRATION"


class DepreciationBlock(BaseModel):
    block_id: str
    asset_class: str
    description: str
    statutory_rate: Decimal
    less_than_180_days_rate: Decimal


class StatutoryTaxRule(BaseModel):
    """
    Versioned, effective-dated statutory tax rule.
    Links calculations to authoritative statutory references under Indian tax law.
    """
    rule_id: str
    act_name: str  # "Income-tax Act, 1961" or "Income-tax Act, 2025"
    statutory_reference: str
    jurisdiction: str = "IN"
    applicable_periods: List[str] = Field(default_factory=list)
    effective_from: str
    effective_to: Optional[str] = None
    taxpayer_category: TaxpayerCategory
    regime: TaxRegime
    base_tax_rate: Decimal
    surcharge_rate: Decimal
    cess_rate: Decimal = Decimal("0.04")  # 4% Health & Education Cess
    effective_tax_rate: Decimal
    eligibility_conditions: List[str] = Field(default_factory=list)
    ineligible_deductions: List[str] = Field(default_factory=list)
    authoritative_source: str
    verification_status: VerificationStatus
    notes: Optional[str] = None


class TaxCalculationResult(BaseModel):
    """
    Deterministic result of corporate tax calculation with complete statutory audit trail.
    """
    calculation_id: str
    financial_year: str
    regime: TaxRegime
    taxpayer_category: TaxpayerCategory
    gross_total_income: str
    allowable_deductions: str
    taxable_income: str
    base_tax: str
    surcharge: str
    cess: str
    total_tax_liability: str
    effective_tax_rate_percent: str
    is_eligible: bool
    eligibility_notes: List[str] = Field(default_factory=list)
    disallowed_deductions: List[str] = Field(default_factory=list)
    statutory_citations: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus
