import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests import ROOT
from brainfuck_research.analysis import StreamingSummary, summarize
from brainfuck_research.config import ExecutionLimits, ExperimentConfig
from brainfuck_research.enumeration import enumerate_programs
from brainfuck_research.experiments import estimate_search, run_experiment
from brainfuck_research.interpreter import run_program


class ExperimentTests(unittest.TestCase):
	def test_estimate_calculates_instruction_ceiling_without_execution(self):
		with patch("brainfuck_research.experiments.run_program", side_effect=AssertionError("Estimate must not execute source")):
			estimate = estimate_search(ExperimentConfig(lengths=(4,), max_programs_per_length=None))
		self.assertEqual(estimate["lengths"][0]["valid_candidates_total"], 1514)
		self.assertEqual(estimate["lengths"][0]["instruction_budget_upper_bound"], 1514 * 512)
		limited = estimate_search(ExperimentConfig(lengths=(7,), max_programs_per_length=10))
		self.assertEqual(limited["lengths"][0]["instruction_budget_upper_bound"], 10 * 512)

	def test_length_four_stream_matches_baseline_and_verified_records(self):
		for budget in (100, 512):
			config = ExperimentConfig(lengths=(4,), max_steps=budget)
			actual = run_experiment(config)["lengths"][0]
			expected = summarize(run_program(program, budget) for program in enumerate_programs(4))
			self.assertEqual(actual["counts"], expected["counts"])
			self.assertEqual(actual["metrics"], {"T": expected["maximum_observed_halting_steps"], "O": 4, "M": 5, "D": 228, "U": 2 if budget == 100 else 0})
			self.assertTrue(actual["coverage"]["exhaustive"])
			self.assertEqual(actual["coverage"]["fully_resolved"], budget == 512)
			self.assertEqual(actual["maximum_steps_per_command"], actual["metrics"]["T"] / 4)
			for metric, record in actual["records"].items():
				witness = run_program(record["program"], budget)
				value = {"T": witness.state.steps, "O": len(witness.state.output), "M": len(witness.state.tape)}[metric]
				self.assertEqual(value, record["value"])

	def test_length_one_matches_hand_count_and_sends_every_record_once(self):
		records = []
		result = run_experiment(ExperimentConfig(lengths=(1,)), on_result=records.append)["lengths"][0]
		self.assertEqual([r.program for r in records], list("><+-.,[]"))
		self.assertEqual(result["metrics"], {"T": 1, "O": 1, "M": 2, "D": 5, "U": 0})
		self.assertEqual(result["counts"]["halted"], 6)
		self.assertEqual(result["counts"]["syntactically_invalid"], 2)
		self.assertEqual(result["duplicate_halted_programs"], 1)

	def test_candidate_limit_is_not_program_nontermination(self):
		result = run_experiment(ExperimentConfig(lengths=(7,), max_programs_per_length=3))["lengths"][0]
		self.assertEqual(result["coverage"]["evaluated_candidates"], 3)
		self.assertEqual(result["coverage"]["not_evaluated_candidates"], 8 ** 7 - 3)
		self.assertEqual(result["coverage"]["stop_reason"], "candidate_limit")
		self.assertFalse(result["coverage"]["exhaustive"])
		self.assertEqual(result["bounds"], "observed_lower_bounds")
		self.assertEqual(result["metrics"]["U"], 0)

	def test_exact_candidate_budget_finishes_length(self):
		result = run_experiment(ExperimentConfig(lengths=(1,), max_programs_per_length=8))["lengths"][0]
		self.assertEqual(result["coverage"]["stop_reason"], "completed")
		self.assertTrue(result["coverage"]["exhaustive"])

	def test_per_program_resource_stops_contribute_to_unresolved(self):
		config = ExperimentConfig(lengths=(1,), limits=ExecutionLimits(max_tape_cells=1, max_output_bytes=0))
		result = run_experiment(config)["lengths"][0]
		self.assertEqual(result["counts"]["resource_limit"], 2)
		self.assertEqual(result["metrics"]["U"], 2)
		self.assertEqual(result["resource_reasons"], {"tape_cells": 1, "output_bytes": 1})
		self.assertTrue(result["coverage"]["exhaustive"])
		self.assertFalse(result["coverage"]["fully_resolved"])

	def test_outcome_count_limit_keeps_exact_prefix_count(self):
		config = ExperimentConfig(lengths=(1,), max_distinct_outcomes=1)
		result = run_experiment(config)["lengths"][0]
		self.assertEqual(result["coverage"]["evaluated_candidates"], 2)
		self.assertEqual(result["coverage"]["stop_reason"], "distinct_outcome_limit")
		self.assertEqual((result["metrics"]["D"], result["retained_outcomes"]), (2, 1))
		self.assertTrue(result["unretained_final_distinct_outcome"])

	def test_outcome_byte_limit_does_not_drop_executed_program(self):
		result = run_experiment(ExperimentConfig(lengths=(1,), max_outcome_bytes=1))["lengths"][0]
		self.assertEqual(result["coverage"]["stop_reason"], "outcome_bytes_limit")
		self.assertEqual(result["counts"]["halted"], 1)
		self.assertEqual(result["metrics"]["D"], 1)
		self.assertEqual(result["retained_outcome_bytes"], 0)

	def test_duplicates_at_storage_cap_do_not_need_new_keys(self):
		accumulator = StreamingSummary(1, 1, 1)
		self.assertIsNone(accumulator.observe(run_program("<")))
		self.assertIsNone(accumulator.observe(run_program(",")))
		self.assertEqual(accumulator.observe(run_program("+")), "distinct_outcome_limit")
		self.assertEqual(accumulator.report()["metrics"]["D"], 2)
		self.assertEqual(accumulator.report()["duplicate_halted_programs"], 1)
		with self.assertRaises(RuntimeError):
			accumulator.observe(run_program("-"))

	def test_global_deadline_reports_all_requested_lengths_as_unevaluated(self):
		with patch("brainfuck_research.experiments.monotonic", side_effect=[0, 2, 2, 2, 2, 2, 2, 2]):
			report = run_experiment(ExperimentConfig(lengths=(1, 2), max_seconds=1))
		for summary in report["lengths"]:
			self.assertEqual(summary["coverage"]["evaluated_candidates"], 0)
			self.assertEqual(summary["coverage"]["stop_reason"], "experiment_time_limit")
			self.assertIsNone(summary["metrics"]["T"])
			self.assertEqual(summary["metrics"]["U"], 0)

	def test_global_remaining_time_is_passed_to_program(self):
		with patch("brainfuck_research.experiments.monotonic", return_value=10), patch("brainfuck_research.experiments.run_program", wraps=run_program) as execute:
			run_experiment(ExperimentConfig(lengths=(1,), max_programs_per_length=1, max_seconds=2))
		self.assertEqual(execute.call_args.kwargs["limits"].max_seconds, 2)

	def test_smaller_program_deadline_is_preserved(self):
		config = ExperimentConfig(lengths=(1,), max_programs_per_length=1, limits=ExecutionLimits(max_seconds=0.25))
		with patch("brainfuck_research.experiments.run_program", wraps=run_program) as execute:
			run_experiment(config)
		self.assertEqual(execute.call_args.kwargs["limits"].max_seconds, 0.25)


class ExperimentCliTests(unittest.TestCase):
	def invoke(self, *args):
		return subprocess.run([sys.executable, "-B", str(ROOT / "generate.py"), "experiment", *args], cwd=ROOT, capture_output=True, text=True)

	def test_streamed_jsonl_and_report_are_consistent(self):
		with tempfile.TemporaryDirectory() as directory:
			from pathlib import Path
			report_path = Path(directory) / "summary.json"
			records_path = Path(directory) / "records.jsonl"
			result = self.invoke("--lengths", "1", "--report", str(report_path), "--records", str(records_path), "--json")
			self.assertEqual(result.returncode, 0, result.stderr)
			report = json.loads(report_path.read_text(encoding="utf-8"))
			self.assertEqual(report, json.loads(result.stdout))
			records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
			self.assertEqual(len(records), report["lengths"][0]["coverage"]["evaluated_candidates"])
			self.assertEqual(records[0]["metrics"]["cells_visited"], 2)
			before = records_path.read_bytes()
			self.assertEqual(self.invoke("--records", str(records_path)).returncode, 2)
			self.assertEqual(records_path.read_bytes(), before)

	def test_config_file_reproduces_validated_baseline(self):
		result = self.invoke("--config", "experiments/configs/phase2-validation.json", "--json")
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(json.loads(result.stdout)["lengths"][-1]["metrics"]["T"], 512)

	def test_invalid_flags_and_config_conflicts_fail(self):
		for args in (("--lengths", "8"), ("--lengths", "2", "1"), ("--max-seconds", "nan"), ("--max-programs", "0"), ("--max-programs", "1", "--exhaustive"), ("--config", "experiments/configs/phase2-validation.json", "--max-steps", "100")):
			with self.subTest(args=args):
				result = self.invoke(*args)
				self.assertEqual(result.returncode, 2, result.stderr)
