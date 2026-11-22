"""
AUDRYN Cross-Year Investigation Service.

Compares financial records across multiple fiscal years to detect:
- Year-over-year balance discrepancies
- Opening/closing balance discontinuities
- Unusual transaction patterns and movements
- Missing period coverage

All monetary calculations use the existing DeterministicFinancialEngine (Python Decimal).
Zero LLM arithmetic.
"""
import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.models.financial import ValidationStatus


class CrossYearInvestigationService:

    def __init__(
        self,
        engine: Optional[DeterministicFinancialEngine] = None,
        materiality_threshold: Decimal = Decimal("5000.00"),
        percentage_threshold: Decimal = Decimal("0.25"),  # 25%
    ):
        self.engine = engine or DeterministicFinancialEngine()
        self.materiality_threshold = materiality_threshold
        self.percentage_threshold = percentage_threshold

    def compare_account_balances(
        self,
        prior_year: Dict[str, Dict[str, str]],
        current_year: Dict[str, Dict[str, str]],
        prior_label: str = "FY_PRIOR",
        current_label: str = "FY_CURRENT",
    ) -> List[Dict[str, Any]]:
        """
        Compare account balances between two fiscal years.
        Each year is {account_code: {"debit": str, "credit": str, "account_name": str}}.
        Returns list of movement records with YoY variances.
        """
        results = []
        all_accounts = set(prior_year.keys()) | set(current_year.keys())

        for acct in sorted(all_accounts):
            prior = prior_year.get(acct, {})
            current = current_year.get(acct, {})
            prior_net = self.engine.round_currency(
                self.engine.to_decimal(prior.get("debit", "0")) -
                self.engine.to_decimal(prior.get("credit", "0"))
            )
            current_net = self.engine.round_currency(
                self.engine.to_decimal(current.get("debit", "0")) -
                self.engine.to_decimal(current.get("credit", "0"))
            )
            variance = self.engine.round_currency(current_net - prior_net)
            abs_variance = abs(variance)

            pct_change = Decimal("0.00")
            if prior_net != Decimal("0"):
                pct_change = self.engine.round_currency(
                    (variance / abs(prior_net)) * Decimal("100")
                )

            is_material = abs_variance >= self.materiality_threshold
            is_unusual = abs(pct_change) >= (self.percentage_threshold * Decimal("100"))

            results.append({
                "account_code": acct,
                "account_name": current.get("account_name", prior.get("account_name", "Unknown")),
                "prior_period": prior_label,
                "prior_net_balance": str(prior_net),
                "current_period": current_label,
                "current_net_balance": str(current_net),
                "variance": str(variance),
                "percentage_change": str(pct_change),
                "is_material": is_material,
                "is_unusual": is_unusual,
                "flag": "MATERIAL" if is_material else ("UNUSUAL" if is_unusual else "NORMAL"),
            })

        return results

    def check_opening_closing_continuity(
        self,
        prior_closing: Dict[str, str],
        current_opening: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        Verify that prior year closing balances match current year opening balances.
        Returns list of discontinuities.
        """
        discontinuities = []
        all_accounts = set(prior_closing.keys()) | set(current_opening.keys())

        for acct in sorted(all_accounts):
            closing = self.engine.round_currency(
                self.engine.to_decimal(prior_closing.get(acct, "0"))
            )
            opening = self.engine.round_currency(
                self.engine.to_decimal(current_opening.get(acct, "0"))
            )
            if closing != opening:
                discontinuities.append({
                    "account_code": acct,
                    "prior_closing": str(closing),
                    "current_opening": str(opening),
                    "variance": str(self.engine.round_currency(opening - closing)),
                    "status": "DISCONTINUITY",
                })

        return discontinuities

    def detect_unusual_movements(
        self,
        movements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Filter movement records to only those flagged as MATERIAL or UNUSUAL.
        """
        return [m for m in movements if m.get("flag") in ("MATERIAL", "UNUSUAL")]

    def generate_cross_year_summary(
        self,
        movements: List[Dict[str, Any]],
        discontinuities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Produce aggregate summary of cross-year investigation.
        """
        material_count = sum(1 for m in movements if m.get("is_material"))
        unusual_count = sum(1 for m in movements if m.get("is_unusual"))
        total_variance = self.engine.round_currency(
            sum(abs(self.engine.to_decimal(m["variance"])) for m in movements)
        )
        return {
            "total_accounts_compared": len(movements),
            "material_movements": material_count,
            "unusual_movements": unusual_count,
            "total_absolute_variance": str(total_variance),
            "discontinuities_found": len(discontinuities),
            "unresolved_differences": [
                d for d in discontinuities if d["status"] == "DISCONTINUITY"
            ],
        }
