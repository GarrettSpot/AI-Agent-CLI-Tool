import os
import shlex
import subprocess
from typing import Any, Dict, List

from utils import atomic_write, ensure_directory, log_error, log_info, log_success


def _run_shell_command(command: str) -> None:
    if not command.strip():
        raise ValueError("Command cannot be empty")

    log_info(f"Executing command: {command}")
    try:
        if os.name == "nt":
            args = shlex.split(command, posix=False)
        else:
            args = shlex.split(command)
    except ValueError as exc:
        raise RuntimeError(f"Failed to parse command: {exc}") from exc

    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        if completed.stdout:
            log_info(completed.stdout.strip())
        if completed.stderr:
            log_info(completed.stderr.strip())
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Command executable not found: {args[0]}" ) from exc
    except subprocess.CalledProcessError as exc:
        output = exc.stdout or ""
        error_output = exc.stderr or ""
        raise RuntimeError(
            f"Command failed with exit code {exc.returncode}.\n{output}{error_output}"
        ) from exc


def create_file(path: str, content: str) -> None:
    log_info(f"Creating file: {path}")
    ensure_directory(os.path.dirname(path))
    atomic_write(path, content)
    log_success(f"Created file {path}")


def modify_file(path: str, content: str) -> None:
    log_info(f"Modifying file: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot modify file because it does not exist: {path}")
    atomic_write(path, content)
    log_success(f"Modified file {path}")


def execute_action(action: Dict[str, Any]) -> None:
    action_type = action["type"]
    if action_type in ("create_file", "modify_file"):
        action["path"] = os.path.join("output", action["path"])
    if action_type == "create_file":
        create_file(action["path"], action["content"])
    elif action_type == "modify_file":
        modify_file(action["path"], action["content"])
    elif action_type == "run_command":
        _run_shell_command(action["command"])
    else:
        raise RuntimeError(f"Unsupported action type: {action_type}")


def execute_actions(actions: List[Dict[str, Any]]) -> None:
    if not actions:
        log_info("No actions to execute.")
        return

    for index, action in enumerate(actions, start=1):
        log_info(f"Executing action {index}/{len(actions)}: {action.get('type')}")
        execute_action(action)
