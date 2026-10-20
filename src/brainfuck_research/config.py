"""Phase 1 exposes only the validated length-four experiment."""

from dataclasses import dataclass

from .interpreter import validate_max_steps


@dataclass(frozen=True)
class BaselineConfig:
	max_steps: int = 100

	def __post_init__(self):
		validate_max_steps(self.max_steps)
