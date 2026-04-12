import math

commands = "><+-.,[]"


# -----------------------------
# Step 1: generate all programs
# -----------------------------
programs = []

for a in commands:
    for b in commands:
        for c in commands:
            for d in commands:
                program = a + b + c + d
                programs.append(program)


# --------------------------------
# Step 2: validate bracket syntax
# --------------------------------
def valid_brackets(program):
    count = 0

    for ch in program:
        if ch == "[":
            count = count + 1
        elif ch == "]":
            count = count - 1

        if count < 0:
            return False

    if count == 0:
        return True
    else:
        return False


valid_programs = []
invalid_programs = []

for program in programs:
    if valid_brackets(program):
        valid_programs.append(program)
    else:
        invalid_programs.append(program)


# -----------------------------------------
# Helpers for running Brainfuck programs
# -----------------------------------------
def find_matching_right(program, start):
    count = 1
    i = start + 1

    while i < len(program):
        if program[i] == "[":
            count = count + 1
        elif program[i] == "]":
            count = count - 1

        if count == 0:
            return i

        i = i + 1

    return -1


def find_matching_left(program, start):
    count = 1
    i = start - 1

    while i >= 0:
        if program[i] == "]":
            count = count + 1
        elif program[i] == "[":
            count = count - 1

        if count == 0:
            return i

        i = i - 1

    return -1


def same_tape(tape1, tape2):
    if len(tape1) != len(tape2):
        return False

    i = 0
    while i < len(tape1):
        if tape1[i] != tape2[i]:
            return False
        i = i + 1

    return True


def state_seen_before(seen_states, ip, pointer, tape, input_pos):
    i = 0

    while i < len(seen_states):
        old_ip = seen_states[i][0]
        old_pointer = seen_states[i][1]
        old_tape = seen_states[i][2]
        old_input_pos = seen_states[i][3]

        if old_ip == ip and old_pointer == pointer and old_input_pos == input_pos:
            if same_tape(old_tape, tape):
                return True

        i = i + 1

    return False


# --------------------------------
# Step 3 and Step 4: run programs
# with cycle detection
# --------------------------------
def run_program(program, max_steps):
    tape = [0]
    pointer = 0
    ip = 0
    steps = 0

    input_data = ""
    input_pos = 0
    output = ""

    seen_states = []

    while ip < len(program) and steps < max_steps:
        if state_seen_before(seen_states, ip, pointer, tape, input_pos):
            status = "cycle_detected"
            return status, steps, output, pointer, tape

        seen_states.append([ip, pointer, tape[:], input_pos])

        cmd = program[ip]

        if cmd == ">":
            pointer = pointer + 1
            if pointer == len(tape):
                tape.append(0)

        elif cmd == "<":
            if pointer > 0:
                pointer = pointer - 1

        elif cmd == "+":
            tape[pointer] = tape[pointer] + 1
            if tape[pointer] > 255:
                tape[pointer] = 0

        elif cmd == "-":
            tape[pointer] = tape[pointer] - 1
            if tape[pointer] < 0:
                tape[pointer] = 255

        elif cmd == ".":
            output = output + chr(tape[pointer])

        elif cmd == ",":
            if input_pos < len(input_data):
                tape[pointer] = ord(input_data[input_pos])
                input_pos = input_pos + 1
            else:
                tape[pointer] = 0

        elif cmd == "[":
            if tape[pointer] == 0:
                ip = find_matching_right(program, ip)

        elif cmd == "]":
            if tape[pointer] != 0:
                ip = find_matching_left(program, ip)

        ip = ip + 1
        steps = steps + 1

    if ip >= len(program):
        status = "halted"
    else:
        status = "step_limit"

    return status, steps, output, pointer, tape

# --------------------------------
# Trace one program step by step
# --------------------------------
def run_program_with_trace(program, max_steps):
    tape = [0]
    pointer = 0
    ip = 0
    steps = 0

    input_data = ""
    input_pos = 0
    output = ""

    print("\n====================================")
    print("Tracing program:", program)
    print("====================================")

    while ip < len(program) and steps < max_steps:
        cmd = program[ip]

        print("\nStep", steps + 1)
        print("Before:")
        print("  ip =", ip)
        print("  cmd =", cmd)
        print("  pointer =", pointer)
        print("  tape =", tape[:])
        print("  output =", repr(output))

        if cmd == ">":
            pointer = pointer + 1
            if pointer == len(tape):
                tape.append(0)

        elif cmd == "<":
            if pointer > 0:
                pointer = pointer - 1

        elif cmd == "+":
            tape[pointer] = tape[pointer] + 1
            if tape[pointer] > 255:
                tape[pointer] = 0

        elif cmd == "-":
            tape[pointer] = tape[pointer] - 1
            if tape[pointer] < 0:
                tape[pointer] = 255

        elif cmd == ".":
            output = output + chr(tape[pointer])

        elif cmd == ",":
            if input_pos < len(input_data):
                tape[pointer] = ord(input_data[input_pos])
                input_pos = input_pos + 1
            else:
                tape[pointer] = 0

        elif cmd == "[":
            if tape[pointer] == 0:
                ip = find_matching_right(program, ip)

        elif cmd == "]":
            if tape[pointer] != 0:
                ip = find_matching_left(program, ip)

        ip = ip + 1
        steps = steps + 1

        print("After:")
        print("  next ip =", ip)
        print("  pointer =", pointer)
        print("  tape =", tape[:])
        print("  output =", repr(output))

    if ip >= len(program):
        status = "halted"
    else:
        status = "step_limit"

    print("\nFinished")
    print("Status:", status)
    print("Total steps:", steps)
    print("Final pointer:", pointer)
    print("Final tape:", tape[:])
    print("Final output:", repr(output))


# -----------------------------
# Run all valid programs
# -----------------------------
max_steps = 100

halted_programs = []
cycle_programs = []
step_limit_programs = []
results = []

for program in valid_programs:
    status, steps, output, pointer, tape = run_program(program, max_steps)

    one_result = {}
    one_result["program"] = program
    one_result["status"] = status
    one_result["steps"] = steps
    one_result["output"] = output
    one_result["pointer"] = pointer
    one_result["tape"] = tape[:]

    results.append(one_result)

    if status == "halted":
        halted_programs.append(program)
    elif status == "cycle_detected":
        cycle_programs.append(program)
    else:
        step_limit_programs.append(program)


# --------------------------------
# Step 5: group repeated outcomes
# --------------------------------
def tape_to_text(tape):
    text = ""

    i = 0
    while i < len(tape):
        text = text + str(tape[i])
        if i < len(tape) - 1:
            text = text + ","
        i = i + 1

    return text


def make_signature(output, pointer, tape):
    signature = ""
    signature = signature + output
    signature = signature + "|"
    signature = signature + str(pointer)
    signature = signature + "|"
    signature = signature + tape_to_text(tape)
    return signature


outcome_groups = []

for item in results:
    if item["status"] == "halted":
        signature = make_signature(item["output"], item["pointer"], item["tape"])

        found_group = False
        i = 0

        while i < len(outcome_groups):
            if outcome_groups[i]["signature"] == signature:
                outcome_groups[i]["programs"].append(item["program"])
                found_group = True
                break
            i = i + 1

        if found_group == False:
            new_group = {}
            new_group["signature"] = signature
            new_group["programs"] = [item["program"]]
            new_group["representative"] = item["program"]
            new_group["output"] = item["output"]
            new_group["pointer"] = item["pointer"]
            new_group["tape"] = item["tape"][:]
            outcome_groups.append(new_group)


duplicate_program_count = 0

i = 0
while i < len(outcome_groups):
    duplicate_program_count = duplicate_program_count + (len(outcome_groups[i]["programs"]) - 1)
    i = i + 1


# --------------------------------
# Step 6: KC-aware summary
# --------------------------------
def serialize_outcome(output, pointer, tape):
    text = ""
    text = text + "OUT="
    text = text + repr(output)
    text = text + "|PTR="
    text = text + str(pointer)
    text = text + "|TAPE="
    text = text + tape_to_text(tape)
    return text


def shortest_program_in_list(program_list):
    shortest = program_list[0]

    i = 1
    while i < len(program_list):
        if len(program_list[i]) < len(shortest):
            shortest = program_list[i]
        i = i + 1

    return shortest


def guaranteed_lower_bound_bits(num_strings):
    b = 0

    while (2 ** b) - 1 < num_strings:
        b = b + 1

    return b - 1


def find_max_halted_steps(results):
    max_steps_seen = -1
    best_programs = []

    i = 0
    while i < len(results):
        if results[i]["status"] == "halted":
            s = results[i]["steps"]

            if s > max_steps_seen:
                max_steps_seen = s
                best_programs = [results[i]["program"]]
            elif s == max_steps_seen:
                best_programs.append(results[i]["program"])

        i = i + 1

    return max_steps_seen, best_programs

def find_min_halted_steps(results):
    min_steps_seen = None
    best_programs = []

    i = 0
    while i < len(results):
        if results[i]["status"] == "halted":
            s = results[i]["steps"]

            if min_steps_seen is None or s < min_steps_seen:
                min_steps_seen = s
                best_programs = [results[i]["program"]]
            elif s == min_steps_seen:
                best_programs.append(results[i]["program"])

        i = i + 1

    return min_steps_seen, best_programs


def find_biggest_unused_group_index(groups, used_indexes):
    biggest_index = -1
    biggest_size = -1

    i = 0
    while i < len(groups):
        already_used = False

        j = 0
        while j < len(used_indexes):
            if used_indexes[j] == i:
                already_used = True
                break
            j = j + 1

        if already_used == False:
            size = len(groups[i]["programs"])
            if size > biggest_size:
                biggest_size = size
                biggest_index = i

        i = i + 1

    return biggest_index


# Add KC-style data to each halted outcome group
i = 0
while i < len(outcome_groups):
    group_size = len(outcome_groups[i]["programs"])

    shortest_program = shortest_program_in_list(outcome_groups[i]["programs"])
    shortest_commands = len(shortest_program)

    # 8 Brainfuck commands = 3 bits per command
    shortest_bits = shortest_commands * 3

    halted_probability = group_size / len(halted_programs)
    kc_proxy_bits = -math.log2(halted_probability)

    outcome_string = serialize_outcome(
        outcome_groups[i]["output"],
        outcome_groups[i]["pointer"],
        outcome_groups[i]["tape"]
    )

    outcome_groups[i]["outcome_string"] = outcome_string
    outcome_groups[i]["group_size"] = group_size
    outcome_groups[i]["shortest_program"] = shortest_program
    outcome_groups[i]["shortest_commands"] = shortest_commands
    outcome_groups[i]["shortest_bits"] = shortest_bits
    outcome_groups[i]["halted_probability"] = halted_probability
    outcome_groups[i]["kc_proxy_bits"] = kc_proxy_bits

    i = i + 1


max_halted_steps, max_step_programs = find_max_halted_steps(results)

num_distinct_outcomes = len(outcome_groups)
kc_lower_bits = guaranteed_lower_bound_bits(num_distinct_outcomes)
at_least_this_many = num_distinct_outcomes - ((2 ** kc_lower_bits) - 1)

print("====================================")
print("BRAINFUCK LENGTH-4 EXPERIMENT REPORT")
print("====================================")

print("\n1. Search space")
print("Total programs:", len(programs))
print("Valid programs:", len(valid_programs))
print("Invalid programs:", len(invalid_programs))

print("\n2. Execution classification")
print("Halted programs:", len(halted_programs))
print("Cycle-detected programs:", len(cycle_programs))
print("Step-limit programs:", len(step_limit_programs))

print("\n3. Distinct halted outcomes")
print("Distinct halted outcomes:", len(outcome_groups))
print("Duplicate halted programs:", duplicate_program_count)

print("\n4. KC upper-bound layer")
print("Each halted outcome is converted into one exact string:")
print("OUT=<repr(output)>|PTR=<pointer>|TAPE=<comma-separated tape>")
print("Every halting Brainfuck witness gives an upper bound on that string's complexity.")
print("Shortest witness length is measured in Brainfuck commands and also in bits.")
print("Because 8 Brainfuck commands need 3 bits each,")
print("shortest_bits = 3 * shortest_commands.")

print("\n5. KC counting lower-bound layer")
print("Number of distinct halted outcome strings:", num_distinct_outcomes)
print("Guaranteed KC lower bound:", kc_lower_bits, "bits")
print("At least this many distinct outcomes have KC at least that large:", at_least_this_many)

print("\n6. Busy-beaver-style lower bound from the simulation")
print("Maximum halting steps actually observed:", max_halted_steps)
print("Witness programs:", max_step_programs)

print("\n7. Cycle-detected programs")
if len(cycle_programs) == 0:
    print("None")
else:
    i = 0
    while i < len(cycle_programs):
        print(cycle_programs[i])
        i = i + 1

print("\n8. Step-limit programs")
if len(step_limit_programs) == 0:
    print("None")
else:
    i = 0
    while i < len(step_limit_programs):
        print(step_limit_programs[i])
        i = i + 1

min_halted_steps, min_step_programs = find_min_halted_steps(results)

print("\n6a. Halting step statistics")
print("Minimum halting steps observed:", min_halted_steps)
print("Programs with minimum halting steps:", min_step_programs)

print("Maximum halting steps observed:", max_halted_steps)
#print("Programs with maximum halting steps:", max_step_programs)

"""
print("\n9. Top 10 most frequent halted outcomes")
used_indexes = []
top_count = 10

if len(outcome_groups) < 10:
    top_count = len(outcome_groups)

k = 0
while k < top_count:
    idx = find_biggest_unused_group_index(outcome_groups, used_indexes)

    if idx == -1:
        break

    used_indexes.append(idx)

    print("\nRank", k + 1)
    print("Representative:", outcome_groups[idx]["representative"])
    print("Group size:", outcome_groups[idx]["group_size"])
    print("Final pointer:", outcome_groups[idx]["pointer"])
    print("Final tape:", outcome_groups[idx]["tape"])
    print("Final output:", repr(outcome_groups[idx]["output"]))
    print("Shortest witness:", outcome_groups[idx]["shortest_program"])
    print("Shortest witness length (commands):", outcome_groups[idx]["shortest_commands"])
    print("Shortest witness length (bits):", outcome_groups[idx]["shortest_bits"])
    print("Empirical halted probability:", outcome_groups[idx]["halted_probability"])
    print("KC proxy bits = -log2(prob):", round(outcome_groups[idx]["kc_proxy_bits"], 4))
    print("Rigorous witness upper bound: K(x) <= shortest_bits + c_U")
    print("Programs:", outcome_groups[idx]["programs"])

    k = k + 1
    """
# --------------------------------
# Trace two programs with distinct outcomes
# --------------------------------
run_program_with_trace(">>>>", 100)
run_program_with_trace(">>>+", 100)