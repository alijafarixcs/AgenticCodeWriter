"""Syntax checking and controlled subprocess execution for candidate code."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile


@dataclass(frozen=True)
class SimulationResult:
    success: bool
    command: tuple[str, ...]
    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    def as_feedback(self) -> str:
        status = "passed" if self.success else "failed"
        details = [f"Local simulation {status}.", f"Command: {' '.join(self.command)}"]
        if self.timed_out:
            details.append("The process exceeded the timeout.")
        if self.return_code is not None:
            details.append(f"Exit code: {self.return_code}")
        if self.stdout:
            details.append(f"Standard output:\n{self.stdout[-4000:]}")
        if self.stderr:
            details.append(f"Standard error:\n{self.stderr[-4000:]}")
        return "\n".join(details)


def simulate_code(
    code: str,
    arguments: list[str] | None = None,
    stdin_text: str = "",
    timeout: float = 10.0,
) -> SimulationResult:
    """Compile and run code in a temporary working directory.

    This limits accidental workspace writes but is not a security sandbox.
    """
    if timeout <= 0:
        raise ValueError("Simulation timeout must be greater than zero")

    try:
        compile(code, "candidate.py", "exec")
    except SyntaxError as exc:
        return SimulationResult(False, (sys.executable, "-I", "candidate.py"), None, "", str(exc))

    with tempfile.TemporaryDirectory(prefix="ai-code-agent-") as directory:
        candidate = Path(directory) / "candidate.py"
        candidate.write_text(code, encoding="utf-8")
        command = (sys.executable, "-I", str(candidate), *(arguments or []))
        try:
            completed = subprocess.run(
                command,
                cwd=directory,
                input=stdin_text,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return SimulationResult(
                False,
                command,
                None,
                exc.stdout or "",
                exc.stderr or "",
                timed_out=True,
            )

    return SimulationResult(
        completed.returncode == 0,
        command,
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )

