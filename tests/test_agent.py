from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_code_agent.agent import CodeAgent, clean_code_block, to_snake_case
from ai_code_agent.simulation import simulate_code


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    def invoke(self, input: str) -> SimpleNamespace:
        return SimpleNamespace(content=next(self.responses))


def test_clean_code_block() -> None:
    assert clean_code_block("```python\nprint('ok')\n```") == "print('ok')"
    assert clean_code_block("print('ok')") == "print('ok')"


def test_to_snake_case() -> None:
    assert to_snake_case("Find a Binary Gap!") == "find_a_binary_gap"
    assert to_snake_case("***") == "generated"


def test_agent_stops_when_goals_are_met(tmp_path: Path) -> None:
    llm = FakeLLM(["```python\nprint('ok')\n```", "Everything is correct.", "True"])
    result = CodeAgent(llm, tmp_path).run("Print ok", ["Runs correctly"])
    assert result.goals_satisfied is True
    assert result.iterations == 1
    assert "print('ok')" in result.path.read_text(encoding="utf-8")


def test_agent_can_review_existing_code_first(tmp_path: Path) -> None:
    llm = FakeLLM(["The existing code meets the goal.", "True"])
    result = CodeAgent(llm, tmp_path).run(
        "Print ok",
        ["Runs correctly"],
        initial_code="print('ok')",
        review_first=True,
    )
    assert result.iterations == 1
    assert result.goals_satisfied is True


def test_simulate_code_with_arguments_and_input() -> None:
    result = simulate_code(
        "import sys\nprint(sys.argv[1], input())",
        arguments=["hello"],
        stdin_text="world\n",
    )
    assert result.success is True
    assert "hello world" in result.stdout


def test_simulate_code_reports_syntax_error() -> None:
    result = simulate_code("if:")
    assert result.success is False
    assert "invalid syntax" in result.stderr


@pytest.mark.parametrize("use_case, goals", [("", ["works"]), ("code", [])])
def test_agent_validates_inputs(tmp_path: Path, use_case: str, goals: list[str]) -> None:
    with pytest.raises(ValueError):
        CodeAgent(FakeLLM([]), tmp_path).run(use_case, goals)
