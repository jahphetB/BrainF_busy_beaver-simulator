"""Dependency-free baseline and trace commands."""

import argparse
import json

from .config import BaselineConfig
from .experiments import run_baseline
from .export import baseline_report, result_record
from .interpreter import run_program
from .models import Status, TraceStep


def print_trace_step(event: TraceStep) -> None:
	print(f"Step {event.after.steps}: {event.command} at ip={event.before.ip}")
	print(f"  Before: pointer={event.before.pointer} tape={list(event.before.tape)} output={event.before.output!r}")
	print(f"  After: ip={event.after.ip} pointer={event.after.pointer} tape={list(event.after.tape)} output={event.after.output!r}")


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(description="Validated Brainfuck length-four research baseline")
	parser.add_argument("--max-steps", type=int, default=100)
	parser.add_argument("--json", action="store_true", help="Print a machine-readable baseline summary")
	parser.add_argument("--trace", metavar="PROGRAM", help="Trace one command-only program instead of enumeration")
	parser.add_argument("--input-hex", default=None, help="Input bytes for --trace, e.g. 00ff41")
	args = parser.parse_args(argv)
	try:
		config = BaselineConfig(args.max_steps)
		input_data = bytes.fromhex(args.input_hex) if args.input_hex is not None else b""
	except ValueError as error:
		parser.error(str(error))
	if args.trace is None and args.input_hex is not None:
		parser.error("--input-hex requires --trace; baseline input is always empty")
	if args.trace is not None:
		if args.json:
			parser.error("--json is for baseline summaries; omit it when tracing")
		result = run_program(args.trace, config.max_steps, input_data, trace=print_trace_step)
		print(json.dumps(result_record(result), indent="\t"))
		return 2 if result.status == Status.INVALID else 0
	report = baseline_report(config, run_baseline(config))
	if args.json:
		print(json.dumps(report, indent="\t"))
	else:
		summary = report["summary"]
		print(f"BRAINFUCK LENGTH-4 BASELINE | max_steps={config.max_steps} | {report['semantics_id']}")
		for key in ("total_programs", "valid_programs", "invalid_programs"):
			print(f"{key}: {summary[key]}")
		for status, count in summary["counts"].items():
			print(f"{status}: {count}")
		for key in ("distinct_halted_outcomes", "duplicate_halted_programs", "minimum_observed_halting_steps", "maximum_observed_halting_steps"):
			print(f"{key}: {summary[key]}")
		witnesses = summary["maximum_step_programs"]
		print(f"Maximum-step witnesses ({len(witnesses)} total, first 10): {witnesses[:10]}")
		print(f"Cycle-detected programs: {summary['cycle_programs']}")
		print(f"Unresolved programs: {summary['unresolved_programs']}")
		print("Step limits are unresolved, not evidence of nontermination. See docs/SEMANTICS.md.")
	return 0
