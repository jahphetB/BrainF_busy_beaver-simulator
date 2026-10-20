"""Finite Brainfuck research with explicit execution semantics."""

from .interpreter import run_program
from .models import ExecutionResult, Status

__version__ = "0.2.0"
SEMANTICS_ID = "legacy-u8-right-v1"

__all__ = ["ExecutionResult", "Status", "run_program"]
