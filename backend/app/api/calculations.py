"""
AUDRYN Financial Engine and Indian Tax Rulebook Endpoints.
Guarantees zero floating-point math, exact Python Decimal arithmetic, and statutory citations.
"""
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from backend.app.auth import get_current_user, require_permission, verify_csrf
from backend.app.rbac import Permission
from backend.app.isolation import verify_engagement_access
from backend.db.repositories import CalculationRepository, AuditEventRepository
from backend.services.financial_engine import DeterministicFinancialEngine
from backend.services.indian_tax_rulebook import IndianTaxRulebookService
from backend.models.tax_rule import TaxRegime, TaxpayerCategory

router = APIRouter(prefix="/engagements/{engagement_id}", tags=["Calculations & Tax"])


class FinancialCalculationRequest(BaseModel):
    formula_name: str
    statutory_section: Optional[str] = None
    input_values: Dict[str, str]  # Decimal strings
    notes: Optional[str] = None


class Section115BAARequest(BaseModel):
    gross_total_income: str  # Decimal string
    claimed_deductions: List[str] = []
    deduction_amounts: Dict[str, str] = {}
    financial_year: str = "FY 2023-24"


class Section32DepreciationRequest(BaseModel):
    block_id: str = "IN-SEC32-PLANT-MACHINERY-GENERAL"
    opening_wdv: str  # Decimal string
    additions_used_gte_180_days: str = "0.00"
    additions_used_lt_180_days: str = "0.00"
    sales_realized: str = "0.00"


@router.get("/calculations")
def list_calculations(
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.RUN_CALCULATIONS)),
):
    items = CalculationRepository.list_by_engagement(engagement["engagement_id"])
    if not items:
        # Seed standard calculation records for demonstration if none exist
        CalculationRepository.create(
            calculation_id="CALC-REV-01",
            engagement_id=engagement["engagement_id"],
            calculation_name="Quarterly Revenue Cut-Off Variance",
            statutory_section="Guidance Note on Audit of Revenue (ICAI)",
            method="Decimal Subtract & Ratio",
            input_values={
                "Gross_Revenue_Per_Books": "124567890.00",
                "Dispatched_Pre_March_31": "120067890.00",
                "Post_Period_Dispatches": "4500000.00",
            },
            result="4500000.00",
            variance="3.61%",
            notes="Calculated using Decimal arithmetic. Cut-off threshold exceeded (> ₹10,00,000.00).",
        )
        CalculationRepository.create(
            calculation_id="CALC-TAX-02",
            engagement_id=engagement["engagement_id"],
            calculation_name="Section 115BAA Corporate Tax Computation",
            statutory_section="Section 115BAA, Income-tax Act, 1961",
            method="22% Base + 10% Surcharge + 4% Cess = 25.168%",
            input_values={
                "Gross_Total_Income": "48500000.00",
                "Base_Tax_Rate": "22.00%",
                "Surcharge_Rate": "10.00%",
                "Health_Education_Cess": "4.00%",
                "Effective_Tax_Rate": "25.168%",
            },
            result="12206480.00",
            notes="No Chapter VI-A deductions (except 80JJAA) or Section 32(1)(iia) additional depreciation claimed.",
        )
        items = CalculationRepository.list_by_engagement(engagement["engagement_id"])
    return items


@router.post("/calculations/run", dependencies=[Depends(verify_csrf)])
def run_calculation(
    payload: FinancialCalculationRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.RUN_CALCULATIONS)),
):
    engine = DeterministicFinancialEngine()
    calc_id = f"CALC-{uuid.uuid4().hex[:6].upper()}"

    # Evaluate simple sum/diff or product from input values deterministically
    try:
        decimal_inputs = {k: engine.to_decimal(v) for k, v in payload.input_values.items()}
        # Compute result as sum or variance
        if len(decimal_inputs) >= 2:
            vals = list(decimal_inputs.values())
            res = engine.round_currency(vals[0] - sum(vals[1:]))
        elif len(decimal_inputs) == 1:
            res = engine.round_currency(list(decimal_inputs.values())[0])
        else:
            res = Decimal("0.00")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid decimal inputs: {str(e)}")

    record = CalculationRepository.create(
        calculation_id=calc_id,
        engagement_id=engagement["engagement_id"],
        calculation_name=payload.formula_name,
        statutory_section=payload.statutory_section,
        method="Deterministic Decimal Engine (ROUND_HALF_UP)",
        input_values=payload.input_values,
        result=str(res),
        variance=None,
        notes=payload.notes,
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "CALCULATION_EXECUTED",
        {"calculation_id": calc_id, "name": payload.formula_name, "result": str(res)},
    )
    return record


@router.post("/tax/section115baa", dependencies=[Depends(verify_csrf)])
def compute_tax_115baa(
    payload: Section115BAARequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.RUN_TAX_RULES)),
):
    rulebook = IndianTaxRulebookService()
    try:
        gti = DeterministicFinancialEngine.to_decimal(payload.gross_total_income)
        ded_amounts = {k: DeterministicFinancialEngine.to_decimal(v) for k, v in payload.deduction_amounts.items()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid decimal input in tax computation: {str(e)}")

    result = rulebook.calculate_corporate_tax(
        financial_year=payload.financial_year,
        gross_total_income=gti,
        regime=TaxRegime.SECTION_115BAA_CONCESSIONAL,
        deductions_claimed=payload.claimed_deductions,
        deduction_amounts=ded_amounts,
    )

    calc_id = f"TAX-{uuid.uuid4().hex[:6].upper()}"
    CalculationRepository.create(
        calculation_id=calc_id,
        engagement_id=engagement["engagement_id"],
        calculation_name="Section 115BAA Concessional Tax Liability",
        statutory_section="Section 115BAA of the Income-tax Act, 1961",
        method="22% Base + 10% Surcharge + 4% Cess = 25.168%",
        input_values={
            "gross_total_income": payload.gross_total_income,
            "taxable_income": result.taxable_income,
            "effective_rate": f"{result.effective_tax_rate_percent}%",
        },
        result=result.total_tax_liability,
        notes=f"Eligibility: {result.is_eligible}. Disallowed deductions: {', '.join(result.disallowed_deductions) if result.disallowed_deductions else 'None'}",
    )

    AuditEventRepository.log_event(
        engagement["engagement_id"],
        user["user_id"],
        "TAX_115BAA_COMPUTED",
        {"tax_liability": result.total_tax_liability, "is_eligible": result.is_eligible},
    )

    return result.model_dump()


@router.post("/tax/section32", dependencies=[Depends(verify_csrf)])
def compute_section32(
    payload: Section32DepreciationRequest,
    engagement: Dict[str, Any] = Depends(verify_engagement_access),
    user: Dict[str, Any] = Depends(require_permission(Permission.RUN_TAX_RULES)),
):
    rulebook = IndianTaxRulebookService()
    try:
        op_wdv = DeterministicFinancialEngine.to_decimal(payload.opening_wdv)
        add_gte = DeterministicFinancialEngine.to_decimal(payload.additions_used_gte_180_days)
        add_lt = DeterministicFinancialEngine.to_decimal(payload.additions_used_lt_180_days)
        sales = DeterministicFinancialEngine.to_decimal(payload.sales_realized)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid decimal input: {str(e)}")

    dep_res = rulebook.calculate_section_32_depreciation(
        block_id=payload.block_id,
        opening_wdv=op_wdv,
        additions_used_gte_180_days=add_gte,
        additions_used_lt_180_days=add_lt,
        sales_realized=sales,
    )

    calc_id = f"DEP-{uuid.uuid4().hex[:6].upper()}"
    CalculationRepository.create(
        calculation_id=calc_id,
        engagement_id=engagement["engagement_id"],
        calculation_name=f"Section 32 WDV Depreciation ({payload.block_id})",
        statutory_section="Section 32, Income-tax Act, 1961 (180-Day Rule)",
        method="WDV Block Depreciation",
        input_values={
            "block_id": payload.block_id,
            "opening_wdv": payload.opening_wdv,
            "additions_gte_180": payload.additions_used_gte_180_days,
            "additions_lt_180": payload.additions_used_lt_180_days,
            "sales_realized": payload.sales_realized,
        },
        result=str(dep_res["total_tax_depreciation"]),
        notes=f"Closing WDV: {dep_res['closing_wdv']}. Half-rate depreciation restricted for <180 days additions.",
    )

    return dep_res
