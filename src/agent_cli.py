import argparse
import re
import sys
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from llm import call_llm
from parser import InvalidAgentResponse, parse_agent_response
from executor import execute_actions
from utils import log_debug, log_error, log_info, log_success, log_warning, set_verbose


def extract_webpage_summary_fallback(url: str) -> str:
    """Fallback webpage extraction using requests and BeautifulSoup."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract CSS links
        css_links = [str(link.get('href', '')).strip() for link in soup.find_all('link', rel='stylesheet') if link.get('href')]
        
        # Extract JS scripts
        js_scripts = []
        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                js_scripts.append(str(src).strip())
        
        css_sample = ', '.join(css_links[:5]) if css_links else "None"
        js_sample = ', '.join(js_scripts[:5]) if js_scripts else "None"
        css_info = f"Number of CSS links: {len(css_links)}, Sample links: {css_sample}"
        js_info = f"Number of JS scripts: {len(js_scripts)}, Sample sources: {js_sample}"
        
        return f"Webpage analysis for {url} (fallback method):\nCSS Summary: {css_info}\nJavaScript Summary: {js_info}\nUse this information to generate HTML, CSS, and JS files that recreate the webpage's appearance and functionality."
    except Exception as e:
        log_warning(f"Fallback extraction failed: {e}")
        return ""


def process_prompt(prompt: str) -> None:
    # Extract webpage information if URL is present
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(prompt)
    enhanced_prompt = prompt
    if urls:
        url = urls[0]  # Take the first URL
        log_info(f"Extracting information from webpage: {url}")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=10000)
                
                # Extract summary of CSS
                css_summary = page.evaluate("""
                    const sheets = Array.from(document.styleSheets);
                    const rules = sheets.flatMap(sheet => {
                        try {
                            return sheet.cssRules ? Array.from(sheet.cssRules) : [];
                        } catch {
                            return [];
                        }
                    });
                    const selectors = rules.map(rule => rule.selectorText).filter(Boolean);
                    const uniqueSelectors = [...new Set(selectors)].slice(0,20);
                    return {
                        numSheets: sheets.length,
                        numRules: rules.length,
                        selectors: uniqueSelectors
                    };
                """)
                
                # Extract summary of JS
                js_summary = page.evaluate("""
                    const scripts = Array.from(document.scripts);
                    const sources = scripts.map(script => script.src).filter(Boolean);
                    const inlineCount = scripts.filter(script => !script.src).length;
                    return {
                        numScripts: scripts.length,
                        externalSources: sources.slice(0,10),
                        inlineCount: inlineCount
                    };
                """)
                
                browser.close()
                css_info = f"Number of stylesheets: {css_summary['numSheets']}, Number of CSS rules: {css_summary['numRules']}, Sample selectors: {', '.join(css_summary['selectors'])}"
                js_info = f"Number of scripts: {js_summary['numScripts']}, External sources: {', '.join(js_summary['externalSources'])}, Inline scripts: {js_summary['inlineCount']}"
                enhanced_prompt += f"\n\nWebpage analysis for {url}:\nCSS Summary: {css_info}\nJavaScript Summary: {js_info}\nUse this information to generate HTML, CSS, and JS files that recreate the webpage's appearance and functionality."
                log_info("Webpage information extracted and added to prompt.")
        except Exception as exc:
            log_warning(f"Playwright extraction failed: {exc}. Trying fallback method.")
            fallback_info = extract_webpage_summary_fallback(url)
            if fallback_info:
                enhanced_prompt += "\n\n" + fallback_info
                log_info("Fallback webpage information extracted and added to prompt.")
            else:
                log_warning("Both extraction methods failed. Proceeding without webpage information.")
    
    log_info("Sending prompt to LLM...")
    raw_response = call_llm(enhanced_prompt)
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
