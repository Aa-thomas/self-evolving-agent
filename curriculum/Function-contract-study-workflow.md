# Bus Ride Function Contract Workflow

# 3-Pass Method for Function Contracts

Use this before coding a function from a lesson, reference, or contract.

The goal is simple:

```
Understand the contract → explain it from memory → turn it into code rules and tests.
```

---

## When to use this

Use this method when you are about to implement a function and you have a written contract, lesson, pseudocode, or reference.

Examples:

- `run_agent`
- `parse_tool_request`
- `validate_tool_args`
- `read_file`
- `write_file`
- `list_files`
- `run_command`

---

# Pass 1 — Compress

Read the contract once. Then reduce it into short jot notes.

Do not write full sentences. Do not copy the contract. Extract only the important parts.

## Template

```
Purpose:

Inputs:

Outputs:

Steps:

Rules/Invariants:

First test:
```

## Example

```
Purpose:
run the agent loop

Inputs:
user_task, model, tools, max_steps

Outputs:
AgentResult

Steps:
make messages → call model → parse → submit/execute/reject → append observation → repeat

Rules/Invariants:
model never executes tools
raw output is untrusted
submit stops
observations update messages
max_steps prevents infinite loop

First test:
test_submit_stops_loop
```

---

# Pass 2 — Reconstruct

Close the source.

Explain the function from memory in plain English. The goal is not perfect writing. The goal is to see whether you understand the function without looking.

## Template

```
This function starts by...

Then it...

If ___ happens, it...

It must never...

The first test proves...
```

## Example

```
run_agent starts by turning the user task into the first message.

Then it asks the model what to do next.

The model returns raw text, so the harness parses it.

If the model asks to submit, the loop stops and returns the answer.

It must never treat submit like a normal external tool.

The first test proves that submit stops the loop without calling read_file.
```

If you forget something, write a gap marker:

```
Fuzzy:
I need to check the exact message order.
```

Then reopen the source, check only the fuzzy part, and correct your note.

---

# Pass 3 — Convert into Code Rules

Turn your explanation into exact implementation rules before coding.

This pass answers:

```
What code am I about to write?
What code am I not writing yet?
What test proves this slice works?
```

## Template

```
Today’s slice:

Code must:
-
-
-

Code must not:
-
-
-

Proof:
```

## Example

```
Today’s slice:
make submit stop the loop

Code must:
- create initial messages from user_task
- call model.complete(messages)
- parse assistant output as JSON
- check if tool == "submit"
- get args["answer"]
- return exit_reason == "submitted"
- return final_answer == answer

Code must not:
- call read_file
- look up submit inside tools
- continue looping after submit
- build trace logging yet
- handle every invalid case yet

Proof:
test_submit_stops_loop passes
```

---

# The 3-Pass Method in One Screen

```
PASS 1 — COMPRESS
Purpose:
Inputs:
Outputs:
Steps:
Rules:
First test:

PASS 2 — RECONSTRUCT
This function starts by...
Then it...
If ___ happens...
It must never...
The first test proves...
Fuzzy:

PASS 3 — CODE RULES
Today’s slice:
Code must:
Code must not:
Proof:
```

---

# Phone Version

Use this on the bus when you want the shortest possible version.

```
Function:

Pass 1 — Compress:
Purpose:
Inputs:
Output:
Steps:
Rules:
Test:

Pass 2 — Memory:
In my own words:
Fuzzy:

Pass 3 — Code Rules:
Today I will code:
Must do:
Must not do:
Proof:
```

---

# Rule of Thumb

You are ready to code when you can answer these three questions:

```
1. What is the function responsible for?
2. What must it never do?
3. What test proves the current slice works?
```

If you cannot answer those yet, do another Pass 2 before coding.
