<div align="center">

# 🤖 AI Code Agent

**Generate, review, improve, and locally test Python programs from your terminal.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-OpenAI--compatible-1C3C3C)](https://python.langchain.com/)
[![Tests](https://img.shields.io/badge/tests-8%20passing-brightgreen)](#testing)

[Quick start](#quick-start) · [Usage](#usage) · [Review existing code](#review-existing-code) · [Documentation](PROJECT_GUIDE.md)

</div>

---

AI Code Agent turns a plain-language programming request into a Python file, reviews the result against your goals, and improves it iteratively. It can also load your existing `.py` files and run controlled CLI simulations so runtime output becomes part of the review.

## ✨ Features

- Generate complete Python programs from a use case and explicit goals.
- Review code for correctness, readability, edge cases, and requirements.
- Iterate automatically until the goals pass or the configured limit is reached.
- Import an existing `.py` file as the starting candidate.
- Review existing code before deciding whether it needs revision.
- Compile and execute candidates with arguments or interactive input.
- Capture exit codes, standard output, errors, and timeouts.
- Work with OpenAI-compatible API endpoints and models.
- Save every final candidate under `generated/` with a unique filename.
- Test the workflow without API calls through a fake model.

## 🔄 How it works

```text
Use case + goals + optional Python file
                  │
                  ▼
        Generate or load candidate
                  │
                  ▼
       Optional local simulation
                  │
                  ▼
        AI review and evaluation
                  │
           Goals satisfied?
             ┌────┴────┐
            yes        no
             │          │
             ▼          └── Revise with feedback
       Save final code
```

Each normal iteration makes up to three model requests: generation, review, and goal evaluation. Review-first mode can accept an existing file without generating a replacement.

## 🚀 Quick start

### Requirements

- Python 3.11 or newer
- An OpenAI-compatible API endpoint and API key
- PowerShell for the commands below

### 1. Create the environment

```powershell
git clone <your-repository-url>
cd FreeAgentTestExamples
pyenv local 3.11
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
```

`pip install -e .` creates the `ai-code-agent` command and keeps the installation connected to your source files.

### 2. Configure the API

```powershell
Copy-Item .env.example .env
notepad .env
```

Add your endpoint, key, and model:

```env
UPSTREAM_PUBLIC_BASE_URL=https://your-openai-compatible-server.example
UPSTREAM_API_KEY=your-secret-api-key
UPSTREAM_MODEL=auto
```

The client automatically appends `/v1` when it is missing from the base URL. Your `.env` file is ignored by Git.

### 3. Generate your first program

```powershell
ai-code-agent "Create a command-line calculator" `
  --goal "Support addition, subtraction, multiplication, and division" `
  --goal "Validate user input" `
  --goal "Handle division by zero" `
  --max-iterations 3
```

The final candidate is written to `generated/`.

## 💻 Usage

The general command shape is:

```powershell
ai-code-agent "USE CASE" --goal "GOAL" [OPTIONS]
```

Repeat `--goal` to provide multiple requirements:

```powershell
ai-code-agent "Create a pure Python website scraper" `
  --goal "Extract the HTML title and meta description" `
  --goal "Validate HTTP and HTTPS URLs" `
  --goal "Use only the Python standard library"
```

Show all available options:

```powershell
ai-code-agent --help
```

### CLI options

| Option | Purpose |
|---|---|
| `use_case` | Description of the program to generate or improve. |
| `--goal TEXT` | Requirement to evaluate; repeat for multiple goals. |
| `--max-iterations N` | Maximum generation/review cycles. Default: `5`. |
| `--output-dir PATH` | Destination for final code. Default: `generated`. |
| `--code FILE.py` | Existing Python file used as the starting candidate. |
| `--review` | Review `--code` before generating a revision. |
| `--simulate` | Compile and execute each candidate locally. |
| `--test-arg VALUE` | CLI argument supplied during simulation; repeat as needed. |
| `--test-input TEXT` | Standard input supplied to an interactive program. |
| `--simulation-timeout SECONDS` | Maximum execution time. Default: `10`. |

## 🔍 Review existing code

Use `--code` with `--review` to evaluate your file before changing it:

```powershell
ai-code-agent "Review and improve my scraper" `
  --goal "Extract the title and description correctly" `
  --goal "Handle network errors clearly" `
  --code generated\my_scraper.py `
  --review `
  --max-iterations 3
```

If the evaluator accepts the original file, it is saved without an unnecessary rewrite. Otherwise, its code and review become context for the next revision.

## 🧪 Simulate command-line programs

### Program with command-line arguments

```powershell
ai-code-agent "Review and test my URL scraper" `
  --goal "Print a website title" `
  --code generated\my_scraper.py `
  --review `
  --simulate `
  --test-arg "https://example.com" `
  --simulation-timeout 20
```

Repeat `--test-arg` for multiple arguments:

```powershell
--test-arg "input.txt" --test-arg "output.txt"
```

### Interactive program

PowerShell uses a backtick followed by `n` for a newline:

```powershell
ai-code-agent "Review and test my interactive scraper" `
  --goal "The help and exit commands work" `
  --code generated\my_scraper.py `
  --review `
  --simulate `
  --test-input "help`nexit`n"
```

Simulation performs a syntax check and runs the candidate with Python's isolated-mode flag in a temporary working directory. Its output, errors, exit code, or timeout become part of the AI review.

> [!CAUTION]
> Simulation is not a security sandbox. Candidate code still runs with your user permissions and may access the network or files through absolute paths. Only execute code you trust and review generated programs before running them.

## 📦 Using it as a Python package

```python
from ai_code_agent import CodeAgent, Settings

settings = Settings.from_env()
agent = CodeAgent.from_settings(settings)

result = agent.run(
    use_case="Create a command-line calculator",
    goals=[
        "Support basic arithmetic",
        "Validate user input",
        "Handle division by zero",
    ],
    max_iterations=3,
)

print(f"Saved to: {result.path}")
print(f"Iterations: {result.iterations}")
print(f"Goals satisfied: {result.goals_satisfied}")
```

## 🗂️ Project structure

```text
.
├── src/ai_code_agent/
│   ├── agent.py          # Generation, review, evaluation, and saving
│   ├── cli.py            # Command-line entry point
│   ├── config.py         # Environment configuration
│   └── simulation.py     # Syntax check and subprocess simulation
├── tests/
│   └── test_agent.py     # Unit and workflow tests
├── .env.example          # Safe configuration template
├── pyproject.toml        # Package metadata and CLI registration
├── requirements.txt      # Runtime dependencies
├── requirements-dev.txt  # Development and test dependencies
└── PROJECT_GUIDE.md      # Detailed technical walkthrough
```

The installed entry point is declared in `pyproject.toml`:

```toml
[project.scripts]
ai-code-agent = "ai_code_agent.cli:main"
```

## ✅ Testing

The tests use a fake language model, so they do not require an API key or consume model tokens:

```powershell
.venv\Scripts\Activate.ps1
pytest
```

Expected result:

```text
8 passed
```

## 🛠️ Development

After modifying the source, run:

```powershell
pytest
ai-code-agent --help
```

Because the package is installed in editable mode, source changes are immediately available to the CLI.

For the full execution flow and an explanation of every module, read [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

## 🤝 Contributing

Issues and pull requests are welcome. A useful contribution should:

1. Keep the CLI simple and backward compatible.
2. Include tests for new behavior.
3. Avoid placing credentials or generated programs in commits.
4. Document new flags or workflows in this README.

---

<div align="center">

Built with Python, LangChain, and an OpenAI-compatible API.

</div>
