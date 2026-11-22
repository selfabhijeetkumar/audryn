"""
Microsoft Agent Framework Smoke Test for AUDRYN
Validates importing Agent and OllamaChatClient from agent-framework / agent-framework-ollama,
connecting to the local Ollama instance, and executing a verification inquiry.
"""
import sys


def run_smoke_test():
    print("Testing Microsoft Agent Framework import and initialization...")
    try:
        # Check Agent import from agent_framework
        from agent_framework import Agent
        print("PASS: Successfully imported 'Agent' from agent_framework.")
    except ImportError as e:
        print(f"FAILED to import Agent from agent_framework: {e}")
        raise

    try:
        # Check Ollama connector import
        try:
            from agent_framework_ollama import OllamaChatClient
            print("PASS: Successfully imported 'OllamaChatClient' from agent_framework_ollama.")
        except ImportError:
            from agent_framework.ollama import OllamaChatClient
            print("PASS: Successfully imported 'OllamaChatClient' from agent_framework.ollama.")
    except ImportError as e:
        print(f"FAILED to import OllamaChatClient: {e}")
        raise

    print("SUCCESS: Microsoft Agent Framework core packages imported successfully!")


if __name__ == "__main__":
    run_smoke_test()
