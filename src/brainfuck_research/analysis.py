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


class StreamingSummary:
	"""Retain bounded distinct keys and one witness per record, not all results.

	If the next new key cannot be retained, count it and require the caller to
	stop immediately. D then remains exact for the evaluated prefix.
	"""

	def __init__(self, length, max_distinct_outcomes, max_outcome_bytes):
		self.length = length
		self.max_distinct_outcomes = max_distinct_outcomes
		self.max_outcome_bytes = max_outcome_bytes
		self.counts = Counter()
		self.resource_reasons = Counter()
		self.outcomes = set()
		self.outcome_bytes = 0
		self.unretained_distinct = 0
		self.stopped = False
		self.records = {name: {"value": None, "program": None, "ties": 0} for name in ("T", "O", "M")}
		self.total_steps = 0
		self.peak_seen_states = 0
		self.peak_state_bytes = 0

	@property
	def evaluated(self):
		return sum(self.counts.values())

	def observe(self, result: ExecutionResult) -> str | None:
		if self.stopped:
			raise RuntimeError("Cannot continue after an outcome-storage stop")
		if len(result.program) != self.length:
			raise ValueError("Program length does not match this summary")
		self.counts[result.status] += 1
		self.total_steps += result.state.steps
		self.peak_seen_states = max(self.peak_seen_states, result.seen_states)
		self.peak_state_bytes = max(self.peak_state_bytes, result.state_bytes)
		if result.status == Status.RESOURCE_LIMIT:
			self.resource_reasons[result.resource_reason] += 1
		if result.status != Status.HALTED:
			return None
		state = result.state
		for name, value in (("T", state.steps), ("O", len(state.output)), ("M", len(state.tape))):
			record = self.records[name]
			if record["value"] is None or value > record["value"]:
				self.records[name] = {"value": value, "program": result.program, "ties": 1}
			elif value == record["value"]:
				record["ties"] += 1
		# Compact byte tape preserves equality of the historical tuple tape.
		key = (state.output, state.pointer, bytes(state.tape))
		if key in self.outcomes:
			return None
		payload_size = len(state.output) + len(state.tape)
		reason = None
		if len(self.outcomes) >= self.max_distinct_outcomes:
			reason = "distinct_outcome_limit"
		elif self.outcome_bytes + payload_size > self.max_outcome_bytes:
			reason = "outcome_bytes_limit"
		if reason:
			self.unretained_distinct = 1
			self.stopped = True
			return reason
		self.outcomes.add(key)
		self.outcome_bytes += payload_size
		return None

	def report(self):
		counts = {status.value: self.counts[status] for status in Status}
		distinct = len(self.outcomes) + self.unretained_distinct
		metrics = {name: record["value"] for name, record in self.records.items()}
		metrics.update(D=distinct, U=self.counts[Status.STEP_LIMIT] + self.counts[Status.RESOURCE_LIMIT])
		return {
			"counts": counts,
			"metrics": metrics,
			"records": {name: dict(record) for name, record in self.records.items()},
			"maximum_steps_per_command": metrics["T"] / self.length if metrics["T"] is not None else None,
			"maximum_output_bytes_per_command": metrics["O"] / self.length if metrics["O"] is not None else None,
			"duplicate_halted_programs": self.counts[Status.HALTED] - distinct,
			"executed_steps_all_programs": self.total_steps,
			"resource_reasons": dict(self.resource_reasons),
			"retained_outcomes": len(self.outcomes),
			"retained_outcome_bytes": self.outcome_bytes,
			"unretained_final_distinct_outcome": bool(self.unretained_distinct),
			"peak_seen_states_per_program": self.peak_seen_states,
			"peak_state_bytes_per_program": self.peak_state_bytes,
		}
