"""Bounded experiment commands; legacy baseline commands remain separate."""

from contextlib import ExitStack
import argparse
import json
from pathlib import Path

from .config import ExperimentConfig
from .experiments import estimate_search, run_experiment
from .export import result_record


def main(argv=None):
	parser = argparse.ArgumentParser(description="Bounded exhaustive Brainfuck enumeration, lengths 1-7")
	parser.add_argument("--config", type=Path, help="JSON configuration; cannot be combined with budget flags")
	parser.add_argument("--lengths", type=int, nargs="+")
	parser.add_argument("--max-steps", type=int)
	coverage = parser.add_mutually_exclusive_group()
	coverage.add_argument("--max-programs", type=int, help="Candidate budget per length; default 10000")
	coverage.add_argument("--exhaustive", action="store_true", help="Remove candidate cap; other limits still apply")
	parser.add_argument("--max-seconds", type=float, help="Total cooperative time budget; default 30 seconds")
	parser.add_argument("--max-tape-cells", type=int)
	parser.add_argument("--max-output-bytes", type=int)
	parser.add_argument("--max-seen-states", type=int)
	parser.add_argument("--max-state-bytes", type=int)
	parser.add_argument("--program-seconds", type=float)
	parser.add_argument("--max-distinct-outcomes", type=int)
	parser.add_argument("--max-outcome-bytes", type=int)
	parser.add_argument("--json", action="store_true", help="Print the full JSON summary")
	parser.add_argument("--estimate", action="store_true", help="Print search-space/instruction ceilings without executing programs")
	parser.add_argument("--report", type=Path, help="Save JSON summary (new file only)")
	parser.add_argument("--records", type=Path, help="Stream all evaluated records to JSONL (new file only)")
	args = parser.parse_args(argv)
	try:
		values = {}
		for name in ("lengths", "max_steps", "max_seconds", "max_distinct_outcomes", "max_outcome_bytes"):
			if getattr(args, name) is not None:
				values[name] = getattr(args, name)
		if args.max_programs is not None:
			values["max_programs_per_length"] = args.max_programs
		if args.exhaustive:
			values["max_programs_per_length"] = None
		limits = {name: getattr(args, name) for name in ("max_tape_cells", "max_output_bytes", "max_seen_states", "max_state_bytes") if getattr(args, name) is not None}
		if args.program_seconds is not None:
			limits["max_seconds"] = args.program_seconds
		if limits:
			values["limits"] = limits
		if args.config:
			if values:
				parser.error("--config cannot be combined with length or budget flags")
			values = json.loads(args.config.read_text(encoding="utf-8"))
		config = ExperimentConfig.from_dict(values)
		if args.estimate:
			if args.report or args.records:
				parser.error("--estimate does not write experiment outputs")
			print(json.dumps(estimate_search(config), indent="\t"))
			return 0
		if args.report and args.records and args.report.resolve() == args.records.resolve():
			parser.error("--report and --records must be different files")
		for path in (args.report, args.records):
			if path is not None and path.exists():
				parser.error(f"Output already exists: {path}")
		with ExitStack() as stack:
			report_file = stack.enter_context(args.report.open("x", encoding="utf-8", newline="\n")) if args.report else None
			records_file = stack.enter_context(args.records.open("x", encoding="utf-8", newline="\n")) if args.records else None
			def write_record(result):
				records_file.write(json.dumps(result_record(result), separators=(",", ":")) + "\n")
			report = run_experiment(config, on_result=write_record if records_file else None)
			encoded = json.dumps(report, indent="\t")
			if report_file:
				report_file.write(encoded + "\n")
	except (ValueError, TypeError, OSError) as error:
		parser.error(str(error))
	if args.json:
		print(encoded)
	else:
		print(f"Brainfuck experiment | {report['semantics_id']} | {report['elapsed_seconds']:.3f}s")
		for summary in report["lengths"]:
			coverage = summary["coverage"]
			print(f"n={summary['length']}: {coverage['evaluated_candidates']}/{coverage['total_candidates']} candidates; {coverage['stop_reason']}")
			print(f"  T/O/M/D/U: {summary['metrics']} | {summary['bounds']}")
		print("U counts evaluated but unresolved programs; unevaluated candidates are reported separately.")
	return 0
