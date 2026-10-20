"""Check paper tables, distributions, provenance, witnesses and PDF structure."""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent
sys.path.insert(0, str(ROOT / "src"))
from brainfuck_research.interpreter import run_program


def require(condition, message):
	if not condition:
		raise ValueError(message)


def main():
	analysis = ROOT / "data/analysis/v1"
	manifest = json.loads((analysis / "manifest.json").read_text())
	for name, expected in manifest["artifacts"].items():
		require(hashlib.sha256((analysis / name).read_bytes()).hexdigest()
			== expected["sha256"], f"Analysis hash mismatch: {name}")
	for run, expected in manifest["input_manifests_sha256"].items():
		directory = ROOT / "data/runs/v1" / run
		require(hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
			== expected, f"Input manifest changed: {run}")
		data_manifest = json.loads((directory / "manifest.json").read_text())
		for name, record in data_manifest["artifacts"].items():
			require(hashlib.sha256((directory / name).read_bytes()).hexdigest()
				== record["sha256"], f"Dataset hash mismatch: {run}/{name}")
		for name, expected_source in data_manifest["provenance"]["source_files_sha256_lf"].items():
			content = (ROOT / name).read_text(encoding="utf-8").encode("utf-8")
			require(hashlib.sha256(content).hexdigest() == expected_source,
				f"Current engine differs from dataset source: {name}")

	with (analysis / "summary.csv").open(newline="", encoding="utf-8") as stream:
		rows = list(csv.DictReader(stream))
	with (analysis / "runtime-output.csv").open(newline="", encoding="utf-8") as stream:
		pairs = list(csv.DictReader(stream))
	statistics = json.loads((PAPER / "statistics.json").read_text())
	for stat in statistics["rows"]:
		group = [r for r in pairs if r["run"] == stat["run"] and int(r["length"]) == stat["length"]]
		halted = sum(int(r["halted_programs"]) for r in group)
		fast = sum(int(r["halted_programs"]) for r in group if int(r["steps"]) <= stat["length"])
		require(halted == stat["halted"], "Statistics total mismatch")
		require(fast == stat["halted_within_n_steps"], "Fast-program count mismatch")
		require(round(100 * fast / halted, 4) == stat["halted_within_n_steps_percent"],
			"Conditional percentage mismatch")

	source = (PAPER / "report.md").read_text(encoding="utf-8")
	for n in range(1, 7):
		run = "primary-n1-5-s512" if n < 4 else "steps4096-n4-6"
		row = next(r for r in rows if r["run"] == run and int(r["length"]) == n)
		valid = sum(int(row[key]) for key in ("halted", "cycle_detected", "U"))
		values = [str(n), str(valid)] + [row[key] for key in ("halted", "cycle_detected", "U", "T", "O", "M", "D")]
		require("| " + " | ".join(values) + " |" in source, f"Table 1 mismatch at n={n}")
	witness_rows = re.findall(r"^\| `([^`]+)` \| (\d+) \| (\d+) \| (\d+) \|$", source, re.M)
	require(len(witness_rows) == 5, "Expected five displayed witnesses")
	for program, n, steps, output in witness_rows:
		result = run_program(program, max_steps=4096)
		require(result.status.value == "halted", f"Witness did not halt: {program}")
		require((len(program), result.state.steps, len(result.state.output)) == (int(n), int(steps), int(output)),
			f"Witness table mismatch: {program}")

	for n in (5, 6):
		stat = next(row for row in statistics["rows"]
			if row["run"] == "steps4096-n4-6" and row["length"] == n)
		require(f'{stat["halted_within_n_steps_percent"]:.2f}%' in source,
			f"Displayed percentage mismatch at n={n}")
	require(source.count("<!-- pagebreak -->") == 7, "Expected eight editorial pages")
	for path in PAPER.glob("*.py"):
		for line in path.read_text(encoding="utf-8").splitlines():
			require(not line.startswith(" "), f"Space-indented maintained code: {path.name}")

	built = json.loads((PAPER / "build-manifest.json").read_text())
	for name, expected in built["artifacts_sha256"].items():
		require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected,
			f"Stale build artifact: {name}")
	pdf = PdfReader(PAPER / "brainfuck-productivity.pdf")
	require(len(pdf.pages) == 8, "PDF must have eight pages")
	require(all(len(p.extract_text()) > 1000 for p in pdf.pages), "Unexpected near-empty PDF page")
	links = []
	for page in pdf.pages:
		for annotation in page.get("/Annots", []):
			action = annotation.get_object().get("/A", {})
			if action.get("/URI"):
				links.append(str(action["/URI"]))
	reference_urls = re.findall(r"\]\((https?://[^)]+)\)", source.split("### References", 1)[1])
	require(set(reference_urls) <= set(links), "Missing active PDF reference links")
	require(len(re.findall(r"^@\w+\{", (PAPER / "references.bib").read_text(), re.M)) == 8,
		"Expected eight bibliography entries")
	print("PASS: dataset/analysis/source hashes, 12 distributions, 6 table rows, "
		"5 witness replays, code indentation, build hashes, 8 PDF pages and reference links.")


if __name__ == "__main__":
	main()
