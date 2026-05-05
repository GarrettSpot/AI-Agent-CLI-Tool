import argparse
import sys
from dotenv import load_dotenv

from llm import call_llm
from parser import InvalidAgentResponse, parse_agent_response
from executor import execute_actions
from utils import log_debug, log_error, log_info, log_success, log_warning, set_verbose


def process_prompt(prompt: str) -> None:
    log_info("Sending prompt to LLM...")
    raw_response = call_llm(prompt)
    log_debug(f"Raw LLM response: {raw_response}")
    log_info("Parsing response from LLM...")
    agent_response = parse_agent_response(raw_response)

    plan = agent_response["plan"]
    actions = agent_response["actions"]

    log_info("Plan received:")
    for index, step in enumerate(plan, start=1):
        log_info(f"  {index}. {step}")

    if not actions:
        log_warning("No actions to execute.")
        return

    execute_actions(actions)
    log_success("All actions completed successfully.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous coding agent CLI that converts a natural language prompt into code actions."
    )
    parser.add_argument(
        "prompt",
        help="Natural language prompt to send to the LLM",
        type=str,
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "--verbose",
        help="Enable verbose logging",
        action="store_true",
    )
    args = parser.parse_args()

    load_dotenv()
    set_verbose(args.verbose)
    if args.verbose:
        log_debug("Verbose logging enabled.")

    log_info("Starting autonomous coding agent. Type 'exit' or 'quit' to stop.")
    current_prompt = args.prompt

    if current_prompt:
        log_info(f"Processing initial prompt: {current_prompt}")

    while True:
        if current_prompt is None:
            try:
                current_prompt = input("agent> ").strip()
            except (EOFError, KeyboardInterrupt):
                log_info("Input terminated. Exiting.")
                break

        if not current_prompt:
            current_prompt = None
            continue

        if current_prompt.lower() in {"exit", "quit"}:
            log_info("Exit command received. Stopping.")
            break

        try:
            process_prompt(current_prompt)
        except InvalidAgentResponse as exc:
            log_error(f"Invalid LLM response: {exc}")
        except Exception as exc:
            log_error(f"Execution aborted: {exc}")

        current_prompt = None

    return 0


if __name__ == "__main__":
    sys.exit(main())
