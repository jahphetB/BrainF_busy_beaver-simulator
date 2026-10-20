"""Outcome equivalence and descriptive statistics, without KC estimates."""

from collections import Counter
from math import log2

from .models import ExecutionResult, Status


def outcome_key(result: ExecutionResult) -> tuple[bytes, int, tuple[int, ...]]:
	if result.status != Status.HALTED:
		raise ValueError("Only halted executions have halted outcome keys")
	state = result.state
	return state.output, state.pointer, state.tape


def group_halted_outcomes(results):
	groups = {}
	for result in results:
		if result.status == Status.HALTED:
			groups.setdefault(outcome_key(result), []).append(result)
	return groups


def empirical_surprisal(group_size: int, halted_count: int) -> float:
	"""Conditional finite-sample surprisal; not Kolmogorov complexity."""
	if not 0 < group_size <= halted_count:
		raise ValueError("Expected 0 < group_size <= halted_count")
	return -log2(group_size / halted_count)


def summarize(results) -> dict:
	results = list(results)
	counts = Counter(result.status for result in results)
	halted = [result for result in results if result.status == Status.HALTED]
	groups = group_halted_outcomes(results)
	maximum = max((result.state.steps for result in halted), default=None)
	minimum = min((result.state.steps for result in halted), default=None)
	return {
		"total_programs": len(results),
		"valid_programs": len(results) - counts[Status.INVALID],
		"invalid_programs": counts[Status.INVALID],
		"counts": {status.value: counts[status] for status in Status},
		"distinct_halted_outcomes": len(groups),
		"duplicate_halted_programs": len(halted) - len(groups),
		"minimum_observed_halting_steps": minimum,
		"maximum_observed_halting_steps": maximum,
		"maximum_step_programs": [r.program for r in halted if r.state.steps == maximum],
		"cycle_programs": [r.program for r in results if r.status == Status.CYCLE],
		"unresolved_programs": [r.program for r in results if r.status == Status.STEP_LIMIT],
	}
