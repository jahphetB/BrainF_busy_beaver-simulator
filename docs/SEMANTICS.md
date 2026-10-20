# Execution semantics: legacy-u8-right-v1

This is the primary research model, preserved from commit
`c86e07947ca2975375d199ae23cc18daa7f49122`. Changes to the model require a new
semantics identifier and separate experiments.

## Programs and initial state

- The alphabet, in enumeration order, is `><+-.,[]`. Length counts commands.
- The research API accepts only these characters and balanced, properly nested
  brackets. Invalid syntax is classified before any instruction executes.
- Arbitrary comments are not accepted by the research API. Any future editor
  that strips comments must explicitly distinguish source and command positions.
- Initially the instruction pointer, data pointer, input position, and step
  count are zero. The allocated tape contains one zero cell; output is empty.
- An empty program is valid and halts in zero steps.

## Instructions

| Command | Behavior |
| --- | --- |
| `>` | Move right; append a zero cell when entering a new position. |
| `<` | Move left unless already at zero, where it is a no-op. |
| `+` / `-` | Add/subtract one modulo 256. |
| `.` | Append the current cell as one output byte. |
| `,` | Consume one byte from fixed input; at EOF set the cell to zero without advancing input position. |
| `[` | If the cell is zero, continue after the matching `]`; otherwise continue to the next instruction. |
| `]` | If the cell is nonzero, continue after the matching `[`; otherwise continue to the next instruction. |

Every executed command costs one step, including brackets, EOF reads, and
left-boundary no-ops. Skipped commands cost no steps. In particular, `]` does
not re-execute `[`. There is no peephole optimization or collapsed loop counting.

Input and output use bytes, not UTF-8 character counts. JSON represents output
as integers from 0 through 255. The compatibility API uses Latin-1 to preserve
the original one-character-per-byte representation. Baseline experiments have
empty input; accepting supplied bytes is a tested API extension.

## Classification and precedence

1. Validate source before execution; invalid source is `syntactically_invalid`.
2. If the instruction pointer has left the program, classify `halted`.
3. If the executed instruction count equals the budget, classify `step_limit`.
4. Otherwise check for an exactly repeated execution state; classify
   `cycle_detected` if one is found, or execute the next instruction.

This preserves historical cutoff precedence: halting on the last permitted
step is recognized; a repeated state first reached at the cutoff is unresolved
until the budget permits checking it. No cycle check itself consumes a step.

The classifications mean proven halted, proven nonterminating by a repeated
state, unresolved after the step limit, and syntactically invalid, respectively.
Other resource limits and `resource_limit` classification belong to Phase 2;
Phase 1 does not pretend to enforce memory or wall-clock budgets.

## Repeated-state argument

For a fixed program and fixed input, the key is
`(instruction_pointer, data_pointer, allocated_tape, input_position)`.
The interpreter is deterministic and a repetition at a nonterminal instruction
therefore repeats future control behavior indefinitely. Output is append-only
and never read by the program, so it is deliberately absent from the key.
An output-producing loop can be proven nonterminating even as its output grows.
Recorded cycle start and period count executed instructions.

Exact tuple equality, not equality of a digest alone, establishes repetition.
Allocations and trailing zero cells remain in the state. This is conservative:
it can miss equivalent states but cannot invent a repetition. Programs with
unbounded tape growth need not repeat any key. Failure to find a cycle is not
proof of termination, and a step limit is not proof of nontermination.

## Halted outcome equivalence

Two halted programs share an outcome iff their output bytes, final data pointer,
and complete allocated tape are equal. Runtime and consumed-input count are
not part of this historical outcome key. Trailing zeros are retained: visiting
an extra cell can create a different outcome even after returning to zero.
No output-only or trimmed-tape equivalence is silently substituted.

## Independent 512-step check

`+[+]` starts at 1 and needs 255 additions modulo 256 to reach zero. `-[-]`
starts at 255 and needs 255 subtractions. Each loop iteration executes its
arithmetic command and `]`. Thus both execute `1 + 1 + 255 * 2 = 512`
instructions and halt with an empty output, pointer zero, and tape `[0]`.
At 511 steps the cell is already zero but the closing bracket has not executed.

## Reference

[Daniel B. Cristofani's Brainfuck reference](https://brainfuck.org/brainfuck.html)
describes the loop convention and byte I/O, and notes implementation variation
in overflow, boundaries, and EOF. Our left-boundary clamp, right-growing tape,
8-bit wrapping, and EOF-zero rule are explicit experimental choices.
