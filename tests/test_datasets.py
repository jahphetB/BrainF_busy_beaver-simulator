import csv
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests import ROOT
from brainfuck_research.config import ExperimentConfig, semantics_id
from brainfuck_research.datasets import create_dataset, read_records, sha256_file, verify_dataset
from brainfuck_research.interpreter import run_program
from brainfuck_research.models import Status


class CellSemanticsTests(unittest.TestCase):
	def test_four_bit_wrapping_loops_halt_at_32_instructions(self):
		for program in ("+[+]", "-[-]"):
			self.assertEqual(run_program(program, 31, cell_bits=4).status, Status.STEP_LIMIT)
			result = run_program(program, 32, cell_bits=4)
			self.assertEqual((result.status, result.state.steps, result.state.tape), (Status.HALTED, 32, (0,)))
			self.assertEqual(run_program(program, 32).status, Status.STEP_LIMIT)

	def test_narrow_cells_reduce_input_but_emit_one_byte(self):
		result = run_program(",.", input_data=bytes([255]), cell_bits=4)
		self.assertEqual(result.state.output, bytes([15]))
		self.assertEqual(result.metrics["output_bytes"], 1)
		self.assertEqual(run_program("-+.", cell_bits=4).state.output, bytes([0]))

	def test_semantics_are_named_and_invalid_widths_rejected(self):
		self.assertEqual(semantics_id(8), "legacy-u8-right-v1")
		self.assertEqual(semantics_id(4), "u4-right-v1")
		for width in (0, 16, True, 4.0):
			with self.assertRaises(ValueError):
				run_program("+", cell_bits=width)
			with self.assertRaises(ValueError):
				ExperimentConfig(cell_bits=width)


class DatasetTests(unittest.TestCase):
	def setUp(self):
		self.temporary = tempfile.TemporaryDirectory()
		self.addCleanup(self.temporary.cleanup)
		self.directory = Path(self.temporary.name) / "run"
		self.config = ExperimentConfig(lengths=(1, 2), max_seconds=30)
		self.provenance = patch("brainfuck_research.datasets.source_provenance", return_value={"git_commit": "test-only", "engine_sources_match_commit": False})
		self.provenance.start()
		self.addCleanup(self.provenance.stop)

	def rewrite_and_rehash(self, name, value):
		path = self.directory / name
		path.write_text(json.dumps(value), encoding="utf-8")
		manifest_path = self.directory / "manifest.json"
		manifest = json.loads(manifest_path.read_text())
		manifest["artifacts"][name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
		manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

	def test_round_trip_and_csv_json_agreement(self):
		report = create_dataset(self.config, self.directory)
		verified = verify_dataset(self.directory)
		self.assertEqual(verified["records_checked"], 72)
		self.assertTrue(verified["verified"])
		self.assertEqual(len(list(read_records(self.directory))), 72)
		self.assertEqual(report["lengths"][0]["metrics"]["D"], 5)

	def test_existing_run_is_never_overwritten(self):
		create_dataset(self.config, self.directory)
		before = sha256_file(self.directory / "manifest.json")
		with self.assertRaises(FileExistsError):
			create_dataset(self.config, self.directory)
		self.assertEqual(sha256_file(self.directory / "manifest.json"), before)

	def test_resource_and_partial_coverage_are_preserved(self):
		config = ExperimentConfig(lengths=(4,), max_steps=0, max_programs_per_length=10, cell_bits=4)
		report = create_dataset(config, self.directory)
		self.assertEqual(report["semantics_id"], "u4-right-v1")
		self.assertFalse(report["lengths"][0]["coverage"]["exhaustive"])
		self.assertEqual(verify_dataset(self.directory)["records_checked"], 10)

	def test_changed_artifact_fails_integrity_check(self):
		create_dataset(self.config, self.directory)
		with (self.directory / "summary.csv").open("a") as output:
			output.write("tamper\n")
		with self.assertRaisesRegex(ValueError, "checksum"):
			verify_dataset(self.directory)

	def test_forged_summary_is_not_accepted_after_rehash(self):
		report = create_dataset(self.config, self.directory)
		report["lengths"][0]["metrics"]["D"] += 1
		self.rewrite_and_rehash("summary.json", report)
		with self.assertRaisesRegex(ValueError, "summary"):
			verify_dataset(self.directory)

	def test_failed_export_has_no_completion_manifest(self):
		with patch("brainfuck_research.datasets.run_experiment", side_effect=RuntimeError("test interruption")):
			with self.assertRaises(RuntimeError):
				create_dataset(self.config, self.directory)
		self.assertFalse((self.directory / "manifest.json").exists())
		with self.assertRaises(FileNotFoundError):
			verify_dataset(self.directory)

	def test_deterministic_records_across_repeated_runs(self):
		create_dataset(self.config, self.directory)
		other = self.directory.parent / "repeat"
		create_dataset(self.config, other)
		for name in ("programs.csv.gz", "programs.jsonl.gz"):
			self.assertEqual(sha256_file(self.directory / name), sha256_file(other / name))

	def test_outcome_storage_stop_verifies_exact_evaluated_prefix(self):
		config = ExperimentConfig(lengths=(1,), max_distinct_outcomes=0)
		report = create_dataset(config, self.directory)
		self.assertEqual(report["lengths"][0]["metrics"]["D"], 1)
		self.assertEqual(verify_dataset(self.directory)["records_checked"], 1)
