from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field


class DepreciationMethod(str, Enum):
    WDV = "WDV"  # Written Down Value
    SLM = "SLM"  # Straight Line Method


class CurrencyCode(str, Enum):
    USD = "USD"
    INR = "INR"
    EUR = "EUR"
    GBP = "GBP"


class ValidationStatus(str, Enum):
    BALANCED = "BALANCED"
    UNBALANCED = "UNBALANCED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    INPUT_ERROR = "INPUT_ERROR"
    REQUIRES_MANUAL_REVIEW = "REQUIRES_MANUAL_REVIEW"


class CalculationRecord(BaseModel):
    calculation_id: str
    calculation_name: str
    method: str
    input_values: Dict[str, str]  # Stored as string representations of Decimals to preserve exact precision
    result: str
    variance: str
    currency: CurrencyCode = CurrencyCode.USD
    precision_policy: str = "Decimal(0.01) with ROUND_HALF_UP"
    source_references: List[str] = Field(default_factory=list)
    validation_status: ValidationStatus
    notes: Optional[str] = None


class TrialBalanceItem(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal = Field(default=Decimal("0.00"))
    credit: Decimal = Field(default=Decimal("0.00"))
    source_reference: Optional[str] = None


class TrialBalance(BaseModel):
    fiscal_year: str
    entity_name: str
    currency: CurrencyCode = CurrencyCode.USD
    items: List[TrialBalanceItem] = Field(default_factory=list)
    total_debits: Decimal = Field(default=Decimal("0.00"))
    total_credits: Decimal = Field(default=Decimal("0.00"))
    variance: Decimal = Field(default=Decimal("0.00"))
    is_balanced: bool = False
    evidence_id: Optional[str] = None


class GeneralLedgerEntry(BaseModel):
    entry_id: str
    date: str
    voucher_id: str
    account_code: str
    account_name: str
    description: str
    debit: Decimal = Field(default=Decimal("0.00"))
    credit: Decimal = Field(default=Decimal("0.00"))
    balance_after: Optional[Decimal] = None
    evidence_id: Optional[str] = None


class GeneralLedger(BaseModel):
    account_code: str
    account_name: str
    fiscal_year: str
    opening_balance: Decimal = Field(default=Decimal("0.00"))
    entries: List[GeneralLedgerEntry] = Field(default_factory=list)
    total_debits: Decimal = Field(default=Decimal("0.00"))
    total_credits: Decimal = Field(default=Decimal("0.00"))
    computed_closing_balance: Decimal = Field(default=Decimal("0.00"))
    reported_closing_balance: Decimal = Field(default=Decimal("0.00"))
    reconciliation_variance: Decimal = Field(default=Decimal("0.00"))
    is_reconciled: bool = False


class BalanceSheet(BaseModel):
    fiscal_year: str
    entity_name: str
    currency: CurrencyCode = CurrencyCode.USD
    total_assets: Decimal = Field(default=Decimal("0.00"))
    total_liabilities: Decimal = Field(default=Decimal("0.00"))
    total_equity: Decimal = Field(default=Decimal("0.00"))
    variance: Decimal = Field(default=Decimal("0.00"))
    is_balanced: bool = False
    evidence_id: Optional[str] = None


class CrossYearMetric(BaseModel):
    metric_name: str
    fy1_value: Decimal
    fy2_value: Decimal
    fy3_value: Decimal
    yoy_change_1_2: Decimal
    yoy_change_2_3: Decimal
    percentage_change_1_2: Decimal
    percentage_change_2_3: Decimal
    materiality_breached: bool = False
    notes: Optional[str] = None
