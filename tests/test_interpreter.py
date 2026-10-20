import dataclasses
import json
import unittest

from tests import ROOT
from brainfuck_research import SEMANTICS_ID
from brainfuck_research.export import result_record
from brainfuck_research.interpreter import run_program
from brainfuck_research.models import Status
from brainfuck_research.syntax import ProgramSyntaxError, build_bracket_map, valid_brackets


class SyntaxTests(unittest.TestCase):
	def test_nested_bidirectional_bracket_map(self):
		self.assertEqual(build_bracket_map("[[]][]"), {0: 3, 3: 0, 1: 2, 2: 1, 4: 5, 5: 4})

	def test_invalid_brackets_and_noncommands(self):
		for program in ("[", "]", "][", "[[]", "[]]", "+ comment", " ", "\n"):
			with self.subTest(program=program):
				self.assertFalse(valid_brackets(program))
				with self.assertRaises(ProgramSyntaxError):
					build_bracket_map(program)
				result = run_program(program)
				self.assertEqual(result.status, Status.INVALID)
				self.assertEqual(result.state.steps, 0)
				self.assertIsNotNone(result.error)

	def test_empty_and_loop_free_are_valid(self):
		for program in ("", "+-.,><", "[[]]"):
			self.assertTrue(valid_brackets(program))


class InterpreterTests(unittest.TestCase):
	def test_shared_hand_derived_fixtures(self):
		fixtures = json.loads((ROOT / "tests/fixtures/semantics.json").read_text(encoding="utf-8"))
		self.assertEqual(fixtures["semantics_id"], SEMANTICS_ID)
		for case in fixtures["cases"]:
			with self.subTest(case=case["name"]):
				actual = result_record(run_program(case["program"], case["max_steps"], bytes(case["input_bytes"])))
				for field, expected in case["expected"].items():
					self.assertEqual(actual[field], expected, field)

	def test_wrapping_loops_with_independent_arithmetic_and_cutoffs(self):
		for program, initial, delta in (("+[+]", 1, 1), ("-[-]", 255, -1)):
			# Solve first zero in the modular sequence without interpreting source.
			iterations = next(k for k in range(1, 257) if (initial + k * delta) % 256 == 0)
			self.assertEqual(iterations, 255)
			for budget in (100, 511, 512, 513):
				with self.subTest(program=program, budget=budget):
					result = run_program(program, budget)
					self.assertEqual(result.status, Status.HALTED if budget >= 512 else Status.STEP_LIMIT)
					self.assertEqual(result.state.steps, min(budget, 2 + 2 * iterations))
					if budget >= 511:
						self.assertEqual(result.state.tape, (0,))

	def test_eof_overwrites_nonzero_cell(self):
		result = run_program("+,.")
		self.assertEqual(result.state.output, b"\x00")
		self.assertEqual(result.state.input_pos, 0)

	def test_repeated_nonzero_input_is_not_a_control_cycle(self):
		result = run_program("+[,]", 100, bytes([1, 1, 1, 0]))
		self.assertEqual(result.status, Status.HALTED)
		self.assertEqual(result.state.steps, 10)
		self.assertEqual(result.state.input_pos, 4)

	def test_unbounded_growth_is_unresolved_not_proven_nonterminating(self):
		result = run_program("+[>+]", 100)
		self.assertEqual(result.status, Status.STEP_LIMIT)
		self.assertIsNone(result.cycle_period)
		self.assertGreater(len(result.state.tape), 1)

	def test_trace_and_normal_execution_agree(self):
		for program in (">>>>", ">>>+", "++[>++[>+<-]<-]", "+[.]", "+[+]"):
			with self.subTest(program=program):
				events = []
				traced = run_program(program, 512, trace=events.append)
				self.assertEqual(traced, run_program(program, 512))
				self.assertEqual(len(events), traced.state.steps)
				self.assertEqual(events[-1].after, traced.state)
				for previous, following in zip(events, events[1:]):
					self.assertEqual(previous.after, following.before)
				for event in events:
					self.assertEqual(event.command, program[event.before.ip])
					self.assertEqual(event.after.steps, event.before.steps + 1)

	def test_cycle_evidence_identifies_equal_control_states(self):
		events = []
		result = run_program("+[.]", trace=events.append)
		start = events[result.cycle_start].before
		end = result.state
		self.assertEqual((start.ip, start.pointer, start.tape, start.input_pos), (end.ip, end.pointer, end.tape, end.input_pos))
		self.assertNotEqual(start.output, end.output)
		self.assertEqual(end.steps - start.steps, result.cycle_period)

	def test_trace_snapshots_are_immutable(self):
		events = []
		run_program("++", trace=events.append)
		self.assertEqual(events[0].after.tape, (1,))
		with self.assertRaises(dataclasses.FrozenInstanceError):
			events[0].after.steps = 99

	def test_no_trace_events_without_executed_instructions(self):
		for program, budget in (("", 10), ("+", 0), ("[", 10)):
			events = []
			run_program(program, budget, trace=events.append)
			self.assertEqual(events, [])

	def test_configuration_validation(self):
		for budget in (-1, 1.5, True, "100", None):
			with self.subTest(budget=budget), self.assertRaises(ValueError):
				run_program("+", budget)
		for input_data in ("abc", [1], bytearray([1])):
			with self.assertRaises(TypeError):
				run_program(",", input_data=input_data)
		with self.assertRaises(TypeError):
			run_program(None)
