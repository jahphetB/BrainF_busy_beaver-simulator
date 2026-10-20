"""Immutable execution records for tests and future browser fixtures."""

from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
	HALTED = "halted"
	CYCLE = "cycle_detected"
	STEP_LIMIT = "step_limit"
	INVALID = "syntactically_invalid"


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
