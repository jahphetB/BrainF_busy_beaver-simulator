import json
import subprocess
import sys
import unittest

from tests import ROOT


class CommandLineTests(unittest.TestCase):
	def invoke(self, *args):
		return subprocess.run([sys.executable, "-B", str(ROOT / "generate.py"), *args], cwd=ROOT, capture_output=True, text=True, check=False)

	def test_import_has_no_execution_or_output(self):
		result = subprocess.run([sys.executable, "-B", "-c", "import generate; assert not hasattr(generate, 'results'); assert generate.run_program('+[+]', 512) == ('halted', 512, '', 0, [0])"], cwd=ROOT, capture_output=True, text=True)
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(result.stdout, "")
		self.assertEqual(result.stderr, "")

	def test_default_command_preserves_historical_budget(self):
		result = self.invoke()
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertIn("max_steps=100", result.stdout)
		self.assertIn("halted: 1482", result.stdout)
		self.assertIn("step_limit: 2", result.stdout)

	def test_json_command_is_parseable_and_identifies_semantics(self):
		result = self.invoke("--max-steps", "512", "--json")
		self.assertEqual(result.returncode, 0, result.stderr)
		report = json.loads(result.stdout)
		self.assertEqual(report["semantics_id"], "legacy-u8-right-v1")
		self.assertEqual(report["summary"]["maximum_step_programs"], ["+[+]", "-[-]"])

	def test_trace_accepts_bytes_and_uses_common_semantics(self):
		result = self.invoke("--trace", ",.", "--input-hex", "ff")
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertIn("Step 2:", result.stdout)
		self.assertIn('"status": "halted"', result.stdout)
		self.assertIn("255", result.stdout)

	def test_invalid_trace_exits_unsuccessfully(self):
		result = self.invoke("--trace", "]")
		self.assertEqual(result.returncode, 2)
		self.assertIn("syntactically_invalid", result.stdout)

	def test_invalid_options_are_rejected(self):
		for args in (("--max-steps", "-1"), ("--input-hex", "ff"), ("--trace", ",", "--input-hex", "zz"), ("--trace", "+", "--json")):
			with self.subTest(args=args):
				result = self.invoke(*args)
				self.assertEqual(result.returncode, 2)
				self.assertIn("error:", result.stderr)
