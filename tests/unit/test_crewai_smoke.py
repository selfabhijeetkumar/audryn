"""
CrewAI Smoke Test for AUDRYN
Validates Agent and Task instantiation and crew compilation without requiring paid cloud API keys.
"""
from crewai import Agent, Task, Crew, Process


def run_smoke_test():
    print("Testing CrewAI Agent & Task initialization...")

    # Define minimal audit agent without paid API dependency
    audit_associate = Agent(
        role="Audit Associate",
        goal="Extract line items and prepare variance summaries",
        backstory="Junior auditor with high attention to detail in financial workpapers.",
        verbose=False,
        allow_delegation=False
    )

    audit_task = Task(
        description="Verify that Trial Balance debits equal credits.",
        expected_output="Verification confirmation statement.",
        agent=audit_associate
    )

    crew = Crew(
        agents=[audit_associate],
        tasks=[audit_task],
        process=Process.sequential,
        verbose=False
    )

    print(f"Crew initialized successfully: {len(crew.agents)} agent(s), {len(crew.tasks)} task(s).")
    assert crew.agents[0].role == "Audit Associate"
    assert len(crew.tasks) == 1
    print("SUCCESS: CrewAI smoke test passed!")


if __name__ == "__main__":
    run_smoke_test()
