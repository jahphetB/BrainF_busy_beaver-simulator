"""Validated, explicit execution and experiment budgets."""

from dataclasses import asdict, dataclass, field
from math import isfinite


def validate_integer(name, value, minimum=0, maximum=None):
	if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
		raise ValueError(f"{name} must be an integer >= {minimum}")
	if maximum is not None and value > maximum:
		raise ValueError(f"{name} must be <= {maximum}")


def validate_seconds(name, value):
	if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0):
		raise ValueError(f"{name} must be a finite positive number or null")


@dataclass(frozen=True)
class ExecutionLimits:
	max_tape_cells: int = 4096
	max_output_bytes: int = 65536
	max_seen_states: int = 100000
	max_state_bytes: int = 16 * 1024 * 1024
	max_seconds: float | None = None

	def __post_init__(self):
		validate_integer("max_tape_cells", self.max_tape_cells, 1)
		for name in ("max_output_bytes", "max_seen_states", "max_state_bytes"):
			validate_integer(name, getattr(self, name))
		validate_seconds("max_seconds", self.max_seconds)


@dataclass(frozen=True)
class BaselineConfig:
	max_steps: int = 100

	def __post_init__(self):
		validate_integer("max_steps", self.max_steps)


@dataclass(frozen=True)
class ExperimentConfig:
	lengths: tuple[int, ...] = (1, 2, 3, 4)
	cell_bits: int = 8
	max_steps: int = 512
	max_programs_per_length: int | None = 10000
	max_seconds: float = 30.0
	max_distinct_outcomes: int = 100000
	max_outcome_bytes: int = 16 * 1024 * 1024
	limits: ExecutionLimits = field(default_factory=ExecutionLimits)

	def __post_init__(self):
		validate_cell_bits(self.cell_bits)
		if not isinstance(self.lengths, tuple) or not self.lengths:
			raise ValueError("lengths must be a nonempty tuple")
		for length in self.lengths:
			validate_integer("length", length, 1, 7)
		if tuple(sorted(set(self.lengths))) != self.lengths:
			raise ValueError("lengths must be unique and increasing")
		validate_integer("max_steps", self.max_steps)
		if self.max_programs_per_length is not None:
			validate_integer("max_programs_per_length", self.max_programs_per_length, 1)
		validate_seconds("max_seconds", self.max_seconds)
		if self.max_seconds is None:
			raise ValueError("Experiments require a finite time budget")
		for name in ("max_distinct_outcomes", "max_outcome_bytes"):
			validate_integer(name, getattr(self, name))
		if not isinstance(self.limits, ExecutionLimits):
			raise TypeError("limits must be ExecutionLimits")

	def to_dict(self):
		return {**asdict(self), "lengths": list(self.lengths)}

	@classmethod
	def from_dict(cls, values):
		values = dict(values)
		if "lengths" in values:
			values["lengths"] = tuple(values["lengths"])
		if "limits" in values:
			values["limits"] = ExecutionLimits(**values["limits"])
		return cls(**values)


def validate_cell_bits(cell_bits):
	validate_integer("cell_bits", cell_bits, 1)
	if cell_bits not in (4, 8):
		raise ValueError("Supported cell widths are 4 and 8 bits")


def semantics_id(cell_bits=8):
	validate_cell_bits(cell_bits)
	return "legacy-u8-right-v1" if cell_bits == 8 else "u4-right-v1"
