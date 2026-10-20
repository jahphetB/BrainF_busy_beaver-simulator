"""Reproduce the frozen original's baseline; never import the new engine."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "data/historical/original_generate.py"


def capture():
	with contextlib.redirect_stdout(io.StringIO()):
		legacy = runpy.run_path(str(ORIGINAL))
	runs = []
	for limit in (100, 512):
		records = []
		counts = {"halted": 0, "cycle_detected": 0, "step_limit": 0}
		outcomes = set()
		for program in legacy["valid_programs"]:
			status, steps, output, pointer, tape = legacy["run_program"](program, limit)
			counts[status] += 1
			records.append([program, status, steps, list(output.encode("latin-1")), pointer, tape])
			if status == "halted":
				outcomes.add((output, pointer, tuple(tape)))
		maximum = max(row[2] for row in records if row[1] == "halted")
		encoded = json.dumps(records, separators=(",", ":")).encode("ascii")
		runs.append({
			"max_steps": limit,
			"total_programs": len(legacy["programs"]),
			"valid_programs": len(legacy["valid_programs"]),
			"invalid_programs": len(legacy["invalid_programs"]),
			"counts": counts,
			"distinct_halted_outcomes": len(outcomes),
			"duplicate_halted_programs": counts["halted"] - len(outcomes),
			"maximum_observed_halting_steps": maximum,
			"maximum_step_programs": [r[0] for r in records if r[1] == "halted" and r[2] == maximum],
			"unresolved_programs": [r[0] for r in records if r[1] == "step_limit"],
			"records_sha256": hashlib.sha256(encoded).hexdigest(),
		})
	return {
		"schema_version": 1,
		"original_git_commit": "c86e07947ca2975375d199ae23cc18daa7f49122",
		"original_source_sha256": hashlib.sha256(ORIGINAL.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
		"alphabet": legacy["commands"],
		"program_length": 4,
		"input_bytes": [],
		"record_encoding": "ASCII compact JSON array, enumeration order; each row: program, status, steps, output byte array, pointer, allocated tape",
		"runs": runs,
	}


if __name__ == "__main__":
	print(json.dumps(capture(), indent="\t"))
