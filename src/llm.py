import json
import os
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai.types import Content, Part
from utils import log_error, log_info

SYSTEM_PROMPT = (
    "You are an autonomous coding agent. Output ONLY JSON in the format:\n"
    "{\n"
    "  'plan': [...],\n"
    "  'actions': [\n"
    "    {\n"
    "      'type': 'create_file' | 'modify_file' | 'run_command',\n"
    "      'path': '...',\n"
    "      'content': '...',\n"
    "      'command': '...'\n"
    "    }\n"
    "  ]\n"
    "}"
)


class LlmClientError(Exception):
    pass


def _load_json_payload(payload_text: str) -> Any:
    # Strip markdown code block if present
    if payload_text.strip().startswith("```json") and payload_text.strip().endswith("```"):
        payload_text = payload_text.strip()[7:-3].strip()
    try:
        return json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise LlmClientError("Failed to decode JSON payload from LLM response") from exc


def call_llm(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL_NAME")

    if not api_key:
        raise LlmClientError("GEMINI_API_KEY environment variable is required")
    if not model_name:
        raise LlmClientError("GEMINI_MODEL_NAME environment variable is required")

    client = genai.Client(api_key=api_key)

    full_prompt = SYSTEM_PROMPT + "\n\nUser query: " + prompt
    contents = Content(role="user", parts=[Part(text=full_prompt)])

    try:
        log_info("LLM request attempt")
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config={
                "temperature": 0.2,
                "max_output_tokens": 1600,
            },
        )
        
        raw_content = response.text
        log_info(f"Raw LLM response: {raw_content}")
        if not isinstance(raw_content, str):
            raise LlmClientError("LLM response content is not a string")

        payload_object = _load_json_payload(raw_content.strip())
        if not isinstance(payload_object, dict):
            raise LlmClientError("Parsed LLM response must be a JSON object")
        return payload_object
    except Exception as exc:
        log_error(f"LLM request failed: {exc}")
        raise LlmClientError("LLM request failed") from exc
