"""Bounded reproducible pilot; does not exhaustively search lengths 5-7."""

import argparse
import contextlib
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import random
import runpy
from statistics import median
import subprocess
import sys
from time import perf_counter
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brainfuck_research import SEMANTICS_ID, __version__
from brainfuck_research.analysis import StreamingSummary
from brainfuck_research.config import BaselineConfig, ExecutionLimits, ExperimentConfig
from brainfuck_research.enumeration import program_at_index, valid_program_count
from brainfuck_research.experiments import run_baseline, run_experiment
from brainfuck_research.interpreter import run_program


def sample_ranks(length, count, seed):
	total = 8 ** length
	return list(range(total)) if count >= total else sorted(random.Random(seed + length).sample(range(total), count))


def source_fingerprint():
	paths = [ROOT / "generate.py", ROOT / "pyproject.toml", Path(__file__).resolve(), *sorted((ROOT / "src").rglob("*.py"))]
	digest = hashlib.sha256()
	for path in paths:
		digest.update(path.relative_to(ROOT).as_posix().encode("utf-8") + b"\0")
		digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
	return digest.hexdigest()


def timed_samples(function, repeats):
	values = []
	for _ in range(repeats):
		started = perf_counter()
		function()
		values.append(perf_counter() - started)
	return {"seconds": values, "median_seconds": median(values)}


def peak_allocations(function):
	tracemalloc.start()
	try:
		result = function()
		_, peak = tracemalloc.get_traced_memory()
		return peak
	finally:
		tracemalloc.stop()


def benchmark(sample_count=2048, repeats=3, seed=20261019):
	limits = ExecutionLimits(max_seen_states=10000, max_state_bytes=4 * 1024 * 1024)
	with contextlib.redirect_stdout(io.StringIO()):
		legacy = runpy.run_path(str(ROOT / "data/historical/original_generate.py"))
	programs = legacy["valid_programs"]
	legacy_timing = timed_samples(lambda: [legacy["run_program"](p, 512) for p in programs], repeats)
	current_timing = timed_samples(lambda: [run_program(p, 512, limits=limits) for p in programs], repeats)
	pilots = []
	for length in range(1, 8):
		ranks = sample_ranks(length, sample_count, seed)
		sources = [program_at_index(length, rank) for rank in ranks]
		elapsed = []
		first_summary = None
		for _ in range(repeats):
			started = perf_counter()
			deadline = started + 30
			accumulator = StreamingSummary(length, sample_count, 16 * 1024 * 1024)
			for program in sources:
				remaining = deadline - perf_counter()
				if remaining <= 0:
					raise TimeoutError("Pilot exceeded its 30-second repetition budget")
				result = run_program(program, 512, limits=replace(limits, max_seconds=min(remaining, 1)))
				if result.resource_reason == "wall_time":
					raise TimeoutError("Pilot program exceeded its cooperative time budget")
				if accumulator.observe(result) is not None:
					raise RuntimeError("Pilot exhausted outcome storage")
			elapsed.append(perf_counter() - started)
			summary = accumulator.report()
			if first_summary is not None and summary != first_summary:
				raise AssertionError("Repeated pilot produced inconsistent results")
			first_summary = summary
		factor = 8 ** length / len(sources)
		pilots.append({
			"length": length,
			"candidate_count": len(sources),
			"total_candidates": 8 ** length,
			"valid_candidates_total": valid_program_count(length),
			"exhaustive": len(sources) == 8 ** length,
			"ranks_sha256": hashlib.sha256(json.dumps(ranks, separators=(",", ":")).encode("ascii")).hexdigest(),
			"seconds": elapsed,
			"median_seconds": median(elapsed),
			"linear_full_search_seconds": median(elapsed) * factor,
			"linear_full_search_seconds_from_fastest_repeat": min(elapsed) * factor,
			"linear_full_search_seconds_from_slowest_repeat": max(elapsed) * factor,
			"summary_for_sample_only": first_summary,
		})
	config = ExperimentConfig(lengths=(4,), max_steps=512)
	stream_timing = timed_samples(lambda: run_experiment(config), repeats)
	baseline_peak = peak_allocations(lambda: run_baseline(BaselineConfig(512)))
	stream_peak = peak_allocations(lambda: run_experiment(config))
	return {
		"schema_version": 1,
		"purpose": "Phase 2 engineering benchmark and feasibility pilot, not Phase 3 research dataset",
		"generated_at_utc": datetime.now(timezone.utc).isoformat(),
		"environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "processor_reported_by_os": platform.processor()},
		"engine_version": __version__,
		"semantics_id": SEMANTICS_ID,
		"git_head_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
		"working_tree_dirty_at_run": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
		"source_sha256": source_fingerprint(),
		"settings": {"seed": seed, "sample_count_cap": sample_count, "repeats": repeats, "max_steps": 512, "limits": asdict(limits), "pilot_program_seconds": 1, "pilot_repetition_seconds": 30},
		"legacy_comparison": {"length": 4, "valid_programs": len(programs), "legacy": legacy_timing, "current_bounded_core": current_timing, "median_speed_ratio_legacy_over_current": legacy_timing["median_seconds"] / current_timing["median_seconds"]},
		"pilots": pilots,
		"streaming_length_four": {"config": config.to_dict(), "timing": stream_timing},
		"memory": {"method": "Separate tracemalloc runs; peak traced Python allocations, not process RSS", "materialized_baseline_peak_bytes": baseline_peak, "streaming_peak_bytes": stream_peak},
		"limitations": [
			"Fixed-seed samples can miss rare long-running or high-output programs; projections are not guaranteed runtimes or confidence intervals.",
			"Projected times apply only to the 512-step budget and configured resource limits; longer budgets require new pilots.",
			"Pilot timings include execution, time-limit configuration, and summary aggregation, but exclude sample construction and file export.",
			"Record maxima and D for incomplete pilots describe only the sample, not the full length-n search space.",
			"Timing varies with host load; working-tree fingerprint identifies the benchmark source even before its commit.",
		],
	}


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--output", type=Path, required=True)
	parser.add_argument("--samples-per-length", type=int, default=2048)
	parser.add_argument("--repeats", type=int, default=3)
	args = parser.parse_args()
	if not 1 <= args.samples_per_length <= 8192 or not 1 <= args.repeats <= 5:
		parser.error("Use 1-8192 samples and 1-5 repeats for this bounded pilot")
	if args.output.exists():
		parser.error("Output already exists; choose a new benchmark filename")
	report = benchmark(args.samples_per_length, args.repeats)
	with args.output.open("x", encoding="utf-8", newline="\n") as output:
		output.write(json.dumps(report, indent="\t") + "\n")
	print(f"Saved benchmark: {args.output}")
	for pilot in report["pilots"]:
		print(f"n={pilot['length']}: sampled {pilot['candidate_count']}/{pilot['total_candidates']}; median {pilot['median_seconds']:.4f}s; linear projection {pilot['linear_full_search_seconds']:.2f}s")
