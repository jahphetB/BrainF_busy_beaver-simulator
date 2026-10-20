"""Baseline runner; broader orchestration belongs to Phase 2."""

from .config import BaselineConfig
from .enumeration import length_four_programs
from .interpreter import run_program


def run_baseline(config: BaselineConfig):
	return [run_program(program, config.max_steps) for program in length_four_programs()]
