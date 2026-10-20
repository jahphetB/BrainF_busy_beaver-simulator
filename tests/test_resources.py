from dataclasses import replace
import unittest
from unittest.mock import patch

from tests import ROOT
from brainfuck_research.config import ExecutionLimits, ExperimentConfig
from brainfuck_research.enumeration import enumerate_programs, program_at_index
from brainfuck_research.export import result_record
from brainfuck_research.interpreter import run_program
from brainfuck_research.models import Status


class ResourceTests(unittest.TestCase):
	def test_tape_limit_stops_before_unvisited_cell(self):
		result = run_program(">>", limits=ExecutionLimits(max_tape_cells=2))
		self.assertEqual((result.status, result.resource_reason), (Status.RESOURCE_LIMIT, "tape_cells"))
		self.assertEqual((result.state.steps, result.state.pointer, result.state.tape), (1, 1, (0, 0)))
		self.assertEqual(result.metrics["cells_visited"], 2)

	def test_output_limit_stops_before_extra_byte(self):
		result = run_program("..", limits=ExecutionLimits(max_output_bytes=1))
		self.assertEqual(result.resource_reason, "output_bytes")
		self.assertEqual((result.state.steps, result.state.output), (1, b"\0"))
		self.assertEqual(run_program(".", limits=ExecutionLimits(max_output_bytes=1)).status, Status.HALTED)

	def test_zero_output_limit_does_not_stop_nonoutput_instructions(self):
		self.assertEqual(run_program("+", limits=ExecutionLimits(max_output_bytes=0)).status, Status.HALTED)
		self.assertEqual(run_program(".", limits=ExecutionLimits(max_output_bytes=0)).state.steps, 0)

	def test_state_count_limit_and_cycle_precedence(self):
		stopped = run_program("+[]", limits=ExecutionLimits(max_seen_states=2))
		self.assertEqual((stopped.resource_reason, stopped.state.steps, stopped.seen_states), ("seen_states", 2, 2))
		cycle = run_program("+[]", limits=ExecutionLimits(max_seen_states=3))
		self.assertEqual(cycle.status, Status.CYCLE)
		self.assertEqual(cycle.seen_states, 3)

	def test_state_payload_limit_accounts_for_growing_tape(self):
		result = run_program("+[>+]", limits=ExecutionLimits(max_state_bytes=4))
		self.assertEqual((result.resource_reason, result.state.steps, result.state_bytes), ("state_bytes", 3, 3))
		self.assertEqual(result.state.tape, (1, 0))

	def test_loop_free_execution_needs_no_cycle_history(self):
		result = run_program("+++>+<", limits=ExecutionLimits(max_seen_states=0, max_state_bytes=0))
		self.assertEqual(result.status, Status.HALTED)
		self.assertEqual((result.seen_states, result.state_bytes), (0, 0))

	def test_wall_clock_limit_is_distinct_and_deterministically_tested(self):
		with patch("brainfuck_research.interpreter.monotonic", side_effect=[0, 1]):
			result = run_program("+", limits=ExecutionLimits(max_seconds=0.5))
		self.assertEqual((result.status, result.resource_reason, result.state.steps), (Status.RESOURCE_LIMIT, "wall_time", 0))

	def test_halt_and_step_cutoff_precede_resource_checks(self):
		limits = ExecutionLimits(max_tape_cells=1, max_seconds=0.5)
		with patch("brainfuck_research.interpreter.monotonic", side_effect=[0, 0.1]):
			self.assertEqual(run_program("+", 1, limits=limits).status, Status.HALTED)
		with patch("brainfuck_research.interpreter.monotonic", return_value=0):
			self.assertEqual(run_program(">", 0, limits=limits).status, Status.STEP_LIMIT)

	def test_trace_stops_at_same_resource_boundary(self):
		events = []
		limits = ExecutionLimits(max_output_bytes=1)
		actual = run_program("..", limits=limits, trace=events.append)
		self.assertEqual(actual, run_program("..", limits=limits))
		self.assertEqual(len(events), 1)
		self.assertEqual(events[-1].after, actual.state)

	def test_metrics_separate_bytes_cells_and_final_nonzero_cells(self):
		result = run_program("+>++<.")
		self.assertEqual(result.metrics, {"program_length": 6, "executed_steps": 6, "output_bytes": 1, "cells_visited": 2, "final_nonzero_cells": 2, "steps_per_command": 1, "output_bytes_per_command": 1 / 6})
		self.assertEqual(run_program("+-").metrics["final_nonzero_cells"], 0)
		self.assertEqual(run_program("").metrics["cells_visited"], 1)
		self.assertIsNone(run_program("").metrics["steps_per_command"])
		self.assertEqual(run_program("[").metrics, {})
		self.assertEqual(result_record(result)["output_bytes"], [1])

	def test_invalid_resource_configuration_is_rejected(self):
		for field, value in (("max_tape_cells", 0), ("max_output_bytes", -1), ("max_seen_states", True), ("max_state_bytes", 0.5), ("max_seconds", 0), ("max_seconds", float("nan")), ("max_seconds", float("inf"))):
			with self.subTest(field=field, value=value), self.assertRaises(ValueError):
				replace(ExecutionLimits(), **{field: value})
		with self.assertRaises(TypeError):
			run_program("+", limits={})


class EnumerationConfigTests(unittest.TestCase):
	def test_small_searches_have_exact_unique_coverage_and_rank_order(self):
		for length in range(1, 5):
			programs = list(enumerate_programs(length))
			self.assertEqual(len(set(programs)), 8 ** length)
			self.assertEqual(programs, [program_at_index(length, index) for index in range(8 ** length)])

	def test_length_seven_is_lazy_and_supports_direct_last_rank(self):
		programs = enumerate_programs(7)
		self.assertIs(iter(programs), programs)
		self.assertEqual(next(programs), ">>>>>>>")
		self.assertEqual(program_at_index(7, 8 ** 7 - 1), "]]]]]]]")

	def test_invalid_lengths_and_ranks_are_rejected(self):
		for length in (0, 8, True, 1.5):
			with self.assertRaises(ValueError):
				next(enumerate_programs(length))
		for index in (-1, 8, True):
			with self.assertRaises(ValueError):
				program_at_index(1, index)

	def test_config_round_trip_and_invalid_values(self):
		config = ExperimentConfig(lengths=(2, 4, 7), max_programs_per_length=None)
		self.assertEqual(ExperimentConfig.from_dict(config.to_dict()), config)
		for values in ({"lengths": []}, {"lengths": [4, 2]}, {"lengths": [2, 2]}, {"lengths": [8]}, {"max_programs_per_length": 0}, {"max_seconds": None}, {"max_steps": -1}, {"limits": {"max_tape_cells": 0}}, {"unknown": 1}):
			with self.subTest(values=values), self.assertRaises((ValueError, TypeError)):
				ExperimentConfig.from_dict(values)
