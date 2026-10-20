"""Streaming experiments with explicit coverage and bounded retained state."""

from dataclasses import replace
from time import monotonic

from . import SEMANTICS_ID, __version__
from .analysis import StreamingSummary
from .config import BaselineConfig, ExperimentConfig, semantics_id
from .enumeration import enumerate_programs, length_four_programs, valid_program_count
from .interpreter import run_program


def run_baseline(config: BaselineConfig):
	return [run_program(program, config.max_steps) for program in length_four_programs()]


def estimate_search(config: ExperimentConfig) -> dict:
	"""Combinatorial ceilings only; does not execute any Brainfuck program."""
	lengths = []
	for length in config.lengths:
		total = 8 ** length
		valid = valid_program_count(length)
		planned = min(total, config.max_programs_per_length) if config.max_programs_per_length is not None else total
		lengths.append({
			"length": length,
			"total_candidates": total,
			"valid_candidates_total": valid,
			"candidate_budget": planned,
			"instruction_budget_upper_bound": min(valid, planned) * config.max_steps,
		})
	return {"kind": "combinatorial_ceiling_not_runtime_forecast", "config": config.to_dict(), "lengths": lengths}


def run_experiment(config: ExperimentConfig, *, on_result=None) -> dict:
	"""Enumerate each requested length in order, retaining no per-program list.

	on_result may stream records to disk. Its cost is included in elapsed time.
	The cooperative global deadline is propagated into individual executions.
	"""
	started = monotonic()
	deadline = started + config.max_seconds
	summaries = []
	for length in config.lengths:
		length_started = monotonic()
		accumulator = StreamingSummary(length, config.max_distinct_outcomes, config.max_outcome_bytes)
		total = 8 ** length
		stop_reason = "completed"
		for program in enumerate_programs(length):
			if config.max_programs_per_length is not None and accumulator.evaluated >= config.max_programs_per_length:
				stop_reason = "candidate_limit"
				break
			remaining = deadline - monotonic()
			if remaining <= 0:
				stop_reason = "experiment_time_limit"
				break
			seconds = min(remaining, config.limits.max_seconds) if config.limits.max_seconds is not None else remaining
			limits = replace(config.limits, max_seconds=seconds)
			result = run_program(program, config.max_steps, limits=limits, cell_bits=config.cell_bits)
			storage_stop = accumulator.observe(result)
			if on_result is not None:
				on_result(result)
			if storage_stop:
				stop_reason = storage_stop
				break
		elapsed = monotonic() - length_started
		summary = accumulator.report()
		evaluated = accumulator.evaluated
		complete = evaluated == total
		fully_resolved = complete and summary["metrics"]["U"] == 0
		summaries.append({
			"length": length,
			"coverage": {
				"total_candidates": total,
				"evaluated_candidates": evaluated,
				"not_evaluated_candidates": total - evaluated,
				"exhaustive": complete,
				"fully_resolved": fully_resolved,
				"stop_reason": stop_reason,
			},
			"bounds": "complete_finite_model_results" if fully_resolved else "observed_lower_bounds",
			"elapsed_seconds": elapsed,
			**summary,
		})
	return {
		"schema_version": 2,
		"engine_version": __version__,
		"semantics_id": semantics_id(config.cell_bits),
		"enumeration": "alphabet_order_prefix",
		"input_bytes": [],
		"config": config.to_dict(),
		"elapsed_seconds": monotonic() - started,
		"lengths": summaries,
	}
