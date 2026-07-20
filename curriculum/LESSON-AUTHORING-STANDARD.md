# Evidence-First Lesson Authoring Standard

## Purpose

A learner-facing lesson is an evidence-first learning episode, not a page template. It must move a learner through a real engineering decision:

```text
failure or decision → prediction → artifact inspection → intervention
→ implementation or reconstruction → executable proof → causal explanation → transfer
```

Filling headings, recognizing an obvious answer, or checking a box is not lesson completion. This standard supplements `MISSION.md` and applies to every Project 1A lesson.

## Pre-authoring evidence packet

Complete this packet before writing lesson prose. A topic alone (for example, “validation” or “message state”) is insufficient.

```yaml
learning_decision: What must the learner decide, diagnose, or build?
starting_artifacts:
  # Existing dependencies and evidence the learner can inspect before this lesson.
  source_files: []
  symbols: []
  tests: []
  traces_or_fixtures: []
target_artifacts:
  # Files, tests, or behavior the learner must create or change.
  source_files: []
  tests: []
  expected_artifact: ""
proof_artifacts:
  # Runnable tests, traces, and output that demonstrate correctness.
  proof_command: []
  assertions: []
  traces_or_output: []
invariant: The behavior that must remain true.
real_failure: A failing test, bad trajectory, defect, ambiguity, or realistic incident.
design_tension: At least two plausible engineering choices.
learner_intervention: The code change, diagnosis, test, trace annotation, or reconstruction task.
reconstruction: annotated | skeleton | blank | none
```

“Real repository artifacts” are actual files or outputs in the learner’s repository: earlier primitives, starter files, types, interfaces, failing tests, fixtures, saved traces, command output, or implementation produced during the lesson. They are never snippets invented only for prose.

`starting_artifacts` are what may be inspected before the learner builds. `target_artifacts` are the destination and need not exist at the start. `proof_artifacts` demonstrate the finished result. Do not reveal a current primitive’s completed solution at the beginning unless the lesson is deliberately a debugging, code-reading, or reconstruction lab.

## Required learner operations

Authors may arrange a lesson in the structure that best fits its decision, but it must cause the learner to:

1. Commit a prediction and short rationale before seeing the answer.
2. Inspect a real repository artifact available at that point in the path.
3. Identify the responsible boundary or first bad transition.
4. Compare plausible interventions or designs.
5. Implement, debug, test, or reconstruct a narrow slice.
6. Run an executable proof.
7. Explain what the proof establishes and what it does not establish.
8. Apply the reasoning to a changed scenario.

## Lesson types and publication

Valid lesson types are `briefing`, `implementation_lab`, `diagnostic_lab`, `reconstruction_lab`, and `specification`.

- A briefing can introduce a concept but cannot establish meaningful practice or completion.
- A specification describes unavailable work and must be `locked`.
- A published Project 1A lesson must include implementation, diagnosis from actual evidence, test/eval construction, or reconstruction.
- A learner-facing page alone is not a completed lesson. A lesson cannot be published until its implementation, proof, and evidence artifacts exist.

## Practice requirements

Practice must require judgment, not recognition. Classification-oriented concepts require 5–8 or more cases (normally at least 6), including an ambiguous or near-boundary case. Cases must use plausible distractors based on real misconceptions, vary correct-answer positions, require a written rationale where judgment matters, and explain the violated boundary after commitment. A single correct recognition answer never establishes mastery.

For diagnostic practice, require the learner to name the first incorrect transition, responsible component, smallest correction, and regression evidence. For reconstruction, provide an annotated, skeleton, or blank-file handoff tied to a runnable proof.

## Rejections

Reject a lesson that:

- reveals the prediction answer in the following paragraph;
- substitutes pseudocode for available real code;
- uses generic “this matters in production” language;
- teaches vocabulary rather than decisions;
- uses absurd distractors or one-answer practice;
- describes an implementation that does not exist;
- claims future work as present evidence;
- removes the implementation’s real ambiguity;
- tests recall of page wording rather than engineering reasoning; or
- treats checklist completion as proof of mastery.

## Pedagogical review rubric

Before publication, score the lesson and record the evidence for each applicable dimension:

| Dimension | Required question |
| --- | --- |
| Procedural | Must the learner build or change something? |
| Diagnostic | Must they locate a failure or responsible component? |
| Conditional | Must they decide when a rule applies? |
| Design | Must they compare plausible choices? |
| Evidence | Must they inspect or produce runnable proof? |
| Reconstruction | Must they reproduce the mechanism without copying? |
| Transfer | Must they handle a changed case? |

Not every primitive needs the maximum score in every dimension, but no lesson passes with declarative knowledge alone.

## Publication checklist

Before publishing, verify that the evidence packet is complete, every referenced artifact resolves, the configured proof passes, practice meets its contract, the learner can make and explain a real intervention, and the manifest and lesson linter both pass. Review against `MISSION.md`, not merely HTML structure.
