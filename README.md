# CLI Coding Agent

An autonomous coding agent CLI that converts a natural language prompt into code actions using Gemini.

## Features

- Sends natural language prompts to an LLM
- Detects webpage URLs in prompts
- Extracts webpage structure and resource summaries
- Adds webpage context to prompts before sending to Gemini
- Executes agent actions such as creating or modifying files and running commands

## Prerequisites

- Python 3.11+
- `GEMINI_API_KEY` and `GEMINI_MODEL_NAME` environment variables set
- Optional: Playwright browser support for richer webpage extraction

## Installation

1. Clone the repository:

```powershell
git clone https://github.com/<your-org>/CLI-coding-agent.git
cd CLI-coding-agent
```

2. Install Python dependencies:

```powershell
python -m pip install -r src/requirements.txt
```

3. Create a `.env` file in the repo root with:

```ini
GEMINI_API_KEY=your_api_key
GEMINI_MODEL_NAME=your_model_name
```

4. If you want Playwright browser extraction, install browsers:

```powershell
python -m playwright install
```

> If browser installation fails or is unavailable, the CLI falls back to a simpler HTML-based extraction using `requests` and `BeautifulSoup`.

## Usage

Run the CLI from the repository root:

```powershell
python src/agent_cli.py "Create a webpage based on https://www.example.com"
```

Or start the interactive prompt:

```powershell
python src/agent_cli.py
```

Then enter prompts at `agent>`.

## Prompt behavior

- If the prompt contains a URL, the agent attempts to extract webpage data first
- It adds a webpage summary to the prompt before sending it to the LLM
- The goal is to produce code files like `index.html`, `styles.css`, and `script.js`

## Notes

- The CLI logs extraction and execution progress
- If Playwright is unavailable, it falls back to requests/BeautifulSoup extraction
- For best results, provide clear instructions such as:
  - `Generate HTML, CSS, and JS that matches the design of https://example.com`

## Troubleshooting

- If the CLI fails to import Playwright, ensure Playwright is installed and `python -m playwright install` has run successfully
- If webpage extraction fails, the fallback method may still provide useful prompt context
- Use `--verbose` to enable more detailed logging:

```powershell
python src/agent_cli.py --verbose "Create a webpage like https://www.example.com"
```
