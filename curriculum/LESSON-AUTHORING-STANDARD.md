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

## Study workspace contract

`study_contract` configures the learner's existing Think → Plan → Reflect workspace. It is personal synthesis and implementation intent, never completion evidence or a second lesson. Every `foundation_build` lesson must define it; other patterns are added as their study defaults are reviewed.

```yaml
study_contract:
  version: 1
  objective: The learner-owned model, action, and evidence interpretation.
  context_cards: [starting_artifacts, target_artifacts, proof_artifacts, failure_contract]
  think:
    jot_notes: {label: Jot notes, placeholder: Keep this messy.}
    prompts:
      - {id: model, label: ..., prompt: ..., kind: explanation}
      - {id: decision, label: ..., prompt: ..., kind: judgment}
      - {id: evidence_or_uncertainty, label: ..., prompt: ..., kind: evidence}
  plan:
    intro: A one-session handoff.
    fields:
      target_function: {label: ..., placeholder: ...}
      smallest_slice: {label: ..., placeholder: ...}
      must_do: {label: ..., placeholder: ...}
      must_not_do: {label: ..., placeholder: ...}
      first_proof: {label: ..., placeholder: ...}
      open_question: {label: ..., placeholder: ...}
  reflect:
    feynman: {label: Explain this to a smart 12-year-old, subject: ..., placeholder: ...}
    feynman_limit: {label: Where does that explanation break?, prompt: ...}
    prediction_vs_evidence: {label: ..., prompt: ...}
    mental_model: {label: ..., prompt: ...}
    next_step: {label: ..., prompt: ...}
```

The jot-notes box and both Feynman prompts are mandatory. `context_cards` resolve from the existing artifact contracts; they do not duplicate source paths. The plan keeps the existing handoff fields and ready-to-implement behavior. A workspace answer cannot satisfy prediction, practice, proof, or recall milestones.

## Composite-system episode schema: `integration_build`

Use `integration_build` when the learner must make behavior work across two or more real components. It is not specific to agent loops: a router, checkpoint flow, trace pipeline, evaluation harness, deployment path, or later repair can all use it. The lesson type still identifies the learner action; `integration_build` supplies the teaching arc.

```yaml
episode_pattern: integration_build
teaching_contract:
  system_problem: An observable cross-component failure, missing capability, or decision.
  integration_responsibility: What composition must now own that no prior component owns.
  prerequisite_bridge:
    existing_components:
      - component: ...
        already_guarantees: ...
        does_not_guarantee: ...
  system_model:
    components:
      - component: ...
        input: ...
        output_or_transition: ...
        responsibility: ...
    system_invariant: The end-to-end behavior that must remain true.
  worked_trajectories:
    success_path: [At least two real transitions.]
    failure_or_edge_path: [At least two contrasting real transitions.]
    comparison_question: What evidence distinguishes plausible causes?
  design_tension:
    options: [Two or more plausible integration choices.]
    decision_rule: Which boundary owns the choice and why.
  prediction_prompt: Commit to the next transition, diagnosis, or intervention.
  artifact_inspection_prompt: Map real predecessor artifacts to their responsibilities.
  intervention_strategy:
    mode: assemble | extend | repair | reconstruct
    build_order: [At least two ordered steps.]
    learner_owns: [The integration work they must perform.]
    leave_unchanged: [Boundaries that should not be edited speculatively.]
    forbidden_shortcuts: [Ways to bypass the architecture.]
    scaffold: Required only when mode is reconstruct.
  integration_proof:
    required_evidence: [At least two composed paths or outcomes.]
    establishes: ...
    does_not_establish: ...
  causal_explanation_prompt: Explain the outcome as component transitions.
  transfer_prompt: Change one system condition and choose an intervention and proof.
```

`reconstruct` mode requires a `reconstruction_lab`, a real scaffold, and the existing reconstruction proof contract. `assemble`, `extend`, and `repair` do not require a scaffold. This keeps reconstruction as a deliberate mode, rather than forcing every system lesson to pretend the learner is rebuilding existing code.

Agent Loop is the first use of this pattern. Eval Runner remains unassigned until the experiment-lab pattern is reviewed.

## Evidence-first failure episode schema: `diagnostic_clinic`

Use `diagnostic_clinic` when the lesson begins with an actual failure, ambiguous outcome, or incomplete evidence record. The learner must investigate rather than guess. A valid conclusion may be **evidence insufficient**; in that case, adding the smallest causal evidence is the intervention rather than a speculative code change.

```yaml
episode_pattern: diagnostic_clinic
teaching_contract:
  incident:
    symptom: The observable failure or ambiguity.
    available_evidence: [At least two real artifacts or outputs.]
    impact: The unsafe or blocked decision created by the uncertainty.
  diagnostic_model:
    first_principle: A symptom is not a root cause.
    candidate_causes:
      - cause: ...
        would_explain: ...
        distinguishing_evidence: ...
    ownership_rule: How the first bad transition or evidence gap finds its owner.
  worked_investigation:
    observations: [Facts supported by the artifacts.]
    elimination_steps: [Why plausible causes are ruled in or out.]
    current_conclusion: A responsible boundary or evidence-insufficient finding.
    confidence_limit: What cannot be concluded.
  prediction_prompt: Commit to the next useful evidence or first bad transition.
  artifact_inspection_sequence:
    - artifact: ...
      question: ...
      fact_established: ...
  diagnosis_commitment:
    required_claims: [first bad transition or gap, owner, rejected alternative, rationale]
    ambiguity_rule: When insufficient evidence is the only justified conclusion.
  intervention_strategy:
    mode: repair | add_evidence | add_regression
    smallest_safe_intervention: ...
    leave_unchanged: [...]
    regression_target: ...
    forbidden_shortcuts: [...]
  diagnostic_proof:
    required_evidence: [Original incident, post-intervention evidence, regression proof.]
    establishes: ...
    does_not_establish: ...
  causal_explanation_prompt: Explain evidence → diagnosis → intervention → regression.
  transfer_prompt: Diagnose a changed symptom from changed evidence.
```

This pattern works for trace review, flaky tests, permission failures, benchmark failure analysis, and incident triage. Trace Logger is its first Project 1A use: the partial run is intentionally non-diagnostic, so the learner builds the minimum trace needed to turn a future run into evidence.

## Behavioral measurement episode schema: `experiment_lab`

Use `experiment_lab` when the learner must turn a behavioral claim into repeatable, interpretable evidence. An experiment may construct an eval runner, compare two harness choices, ablate a component, or calibrate a grader. It is not a single passing test and it must preserve per-case failure evidence rather than only an aggregate score.

```yaml
episode_pattern: experiment_lab
teaching_contract:
  decision_question: The engineering decision that the measurement informs.
  behavioral_claim:
    hypothesis: If X, behavior Y should occur for the defined cases because Z.
    scope: The cases or task family this claim covers.
    expected_failure_modes: [...]
  baseline:
    existing_evidence: [At least two real artifacts or outputs.]
    what_baseline_establishes: ...
    what_baseline_does_not_establish: ...
  measurement_model:
    unit_of_evaluation: One full trajectory, task, case, or run.
    cases:
      source: A real fixture or case set.
      inclusion_rule: Why the cases belong.
      minimum_coverage: [At least two behavior or edge categories.]
    outcome_contract:
      - outcome: ...
        pass_condition: ...
        failure_evidence: ...
    controlled_conditions: [...]
    confounders: [...]
  worked_comparison:
    baseline_run: [...]
    measured_run: [...]
    interpretation: ...
  prediction_prompt: Commit to an outcome before the measurement runs.
  artifact_inspection_prompt: Separate prior unit guarantees from composed behavior.
  experiment_strategy:
    mode: construct | compare | ablate | calibrate
    intervention_or_measurement_change: ...
    keep_constant: [...]
    learner_owns: [...]
    leave_unchanged: [...]
    forbidden_shortcuts: [...]
  measurement_proof:
    required_evidence: [Case set, per-case outcomes, failed-case artifact, aggregate result.]
    establishes: ...
    does_not_establish: ...
  interpretation_prompt: State whether evidence supports, weakens, or leaves the claim unresolved.
  transfer_prompt: Change a case, component, or assertion and redesign the measurement.
```

Eval Runner is the first Project 1A use in `construct` mode. Later phases can use `compare` for harness choices, `ablate` for component attribution, and `calibrate` for evaluator behavior.

## Constrained execution episode schema: `operational_drill`

Use `operational_drill` when the learner must carry out a repeatable, authorized procedure under operating constraints. The lesson requires evidence for every important decision and a safe response to a degraded signal. It is not a checklist completed from memory.

```yaml
episode_pattern: operational_drill
teaching_contract:
  operational_context:
    objective: The outcome to achieve or verify.
    trigger: The event requiring the procedure.
    impact_if_wrong: The cost of unsafe or unverifiable action.
    constraints: [Authority, time, environment, safety, or change-control limits.]
  operating_model:
    first_principle: Operational work is authorized decisions plus observable evidence.
    system_boundaries:
      - boundary: ...
        authority: ...
        signal: ...
        unsafe_assumption: ...
  readiness_check:
    required_starting_artifacts: [Real runbook, trace, configuration, or report.]
    preflight_checks: [At least two checks required to proceed.]
    no_go_conditions: [When to stop or escalate before action.]
  worked_run:
    normal_path: [Ordered action and expected signal.]
    degraded_or_failure_path: [Deviation and safe response.]
    decision_point: Evidence distinguishing continue, stop, rollback, or escalate.
  prediction_prompt: Commit to the next safe action and expected evidence.
  execution_contract:
    mode: verify | replay | recover | deploy | rollback | audit
    procedure:
      - action: ...
        expected_signal: ...
        record: ...
    authority_boundary: What the learner may do versus must escalate.
    guardrails: [...]
    forbidden_shortcuts: [...]
  operational_proof:
    required_evidence: [Preflight, procedure output, state artifact, verification or safe-stop evidence.]
    establishes: ...
    does_not_establish: ...
  handoff_or_postmortem:
    required_record: [Runbook update, handoff, or incident note.]
    explanation_prompt: Explain decisions, evidence, and deviations.
  transfer_prompt: Change a constraint or signal and choose a safe response.
```

The first appropriate uses are later trace replay and production incident drills. Do not assign this pattern to Project 1A merely because it is available; it needs a real procedure, authority boundary, and evidence-bearing outcome.

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
