"""Baseline enumeration, preserving the original alphabet order."""

from itertools import product
from math import comb

from .syntax import COMMANDS
from .config import validate_integer


def length_four_programs():
	"""Yield all 4096 candidates, including invalid strings."""
	return enumerate_programs(4)


def enumerate_programs(length: int):
	"""Lazily yield exact-length source, without materializing the search space."""
	validate_integer("length", length, 1, 7)
	for commands in product(COMMANDS, repeat=length):
		yield "".join(commands)


def program_at_index(length: int, index: int) -> str:
	"""Decode an enumeration rank directly, for reproducible benchmark sampling."""
	validate_integer("length", length, 1, 7)
	validate_integer("index", index, 0, 8 ** length - 1)
	characters = [COMMANDS[0]] * length
	for position in range(length - 1, -1, -1):
		index, remainder = divmod(index, 8)
		characters[position] = COMMANDS[remainder]
	return "".join(characters)


def valid_program_count(length: int) -> int:
	"""Choose bracket positions, a balanced Catalan word, and six other commands."""
	validate_integer("length", length, 1, 7)
	return sum(comb(length, 2 * pairs) * (comb(2 * pairs, pairs) // (pairs + 1)) * 6 ** (length - 2 * pairs) for pairs in range(length // 2 + 1))
