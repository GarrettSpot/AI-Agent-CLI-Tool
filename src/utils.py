import datetime
import os
import tempfile
from typing import Optional

_VERBOSE = True


def set_verbose(enabled: bool) -> None:
    global _VERBOSE
    _VERBOSE = enabled


def _timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")


def _format_message(prefix: str, message: str) -> str:
    return f"[{_timestamp()}] {prefix} {message}"


def log_info(message: str) -> None:
    print(_format_message("INFO", message))


def log_debug(message: str) -> None:
    if _VERBOSE:
        print(_format_message("DEBUG", message))


def log_success(message: str) -> None:
    print(_format_message("SUCCESS", message))


def log_warning(message: str) -> None:
    print(_format_message("WARNING", message))


def log_error(message: str) -> None:
    print(_format_message("ERROR", message))


def exit_with_error(message: str, code: int = 1) -> None:
    log_error(message)
    raise SystemExit(code)


def ensure_directory(path: Optional[str]) -> None:
    if not path:
        return
    os.makedirs(path, exist_ok=True)


def atomic_write(path: str, content: str, encoding: str = "utf-8") -> None:
    directory = os.path.dirname(path)
    if not directory:
        directory = os.getcwd()
    ensure_directory(directory)

    with tempfile.NamedTemporaryFile("w", delete=False, dir=directory, encoding=encoding) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    os.replace(temp_path, path)
