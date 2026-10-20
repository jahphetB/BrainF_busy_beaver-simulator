"""One instruction implementation for ordinary execution and tracing."""

from collections.abc import Callable

from .models import ExecutionResult, State, Status, TraceStep
from .syntax import ProgramSyntaxError, build_bracket_map


def validate_max_steps(max_steps: int) -> None:
	if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 0:
		raise ValueError("max_steps must be a nonnegative integer")


class _Machine:
	def __init__(self, program: str, brackets: dict[int, int], input_data: bytes):
		self.program = program
		self.brackets = brackets
		self.input_data = input_data
		self.ip = 0
		self.pointer = 0
		self.tape = [0]
		self.input_pos = 0
		self.output = bytearray()
		self.steps = 0

	def snapshot(self) -> State:
		return State(self.ip, self.pointer, tuple(self.tape), self.input_pos, bytes(self.output), self.steps)

	def control_key(self) -> tuple[int, int, bytes, int]:
		return (self.ip, self.pointer, bytes(self.tape), self.input_pos)

	def step(self) -> None:
		command = self.program[self.ip]
		if command == ">":
			self.pointer += 1
			if self.pointer == len(self.tape):
				self.tape.append(0)
		elif command == "<":
			self.pointer = max(0, self.pointer - 1)
		elif command == "+":
			self.tape[self.pointer] = (self.tape[self.pointer] + 1) % 256
		elif command == "-":
			self.tape[self.pointer] = (self.tape[self.pointer] - 1) % 256
		elif command == ".":
			self.output.append(self.tape[self.pointer])
		elif command == ",":
			if self.input_pos < len(self.input_data):
				self.tape[self.pointer] = self.input_data[self.input_pos]
				self.input_pos += 1
			else:
				self.tape[self.pointer] = 0
		elif command == "[" and self.tape[self.pointer] == 0:
			self.ip = self.brackets[self.ip]
		elif command == "]" and self.tape[self.pointer] != 0:
			self.ip = self.brackets[self.ip]
		self.ip += 1
		self.steps += 1


def run_program(
	program: str,
	max_steps: int = 100,
	input_data: bytes = b"",
	*,
	trace: Callable[[TraceStep], None] | None = None,
) -> ExecutionResult:
	"""Execute with a finite budget and exact repeated-state detection.

	Syntax failures are results; invalid API configuration raises an exception.
	Trace callbacks receive immutable before/after snapshots per instruction.
	"""
	validate_max_steps(max_steps)
	if not isinstance(input_data, bytes):
		raise TypeError("input_data must be bytes")
	try:
		brackets = build_bracket_map(program)
	except ProgramSyntaxError as error:
		return ExecutionResult(program, Status.INVALID, State(), error=str(error))
	machine = _Machine(program, brackets, input_data)
	seen = {}
	while machine.ip < len(program) and machine.steps < max_steps:
		key = machine.control_key()
		if key in seen:
			start = seen[key]
			return ExecutionResult(
				program, Status.CYCLE, machine.snapshot(),
				cycle_start=start, cycle_period=machine.steps - start,
			)
		seen[key] = machine.steps
		before = machine.snapshot() if trace is not None else None
		command = program[machine.ip]
		machine.step()
		if trace is not None:
			trace(TraceStep(command, before, machine.snapshot()))
	status = Status.HALTED if machine.ip >= len(program) else Status.STEP_LIMIT
	return ExecutionResult(program, status, machine.snapshot())
