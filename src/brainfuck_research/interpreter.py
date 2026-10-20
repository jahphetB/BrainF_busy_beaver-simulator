"""One instruction implementation for ordinary execution and tracing."""

from collections.abc import Callable
from time import monotonic

from .config import ExecutionLimits, validate_cell_bits, validate_integer
from .models import ExecutionResult, State, Status, TraceStep
from .syntax import ProgramSyntaxError, build_bracket_map


def validate_max_steps(max_steps: int) -> None:
	validate_integer("max_steps", max_steps)


class _Machine:
	def __init__(self, program: str, brackets: dict[int, int], input_data: bytes, cell_bits: int):
		self.program = program
		self.brackets = brackets
		self.input_data = input_data
		self.ip = 0
		self.pointer = 0
		self.tape = bytearray([0])
		self.input_pos = 0
		self.output = bytearray()
		self.steps = 0
		self.modulus = 1 << cell_bits

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
			self.tape[self.pointer] = (self.tape[self.pointer] + 1) % self.modulus
		elif command == "-":
			self.tape[self.pointer] = (self.tape[self.pointer] - 1) % self.modulus
		elif command == ".":
			self.output.append(self.tape[self.pointer])
		elif command == ",":
			if self.input_pos < len(self.input_data):
				self.tape[self.pointer] = self.input_data[self.input_pos] % self.modulus
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
	limits: ExecutionLimits | None = None,
	cell_bits: int = 8,
) -> ExecutionResult:
	"""Execute with a finite budget and exact repeated-state detection.

	Syntax failures are results; invalid API configuration raises an exception.
	Trace callbacks receive immutable before/after snapshots per instruction.
	"""
	validate_max_steps(max_steps)
	validate_cell_bits(cell_bits)
	if limits is not None and not isinstance(limits, ExecutionLimits):
		raise TypeError("limits must be ExecutionLimits or None")
	if not isinstance(input_data, bytes):
		raise TypeError("input_data must be bytes")
	try:
		brackets = build_bracket_map(program)
	except ProgramSyntaxError as error:
		return ExecutionResult(program, Status.INVALID, State(), error=str(error))
	machine = _Machine(program, brackets, input_data, cell_bits)
	seen = {}
	state_bytes = 0
	# Without brackets the instruction pointer strictly increases: no cycle is possible.
	track_states = bool(brackets)
	deadline = monotonic() + limits.max_seconds if limits is not None and limits.max_seconds is not None else None

	def finish(status, **details):
		return ExecutionResult(program, status, machine.snapshot(), seen_states=len(seen), state_bytes=state_bytes, **details)

	while machine.ip < len(program) and machine.steps < max_steps:
		if deadline is not None and monotonic() >= deadline:
			return finish(Status.RESOURCE_LIMIT, resource_reason="wall_time")
		key = machine.control_key() if track_states else None
		if track_states and key in seen:
			return finish(Status.CYCLE, cycle_start=seen[key], cycle_period=machine.steps - seen[key])
		command = program[machine.ip]
		if limits is not None:
			reason = None
			if command == ">" and machine.pointer + 1 == len(machine.tape) and len(machine.tape) >= limits.max_tape_cells:
				reason = "tape_cells"
			elif command == "." and len(machine.output) >= limits.max_output_bytes:
				reason = "output_bytes"
			elif track_states and len(seen) >= limits.max_seen_states:
				reason = "seen_states"
			elif track_states and state_bytes + len(machine.tape) > limits.max_state_bytes:
				reason = "state_bytes"
			if reason is not None:
				return finish(Status.RESOURCE_LIMIT, resource_reason=reason)
		if track_states:
			seen[key] = machine.steps
			state_bytes += len(machine.tape)
		before = machine.snapshot() if trace is not None else None
		machine.step()
		if trace is not None:
			trace(TraceStep(command, before, machine.snapshot()))
	status = Status.HALTED if machine.ip >= len(program) else Status.STEP_LIMIT
	return finish(status)
