"""Command-line interface."""

import argparse
from pathlib import Path

from .agent import CodeAgent
from .config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and iteratively review Python code.")
    parser.add_argument("use_case", help="Description of the Python program to generate")
    parser.add_argument("--goal", action="append", required=True, help="Goal to satisfy; repeat as needed")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path("generated"))
    parser.add_argument("--code", type=Path, help="Existing .py file to use as the starting code")
    parser.add_argument("--review", action="store_true", help="Review --code before generating a revision")
    parser.add_argument("--simulate", action="store_true", help="Compile and run each candidate locally")
    parser.add_argument("--test-arg", action="append", default=[], help="Argument passed to the candidate; repeat as needed")
    parser.add_argument("--test-input", default="", help="Text supplied to the candidate's standard input")
    parser.add_argument("--simulation-timeout", type=float, default=10.0, help="Execution timeout in seconds")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.review and not args.code:
        parser.error("--review requires --code FILE")
    initial_code = ""
    if args.code:
        if args.code.suffix.casefold() != ".py" or not args.code.is_file():
            parser.error("--code must point to an existing .py file")
        initial_code = args.code.read_text(encoding="utf-8")
    settings = Settings.from_env()
    print(f"Using {settings.model} at {settings.base_url}")
    result = CodeAgent.from_settings(settings, args.output_dir).run(
        args.use_case,
        args.goal,
        args.max_iterations,
        initial_code=initial_code,
        review_first=args.review,
        simulate=args.simulate,
        test_arguments=args.test_arg,
        test_input=args.test_input,
        simulation_timeout=args.simulation_timeout,
    )
    status = "satisfied" if result.goals_satisfied else "iteration limit reached"
    print(f"Saved {result.path} after {result.iterations} iteration(s): {status}")
    if result.simulation:
        print(result.simulation.as_feedback())


if __name__ == "__main__":
    main()
