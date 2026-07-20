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

## Project 1A primitive episode schema: `foundation_build`

Lessons 1–5 teach isolated harness primitives to a learner starting from zero. Their manifest entry must use `"episode_pattern": "foundation_build"` and include this `teaching_contract`:

```yaml
episode_pattern: foundation_build
teaching_contract:
  concrete_problem: A specific engineering symptom or decision.
  first_principle: The small causal model needed before practice.
  worked_walkthrough:
    - A concrete pass through real starting artifacts.
    - A contrasting pass that exposes the missing responsibility.
  boundary_and_invariant:
    boundary: The component that owns the transition or correction.
    invariant: The behavior that remains true after the learner's change.
  design_tension:
    options: [Two or more plausible choices.]
    decision_rule: Why this primitive chooses one without claiming later boundaries are solved.
  prediction_prompt: The commitment required before the answer is revealed.
  artifact_inspection_prompt: What existing repository artifact establishes.
  implementation_scope:
    build: [The narrow slice to create or change.]
    leave_unchanged: [Responsibilities intentionally outside this primitive.]
  proof_interpretation:
    establishes: What the configured proof demonstrates.
    does_not_establish: The explicit limit of that evidence.
  transfer_prompt: A changed case requiring the same reasoning.
```

This is a **teaching contract**, not an HTML heading template and not a new study-state machine. Authors may use approachable headings such as “Why this exists,” “Walkthrough,” “Tradeoff,” and “Try the changed case.” They must teach the causal model and worked example before demanding the prediction or implementation handoff.

Every `foundation_build` episode needs at least one inspectable `starting_artifact`. A starter test is a valid starting artifact when it already exists before the learner changes the target. A completed solution for the current primitive is not.

The contract deliberately applies only to isolated Project 1A primitives. Agent Loop, Trace Logger, and Eval Runner retain their current lesson types until their reconstruction, diagnostic, and experiment episode schemas are defined separately.

## Lesson types and publication

Valid lesson types are `briefing`, `implementation_lab`, `diagnostic_lab`, `reconstruction_lab`, and `specification`.

- A briefing can introduce a concept but cannot establish meaningful practice or completion.
- A specification describes unavailable work and must be `locked`.
- A published Project 1A lesson must include implementation, diagnosis from actual evidence, test/eval construction, or reconstruction.
- A learner-facing page alone is not a completed lesson. A lesson cannot be published until its implementation, proof, and evidence artifacts exist.

A learner-build implementation lab may publish before the learner's target behavior passes: its starter source, failing test or fixture, and executable proof must already exist. The page must state that the proof starts red and identify the narrow behavior the learner changes. That initial failure never counts as `proof_passed`, consolidation, or completion, and the lesson must not claim that the target capability exists. Use a locked specification only when even this real starter slice and proof do not exist.

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

Before publishing, verify that the evidence packet is complete, every referenced artifact resolves, practice meets its contract, the learner can make and explain a real intervention, and the manifest and lesson linter both pass. A completed or reconstruction lab's configured proof must pass before publication. A learner-build lab may begin with a deliberately failing implementation proof only when the starter source, failure fixture, and exact green-after-build assertion are present; record that distinction in the lesson and never advance completion from the starting failure. Review against `MISSION.md`, not merely HTML structure.
