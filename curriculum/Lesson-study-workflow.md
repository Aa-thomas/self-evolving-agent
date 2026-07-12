# Lesson Study Workflow

## Purpose

This document is a repeatable workflow for studying Project 1A lessons before coding.

The goal is not to create perfect notes. The goal is to prove understanding before touching the code, then turn that understanding into tests, implementation, private logs, and eventually public writing.

Use this process when learning any Project 1A primitive, especially:

- model calls
- message state
- tool request parsing
- tool validation
- sandboxed file tools
- the agent loop
- trace logging
- eval running

## Core Principle

Do not copy the lesson into your notes.

Convert the lesson into:

1. fragments,
2. memory-based explanation,
3. concrete examples,
4. code proof,
5. post-coding evidence.

The final goal is not just to understand the concept. The final goal is to create a runnable proof: a test, trace, eval, failure note, or working code slice.

---

# The Four-Pass Method

## Pass 1 — Extract

Read the lesson once and extract only the important ideas.

Do not write full sentences yet.

Use fragments only.

Example:

```
model ≠ executor
harness = judge + executor
messages = state
submit = internal stop
tool result = observation
max_steps = safety brake
```

Fragments prevent copying because they force you to rebuild the idea later in your own structure.

## Pass 2 — Close the Source

After reading, close the lesson.

Do not look at the original text while writing your explanation.

This matters because if the original wording is still visible, you will probably copy its structure.

## Pass 3 — Explain From Memory

Write a rough explanation from memory.

Use simple language.

Pretend you are explaining the concept to someone who understands basic programming but has never built an agent loop.

Use this format:

```
I think this means:

Tiny example:

Why it matters:

Where I might be wrong:

Code proof:
```

## Pass 4 — Check and Correct

Reopen the lesson.

Compare your explanation against the source.

Do not rewrite everything.

Only correct what is wrong, missing, or unclear.

Mark corrections like this:

```
Correction:
I forgot that the assistant message should also be appended to messages before the next step.
```

---

# Phone-Friendly Lesson Note Template

Create one note per lesson.

Use this title format:

```
Project 1A — <Lesson Name> — Bus Notes
```

Example:

```
Project 1A — Agent Loop — Bus Notes
```

Then use this template:

```markdown
# Project 1A — <Lesson Name> — Bus Notes

## 1. What is the thing?

## 2. What problem does it solve?

## 3. What are the moving parts?

## 4. What must never happen?

## 5. What test proves I understand it?

## 6. What am I about to code?

## 7. What still feels fuzzy?

## 8. Correction after checking the source

## 9. Post-coding evidence note

## 10. Possible public writing angle
```

---

# Example: Agent Loop Bus Notes

```markdown
# Project 1A — Agent Loop — Bus Notes

## 1. What is the thing?

The agent loop is the harness control flow that keeps asking the model what to do next, then decides what to do with the model's output.

## 2. What problem does it solve?

The model only returns text. It does not execute code. The harness needs a loop that can read the model's text, parse it, validate it, execute allowed tools, reject bad requests, or stop when the model submits an answer.

## 3. What are the moving parts?

- user task becomes first message
- model.complete(messages)
- assistant output is raw text
- parse raw text as JSON
- validate tool request shape
- if submit, stop
- if invalid, reject
- if known tool, execute
- append observation
- continue until submit or max_steps

## 4. What must never happen?

- the model must not execute tools directly
- raw assistant text must not be trusted automatically
- submit must not be treated like an external tool
- invalid JSON must not crash the whole loop
- the loop must not run forever

## 5. What test proves I understand it?

`test_submit_stops_loop`

It proves that when the model returns:

```json
{"tool": "submit", "args": {"answer": "done"}}
```

then `run_agent` should:

- call the model once
- not execute `read_file`
- return `exit_reason == "submitted"`
- return `final_answer == "done"`

## 6. What am I about to code?

I am about to make `run_agent` handle the smallest useful loop slice:

- create initial messages
- call the model
- parse the assistant output
- detect `submit`
- return a submitted result

## 7. What still feels fuzzy?

I need to confirm whether I should append the assistant message before or after parsing.

## 8. Correction after checking the source

The minimal algorithm appends the assistant message to messages, then parses and validates the request. The tool result or rejection gets appended as a tool observation before the next model call.

## 9. Post-coding evidence note

What I built:
I made `run_agent` stop when the model returns a submit request.

What failed:
At first I was tempted to treat `submit` like a normal tool, but it should be handled internally by the harness.

What I misunderstood:
The model is not choosing executable behavior directly. It is proposing structured text that the harness must interpret.

What test now proves it:
`test_submit_stops_loop` proves the model is called once, `read_file` is not called, `exit_reason` is `submitted`, and `final_answer` is `done`.

## 10. Possible public writing angle

The model does not use tools. The harness does.

The model proposes an action. The harness validates, executes, rejects, observes, or stops.

```

---

# The Feynman Template

Use this when a concept feels fuzzy.

```markdown
# Feynman Explanation — <Concept>

## Concept

## My plain-English explanation

## Tiny example

## Why this matters in the harness

## What would break if I misunderstood this?

## The test or artifact that proves it

## My current uncertainty

## Correction after checking
```

## Example

```markdown
# Feynman Explanation — submit

## Concept

`submit` in the agent loop.

## My plain-English explanation

`submit` is how the model says the task is finished. It looks like a tool request, but the harness handles it internally. It should not be looked up in the external tools dictionary.

## Tiny example

If the model returns:

```json
{"tool": "submit", "args": {"answer": "done"}}
```

then the loop should stop and return `done`.

## Why this matters in the harness

If `submit` is treated like a normal tool, the harness might try to execute something that should only be a stop signal.

## What would break if I misunderstood this?

The loop might call tools when it should stop, or it might reject a valid final answer as an unknown tool.

## The test or artifact that proves it

`test_submit_stops_loop`

## My current uncertainty

Should the loop append the assistant output before returning?

## Correction after checking

The reference algorithm appends the assistant output before parsing, but for the first narrow test, the key behavior is that `submit` stops the loop and no external tool is called.

```

---

# Anti-Copying Rules

## Rule 1 — No full sentences during extraction

Bad:

```text
The model requests and the harness validates, executes or rejects, records an observation, and decides whether to continue.
```

Better:

```
model requests
harness validates
execute / reject / stop
observation added
continue?
```

## Rule 2 — Use a different structure than the lesson

If the lesson explains the concept as a numbered list, explain it as an analogy.

If the lesson explains it abstractly, explain it with one concrete test.

If the lesson explains it with code, explain it with a real-world metaphor.

## Rule 3 — Use one analogy

For the agent loop:

```
The model is like a worker filling out request forms.
The harness is the supervisor.
The supervisor checks the form, decides whether it is allowed, performs the action through approved systems, writes down what happened, and gives that result back to the worker.
submit is not another errand. It means the worker is done.
```

Other analogy options:

```
Restaurant:
model = customer order
harness = kitchen plus rules
tools = approved kitchen stations
observation = result returned
submit = meal complete
```

```
Video game:
model = player input
harness = game engine
tools = allowed actions
messages = game state
max_steps = turn limit
submit = finish level
```

## Rule 4 — Force yourself to answer from memory

Before checking the lesson again, answer:

```
What is this?
Why does it exist?
What are the parts?
What breaks if I get it wrong?
What test proves it?
```

---

# Before-Coding Checklist

Use this before opening your editor.

```markdown
# Before Coding Checklist

## Concept

## In one sentence, what am I building?

## What is the smallest passing test?

## What behavior should happen?

## What behavior should not happen?

## What inputs matter?

## What output/result should exist?

## What is out of scope right now?
```

## Example: `test_submit_stops_loop`

```markdown
# Before Coding Checklist

## Concept

Agent loop stop condition.

## In one sentence, what am I building?

I am making the loop stop when the model returns a valid `submit` request.

## What is the smallest passing test?

`test_submit_stops_loop`

## What behavior should happen?

- call model once
- parse assistant output
- detect submit
- return submitted result
- final answer is `done`

## What behavior should not happen?

- do not call `read_file`
- do not continue the loop
- do not treat `submit` as unknown tool
- do not add tracing or extra abstractions yet

## What inputs matter?

User task, fake model response, tools dictionary, max_steps.

## What output/result should exist?

An `AgentResult` with:

- `exit_reason == "submitted"`
- `final_answer == "done"`

## What is out of scope right now?

- tool execution
- invalid JSON handling
- unknown tool rejection
- max_steps result
- trace logging
- eval runner
```

---

# After-Coding Evidence Note

Use this after each coding session.

```markdown
# After-Coding Evidence Note

## What I built

## What failed

## What I misunderstood

## What test now proves it

## What changed in my mental model

## What should I do next
```

## Example

```markdown
# After-Coding Evidence Note

## What I built

I made `run_agent` stop when the model returns a valid `submit` request.

## What failed

I initially thought of `submit` as another tool-like action, but it should not be executed through the external tools dictionary.

## What I misunderstood

The model does not directly control the program. It produces text. The harness turns that text into a decision.

## What test now proves it

`test_submit_stops_loop` proves the model is called once, no file tool is called, and the loop returns a submitted result with the final answer.

## What changed in my mental model

The agent loop is not magic. It is just controlled request handling around untrusted model output.

## What should I do next

Add the next narrow behavior: invalid request rejection or max_steps exit.
```

---

# Bus Ride Routine

## Morning Bus — Before Coding

Use this when traveling to work.

```
1. Read one lesson section for 3–5 minutes.
2. Close the lesson.
3. Write fragment notes only.
4. Explain the concept from memory.
5. Write the smallest test target.
6. Write one fuzzy question.
```

Do not try to finish the whole lesson.

The goal is to arrive with one clear coding target.

## Evening Bus — After Coding

Use this when traveling home.

```
1. Write what changed in the code.
2. Write what broke or confused you.
3. Write what the passing test proves.
4. Write what the next test should be.
5. Write one possible public post angle.
```

The goal is to convert the coding session into durable understanding.

---

# Concept Dictionary

Keep a permanent note with short definitions.

Each definition must be one sentence max.

```markdown
# Project 1A Concept Dictionary

## Agent loop

The harness control flow that repeatedly asks the model for the next action, validates the output, executes or rejects tools, records observations, and stops when done.

## Model

The component that returns text based on the current messages.

## Harness

The software system around the model that controls validation, execution, observations, state, safety, and stopping.

## Messages

The state passed back to the model so it can react to the user task, previous assistant outputs, and tool observations.

## Tool request

A structured action request produced by the model, usually as JSON.

## Tool

A real function controlled by the harness, not by the model directly.

## Observation

The result of a tool execution or rejection appended back into messages.

## submit

An internal stop signal that tells the harness to return a final answer.

## max_steps

A loop limit that prevents the agent from running forever.

## Trace

A saved causal record of what happened during a run.

## Eval

A repeatable task used to test whether the harness behaves correctly.
```

Update this dictionary as your understanding improves.

---

# Turning Notes Into Public Writing

Do not write public content first.

Use this sequence:

```
lesson notes
→ code attempt
→ failing test or confusion
→ fix
→ passing proof
→ evidence note
→ public post
```

Public writing should come from evidence, not from claims.

## Public Post Template

```markdown
# Public Field Note Draft

I used to think:

What changed:

The test/code that proved it:

The actual lesson:

Why this matters for AI agents:

What I am building next:
```

## Example Public Post

```markdown
I used to think an AI agent “uses tools.”

That phrasing hides the most important part.

In my tiny agent loop, the model never executes anything. It only returns text like:

```json
{"tool": "submit", "args": {"answer": "done"}}
```

The harness decides what that text means.

Today’s test was small but important: when the model asks to submit, the loop must stop. It must not call `read_file`, `write_file`, or any external tool.

That one test clarified the control boundary:

```
model proposes
harness validates
harness executes or rejects
messages record what happened
the loop continues or stops
```

The lesson: agent reliability starts where model output stops being trusted.

```

---

# Weekly Review

At the end of each week, review your notes and answer:

```markdown
# Weekly Project 1A Review

## What concepts became clearer this week?

## What tests did I make pass?

## What did I misunderstand at first?

## What failure taught me the most?

## What concept can I now explain without notes?

## What concept still feels weak?

## What should I rebuild from memory?

## What public artifact could come from this week?
```

---

# Definition of a Successful Study Session

A study session is successful if it produces at least one of these:

- a clearer explanation
- a passing test
- a failing test that reveals the next step
- a correction to your mental model
- a private evidence note
- a concept dictionary update
- a public post angle

A session is not successful just because you reread the lesson.

Reading must turn into proof.

---

# Minimum Viable Bus Ride

When tired, do only this:

```
1. One concept
2. Five fragment notes
3. One plain-English explanation
4. One test target
5. One fuzzy question
```

Example:

```
Concept:
submit

Fragments:
stop signal
internal
not external tool
returns final answer
proves loop can end

Explanation:
submit is how the model tells the harness the task is done. The harness should return the answer instead of calling a tool.

Test:
test_submit_stops_loop

Fuzzy question:
Should submit still appear in the trace later?
```

This is enough to keep momentum.

---

# Master Checklist

Before coding a Project 1A slice, confirm:

```markdown
- [ ] I can name the concept.
- [ ] I can explain the problem it solves.
- [ ] I can list the moving parts.
- [ ] I can say what must never happen.
- [ ] I know the smallest test.
- [ ] I know what is out of scope.
- [ ] I have one fuzzy question written down.
```

After coding, confirm:

```markdown
- [ ] I wrote what I built.
- [ ] I wrote what failed or confused me.
- [ ] I wrote what I misunderstood.
- [ ] I wrote what test now proves it.
- [ ] I updated my concept dictionary if needed.
- [ ] I wrote the next smallest step.
```

---

# Summary

This workflow turns lessons into understanding by forcing a loop:

```
read
compress
close source
explain from memory
check
code
prove
log
publish only if evidence exists
```

The point is not to sound smart.

The point is to make your understanding testable before you code, then make your code explainable after it works.
