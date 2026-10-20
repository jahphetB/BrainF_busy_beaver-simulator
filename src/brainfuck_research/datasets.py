"""Versioned compressed datasets, provenance, and independent export accounting."""

from contextlib import ExitStack
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys

from . import __version__
from .analysis import StreamingSummary
from .config import ExperimentConfig, semantics_id
from .enumeration import program_at_index, valid_program_count
from .experiments import run_experiment
from .export import result_record
from .models import ExecutionResult, State, Status

ROOT = Path(__file__).resolve().parents[2]
CSV_FIELDS = ("program", "status", "steps", "output_byte_count", "cells_visited", "final_nonzero_cells", "steps_per_command", "output_bytes_per_command", "pointer", "ip", "input_pos", "output_hex", "tape_json", "cycle_start", "cycle_period", "resource_reason")
SUMMARY_FIELDS = ("length", "semantics_id", "max_steps", "evaluated", "not_evaluated", "exhaustive", "fully_resolved", "halted", "cycle_detected", "step_limit", "resource_limit", "syntactically_invalid", "T", "O", "M", "D", "U", "T_program", "O_program", "M_program", "elapsed_seconds")


def sha256_file(path):
	digest = hashlib.sha256()
	with Path(path).open("rb") as source:
		for block in iter(lambda: source.read(1024 * 1024), b""):
			digest.update(block)
	return digest.hexdigest()


def write_json(path, value):
	with Path(path).open("x", encoding="utf-8", newline="\n") as output:
		json.dump(value, output, indent="\t")
		output.write("\n")


def source_provenance():
	paths = [ROOT / "generate.py", ROOT / "pyproject.toml", *sorted((ROOT / "src").rglob("*.py"))]
	files = {}
	committed = True
	for path in paths:
		name = path.relative_to(ROOT).as_posix()
		content = path.read_bytes().replace(b"\r\n", b"\n")
		files[name] = hashlib.sha256(content).hexdigest()
		stored = subprocess.run(["git", "show", f"HEAD:{name}"], cwd=ROOT, capture_output=True)
		committed = committed and stored.returncode == 0 and stored.stdout.replace(b"\r\n", b"\n") == content
	return {
		"git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
		"engine_sources_match_commit": committed,
		"source_files_sha256_lf": files,
		"source_tree_sha256": hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
	}


def record_csv_row(record):
	metrics = record["metrics"]
	return {
		"program": record["program"], "status": record["status"], "steps": record["steps"],
		"output_byte_count": metrics.get("output_bytes"), "cells_visited": metrics.get("cells_visited"),
		"final_nonzero_cells": metrics.get("final_nonzero_cells"),
		"steps_per_command": metrics.get("steps_per_command"), "output_bytes_per_command": metrics.get("output_bytes_per_command"),
		"pointer": record["pointer"], "ip": record["ip"], "input_pos": record["input_pos"],
		"output_hex": bytes(record["output_bytes"]).hex(), "tape_json": json.dumps(record["tape"], separators=(",", ":")),
		"cycle_start": record["cycle_start"], "cycle_period": record["cycle_period"], "resource_reason": record["resource_reason"],
	}


def summary_rows(report):
	for item in report["lengths"]:
		coverage = item["coverage"]
		yield {
			"length": item["length"], "semantics_id": report["semantics_id"], "max_steps": report["config"]["max_steps"],
			"evaluated": coverage["evaluated_candidates"], "not_evaluated": coverage["not_evaluated_candidates"],
			"exhaustive": coverage["exhaustive"], "fully_resolved": coverage["fully_resolved"],
			**item["counts"], **item["metrics"],
			**{f"{name}_program": item["records"][name]["program"] for name in ("T", "O", "M")},
			"elapsed_seconds": item["elapsed_seconds"],
		}


def compressed_writer(stack, path):
	raw = stack.enter_context(path.open("xb"))
	compressed = stack.enter_context(gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6))
	return stack.enter_context(io.TextIOWrapper(compressed, encoding="utf-8", newline="\n"))


def create_dataset(config, destination):
	"""Create a new run directory; manifest is written last, only after success."""
	destination = Path(destination)
	provenance = source_provenance()
	destination.mkdir(parents=True, exist_ok=False)
	started = datetime.now(timezone.utc).isoformat()
	write_json(destination / "config.json", config.to_dict())
	with ExitStack() as stack:
		json_output = compressed_writer(stack, destination / "programs.jsonl.gz")
		csv_output = compressed_writer(stack, destination / "programs.csv.gz")
		writer = csv.DictWriter(csv_output, fieldnames=CSV_FIELDS, lineterminator="\n")
		writer.writeheader()
		def record(result):
			value = result_record(result)
			json_output.write(json.dumps(value, separators=(",", ":")) + "\n")
			writer.writerow(record_csv_row(value))
		report = run_experiment(config, on_result=record)
	write_json(destination / "summary.json", report)
	with (destination / "summary.csv").open("x", encoding="utf-8", newline="") as output:
		writer = csv.DictWriter(output, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
		writer.writeheader()
		writer.writerows(summary_rows(report))
	artifacts = ("config.json", "summary.json", "summary.csv", "programs.jsonl.gz", "programs.csv.gz")
	manifest = {
		"dataset_schema_version": 1, "dataset_version": "v1", "status": "completed",
		"started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
		"engine_version": __version__, "semantics_id": semantics_id(config.cell_bits),
		"environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "processor_reported_by_os": platform.processor()},
		"provenance": provenance,
		"classification_note": "Completed artifact creation does not imply exhaustive coverage or resolved programs; consult summary coverage and U.",
		"records": sum(item["coverage"]["evaluated_candidates"] for item in report["lengths"]),
		"artifacts": {name: {"sha256": sha256_file(destination / name), "bytes": (destination / name).stat().st_size} for name in artifacts},
		"reproduce": "python generate.py dataset run --config config.json --output NEW_DIRECTORY",
	}
	write_json(destination / "manifest.json", manifest)
	return report


def read_records(directory):
	with gzip.open(Path(directory) / "programs.jsonl.gz", "rt", encoding="utf-8") as source:
		for line in source:
			yield json.loads(line)


def decode_result(record):
	state = State(record["ip"], record["pointer"], tuple(record["tape"]), record["input_pos"], bytes(record["output_bytes"]), record["steps"])
	result = ExecutionResult(record["program"], Status(record["status"]), state, record["cycle_start"], record["cycle_period"], record["error"], record["resource_reason"], record["seen_states"], record["state_bytes"])
	if result_record(result) != record:
		raise ValueError("Record fields or derived metrics disagree")
	return result


def csv_strings(row):
	return {key: "" if value is None else str(value) for key, value in row.items()}


def verify_dataset(directory):
	"""Verify hashes, both record encodings, enumeration order and summary counts.

	This audits saved artifacts without re-executing every program. Witness
	replay and cycle certificates are handled separately by the study analysis.
	"""
	directory = Path(directory)
	manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
	if manifest["status"] != "completed" or manifest["dataset_schema_version"] != 1:
		raise ValueError("Dataset has no supported completion manifest")
	expected_names = {"config.json", "summary.json", "summary.csv", "programs.jsonl.gz", "programs.csv.gz"}
	if set(manifest["artifacts"]) != expected_names:
		raise ValueError("Unexpected artifact set")
	for name, metadata in manifest["artifacts"].items():
		if (directory / name).stat().st_size != metadata["bytes"] or sha256_file(directory / name) != metadata["sha256"]:
			raise ValueError(f"Artifact checksum/size mismatch: {name}")
	config = ExperimentConfig.from_dict(json.loads((directory / "config.json").read_text(encoding="utf-8")))
	report = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
	if report["config"] != config.to_dict() or manifest["semantics_id"] != semantics_id(config.cell_bits) or report["semantics_id"] != semantics_id(config.cell_bits):
		raise ValueError("Configuration/semantics mismatch")
	if report["engine_version"] != manifest["engine_version"]:
		raise ValueError("Engine version mismatch")
	if [item["length"] for item in report["lengths"]] != list(config.lengths):
		raise ValueError("Summary lengths differ from configuration")
	with (directory / "summary.csv").open(encoding="utf-8", newline="") as source:
		if list(csv.DictReader(source)) != [csv_strings(row) for row in summary_rows(report)]:
			raise ValueError("CSV summary differs from JSON summary")
	records = iter(read_records(directory))
	total_records = 0
	with gzip.open(directory / "programs.csv.gz", "rt", encoding="utf-8", newline="") as source:
		csv_records = iter(csv.DictReader(source))
		for item in report["lengths"]:
			length = item["length"]
			accumulator = StreamingSummary(length, config.max_distinct_outcomes, config.max_outcome_bytes)
			for rank in range(item["coverage"]["evaluated_candidates"]):
				record = next(records, None)
				if record is None or record["program"] != program_at_index(length, rank):
					raise ValueError("Missing or reordered execution record")
				if next(csv_records, None) != csv_strings(record_csv_row(record)):
					raise ValueError("CSV/JSON execution records disagree")
				accumulator.observe(decode_result(record))
				total_records += 1
			for name, value in accumulator.report().items():
				if item[name] != value:
					raise ValueError(f"Summary disagrees with records: n={length}, {name}")
			coverage = item["coverage"]
			exhaustive = accumulator.evaluated == 8 ** length
			resolved = exhaustive and item["metrics"]["U"] == 0
			if item["bounds"] != ("complete_finite_model_results" if resolved else "observed_lower_bounds"):
				raise ValueError("Incorrect uncertainty label")
			if coverage["total_candidates"] != 8 ** length or coverage["not_evaluated_candidates"] != 8 ** length - accumulator.evaluated or coverage["exhaustive"] != exhaustive or coverage["fully_resolved"] != resolved:
				raise ValueError("Coverage accounting mismatch")
			if exhaustive and item["counts"]["syntactically_invalid"] != 8 ** length - valid_program_count(length):
				raise ValueError("Syntax counts disagree with combinatorial total")
		if next(records, None) is not None or next(csv_records, None) is not None:
			raise ValueError("Unexpected extra records")
	if total_records != manifest["records"]:
		raise ValueError("Manifest record count mismatch")
	return {"verified": True, "records_checked": total_records, "semantics_id": manifest["semantics_id"], "source_commit": manifest["provenance"]["git_commit"]}
