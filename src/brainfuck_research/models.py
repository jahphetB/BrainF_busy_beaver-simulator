"""Immutable execution records for tests and future browser fixtures."""

from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
	HALTED = "halted"
	CYCLE = "cycle_detected"
	STEP_LIMIT = "step_limit"
	INVALID = "syntactically_invalid"
	RESOURCE_LIMIT = "resource_limit"


@dataclass(frozen=True)
class State:
	ip: int = 0
	pointer: int = 0
	tape: tuple[int, ...] = (0,)
	input_pos: int = 0
	output: bytes = b""
	steps: int = 0


@dataclass(frozen=True)
class TraceStep:
	command: str
	before: State
	after: State


@dataclass(frozen=True)
class ExecutionResult:
	program: str
	status: Status
	state: State
	cycle_start: int | None = None
	cycle_period: int | None = None
	error: str | None = None
	resource_reason: str | None = None
	seen_states: int = 0
	state_bytes: int = 0

	@property
	def metrics(self) -> dict:
		length = len(self.program)
		if self.status == Status.INVALID:
			return {}
		return {
			"program_length": length,
			"executed_steps": self.state.steps,
			"output_bytes": len(self.state.output),
			"cells_visited": len(self.state.tape),
			"final_nonzero_cells": sum(value != 0 for value in self.state.tape),
			"steps_per_command": self.state.steps / length if length else None,
			"output_bytes_per_command": len(self.state.output) / length if length else None,
		}
