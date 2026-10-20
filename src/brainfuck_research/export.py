"""JSON-safe baseline summaries and execution records."""

from . import SEMANTICS_ID, __version__
from .analysis import summarize
from .config import BaselineConfig
from .models import ExecutionResult, State
from .syntax import COMMANDS


def state_record(state: State) -> dict:
	return {
		"ip": state.ip,
		"pointer": state.pointer,
		"tape": list(state.tape),
		"input_pos": state.input_pos,
		"output_bytes": list(state.output),
		"steps": state.steps,
	}


def result_record(result: ExecutionResult) -> dict:
	return {
		"program": result.program,
		"status": result.status.value,
		**state_record(result.state),
		"cycle_start": result.cycle_start,
		"cycle_period": result.cycle_period,
		"error": result.error,
	}


def baseline_report(config: BaselineConfig, results) -> dict:
	return {
		"schema_version": 1,
		"engine_version": __version__,
		"semantics_id": SEMANTICS_ID,
		"config": {"program_length": 4, "alphabet": COMMANDS, "input_bytes": [], "max_steps": config.max_steps},
		"summary": summarize(results),
	}
