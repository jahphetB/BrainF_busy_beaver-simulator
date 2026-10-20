"""Strict research syntax; comments are not silently counted as commands."""

COMMANDS = "><+-.,[]"


class ProgramSyntaxError(ValueError):
	pass


def build_bracket_map(program: str) -> dict[int, int]:
	if not isinstance(program, str):
		raise TypeError("program must be a string")
	stack = []
	brackets = {}
	for position, command in enumerate(program):
		if command not in COMMANDS:
			raise ProgramSyntaxError(f"Non-command character at position {position}: {command!r}")
		if command == "[":
			stack.append(position)
		elif command == "]":
			if not stack:
				raise ProgramSyntaxError(f"Unmatched ] at position {position}")
			opening = stack.pop()
			brackets[opening] = position
			brackets[position] = opening
	if stack:
		raise ProgramSyntaxError(f"Unmatched [ at position {stack[-1]}")
	return brackets


def valid_brackets(program: str) -> bool:
	"""Validate command-only research source."""
	try:
		build_bracket_map(program)
	except ProgramSyntaxError:
		return False
	return True
