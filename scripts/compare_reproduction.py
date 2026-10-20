"""Compare deterministic records and scientific summaries from two dataset runs."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brainfuck_research.datasets import sha256_file, write_json


def scientific_summary(directory):
	report = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
	report.pop("elapsed_seconds")
	for row in report["lengths"]:
		row.pop("elapsed_seconds")
	return report


def compare(original, repeat):
	original, repeat = Path(original), Path(repeat)
	hashes = {}
	for name in ("config.json", "programs.jsonl.gz", "programs.csv.gz"):
		first, second = sha256_file(original / name), sha256_file(repeat / name)
		if first != second:
			raise ValueError(f"Reproduction differs: {name}")
		hashes[name] = first
	if scientific_summary(original) != scientific_summary(repeat):
		raise ValueError("Scientific summaries differ after removing elapsed times")
	original_manifest = json.loads((original / "manifest.json").read_text(encoding="utf-8"))
	repeated_manifest = json.loads((repeat / "manifest.json").read_text(encoding="utf-8"))
	return {
		"reproduced": True, "original_run": original.name,
		"record_count": original_manifest["records"], "matching_artifact_sha256": hashes,
		"scientific_summaries_equal": True,
		"original_manifest_sha256": sha256_file(original / "manifest.json"),
		"repeat_manifest_sha256": sha256_file(repeat / "manifest.json"),
		"same_source_tree": original_manifest["provenance"]["source_tree_sha256"] == repeated_manifest["provenance"]["source_tree_sha256"],
		"original_source_commit": original_manifest["provenance"]["git_commit"],
		"repeat_source_commit": repeated_manifest["provenance"]["git_commit"],
		"repeat_finished_at_utc": repeated_manifest["finished_at_utc"],
		"note": "Elapsed times and timestamped/environment manifests vary; compressed records use deterministic gzip headers.",
	}


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("original", type=Path)
	parser.add_argument("repeat", type=Path)
	parser.add_argument("--output", type=Path)
	args = parser.parse_args()
	result = compare(args.original, args.repeat)
	if args.output:
		write_json(args.output, result)
	print(json.dumps(result, indent="\t"))
