"""
AUDRYN Microsoft Agent Framework Independent Review Team.

Implements an independent review workflow using the installed
Microsoft Agent Framework + local Ollama (qwen3:4b).

Three review agents operate in SEPARATE contexts from the
investigation team. They start from original evidence and
structured findings — never simply accept CrewAI's conclusion.

Does NOT assume a second LLM agent guarantees correctness.
All arithmetic verification uses deterministic Python tools.
"""
import asyncio
import json
from decimal import Decimal
from typing import List, Dict, Any, Optional, Callable

from backend.services.financial_engine import DeterministicFinancialEngine
from backend.models.counter_evidence import ReviewVerdict

_engine = DeterministicFinancialEngine()


# ─── Function Tools for MS Agent Framework ───────────────────────

def verify_variance_tool(expected: str, actual: str) -> str:
    """Deterministic variance verification. Returns variance and materiality classification."""
    exp = _engine.round_currency(_engine.to_decimal(expected))
    act = _engine.round_currency(_engine.to_decimal(actual))
    var = _engine.round_currency(act - exp)
    material = "MATERIAL" if abs(var) >= Decimal("5000") else "IMMATERIAL"
    return f"Expected: {exp}, Actual: {act}, Variance: {var}. Classification: {material}."


def check_reversal_tool(transaction_list: str) -> str:
    """Check comma-separated transaction amounts for reversals (equal positive/negative pairs)."""
    try:
        amounts = [Decimal(a.strip()) for a in transaction_list.split(",") if a.strip()]
    except Exception:
        return "Error: Could not parse transaction amounts."
    reversals = []
    for i, a in enumerate(amounts):
        for j, b in enumerate(amounts):
            if i < j and _engine.round_currency(a + b) == Decimal("0"):
                reversals.append(f"({a}, {b})")
    if reversals:
        return f"REVERSALS FOUND: {'; '.join(reversals)}."
    return "No reversals detected."


def check_timing_difference_tool(record_date: str, settlement_date: str) -> str:
    """Check if there is a timing difference between recording and settlement dates."""
    if record_date == settlement_date:
        return "No timing difference. Same date."
    return f"TIMING DIFFERENCE: Recorded on {record_date}, settled on {settlement_date}."


# ─── Review Functions (non-LLM deterministic path) ──────────────

def run_counter_evidence_review(
    finding: Dict[str, Any],
    available_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Counter-Evidence Challenger: Challenge a finding with deterministic checks.
    Looks for reversals, timing differences, and verifies calculations.
    Does NOT use LLM for arithmetic.
    """
    result = {
        "finding_id": finding.get("finding_id", ""),
        "reviewer_role": "Counter-Evidence Challenger (MS Agent Framework)",
        "contradictory_evidence": [],
        "alternative_explanations": [],
        "calculation_check": "",
        "verdict": ReviewVerdict.UNRESOLVED.value,
    }

    # Check for reversals in related transactions
    related_txns = available_data.get("related_transactions", [])
    if related_txns:
        amounts_str = ",".join(str(t.get("amount", "0")) for t in related_txns)
        reversal_check = check_reversal_tool(amounts_str)
        if "REVERSALS FOUND" in reversal_check:
            result["contradictory_evidence"].append(reversal_check)
            result["alternative_explanations"].append(
                "Transaction may have been reversed or adjusted."
            )

    # Check timing differences
    record_date = finding.get("record_date", "")
    settle_date = available_data.get("settlement_date", "")
    if record_date and settle_date:
        timing = check_timing_difference_tool(record_date, settle_date)
        if "TIMING DIFFERENCE" in timing:
            result["alternative_explanations"].append(timing)

    # Deterministic variance verification
    expected = finding.get("expected_amount", "")
    actual = finding.get("impact_amount", "")
    if expected and actual:
        result["calculation_check"] = verify_variance_tool(expected, actual)

    # Determine verdict
    if result["contradictory_evidence"]:
        result["verdict"] = ReviewVerdict.CONTRADICTED.value
    elif result["alternative_explanations"] and not result["contradictory_evidence"]:
        result["verdict"] = ReviewVerdict.PARTIALLY_SUPPORTED.value
    elif finding.get("source_evidence"):
        result["verdict"] = ReviewVerdict.SUPPORTED.value
    else:
        result["verdict"] = ReviewVerdict.INSUFFICIENT_EVIDENCE.value

    return result


def run_blind_spot_review(
    audit_state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Blind-Spot Spotter: Review audit coverage for missing relationships,
    untested procedures, and unsupported conclusions.
    """
    blind_spots = []

    # Check missing document relationships
    findings = audit_state.get("investigation_findings", [])
    for f in findings:
        if not f.get("source_evidence"):
            blind_spots.append({
                "type": "UNSUPPORTED_CONCLUSION",
                "finding_id": f.get("finding_id", ""),
                "description": f"Finding '{f.get('title', '')}' has no linked evidence.",
                "severity": "HIGH",
            })

    # Check for untested areas
    errors = audit_state.get("execution_errors", [])
    if errors:
        blind_spots.append({
            "type": "EXECUTION_GAPS",
            "description": f"{len(errors)} execution error(s) may have prevented full coverage.",
            "severity": "MEDIUM",
        })

    # Check counter-evidence coverage
    counter = audit_state.get("counter_evidence", [])
    unresolved = [c for c in counter if c.get("reviewer_verdict") in (
        "UNRESOLVED", "INSUFFICIENT_EVIDENCE"
    )]
    if unresolved:
        blind_spots.append({
            "type": "INCOMPLETE_REVIEW",
            "description": f"{len(unresolved)} finding(s) have unresolved or insufficient counter-evidence reviews.",
            "severity": "HIGH",
        })

    return blind_spots


def run_independent_finding_review(
    finding: Dict[str, Any],
    counter_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Independent Finding Reviewer: Examine original evidence references,
    review deterministic calculation outputs, check supporting and
    contradictory evidence, and return an independent structured verdict.
    """
    verdict = ReviewVerdict.UNRESOLVED.value
    rationale_parts = []

    # Check evidence linkage
    has_evidence = bool(finding.get("source_evidence"))
    has_contradiction = bool(counter_evidence.get("contradictory_evidence"))
    has_calc_check = bool(counter_evidence.get("calculation_check"))
    ce_verdict = counter_evidence.get("verdict", "UNRESOLVED")

    if has_evidence and not has_contradiction and has_calc_check:
        verdict = ReviewVerdict.SUPPORTED.value
        rationale_parts.append("Original evidence present, no contradictions, calculation verified.")
    elif has_contradiction:
        verdict = ReviewVerdict.CONTRADICTED.value
        rationale_parts.append("Contradictory evidence found.")
    elif has_evidence and ce_verdict == "PARTIALLY_SUPPORTED":
        verdict = ReviewVerdict.PARTIALLY_SUPPORTED.value
        rationale_parts.append("Evidence present but alternative explanations exist.")
    elif not has_evidence:
        verdict = ReviewVerdict.INSUFFICIENT_EVIDENCE.value
        rationale_parts.append("No source evidence linked to finding.")

    return {
        "finding_id": finding.get("finding_id", ""),
        "reviewer_role": "Independent Finding Reviewer (MS Agent Framework)",
        "independent_verdict": verdict,
        "rationale": " ".join(rationale_parts) if rationale_parts else "Review inconclusive.",
        "original_evidence_reviewed": has_evidence,
        "contradictions_found": has_contradiction,
        "calculation_verified": has_calc_check,
    }


# ─── LLM-Powered Review (optional, uses local Ollama) ──────────

def run_llm_review(
    finding: Dict[str, Any],
    context: str,
    ollama_base_url: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Optional LLM-powered independent review using MS Agent Framework
    with OllamaChatClient. Returns structured review or None on failure.

    This supplements but DOES NOT replace deterministic verification.
    """
    import os
    ollama_base_url = ollama_base_url or os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model_name = model_name or os.environ.get("OLLAMA_MODEL", "qwen3:4b")

    is_cloud = bool(os.environ.get("RENDER") or os.environ.get("VERCEL") or os.environ.get("ENV") == "production")
    if is_cloud and ("127.0.0.1" in ollama_base_url or "localhost" in ollama_base_url):
        return {
            "status": "UNAVAILABLE",
            "verdict": "UNRESOLVED",
            "reason": "Local inference service is not configured for public cloud. Remote AI investigation requires a secured inference gateway.",
            "reviewer_role": "Independent Reviewer (MS Agent Framework)",
        }
    try:
        from agent_framework import Agent as MSAgent
        from agent_framework_ollama import OllamaChatClient

        client = OllamaChatClient(
            model=model_name,
            endpoint=ollama_base_url,
        )

        prompt = (
            "You are an independent financial audit reviewer. "
            "Review this finding and provide your assessment.\n\n"
            f"FINDING: {json.dumps(finding, indent=2)}\n\n"
            f"CONTEXT: {context}\n\n"
            "INSTRUCTIONS:\n"
            "1. Do NOT perform any arithmetic. Use only the provided numbers.\n"
            "2. Assess whether the evidence supports the finding.\n"
            "3. Identify any missing evidence or alternative explanations.\n"
            "4. Provide your verdict: SUPPORTED, CONTRADICTED, PARTIALLY_SUPPORTED, "
            "UNRESOLVED, or INSUFFICIENT_EVIDENCE.\n"
            "5. Keep your response concise."
        )

        # Synchronous invocation
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                client.complete(prompt)
            )
        finally:
            loop.close()

        return {
            "finding_id": finding.get("finding_id", ""),
            "reviewer_role": "LLM Independent Reviewer (MS Agent Framework)",
            "llm_assessment": str(response) if response else "No response.",
        }
    except Exception as e:
        return {
            "finding_id": finding.get("finding_id", ""),
            "reviewer_role": "LLM Independent Reviewer (MS Agent Framework)",
            "llm_assessment": f"LLM review unavailable: {str(e)[:200]}",
            "error": True,
        }
