import json
from typing import Any, Dict, List, Sequence

from utils import log_error


class InvalidAgentResponse(Exception):
    pass


VALID_ACTION_TYPES = {"create_file", "modify_file", "run_command"}
REQUIRED_FIELDS = {
    "create_file": {"type", "path", "content"},
    "modify_file": {"type", "path", "content"},
    "run_command": {"type", "command"},
}


def _ensure_dict(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise InvalidAgentResponse("Response must be a JSON object")
    return data


def _ensure_list(data: Any, name: str) -> List[Any]:
    if not isinstance(data, list):
        raise InvalidAgentResponse(f"'{name}' must be a list")
    return data


def _validate_action(action: Any, index: int) -> Dict[str, Any]:
    if not isinstance(action, dict):
        raise InvalidAgentResponse(f"Action at index {index} must be an object")

    action_type = action.get("type")
    if action_type not in VALID_ACTION_TYPES:
        raise InvalidAgentResponse(
            f"Action at index {index} has invalid type '{action_type}'."
        )

    required_fields = REQUIRED_FIELDS[action_type]
    missing = required_fields - action.keys()
    if missing:
        raise InvalidAgentResponse(
            f"Action at index {index} is missing required fields: {', '.join(sorted(missing))}."
        )

    if action_type in {"create_file", "modify_file"}:
        if not isinstance(action["path"], str) or not action["path"].strip():
            raise InvalidAgentResponse(f"Action at index {index} must include a non-empty 'path'.")
        if not isinstance(action["content"], str):
            raise InvalidAgentResponse(f"Action at index {index} must include a string 'content'.")
    elif action_type == "run_command":
        if not isinstance(action["command"], str) or not action["command"].strip():
            raise InvalidAgentResponse(f"Action at index {index} must include a non-empty 'command'.")

    return action


def parse_agent_response(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise InvalidAgentResponse("Agent response is not valid JSON") from exc

    payload = _ensure_dict(payload)
    plan = payload.get("plan")
    if plan is None:
        raise InvalidAgentResponse("Response must include a 'plan' field")
    actions = payload.get("actions")
    if actions is None:
        raise InvalidAgentResponse("Response must include an 'actions' field")

    plan_list = _ensure_list(plan, "plan")
    actions_list = _ensure_list(actions, "actions")

    for index, action in enumerate(actions_list):
        _validate_action(action, index)

    return {"plan": plan_list, "actions": actions_list}
