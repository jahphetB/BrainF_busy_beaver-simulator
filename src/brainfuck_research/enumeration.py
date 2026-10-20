"""Baseline enumeration, preserving the original alphabet order."""

from itertools import product

from .syntax import COMMANDS


def length_four_programs():
	"""Yield all 4096 candidates, including invalid strings."""
	for commands in product(COMMANDS, repeat=4):
		yield "".join(commands)
