"""
Ollama Capability Benchmark: Inference, Tool-Calling, and Structured Output.
Verifies local-first execution on Qwen 4B without cloud dependencies.
"""
import json
import urllib.request
import urllib.error


OLLAMA_API = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:4b"


def test_basic_inference():
    print(f"--- 1. Testing Basic Local Inference on {MODEL} ---")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "What is 15% tax on $120,000? Answer with just the number."}
        ],
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "")
        print(f"Response: {content.strip()}")
        assert len(content) > 0, "Empty response from Ollama"
        print("PASS: Basic inference functional.")


def test_structured_json_output():
    print(f"--- 2. Testing Structured JSON Output on {MODEL} ---")
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Extract financial data from: 'Entity ABC Corp has Revenue of $5,000,000 and Tax Expense of $1,050,000 in FY2026.'"
            }
        ],
        "format": {
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "revenue": {"type": "number"},
                "tax_expense": {"type": "number"},
                "fiscal_year": {"type": "string"}
            },
            "required": ["entity", "revenue", "tax_expense", "fiscal_year"]
        },
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "")
        print(f"Raw JSON output:\n{content}")
        parsed = json.loads(content)
        assert "revenue" in parsed, "JSON output missing required 'revenue' field"
        print(f"Parsed JSON: {parsed}")
        print("PASS: Structured JSON output functional.")


def test_tool_calling():
    print(f"--- 3. Testing Tool Calling on {MODEL} ---")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "verify_voucher_exists",
                "description": "Look up an accounting voucher in the general ledger database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "voucher_id": {
                            "type": "string",
                            "description": "The voucher reference code (e.g., VOUCH-1029)"
                        }
                    },
                    "required": ["voucher_id"]
                }
            }
        }
    ]

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Please verify if voucher VOUCH-9872 exists in the ledger."}
        ],
        "tools": tools,
        "stream": False
    }

    req = urllib.request.Request(
        OLLAMA_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        tool_calls = data.get("message", {}).get("tool_calls", [])
        print(f"Tool calls received: {tool_calls}")
        assert len(tool_calls) > 0, "Expected at least one tool call from Ollama"
        func_name = tool_calls[0].get("function", {}).get("name")
        args = tool_calls[0].get("function", {}).get("arguments")
        print(f"Tool called: {func_name} with args: {args}")
        assert func_name == "verify_voucher_exists"
        print("PASS: Tool calling functional.")


if __name__ == "__main__":
    test_basic_inference()
    test_structured_json_output()
    test_tool_calling()
