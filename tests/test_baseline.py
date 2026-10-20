import contextlib
import hashlib
import io
import json
import runpy
import unittest

from tests import ROOT
from scripts.capture_legacy_baseline import capture
from brainfuck_research.analysis import group_halted_outcomes
from brainfuck_research.config import BaselineConfig
from brainfuck_research.enumeration import length_four_programs
from brainfuck_research.experiments import run_baseline
from brainfuck_research.export import baseline_report
from brainfuck_research.models import Status


class BaselineTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		with contextlib.redirect_stdout(io.StringIO()):
			cls.legacy = runpy.run_path(str(ROOT / "data/historical/original_generate.py"))
		cls.frozen = json.loads((ROOT / "data/historical/baseline.json").read_text(encoding="utf-8"))
		cls.runs = {limit: run_baseline(BaselineConfig(limit)) for limit in (100, 512)}

	def test_enumeration_matches_original_order_without_duplicates(self):
		programs = list(length_four_programs())
		self.assertEqual(programs, self.legacy["programs"])
		self.assertEqual(len(set(programs)), 4096)
		self.assertTrue(all(len(program) == 4 for program in programs))

	def test_archive_reproduces_frozen_baseline(self):
		self.assertEqual(capture(), self.frozen)

	def test_every_valid_result_matches_independent_original_at_both_limits(self):
		for limit, results in self.runs.items():
			for result in results:
				with self.subTest(limit=limit, program=result.program):
					if not self.legacy["valid_brackets"](result.program):
						self.assertEqual(result.status, Status.INVALID)
						continue
					state = result.state
					actual = (result.status.value, state.steps, state.output.decode("latin-1"), state.pointer, list(state.tape))
					self.assertEqual(actual, self.legacy["run_program"](result.program, limit))

	def test_summaries_and_full_record_hashes_match_frozen_evidence(self):
		for frozen in self.frozen["runs"]:
			limit = frozen["max_steps"]
			results = self.runs[limit]
			report = baseline_report(BaselineConfig(limit), results)
			summary = report["summary"]
			with self.subTest(limit=limit):
				for key in ("total_programs", "valid_programs", "invalid_programs", "distinct_halted_outcomes", "duplicate_halted_programs", "maximum_observed_halting_steps", "maximum_step_programs", "unresolved_programs"):
					self.assertEqual(summary[key], frozen[key], key)
				for status, count in frozen["counts"].items():
					self.assertEqual(summary["counts"][status], count)
				self.assertEqual(sum(summary["counts"].values()), 4096)
				rows = [[r.program, r.status.value, r.state.steps, list(r.state.output), r.state.pointer, list(r.state.tape)] for r in results if r.status != Status.INVALID]
				digest = hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode("ascii")).hexdigest()
				self.assertEqual(digest, frozen["records_sha256"])

	def test_historical_group_memberships_match_original(self):
		actual = {key: [r.program for r in group] for key, group in group_halted_outcomes(self.runs[100]).items()}
		expected = {
			(group["output"].encode("latin-1"), group["pointer"], tuple(group["tape"])): group["programs"]
			for group in self.legacy["outcome_groups"]
		}
		self.assertEqual(actual, expected)
