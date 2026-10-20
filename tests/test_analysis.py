import unittest

from tests import ROOT
from brainfuck_research.analysis import empirical_surprisal, group_halted_outcomes, outcome_key, summarize
from brainfuck_research.interpreter import run_program


class AnalysisTests(unittest.TestCase):
	def test_equivalence_retains_allocated_zero_cells_and_pointer(self):
		self.assertEqual(outcome_key(run_program("")), outcome_key(run_program("+-")))
		self.assertNotEqual(outcome_key(run_program("")), outcome_key(run_program("><")))
		self.assertNotEqual(outcome_key(run_program(">")), outcome_key(run_program("><")))

	def test_output_is_distinct_from_memory(self):
		self.assertNotEqual(outcome_key(run_program("+")), outcome_key(run_program("+.")))
		self.assertEqual(outcome_key(run_program("+"))[0], b"")

	def test_output_delimiters_and_null_bytes_are_safe(self):
		first = run_program(",.", input_data=b"|")
		second = run_program(",.", input_data=b"\x00")
		self.assertEqual(len(group_halted_outcomes([first, first, second])), 2)

	def test_nonhalted_results_are_excluded(self):
		results = [run_program("+[]"), run_program("+[+]", 100), run_program("[")]
		self.assertEqual(group_halted_outcomes(results), {})
		for result in results:
			with self.assertRaises(ValueError):
				outcome_key(result)
		self.assertIsNone(summarize(results)["maximum_observed_halting_steps"])

	def test_empty_summary_has_no_fabricated_extrema(self):
		summary = summarize([])
		self.assertEqual(summary["total_programs"], 0)
		self.assertIsNone(summary["minimum_observed_halting_steps"])
		self.assertIsNone(summary["maximum_observed_halting_steps"])

	def test_empirical_surprisal_is_conditional_frequency_only(self):
		self.assertEqual(empirical_surprisal(1, 4), 2)
		self.assertEqual(empirical_surprisal(4, 4), 0)
		for sizes in ((0, 4), (5, 4), (1, 0)):
			with self.assertRaises(ValueError):
				empirical_surprisal(*sizes)
