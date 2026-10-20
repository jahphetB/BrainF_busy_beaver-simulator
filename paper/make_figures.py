"""Rebuild publication figures and descriptive statistics from audited data."""

import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
DATA = ROOT / "data/analysis/v1"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv/matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import MaxNLocator


def read_csv(name):
	with (DATA / name).open(newline="", encoding="utf-8") as stream:
		return list(csv.DictReader(stream))


def main():
	manifest = json.loads((DATA / "manifest.json").read_text())
	for name in ("summary.csv", "runtime-output.csv"):
		actual = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
		if actual != manifest["artifacts"][name]["sha256"]:
			raise ValueError(f"Audited input changed: {name}")
	rows = read_csv("summary.csv")
	pairs = read_csv("runtime-output.csv")
	for row in rows:
		for key in ("length", "halted", "cycle_detected", "U", "evaluated", "T", "O", "M", "D"):
			row[key] = int(row[key])
	for row in pairs:
		for key in ("length", "steps", "output_bytes", "halted_programs"):
			row[key] = int(row[key])

	primary = [row for row in rows if row["run"].startswith("primary")]
	high = [row for row in rows if row["run"] == "steps4096-n4-6"]
	cell4 = [row for row in rows if row["run"] == "cell4-n4-6-s4096"]
	best = primary[:3] + high
	output = PAPER / "figures"
	output.mkdir(parents=True, exist_ok=True)
	plt.rcParams.update({
		"font.family": "DejaVu Sans", "font.size": 9,
		"axes.spines.top": False, "axes.spines.right": False,
		"axes.titleweight": "bold", "axes.labelcolor": "#253247",
		"axes.edgecolor": "#6b7280", "grid.alpha": 0.18,
		"svg.hashsalt": "brainfuck-phase4-v1", "pdf.fonttype": 42,
	})

	def save(fig, name):
		for suffix in ("svg", "pdf", "png"):
			metadata = {"Date": None} if suffix == "svg" else (
				{"CreationDate": None, "ModDate": None} if suffix == "pdf" else {}
			)
			fig.savefig(output / f"{name}.{suffix}", dpi=300, metadata=metadata)
			if suffix == "svg":
				path = output / f"{name}.{suffix}"
				path.write_text("\n".join(line.rstrip() for line in
					path.read_text(encoding="utf-8").splitlines()) + "\n",
					encoding="utf-8", newline="\n")
		plt.close(fig)

	fig, axes = plt.subplots(1, 2, figsize=(7, 3.15), layout="constrained")
	for ax, key, title, ylabel in zip(axes, ("T", "O"),
		("A  Observed halting runtime", "B  Observed halting output"),
		("Maximum instructions (log scale)", "Maximum output bytes (log scale)")):
		for group, label, color, marker, style in (
			(primary, "8-bit / 512 steps", "#0072B2", "o", "-"),
			(high, "8-bit / 4096 steps", "#D55E00", "s", "--"),
			(cell4, "4-bit / 4096 steps", "#009E73", "^", ":"),
		):
			ax.plot([r["length"] for r in group], [r[key] for r in group],
				label=label, color=color, marker=marker, linestyle=style, markersize=5)
		ax.set(title=title, xlabel="Source length (commands)", ylabel=ylabel, yscale="log")
		ax.set_xticks(range(1, 7))
		ax.grid(axis="y")
	axes[0].legend(fontsize=7, loc="upper left")
	save(fig, "01-records")

	fig, axes = plt.subplots(1, 2, figsize=(7, 3.15), layout="constrained")
	for ax, n in zip(axes, (5, 6)):
		group = [r for r in pairs if r["run"] == "steps4096-n4-6" and r["length"] == n]
		plot = ax.scatter([r["steps"] for r in group], [r["output_bytes"] for r in group],
			c=[r["halted_programs"] for r in group], norm=LogNorm(1, 50000),
			s=28, cmap="viridis", edgecolors="#ffffff", linewidths=0.3)
		ax.set(xscale="symlog", yscale="symlog",
			xlabel="Instructions (symlog; linear within +/-1)",
			ylabel="Output bytes (symlog; linear within +/-1)",
			title=f"{'A' if n == 5 else 'B'}  Length {n}, 8-bit / 4096 steps")
		ax.grid()
	fig.colorbar(plot, ax=axes, label="Halted programs at each pair", shrink=0.88)
	save(fig, "02-runtime-output")

	fig, axes = plt.subplots(1, 2, figsize=(7, 2.85), layout="constrained")
	ns = [r["length"] for r in best]
	axes[0].plot(ns, [r["M"] for r in best], "o-", color="#0072B2")
	axes[0].set(title="A  Memory visitation", xlabel="Source length (commands)",
		ylabel="Maximum visited cells among halted")
	axes[0].yaxis.set_major_locator(MaxNLocator(integer=True))
	axes[1].plot(ns, [r["D"] for r in best], "s-", color="#D55E00")
	axes[1].set(title="B  Distinct halted outcomes", xlabel="Source length (commands)",
		ylabel="Outcome count D (log scale)", yscale="log")
	for ax in axes:
		ax.set_xticks(ns)
		ax.grid(axis="y")
	save(fig, "03-memory-outcomes")

	statistics = []
	for row in rows:
		group = [p for p in pairs if p["run"] == row["run"] and p["length"] == row["length"]]
		if sum(p["halted_programs"] for p in group) != row["halted"]:
			raise ValueError("Distribution count does not match summary")
		for key, metric in (("steps", "T"), ("output_bytes", "O")):
			if max(p[key] for p in group) != row[metric]:
				raise ValueError("Distribution maximum does not match summary")
		within_n = sum(p["halted_programs"] for p in group if p["steps"] <= row["length"])
		zero_output = sum(p["halted_programs"] for p in group if p["output_bytes"] == 0)
		statistics.append({
			"run": row["run"], "length": row["length"], "halted": row["halted"],
			"halted_within_n_steps": within_n,
			"halted_within_n_steps_percent": round(100 * within_n / row["halted"], 4),
			"halted_with_zero_output": zero_output,
			"distinct_outcomes": row["D"],
			"halted_programs_per_outcome": round(row["halted"] / row["D"], 4),
		})
	(PAPER / "statistics.json").write_text(json.dumps({
		"scope": "Descriptive counts conditional on observed halting; no sampling inference.",
		"input_sha256": {name: manifest["artifacts"][name]["sha256"]
			for name in ("summary.csv", "runtime-output.csv")},
		"rows": statistics,
	}, indent="\t") + "\n", encoding="utf-8", newline="\n")
	print("Verified 12 distribution totals and maxima; wrote 3 figures in SVG/PDF/PNG.")


if __name__ == "__main__":
	main()
