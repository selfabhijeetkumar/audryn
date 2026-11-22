import uuid
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple
from backend.models.financial import (
    CurrencyCode,
    ValidationStatus,
    CalculationRecord,
    TrialBalance,
    TrialBalanceItem,
    GeneralLedger,
    BalanceSheet,
    CrossYearMetric,
    DepreciationMethod,
)


class FinancialEngineException(Exception):
    pass


class DeterministicFinancialEngine:
    """
    Deterministic Financial Calculation Engine for AUDRYN.
    
    STRICT MANDATORY RULES:
    1. ZERO LLM ARITHMETIC: All mathematics are purely calculated via Python Decimal.
    2. ZERO FLOAT CONVERSION: Monetary calculations strictly forbid IEEE-754 floats.
    3. EXPLICIT ROUNDING: All operations apply ROUND_HALF_UP with standard two-decimal precision.
    """

    TWO_PLACES = Decimal("0.01")

    def __init__(
        self,
        default_currency: CurrencyCode = CurrencyCode.USD,
        default_materiality_threshold: Decimal = Decimal("5000.00"),
        materiality_percentage_threshold: Decimal = Decimal("0.05"),  # 5%
    ):
        self.default_currency = default_currency
        self.default_materiality_threshold = default_materiality_threshold
        self.materiality_percentage_threshold = materiality_percentage_threshold

    @staticmethod
    def to_decimal(val: Any) -> Decimal:
        """Safely convert any numeric input to Decimal without floating point loss."""
        if isinstance(val, Decimal):
            return val
        if val is None or str(val).strip() in ("", "None", "nan"):
            return Decimal("0.00")
        try:
            cleaned = (
                str(val)
                .strip()
                .replace(",", "")
                .replace("$", "")
                .replace("₹", "")
                .replace("INR", "")
                .strip()
            )
            return Decimal(cleaned)
        except InvalidOperation:
            raise ValueError(f"Cannot parse monetary value to Decimal: {val}")

    @classmethod
    def round_currency(cls, value: Decimal) -> Decimal:
        """Applies explicit statutory rounding: ROUND_HALF_UP to two decimal places."""
        return value.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def format_inr(cls, value: Decimal, include_symbol: bool = True) -> str:
        """
        Formats Decimal according to the Indian numbering system.
        Last 3 digits grouped, followed by groups of 2 digits (e.g., 12,34,567.89).
        """
        val = cls.round_currency(value)
        is_neg = val < Decimal("0.00")
        abs_val = abs(val)
        s = f"{abs_val:.2f}"
        int_part, dec_part = s.split(".")

        if len(int_part) <= 3:
            formatted = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            pairs = []
            while remaining:
                pairs.append(remaining[-2:])
                remaining = remaining[:-2]
            pairs.reverse()
            formatted = ",".join(pairs) + "," + last_three

        res = f"{formatted}.{dec_part}"
        if include_symbol:
            return f"-₹ {formatted}.{dec_part}" if is_neg else f"₹ {formatted}.{dec_part}"
        return f"-{formatted}.{dec_part}" if is_neg else f"{formatted}.{dec_part}"

    @classmethod
    def format_inr_lakhs_crores(cls, value: Decimal) -> str:
        """Expresses monetary values in Lakhs (10^5) or Crores (10^7)."""
        val = cls.round_currency(value)
        abs_val = abs(val)
        sign = "-" if val < Decimal("0.00") else ""
        if abs_val >= Decimal("10000000.00"):  # 1 Crore = 10,000,000
            cr = (abs_val / Decimal("10000000.00")).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)
            return f"{sign}₹ {cr} Crore"
        elif abs_val >= Decimal("100000.00"):  # 1 Lakh = 100,000
            lakh = (abs_val / Decimal("100000.00")).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)
            return f"{sign}₹ {lakh} Lakh"
        else:
            return cls.format_inr(val, include_symbol=True)

    # -------------------------------------------------------------
    # A. Trial Balance Verification
    # -------------------------------------------------------------
    def verify_trial_balance(
        self,
        items: List[TrialBalanceItem],
        fiscal_year: str,
        entity_name: str,
        currency: Optional[CurrencyCode] = None,
        source_reference: Optional[str] = None,
    ) -> Tuple[TrialBalance, CalculationRecord]:
        """
        Verifies that Total Debits equal Total Credits.
        Formula: Total Debits - Total Credits = Variance.
        """
        curr = currency or self.default_currency
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for item in items:
            total_debits += self.to_decimal(item.debit)
            total_credits += self.to_decimal(item.credit)

        total_debits = self.round_currency(total_debits)
        total_credits = self.round_currency(total_credits)
        variance = self.round_currency(abs(total_debits - total_credits))
        is_balanced = (variance == Decimal("0.00"))

        status = ValidationStatus.BALANCED if is_balanced else ValidationStatus.UNBALANCED

        tb = TrialBalance(
            fiscal_year=fiscal_year,
            entity_name=entity_name,
            currency=curr,
            items=items,
            total_debits=total_debits,
            total_credits=total_credits,
            variance=variance,
            is_balanced=is_balanced,
            evidence_id=source_reference,
        )

        calc_record = CalculationRecord(
            calculation_id=f"CALC-TB-{uuid.uuid4().hex[:8]}",
            calculation_name="Trial Balance Debit-Credit Verification",
            method="Total Debits - Total Credits = Variance (Decimal precision)",
            input_values={
                "total_debits": str(total_debits),
                "total_credits": str(total_credits),
                "item_count": str(len(items)),
            },
            result="BALANCED" if is_balanced else "UNBALANCED",
            variance=str(variance),
            currency=curr,
            precision_policy="Decimal(0.01) with ROUND_HALF_UP",
            source_references=[source_reference] if source_reference else [],
            validation_status=status,
            notes=f"Total Debits: {total_debits}, Total Credits: {total_credits}, Variance: {variance}",
        )

        return tb, calc_record

    # -------------------------------------------------------------
    # B. Balance Sheet Verification
    # -------------------------------------------------------------
    def verify_balance_sheet(
        self,
        total_assets: Decimal,
        total_liabilities: Decimal,
        total_equity: Decimal,
        fiscal_year: str,
        entity_name: str,
        currency: Optional[CurrencyCode] = None,
        source_reference: Optional[str] = None,
    ) -> Tuple[BalanceSheet, CalculationRecord]:
        """
        Verifies fundamental accounting equation:
        Assets = Liabilities + Equity (Assets - Liabilities - Equity = 0)
        """
        curr = currency or self.default_currency
        assets = self.round_currency(self.to_decimal(total_assets))
        liabilities = self.round_currency(self.to_decimal(total_liabilities))
        equity = self.round_currency(self.to_decimal(total_equity))

        claims = liabilities + equity
        variance = self.round_currency(abs(assets - claims))
        is_balanced = (variance == Decimal("0.00"))

        status = ValidationStatus.BALANCED if is_balanced else ValidationStatus.UNBALANCED

        bs = BalanceSheet(
            fiscal_year=fiscal_year,
            entity_name=entity_name,
            currency=curr,
            total_assets=assets,
            total_liabilities=liabilities,
            total_equity=equity,
            variance=variance,
            is_balanced=is_balanced,
            evidence_id=source_reference,
        )

        calc_record = CalculationRecord(
            calculation_id=f"CALC-BS-{uuid.uuid4().hex[:8]}",
            calculation_name="Balance Sheet Fundamental Equation Verification",
            method="Assets - (Liabilities + Equity) = Variance",
            input_values={
                "total_assets": str(assets),
                "total_liabilities": str(liabilities),
                "total_equity": str(equity),
                "total_claims": str(claims),
            },
            result="BALANCED" if is_balanced else "UNBALANCED",
            variance=str(variance),
            currency=curr,
            precision_policy="Decimal(0.01) with ROUND_HALF_UP",
            source_references=[source_reference] if source_reference else [],
            validation_status=status,
            notes=f"Assets: {assets}, Liabilities+Equity: {claims}, Variance: {variance}",
        )

        return bs, calc_record

    # -------------------------------------------------------------
    # C. General Ledger Reconciliation
    # -------------------------------------------------------------
    def reconcile_general_ledger(
        self,
        gl: GeneralLedger,
        source_reference: Optional[str] = None,
    ) -> Tuple[GeneralLedger, CalculationRecord]:
        """
        Reconciles opening balance + debit movements - credit movements = closing balance.
        """
        opening = self.round_currency(self.to_decimal(gl.opening_balance))
        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for entry in gl.entries:
            total_debits += self.to_decimal(entry.debit)
            total_credits += self.to_decimal(entry.credit)

        total_debits = self.round_currency(total_debits)
        total_credits = self.round_currency(total_credits)

        # In standard asset/expense ledgers: Closing = Opening + Debits - Credits
        # In liability/equity/revenue ledgers: Closing = Opening + Credits - Debits
        # Here we compute net movement: Debits - Credits
        computed_closing = self.round_currency(opening + total_debits - total_credits)
        reported_closing = self.round_currency(self.to_decimal(gl.reported_closing_balance))

        variance = self.round_currency(abs(computed_closing - reported_closing))
        is_reconciled = (variance == Decimal("0.00"))

        gl.total_debits = total_debits
        gl.total_credits = total_credits
        gl.computed_closing_balance = computed_closing
        gl.reported_closing_balance = reported_closing
        gl.reconciliation_variance = variance
        gl.is_reconciled = is_reconciled

        status = ValidationStatus.BALANCED if is_reconciled else ValidationStatus.ANOMALY_DETECTED

        calc_record = CalculationRecord(
            calculation_id=f"CALC-GL-{uuid.uuid4().hex[:8]}",
            calculation_name=f"General Ledger Reconciliation ({gl.account_code})",
            method="Opening + Total Debits - Total Credits = Computed Closing",
            input_values={
                "opening_balance": str(opening),
                "total_debits": str(total_debits),
                "total_credits": str(total_credits),
                "reported_closing": str(reported_closing),
            },
            result=str(computed_closing),
            variance=str(variance),
            currency=self.default_currency,
            precision_policy="Decimal(0.01) with ROUND_HALF_UP",
            source_references=[source_reference] if source_reference else [],
            validation_status=status,
            notes=f"Account {gl.account_name}: Computed {computed_closing} vs Reported {reported_closing}",
        )

        return gl, calc_record

    # -------------------------------------------------------------
    # D. Cross-Year Comparison (Three Financial Years)
    # -------------------------------------------------------------
    def compare_cross_year_metrics(
        self,
        metric_name: str,
        fy1_val: Decimal,
        fy2_val: Decimal,
        fy3_val: Decimal,
        materiality_limit: Optional[Decimal] = None,
        source_reference: Optional[str] = None,
    ) -> CrossYearMetric:
        """
        Computes YoY variances and percentage shifts across three years.
        Flags variance if exceeding materiality limits.
        """
        m_limit = materiality_limit or self.default_materiality_threshold
        v1 = self.round_currency(self.to_decimal(fy1_val))
        v2 = self.round_currency(self.to_decimal(fy2_val))
        v3 = self.round_currency(self.to_decimal(fy3_val))

        yoy_1_2 = self.round_currency(v2 - v1)
        yoy_2_3 = self.round_currency(v3 - v2)

        # Percentage change = (Change / Base) * 100
        pct_1_2 = Decimal("0.00")
        if v1 != Decimal("0.00"):
            pct_1_2 = self.round_currency(((v2 - v1) / abs(v1)) * Decimal("100"))

        pct_2_3 = Decimal("0.00")
        if v2 != Decimal("0.00"):
            pct_2_3 = self.round_currency(((v3 - v2) / abs(v2)) * Decimal("100"))

        # Check materiality
        breached = abs(yoy_1_2) > m_limit or abs(yoy_2_3) > m_limit

        notes = []
        if abs(yoy_1_2) > m_limit:
            notes.append(f"FY1->FY2 variance {yoy_1_2} exceeds threshold {m_limit}")
        if abs(yoy_2_3) > m_limit:
            notes.append(f"FY2->FY3 variance {yoy_2_3} exceeds threshold {m_limit}")

        return CrossYearMetric(
            metric_name=metric_name,
            fy1_value=v1,
            fy2_value=v2,
            fy3_value=v3,
            yoy_change_1_2=yoy_1_2,
            yoy_change_2_3=yoy_2_3,
            percentage_change_1_2=pct_1_2,
            percentage_change_2_3=pct_2_3,
            materiality_breached=breached,
            notes="; ".join(notes) if notes else "Within standard tolerance.",
        )

    # -------------------------------------------------------------
    # E. Tax Calculation (Demonstration Statutory Rules)
    # -------------------------------------------------------------
    def compute_demonstration_corporate_tax(
        self,
        gross_profit: Decimal,
        allowable_expenses: Decimal,
        disallowed_expenses: Decimal,
        base_tax_rate: Decimal = Decimal("0.25"),  # 25% demonstration corporate rate
        surcharge_rate: Decimal = Decimal("0.07"),  # 7% demonstration surcharge
        cess_rate: Decimal = Decimal("0.04"),       # 4% demonstration health/education cess
        source_reference: Optional[str] = None,
    ) -> Tuple[Decimal, CalculationRecord]:
        """
        Computes statutory taxable income and final tax liability.
        Demonstration Tax Formula:
        Taxable Income = Gross Profit - Allowable Expenses + Disallowed Expenses
        Base Tax = Taxable Income * base_tax_rate
        Surcharge = Base Tax * surcharge_rate
        Cess = (Base Tax + Surcharge) * cess_rate
        Total Tax Liability = Base Tax + Surcharge + Cess
        """
        gp = self.round_currency(self.to_decimal(gross_profit))
        allowable = self.round_currency(self.to_decimal(allowable_expenses))
        disallowed = self.round_currency(self.to_decimal(disallowed_expenses))

        taxable_income = self.round_currency(gp - allowable + disallowed)
        if taxable_income < Decimal("0.00"):
            taxable_income = Decimal("0.00")

        base_tax = self.round_currency(taxable_income * base_tax_rate)
        surcharge = self.round_currency(base_tax * surcharge_rate)
        cess = self.round_currency((base_tax + surcharge) * cess_rate)
        total_tax = self.round_currency(base_tax + surcharge + cess)

        calc_record = CalculationRecord(
            calculation_id=f"CALC-TAX-{uuid.uuid4().hex[:8]}",
            calculation_name="Demonstration Corporate Income Tax Calculation",
            method="Taxable = (Gross - Allowable + Disallowed); Tax = Base + Surcharge + Cess",
            input_values={
                "gross_profit": str(gp),
                "allowable_expenses": str(allowable),
                "disallowed_expenses": str(disallowed),
                "taxable_income": str(taxable_income),
                "base_tax_rate": str(base_tax_rate),
                "surcharge_rate": str(surcharge_rate),
                "cess_rate": str(cess_rate),
            },
            result=str(total_tax),
            variance="0.00",
            currency=self.default_currency,
            precision_policy="Decimal(0.01) with ROUND_HALF_UP",
            source_references=[source_reference] if source_reference else [],
            validation_status=ValidationStatus.BALANCED,
            notes=f"Taxable Income: {taxable_income}, Base Tax: {base_tax}, Surcharge: {surcharge}, Cess: {cess}, Total: {total_tax}",
        )

        return total_tax, calc_record

    # -------------------------------------------------------------
    # F. Depreciation Engine (WDV & SLM)
    # -------------------------------------------------------------
    def compute_depreciation(
        self,
        asset_cost: Decimal,
        accumulated_depreciation: Decimal,
        rate: Decimal,
        method: DepreciationMethod = DepreciationMethod.WDV,
        source_reference: Optional[str] = None,
    ) -> Tuple[Decimal, Decimal, CalculationRecord]:
        """
        Computes depreciation and closing asset value.
        - SLM: Depreciation = Cost * rate
        - WDV: Net Book Value = Cost - AccDep; Depreciation = NBV * rate
        Closing NBV = Opening NBV - Depreciation
        """
        cost = self.round_currency(self.to_decimal(asset_cost))
        acc_dep = self.round_currency(self.to_decimal(accumulated_depreciation))
        rate_dec = self.to_decimal(rate)

        opening_nbv = self.round_currency(cost - acc_dep)
        if opening_nbv < Decimal("0.00"):
            opening_nbv = Decimal("0.00")

        if method == DepreciationMethod.SLM:
            depreciation = self.round_currency(cost * rate_dec)
        elif method == DepreciationMethod.WDV:
            depreciation = self.round_currency(opening_nbv * rate_dec)
        else:
            raise ValueError(f"Unsupported depreciation method: {method}")

        # Ensure depreciation does not exceed remaining book value
        if depreciation > opening_nbv:
            depreciation = opening_nbv

        closing_nbv = self.round_currency(opening_nbv - depreciation)

        calc_record = CalculationRecord(
            calculation_id=f"CALC-DEP-{uuid.uuid4().hex[:8]}",
            calculation_name=f"Depreciation Engine ({method.value})",
            method=f"{method.value} at {rate_dec * Decimal('100')}%",
            input_values={
                "asset_cost": str(cost),
                "accumulated_depreciation": str(acc_dep),
                "opening_nbv": str(opening_nbv),
                "rate": str(rate_dec),
            },
            result=str(depreciation),
            variance="0.00",
            currency=self.default_currency,
            precision_policy="Decimal(0.01) with ROUND_HALF_UP",
            source_references=[source_reference] if source_reference else [],
            validation_status=ValidationStatus.BALANCED,
            notes=f"Opening NBV: {opening_nbv}, Depreciation: {depreciation}, Closing NBV: {closing_nbv}",
        )

        return depreciation, closing_nbv, calc_record
