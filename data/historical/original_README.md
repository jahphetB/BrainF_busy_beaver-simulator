# BrainF Busy Beaver Simulator

A research Python project that explores **all Brainfuck programs of length 4**, classifies their behavior, filters invalid programs, detects cycles, groups duplicate outcomes, and connects the results to a simple **Kolmogorov complexity** argument.

## Overview

This project is a **finite Busy Beaver experiment** on Brainfuck.

Instead of studying all possible Turing machines, this project studies all possible **Brainfuck strings of length 4** over the 8 Brainfuck commands:

```text
><+-.,[]
```

Since there are 8 commands and the program length is 4, the total search space is:

```text
8^4 = 4096 programs
```

The simulator:

- generates all length-4 programs
- filters out syntactically invalid programs
- runs valid programs with a Brainfuck interpreter
- detects halting, cycles, and step-limit cases
- groups programs by their final halted outcome
- uses the results to make a simple Kolmogorov complexity observation

## What this project does

### 1. Generate all programs of length 4
Every possible string of length 4 over the Brainfuck alphabet is generated.

### 2. Filter invalid programs
Programs with unmatched `[` or `]` are rejected before execution.

### 3. Execute valid programs
Valid programs are run with a simple Brainfuck interpreter.

The interpreter tracks:

- instruction pointer
- data pointer
- tape contents
- output
- execution steps

### 4. Detect non-halting behavior
The simulator uses **cycle detection** by storing previously seen execution states.

A state includes enough information to tell whether the program has returned to the same situation again. If the same state appears again, the program is classified as cycling.

### 5. Group equivalent halted outcomes
Different programs may halt with the **same final result**.

A halted outcome is encoded using:

```text
OUT=<repr(output)>|PTR=<pointer>|TAPE=<comma-separated tape>
```

This makes it possible to count:

- how many halted programs are unique
- how many are duplicates of another halted outcome

### 6. Connect outcomes to Kolmogorov complexity
For each halted outcome, we can view a shortest halting Brainfuck program as a **description** of that outcome.

Because Brainfuck has 8 commands, each command can be encoded in:

```text
3 bits
```

So a halting witness program of length 4 gives an upper bound of:

```text
4 × 3 = 12 bits
```

for the description length of its outcome, up to a fixed additive constant.

We also use a counting argument from the number of distinct halted outcomes to get a simple lower-bound observation.

## Main results

### Search space
- Total programs: **4096**
- Valid programs: **1514**
- Invalid programs: **2582**

### Execution classification
- Halted programs: **1482**
- Cycle-detected programs: **30**
- Step-limit programs: **2**

### Halted outcome analysis
- Distinct halted outcomes: **228**
- Duplicate halted programs: **1254**

### Step behavior
- Maximum halting steps observed: **4**

## Kolmogorov complexity connection

This project does **not** compute exact Kolmogorov complexity, because exact KC is uncomputable in general.

What it does provide is:

### Upper-bound idea
If an outcome is produced by a halting Brainfuck program of length 4, then that outcome has a description of at most:

```text
12 bits + constant
```

because each of the 4 commands can be encoded with 3 bits.

### Lower-bound idea
Since there are **228 distinct halted outcomes**, at least some outcomes must require about:

```text
log2(228) ≈ 7 bits
```

to distinguish them by counting alone.

So, in this finite experiment, we can confidently say:

- some outcomes have a short description via a halting program
- the shortest description is at most 12 bits for outcomes witnessed by length-4 programs
- the number of distinct outcomes gives a simple counting-based lower bound of about 7 bits

## Why cycle detection matters

Cycle detection is important because some programs never halt.

Without cycle detection, the simulator could keep running forever on looping programs.

Cycle detection lets us:

- recognize repeated execution states
- stop infinite repetition safely
- separate halting behavior from non-halting behavior
- make the search over all programs practical

## Project structure

This project includes code for:

- cleaning/filtering Brainfuck commands
- matching brackets
- interpreting Brainfuck programs
- generating all length-4 programs
- classifying execution behavior
- grouping equivalent halted outcomes
- summarizing the final statistics

## Core functions

Core logic includes functions such as:

- `clean_program(program)`
- `build_bracket_map(program)`
- `run_brainfuck(...)`

and a simulation script that generates and analyzes all length-4 programs.

## How to run

Run the main simulation script:

```bash
python generate.py
```

This prints summary statistics such as:

- total programs
- valid and invalid counts
- halted / cycle / step-limit counts
- number of distinct halted outcomes
- duplicate outcomes

## What this project is useful for

This project is useful as a small computational experiment in:

- computability
- small-program behavior
- halting vs looping classification
- state-based cycle detection
- finite approximations to Busy Beaver–style questions
- simple Kolmogorov complexity reasoning

## Limitations

This is a **finite experimental study**, not a full Busy Beaver solution.

In particular:

- it only studies Brainfuck programs of length 4
- exact Kolmogorov complexity is not computed
- step-limit cases are only bounded experimentally
- results depend on the chosen execution model and outcome encoding

## Future improvements

Possible next steps:

- test longer program lengths
- compare behavior across different lengths
- record full execution traces automatically
- visualize outcome families
- study shortest witnesses for each halted outcome
- tighten finite upper/lower bound arguments

## Summary

This project built a complete simulator for all Brainfuck strings of length 4, filtered invalid programs, detected cycles, classified execution behavior, grouped duplicate halted outcomes, and connected the resulting finite outcome set to a simple Kolmogorov complexity argument.

Final headline numbers:

- **4096** total programs
- **1514** valid programs
- **1482** halted
- **30** cycle-detected
- **2** step-limit
- **228** distinct halted outcomes