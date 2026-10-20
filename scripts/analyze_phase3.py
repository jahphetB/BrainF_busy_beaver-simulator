"""Verify saved Phase 3 runs and derive reproducible tables and proof evidence."""

import argparse
from collections import Counter
from contextlib import ExitStack, redirect_stdout
import csv
import hashlib
import io
from itertools import zip_longest
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brainfuck_research.config import ExperimentConfig
from brainfuck_research.datasets import compressed_writer, decode_result, read_records, sha256_file, summary_rows, verify_dataset, write_json
from brainfuck_research.export import result_record
from brainfuck_research.interpreter import run_program
from brainfuck_research.models import Status

RUNS = ("primary-n1-5-s512", "primary-n6-s512", "steps4096-n4-6", "cell4-n4-6-s4096")


def control_state(state):
	return {"ip": state.ip, "pointer": state.pointer, "tape": list(state.tape), "input_pos": state.input_pos}


def cycle_certificate(record, config):
	if record["status"] != Status.CYCLE.value:
		raise ValueError("A cycle certificate requires a cycle-detected record")
	start_state = None
	def capture(event):
		nonlocal start_state
		if event.before.steps == record["cycle_start"]:
			start_state = event.before
	result = run_program(record["program"], config.max_steps, cell_bits=config.cell_bits, limits=config.limits, trace=capture)
	if result_record(result) != record or start_state is None:
		raise AssertionError("Cycle replay differs from dataset")
	if control_state(start_state) != control_state(result.state) or result.state.steps - start_state.steps != result.cycle_period:
		raise AssertionError("Repeated-state certificate failed")
	return {
		"program": result.program, "cell_bits": config.cell_bits,
		"first_seen_step": start_state.steps, "repeated_at_step": result.state.steps,
		"period": result.cycle_period, "equal_control_state": control_state(start_state),
		"output_bytes_during_cycle": list(result.state.output[len(start_state.output):]),
	}


def fresh_cell_growth_proof(program, cell_bits):
	"""A deliberately narrow, explicit proof family, not a heuristic detector."""
	if cell_bits not in (4, 8) or program not in ("+[>+]", "+[>-]", "-[>+]", "-[>-]"):
		return None
	return {
		"program": program, "cell_bits": cell_bits,
		"classification": "proven_nonterminating_by_fresh_cell_invariant",
		"argument": "The initial +/- makes cell zero nonzero. Each iteration moves right to a fresh zero cell and changes it by +/-1 modulo 2^b. That cell is nonzero for b=4 or 8, so ] always jumps back to >. By induction the pointer strictly increases and execution never exits the loop on the right-unbounded tape. A resource stop does not change this model-level argument.",
	}


def analyze(runs_root, output):
	output = Path(output)
	output.mkdir(parents=True, exist_ok=False)
	runs_root = Path(runs_root)
	with redirect_stdout(io.StringIO()):
		legacy = runpy.run_path(str(ROOT / "data/historical/original_generate.py"))
	verifications, witnesses, combined, transitions, unresolved, proofs = {}, [], [], [], {}, []
	pairs = Counter()
	cycle_counts = Counter()
	input_hashes = {}
	with ExitStack() as stack:
		certificates = compressed_writer(stack, output / "cycle-certificates.jsonl.gz")
		for name in RUNS:
			directory = runs_root / name
			verifications[name] = verify_dataset(directory)
			input_hashes[name] = sha256_file(directory / "manifest.json")
			report = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
			config = ExperimentConfig.from_dict(report["config"])
			selected = {}
			for summary in report["lengths"]:
				for metric, record in summary["records"].items():
					if record["program"] is not None:
						selected.setdefault(record["program"], []).append(metric)
			combined.extend({"run": name, **row} for row in summary_rows(report))
			unresolved[name] = []
			for record in read_records(directory):
				length = len(record["program"])
				if record["status"] == Status.HALTED:
					pairs[(name, length, record["steps"], record["metrics"]["output_bytes"])] += 1
				if record["program"] in selected:
					replayed = run_program(record["program"], config.max_steps, limits=config.limits, cell_bits=config.cell_bits)
					if result_record(replayed) != record:
						raise AssertionError("Maximum witness replay failed")
					legacy_agrees = None
					if config.cell_bits == 8:
						old = legacy["run_program"](record["program"], record["steps"])
						legacy_agrees = old == (record["status"], record["steps"], bytes(record["output_bytes"]).decode("latin-1"), record["pointer"], record["tape"])
						if not legacy_agrees:
							raise AssertionError("Archived interpreter disagrees with maximum witness")
					witnesses.append({"run": name, "metrics": selected[record["program"]], "independent_legacy_agreement": legacy_agrees, "record": record})
				if record["status"] == Status.CYCLE:
					certificate = cycle_certificate(record, config)
					certificates.write(json.dumps({"run": name, **certificate}, separators=(",", ":")) + "\n")
					cycle_counts[name] += 1
				if record["status"] in (Status.STEP_LIMIT, Status.RESOURCE_LIMIT):
					unresolved[name].append(record)
					proof = fresh_cell_growth_proof(record["program"], config.cell_bits)
					if proof:
						proofs.append({"run": name, **proof})
			for summary in report["lengths"]:
				count = sum(count for (run, length, _, _), count in pairs.items() if run == name and length == summary["length"])
				if count != summary["counts"]["halted"]:
					raise AssertionError("Runtime/output distribution accounting mismatch")
			if cycle_counts[name] != sum(s["counts"]["cycle_detected"] for s in report["lengths"]):
				raise AssertionError("Cycle certificate coverage mismatch")
	low_unresolved = {r["program"]: r for name in RUNS[:2] for r in unresolved[name]}
	transition_counts = Counter()
	for record in read_records(runs_root / "steps4096-n4-6"):
		if record["program"] in low_unresolved:
			transition_counts[(len(record["program"]), record["status"])] += 1
			transitions.append({"program": record["program"], "from_status": low_unresolved[record["program"]]["status"], "to_status": record["status"], "steps_at_higher_limit": record["steps"]})
	if len(transitions) != len(low_unresolved):
		raise AssertionError("Not every lower-limit unresolved case was followed up")
	cell_transitions = Counter()
	changed_halted_steps = Counter()
	for eight, four in zip_longest(read_records(runs_root / "steps4096-n4-6"), read_records(runs_root / "cell4-n4-6-s4096")):
		if eight is None or four is None or eight["program"] != four["program"]:
			raise AssertionError("Cell-width comparison requires matched complete coverage")
		length = len(eight["program"])
		cell_transitions[(length, eight["status"], four["status"])] += 1
		if eight["status"] == four["status"] == Status.HALTED and eight["steps"] != four["steps"]:
			changed_halted_steps[length] += 1
	write_json(output / "verification.json", {"dataset_checks": verifications, "cycle_certificates_by_run": dict(cycle_counts), "maximum_witness_replays": len(witnesses), "independent_legacy_witness_replays": sum(w["independent_legacy_agreement"] is True for w in witnesses)})
	write_json(output / "summary.json", combined)
	with (output / "summary.csv").open("x", encoding="utf-8", newline="") as destination:
		writer = csv.DictWriter(destination, fieldnames=list(combined[0]), lineterminator="\n")
		writer.writeheader()
		writer.writerows(combined)
	with (output / "runtime-output.csv").open("x", encoding="utf-8", newline="") as destination:
		writer = csv.writer(destination, lineterminator="\n")
		writer.writerow(["run", "length", "steps", "output_bytes", "halted_programs"])
		writer.writerows((*key, count) for key, count in sorted(pairs.items()))
	write_json(output / "witnesses.json", witnesses)
	# Keep unresolved states compressed: growing tapes can be large.
	with ExitStack() as stack:
		destination = compressed_writer(stack, output / "unresolved.json.gz")
		json.dump(unresolved, destination, separators=(",", ":"))
	write_json(output / "sensitivity.json", {
		"step_limit_transitions": [{"length": length, "new_status": status, "count": count} for (length, status), count in sorted(transition_counts.items())],
		"step_limit_programs": transitions,
		"cell_width_transitions": [{"length": length, "eight_bit_status": eight, "four_bit_status": four, "count": count} for (length, eight, four), count in sorted(cell_transitions.items())],
		"halted_in_both_models_with_changed_steps": dict(changed_halted_steps),
	})
	write_json(output / "structural-proofs.json", {"note": "Supplemental proofs do not overwrite saved runner classifications or raw U counts.", "proofs": proofs})
	write_json(output / "manifest.json", {
		"analysis_schema_version": 1, "input_manifests_sha256": input_hashes,
		"analysis_script_sha256_lf": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
		"artifacts": {path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size} for path in sorted(output.iterdir()) if path.is_file()},
	})
	return {"records_verified": sum(v["records_checked"] for v in verifications.values()), "cycle_certificates": sum(cycle_counts.values()), "witnesses": len(witnesses), "step_limit_transitions": dict((str(k), v) for k, v in transition_counts.items())}


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--runs", type=Path, default=ROOT / "data/runs/v1")
	parser.add_argument("--output", type=Path, required=True)
	args = parser.parse_args()
	print(json.dumps(analyze(args.runs, args.output), indent="\t"))
