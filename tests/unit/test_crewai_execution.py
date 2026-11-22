"""
CrewAI Deterministic Execution Test for AUDRYN
Verifies:
1. Agent Execution
2. Task Completion
3. Tool Invocation (Local Python Tool)
4. Structured / Verified Result using local Ollama model (Zero Paid API)
"""
from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool


@tool("verify_depreciation_method")
def verify_depreciation_method(asset_class: str) -> str:
    """Verifies allowable statutory tax depreciation method for corporate assets."""
    if asset_class.lower() == "machinery":
        return "ALLOWABLE: WDV at 15% rate under Section 32."
    elif asset_class.lower() == "computer_software":
        return "ALLOWABLE: WDV at 40% rate under Section 32."
    return "STANDARD: Straight-line method 10% rate."


def test_crewai_execution():
    print("Initializing CrewAI with local Ollama qwen3:4b...")
    llm = LLM(model="ollama/qwen3:4b", base_url="http://127.0.0.1:11434", temperature=0.0)

    tax_agent = Agent(
        role="Corporate Tax Reviewer",
        goal="Verify corporate asset depreciation against statutory schedules using provided tools",
        backstory="Certified tax auditor verifying compliance with statutory depreciation rates. Always uses verified tools.",
        tools=[verify_depreciation_method],
        llm=llm,
        verbose=False
    )

    task = Task(
        description="You MUST execute the verify_depreciation_method tool for asset_class 'Machinery'. Return the exact statutory method and rate reported by the tool.",
        expected_output="Verification determination with statutory rate.",
        agent=tax_agent
    )

    crew = Crew(
        agents=[tax_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()
    print(f"Task output: {result.raw}")
    assert "WDV" in result.raw or "15%" in result.raw or "ALLOWABLE" in result.raw, "Tool invocation result not reflected in final output!"
    print("SUCCESS: CrewAI full execution test passed with local tool calling!")


if __name__ == "__main__":
    test_crewai_execution()
