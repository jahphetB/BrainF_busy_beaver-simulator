"""Compatibility entry point; importing does not run an experiment."""

from pathlib import Path
import sys

# Allow a fresh checkout to run without installation or network access.
SOURCE = str(Path(__file__).resolve().parent / "src")
if SOURCE not in sys.path:
	sys.path.insert(0, SOURCE)

from brainfuck_research.cli import main, print_trace_step
from brainfuck_research.interpreter import run_program as execute_program
from brainfuck_research.syntax import valid_brackets


def run_program(program, max_steps):
	"""Preserve the legacy five-item tuple for valid command-only programs."""
	result = execute_program(program, max_steps)
	state = result.state
	return result.status.value, state.steps, state.output.decode("latin-1"), state.pointer, list(state.tape)


def run_program_with_trace(program, max_steps):
	result = execute_program(program, max_steps, trace=print_trace_step)
	print(f"Status: {result.status.value}; total steps: {result.state.steps}")
	return result


if __name__ == "__main__":
	raise SystemExit(main())
