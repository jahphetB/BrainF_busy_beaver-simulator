import unittest

from tests import ROOT
from scripts.analyze_phase3 import cycle_certificate, fresh_cell_growth_proof
from brainfuck_research.config import ExperimentConfig
from brainfuck_research.export import result_record
from brainfuck_research.interpreter import run_program


class EvidenceTests(unittest.TestCase):
	def test_runtime_records_match_modular_iteration_counts(self):
		for bits in (4, 8):
			modulus = 2 ** bits
			five = run_program("+[<+]", 4096, cell_bits=bits)
			six = run_program("+[<>+]", 4096, cell_bits=bits)
			self.assertEqual(five.state.steps, 2 + 3 * (modulus - 1))
			self.assertEqual(six.state.steps, 2 + 4 * modulus)
			self.assertEqual(six.state.tape, (1, 0))
			self.assertEqual(six.state.pointer, 1)

	def test_output_records_count_emitted_bytes_not_final_tape(self):
		for bits in (4, 8):
			modulus = 2 ** bits
			five = run_program("+[+.]", 4096, cell_bits=bits)
			six = run_program("+[+..]", 4096, cell_bits=bits)
			self.assertEqual(len(five.state.output), modulus - 1)
			self.assertEqual(len(six.state.output), 2 * (modulus - 1))
			self.assertEqual(five.state.tape, (0,))
			self.assertEqual(six.state.output, b"".join(bytes([value, value]) for value in five.state.output))

	def test_output_cycle_certificate_has_equal_control_states(self):
		record = result_record(run_program("+[.]", 512))
		certificate = cycle_certificate(record, ExperimentConfig(lengths=(4,)))
		self.assertEqual(certificate["first_seen_step"], 2)
		self.assertEqual(certificate["period"], 2)
		self.assertEqual(certificate["output_bytes_during_cycle"], [1])

	def test_forged_cycle_is_rejected(self):
		record = result_record(run_program("+[]", 512))
		record["cycle_period"] = 2
		with self.assertRaises(AssertionError):
			cycle_certificate(record, ExperimentConfig(lengths=(3,)))

	def test_structural_proof_is_restricted_to_its_exact_family(self):
		for program in ("+[>+]", "+[>-]", "-[>+]", "-[>-]"):
			for bits in (4, 8):
				self.assertIsNotNone(fresh_cell_growth_proof(program, bits))
		for program in ("+[+]", "+[>+<]", "+[>+]>", "+[>]"):
			self.assertIsNone(fresh_cell_growth_proof(program, 8))
		self.assertIsNone(fresh_cell_growth_proof("+[>+]", 1))
