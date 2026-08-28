# AI Code Agent — Project Guide

## 1. What this project does

This project is a Python command-line application that uses an OpenAI-compatible language model to generate Python programs.

The application follows an iterative process:

1. The user provides a use case and one or more goals.
2. The model generates Python code.
3. The model reviews the generated code against the goals.
4. The model decides whether all goals are satisfied.
5. If the goals are not satisfied, the code and review feedback are sent through another iteration.
6. The final code is saved in the `generated/` directory.

The application saves the latest code even when the maximum number of iterations is reached.

## 2. Project structure

```text
FreeAgentTestExamples/
├── .env.example
├── .gitignore
├── PROJECT_GUIDE.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── rules.md
├── generated/
├── src/
│   └── ai_code_agent/
│       ├── __init__.py
│       ├── agent.py
│       ├── cli.py
│       └── config.py
└── tests/
    └── test_agent.py
```

The `generated/`, `.venv/`, and `.env` paths may only appear after setup or after running the application. They are intentionally excluded from Git.

## 3. Entry point

The application entry point is the `main()` function in:

```text
src/ai_code_agent/cli.py
```

The following configuration in `pyproject.toml` creates the `ai-code-agent` terminal command:

```toml
[project.scripts]
ai-code-agent = "ai_code_agent.cli:main"
```

This means:

- `ai-code-agent` is the command typed in the terminal.
- `ai_code_agent.cli` refers to `src/ai_code_agent/cli.py`.
- `main` is the function called to start the program.

The bottom of `cli.py` also contains:

```python
if __name__ == "__main__":
    main()
```

This allows the CLI to be started as a Python module as well:

```powershell
python -m ai_code_agent.cli --help
```

The installed command is normally more convenient:

```powershell
ai-code-agent --help
```

## 4. Complete execution flow

When this command is executed:

```powershell
ai-code-agent "Create a command-line calculator" `
  --goal "Supports basic arithmetic" `
  --goal "Handles invalid input"
```

the application performs the following steps.

### Step 1: Parse command-line arguments

`cli.py` uses Python's `argparse` module to read:

- `use_case`: the program to create.
- `--goal`: a requirement for the generated program. This option can be repeated.
- `--max-iterations`: the maximum generation attempts; the default is `5`.
- `--output-dir`: where generated files are saved; the default is `generated`.
- `--code`: an existing `.py` file used as the starting candidate.
- `--review`: reviews the file supplied by `--code` before generating a revision.
- `--simulate`: syntax-checks and runs every candidate.
- `--test-arg`: passes one CLI argument to simulated code; it can be repeated.
- `--test-input`: supplies standard input to interactive simulated code.
- `--simulation-timeout`: stops a simulated process after this many seconds.

### Step 2: Load configuration

`Settings.from_env()` in `config.py` loads `.env` through `python-dotenv`.

It requires:

- `UPSTREAM_PUBLIC_BASE_URL`: the OpenAI-compatible server address.
- `UPSTREAM_API_KEY`: the authentication key for that server.

It also reads:

- `UPSTREAM_MODEL`: the selected model; the default is `auto`.

The server address is normalized so it ends in `/v1`. For example:

```text
https://your-openai-compatible-server.example
```

becomes:

```text
https://your-openai-compatible-server.example/v1
```

### Step 3: Create the model client

`CodeAgent.from_settings()` creates a LangChain `ChatOpenAI` client using the configured server, key, model, and a temperature of `0.3`.

A lower temperature encourages more consistent code generation.

### Step 4: Start the agent

The CLI calls:

```python
agent.run(use_case, goals, max_iterations)
```

`CodeAgent.run()` validates that:

- The use case is not empty.
- At least one goal was supplied.
- The maximum iteration count is at least one.

### Step 5: Generate code

`generate_prompt()` builds a prompt containing:

- The requested use case.
- Every goal.
- Previously generated code, when this is not the first iteration.
- Feedback from the previous review, when available.

The model is instructed to return only runnable Python code.

### Step 6: Clean the response

`clean_code_block()` removes an outer Markdown code fence if the model returns one despite the instruction.

For example:

````text
```python
print("Hello")
```
````

becomes:

```python
print("Hello")
```

### Step 7: Review the code

`review()` sends the generated code and goals back to the model. The reviewer checks:

- Correctness.
- Simplicity.
- Readability.
- Edge cases.
- Possible bugs.
- Compliance with every goal.

### Step 8: Evaluate the result

`goals_met()` asks the model to return exactly `True` or `False` based on the review.

- `True`: iteration stops.
- `False`: another iteration begins with the previous code and feedback.

### Step 9: Save the result

`save()` creates the output directory and writes the final code to a unique `.py` file.

A description such as:

```text
Create a command-line calculator
```

may produce a filename like:

```text
generated/create_a_command_line_calculator_a1b2.py
```

The random suffix prevents an earlier generated file from being overwritten.

### Step 10: Print the result

The CLI prints:

- The generated file path.
- The number of iterations used.
- Whether the goals were satisfied or the iteration limit was reached.

## 5. Source files

### `src/ai_code_agent/cli.py`

This is the command-line layer and application entry point.

Its responsibilities are:

- Defining CLI arguments in `build_parser()`.
- Reading the user's command.
- Loading environment settings.
- Constructing the agent.
- Starting the generation workflow.
- Printing the final status.

Business logic is kept out of this file so that the agent can also be called from another Python program.

### `src/ai_code_agent/config.py`

This module contains the immutable `Settings` dataclass.

Its responsibilities are:

- Loading `.env`.
- Reading environment variables.
- Reporting missing required settings.
- Normalizing the OpenAI-compatible URL.

Configuration is loaded when `Settings.from_env()` is called, not when the package is imported. This allows tests and other modules to import the project without requiring a real API key.

### `src/ai_code_agent/agent.py`

This module contains the main application logic.

Important components include:

#### `LanguageModel`

A Python protocol describing an object with an `invoke()` method. Both `ChatOpenAI` and the fake test model follow this interface.

This makes the core workflow testable without making network requests.

#### `RunResult`

An immutable dataclass returned after a run.

It contains:

- `path`: location of the generated file.
- `iterations`: number of iterations performed.
- `goals_satisfied`: whether the evaluator accepted all goals.

#### `clean_code_block()`

Removes optional Markdown fences surrounding generated Python code.

#### `to_snake_case()`

Converts a use-case description into a safe filename component.

#### `CodeAgent`

The main service class. It owns the language model and output directory and implements generation, review, evaluation, iteration, and saving.

Its methods are:

- `from_settings()`: creates a real `ChatOpenAI` client.
- `_goals_text()`: formats goals as a bullet list for prompts.
- `generate_prompt()`: creates the generation or revision prompt.
- `review()`: requests a code review.
- `goals_met()`: asks whether the goals are satisfied.
- `_content()`: safely extracts text from a model response.
- `save()`: creates a unique output file.
- `run()`: coordinates the complete workflow.

### `src/ai_code_agent/__init__.py`

This file makes `ai_code_agent` a Python package and exposes the most useful public classes:

```python
from ai_code_agent import CodeAgent, RunResult, Settings
```

## 6. Project and dependency files

### `pyproject.toml`

This is the main Python project definition. It declares:

- Package name and version.
- Python 3.11 or newer as the supported runtime.
- Runtime dependencies.
- The `ai-code-agent` command.
- The `src/` package layout.
- Pytest configuration.

Running this command installs the project and creates its entry-point command:

```powershell
pip install -e .
```

The `-e` means editable installation. Source-code changes are used immediately without reinstalling the package.

### `requirements.txt`

Contains runtime dependencies:

- `langchain-openai`: supplies the `ChatOpenAI` integration.
- `openai`: provides the underlying OpenAI-compatible client functionality.
- `python-dotenv`: loads values from `.env`.

### `requirements-dev.txt`

Includes all runtime requirements and adds `pytest` for automated testing.

### `.env.example`

A safe template showing which environment variables are needed. Copy it to `.env` and replace the placeholder key:

```powershell
Copy-Item .env.example .env
```

Never place a real secret in `.env.example`.

### `.gitignore`

Prevents local or generated files from being committed, including:

- `.env` secrets.
- `.venv/` installed packages.
- Python cache files.
- Pytest cache files.
- Generated programs.

### `README.md`

Contains the quick setup, run, and test instructions.

### `rules.md`

Contains workspace-specific implementation instructions, including the required Python 3.11 setup commands.

## 7. Tests

Tests are located in `tests/test_agent.py`.

The test suite checks:

- Removal of Markdown code fences.
- Conversion of descriptions to safe filenames.
- Successful completion when goals are accepted.
- Validation of an empty use case.
- Validation of an empty goal list.

`FakeLLM` supplies predetermined responses. Therefore, tests do not use the API, consume tokens, or require internet access.

Run the tests with:

```powershell
.venv\Scripts\Activate.ps1
pytest
```

## 8. Installation

Open PowerShell in the project directory:

```powershell
Set-Location C:\projects\FreeAgentTestExamples
pyenv local 3.11
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e .
Copy-Item .env.example .env
```

Open the configuration file:

```powershell
notepad .env
```

Set the values:

```env
UPSTREAM_PUBLIC_BASE_URL=https://your-openai-compatible-server.example
UPSTREAM_API_KEY=your-real-api-key
UPSTREAM_MODEL=auto
```

## 9. Usage examples

### Generate a calculator

```powershell
ai-code-agent "Create a command-line calculator" `
  --goal "Supports addition, subtraction, multiplication, and division" `
  --goal "Validates user input" `
  --goal "Handles division by zero"
```

### Change the iteration limit

```powershell
ai-code-agent "Create a password generator" `
  --goal "Uses secure randomness" `
  --goal "Allows configurable length" `
  --max-iterations 3
```

### Change the output directory

```powershell
ai-code-agent "Create a CSV reader" `
  --goal "Handles missing files" `
  --output-dir output
```

### Run generated code

First list the generated files:

```powershell
Get-ChildItem generated
```

Then run the desired file:

```powershell
python generated\generated_filename.py
```

Generated programs are model output. Review them before executing them, especially if they access files, commands, credentials, or external services.

## 10. Using the agent from Python

The CLI is not required. The package can be called directly:

```python
from ai_code_agent import CodeAgent, Settings

settings = Settings.from_env()
agent = CodeAgent.from_settings(settings)

result = agent.run(
    use_case="Create a command-line calculator",
    goals=[
        "Supports basic arithmetic",
        "Validates user input",
        "Handles division by zero",
    ],
    max_iterations=5,
)

print(result.path)
print(result.iterations)
print(result.goals_satisfied)
```

## 11. API request count

Each iteration normally makes three model requests:

1. Generate or revise the code.
2. Review the code.
3. Evaluate whether the goals are satisfied.

With the default limit of five iterations, a run can make up to fifteen model requests. It may stop earlier when the evaluator returns `True`.

## 12. Current limitations

- Execution simulation is opt-in with `--simulate`; it cannot prove every behavior is correct.
- The temporary simulation directory is not a security sandbox. Simulated code retains the current user's permissions and may access the network or files through absolute paths.
- The reviewer and evaluator use the same configured model as the generator.
- A model can incorrectly approve or reject code.
- Requests do not currently have application-level retry or timeout settings.
- The latest candidate is saved even if the evaluator does not approve it.
- Goals must be supplied individually with repeated `--goal` options.

These choices keep the initial project small and make its behavior easy to understand. Automated syntax validation, isolated execution, retry handling, and separate generator/reviewer models can be added later.
