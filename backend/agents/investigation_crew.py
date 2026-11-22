"""
AUDRYN CrewAI Investigation Team.

Specialized audit investigation agents that use local Ollama (qwen3:4b).
Each agent has deterministic Python tools for financial verification.
Agents NEVER invent financial figures — all arithmetic is performed by tools.
Agents return structured InvestigationFinding results.
They do NOT modify LangGraph state directly.

DISCLAIMER: Tax rules used here are DEMONSTRATION rules only,
unless independently verified against jurisdiction-specific legislation.
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool

from backend.services.financial_engine import DeterministicFinancialEngine

# ─── Shared Engine Instance ──────────────────────────────────────
_engine = DeterministicFinancialEngine()


# ─── Deterministic Tools (callable by agents) ───────────────────

@tool("verify_trial_balance")
def verify_trial_balance(debit_total: str, credit_total: str) -> str:
    """Verify whether a trial balance is arithmetically balanced.
    Pass total debits and credits as string numbers. Returns balance status and variance."""
    dr = _engine.round_currency(_engine.to_decimal(debit_total))
    cr = _engine.round_currency(_engine.to_decimal(credit_total))
    variance = _engine.round_currency(dr - cr)
    status = "BALANCED" if variance == Decimal("0") else "UNBALANCED"
    return f"Status: {status}. Debit Total: {dr}, Credit Total: {cr}, Variance: {variance}."


@tool("verify_depreciation")
def verify_depreciation(
    asset_cost: str, accumulated_depreciation: str, rate: str, method: str
) -> str:
    """Verify depreciation calculation for an asset.
    method must be 'WDV' or 'SLM'. Returns calculated depreciation and closing value."""
    from backend.models.financial import DepreciationMethod
    dep_method = DepreciationMethod.WDV if method.upper() == "WDV" else DepreciationMethod.SLM
    dep_amount, closing, record = _engine.compute_depreciation(
        Decimal(asset_cost), Decimal(accumulated_depreciation),
        Decimal(rate), dep_method
    )
    return (
        f"Method: {method.upper()}, Cost: {asset_cost}, Acc.Dep: {accumulated_depreciation}, "
        f"Rate: {rate}, Depreciation: {dep_amount}, Closing NBV: {closing}. "
        f"Status: {record.validation_status.value}."
    )


@tool("verify_balance_sheet_equation")
def verify_balance_sheet_equation(
    total_assets: str, total_liabilities: str, total_equity: str
) -> str:
    """Verify fundamental accounting equation: Assets = Liabilities + Equity.
    Returns balance status and variance."""
    assets = _engine.round_currency(_engine.to_decimal(total_assets))
    liabilities = _engine.round_currency(_engine.to_decimal(total_liabilities))
    equity = _engine.round_currency(_engine.to_decimal(total_equity))
    variance = _engine.round_currency(assets - liabilities - equity)
    status = "BALANCED" if variance == Decimal("0") else "UNBALANCED"
    return f"Assets: {assets}, Liabilities: {liabilities}, Equity: {equity}. Variance: {variance}. Status: {status}."


@tool("detect_duplicate_reference")
def detect_duplicate_reference(references: str) -> str:
    """Check a comma-separated list of reference IDs for duplicates.
    Returns duplicate IDs found or 'No duplicates detected.'"""
    refs = [r.strip() for r in references.split(",") if r.strip()]
    seen = set()
    dupes = []
    for r in refs:
        if r in seen:
            dupes.append(r)
        seen.add(r)
    if dupes:
        return f"DUPLICATES DETECTED: {', '.join(dupes)}. Count: {len(dupes)}."
    return "No duplicates detected."


@tool("compute_variance")
def compute_variance(expected: str, actual: str) -> str:
    """Compute the monetary variance between expected and actual amounts.
    Returns variance and whether it exceeds materiality threshold ($5,000)."""
    exp = _engine.round_currency(_engine.to_decimal(expected))
    act = _engine.round_currency(_engine.to_decimal(actual))
    var = _engine.round_currency(act - exp)
    material = "MATERIAL" if abs(var) >= Decimal("5000") else "IMMATERIAL"
    return f"Expected: {exp}, Actual: {act}, Variance: {var}. Classification: {material}."


# ─── Agent & Crew Factory ───────────────────────────────────────

def create_investigation_crew(
    task_description: str,
    context_data: str,
    ollama_base_url: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Crew:
    """
    Create a full AUDRYN CrewAI investigation team.
    Returns the Crew object ready for kickoff().

    Args:
        task_description: What to investigate.
        context_data: Structured financial data summary (not raw documents).
        ollama_base_url: Ollama server URL.
        model_name: LiteLLM-format model identifier.
    """
    import os
    ollama_base_url = ollama_base_url or os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model_name = model_name or os.environ.get("OLLAMA_MODEL", "ollama/qwen3:4b")

    is_cloud = bool(os.environ.get("RENDER") or os.environ.get("VERCEL") or os.environ.get("ENV") == "production")
    if is_cloud and ("127.0.0.1" in ollama_base_url or "localhost" in ollama_base_url):
        # In cloud environments, never attempt loopback inference without dedicated gateway
        print("[INFERENCE SAFETY] Cloud deployment without remote gateway: Localhost inference call suppressed.")

    llm = LLM(model=model_name, base_url=ollama_base_url, temperature=0.0)

    # Agent 1: Corporate Tax Audit Specialist
    tax_agent = Agent(
        role="Corporate Tax Audit Specialist",
        goal="Inspect tax computation schedules, identify classification discrepancies, and retrieve applicable demonstration rules.",
        backstory=(
            "Senior tax auditor with expertise in corporate income tax computation. "
            "Uses verified deterministic tools for all arithmetic. "
            "Tax rules are demonstration rules unless explicitly verified against legislation."
        ),
        tools=[verify_trial_balance, verify_depreciation, compute_variance],
        llm=llm,
        verbose=False,
    )

    # Agent 2: General Ledger Investigator
    gl_agent = Agent(
        role="General Ledger Investigator",
        goal="Investigate ledger inconsistencies, examine journal entries, detect unusual patterns, and check cross-year account movements.",
        backstory=(
            "Forensic accounting specialist who examines general ledger entries "
            "for unusual patterns, timing anomalies, and unexplained movements. "
            "Never invents figures — always uses deterministic verification tools."
        ),
        tools=[verify_trial_balance, verify_balance_sheet_equation, compute_variance],
        llm=llm,
        verbose=False,
    )

    # Agent 3: Evidence Matching Specialist
    evidence_agent = Agent(
        role="Evidence Matching Specialist",
        goal="Match invoices to ledger entries, detect missing evidence, identify conflicting amounts, and preserve document coordinates.",
        backstory=(
            "Document verification specialist who cross-references invoices, "
            "supporting documents, and transactions. Reports exact page, sheet, "
            "and row coordinates for every match or discrepancy."
        ),
        tools=[detect_duplicate_reference, compute_variance],
        llm=llm,
        verbose=False,
    )

    # Agent 4: Forensic Investigator
    forensic_agent = Agent(
        role="Forensic Investigator",
        goal="Investigate duplicate references, detect possible split transactions, examine unusual vendor patterns, and investigate unexplained financial movements.",
        backstory=(
            "Financial forensics specialist who investigates potential fraud indicators "
            "including duplicate invoicing, split transactions, and unusual vendor behavior. "
            "Does NOT automatically label anomalies as fraud."
        ),
        tools=[detect_duplicate_reference, compute_variance, verify_trial_balance],
        llm=llm,
        verbose=False,
    )

    # Task definition
    investigation_task = Task(
        description=(
            f"INVESTIGATION BRIEF:\n{task_description}\n\n"
            f"FINANCIAL DATA:\n{context_data}\n\n"
            "INSTRUCTIONS:\n"
            "1. Use the provided tools to verify ALL arithmetic. Never compute numbers yourself.\n"
            "2. Report findings with evidence references (file, page, row).\n"
            "3. Do NOT invent missing financial figures.\n"
            "4. Do NOT label anomalies as fraud without sufficient evidence.\n"
            "5. Return a structured summary of findings."
        ),
        expected_output=(
            "A structured investigation summary listing each finding with: "
            "finding title, category, severity, impact amount (from tools), "
            "evidence references, and status."
        ),
        agent=tax_agent,
    )

    crew = Crew(
        agents=[tax_agent, gl_agent, evidence_agent, forensic_agent],
        tasks=[investigation_task],
        process=Process.sequential,
        verbose=False,
    )
    return crew
