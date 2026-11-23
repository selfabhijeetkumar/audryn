"""
AUDRYN Response Normalizer.
Extracts structured JSON, markdown content, and usage metrics across heterogeneous LLMs.
"""
import json
import re
from typing import Dict, Any, Optional, Tuple


class ResponseNormalizer:
    @staticmethod
    def extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from raw text or markdown code fence."""
        if not text:
            return None
        text_clean = text.strip()
        # Direct parse attempt
        try:
            return json.loads(text_clean)
        except Exception:
            pass

        # Match ```json ... ``` code fence
        json_fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_clean, re.IGNORECASE)
        if json_fence:
            fence_content = json_fence.group(1).strip()
            try:
                return json.loads(fence_content)
            except Exception:
                pass

        # Match first { ... } or [ ... ] block
        brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text_clean)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except Exception:
                pass

        return None

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes trailing markdown code markers if incomplete."""
        if not text:
            return ""
        return text.strip()
