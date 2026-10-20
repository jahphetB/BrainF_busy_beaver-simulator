"""Create or verify a versioned research dataset."""

import argparse
import json
from pathlib import Path

from .config import ExperimentConfig
from .datasets import create_dataset, verify_dataset


def main(argv=None):
	parser = argparse.ArgumentParser(description=__doc__)
	commands = parser.add_subparsers(dest="command", required=True)
	run = commands.add_parser("run")
	run.add_argument("--config", type=Path, required=True)
	run.add_argument("--output", type=Path, required=True)
	verify = commands.add_parser("verify")
	verify.add_argument("directory", type=Path)
	args = parser.parse_args(argv)
	try:
		if args.command == "verify":
			print(json.dumps(verify_dataset(args.directory), indent="\t"))
		else:
			config = ExperimentConfig.from_dict(json.loads(args.config.read_text(encoding="utf-8")))
			report = create_dataset(config, args.output)
			print(f"Saved {args.output}; execution/export time {report['elapsed_seconds']:.3f}s")
			for row in report["lengths"]:
				print(f"n={row['length']} {row['coverage']} {row['metrics']}")
	except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
		parser.error(str(error))
	return 0
