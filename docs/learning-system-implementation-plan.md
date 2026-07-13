# Learning System Implementation Plan

## Outcome

Build one coherent learning loop in which the lesson site, the `teach` skill, implementation sessions, executable evidence, explainers, micro-worlds, learning records, and spaced review all respond to the same learner state.

The finished flow is:

```text
Mission + prior learning
        ↓
Choose or resume the right lesson
        ↓
Prediction → explanation → meaningful practice
        ↓
Implementation handoff
        ↓
Smallest executable proof
        ↓
Evidence-based explainer and micro-world when justified
        ↓
Implementation-specific recall
        ↓
Learning record
        ↓
Spaced and interleaved review → next unlocked lesson
```

The system must never equate exposure, finishing a page, self-confidence, or a passing test by itself with demonstrated understanding.

## Design Principles

1. **One source of learner state.** Every surface reads and updates the same milestones.
2. **Evidence before mastery.** A lesson becomes learned only after an executable proof and successful explanation or recall.
3. **Real artifacts before generated teaching.** Explainers, questions, and micro-worlds derive from actual diffs, tests, traces, schemas, and learner responses.
4. **Smallest effective teaching form.** Use prose, diagrams, quizzes, or playgrounds unless evolving hidden state genuinely calls for a micro-world.
5. **Durable records stay concise.** Detailed explainers are learning artifacts; `learning-records` remain decision-grade statements used to choose future teaching.
6. **Automatic transitions remain inspectable.** Every hook records why it fired, what evidence it used, and what it changed.
7. **Local and remote paths behave consistently.** SQLite and Netlify storage implement the same schema and transition rules.

## System Boundaries

| Component | Owns | Does not own |
|---|---|---|
| Lesson HTML and shared assets | Explanation, prediction, practice, immediate feedback | Deciding durable mastery |
| Study API and learner store | State, responses, milestones, evidence references, review schedule | Interpreting code correctness |
| `teach` skill | Choosing/resuming the next learning action and interpreting evidence with the learner | Inventing evidence or silently advancing mastery |
| Proof runner | Executing configured tests and capturing machine-readable results | Claiming conceptual understanding |
| Explainer builder | Turning real evidence into a personalized, literate explanation | Writing learning records directly |
| Micro-world component | Exposing causal behavior through grounded scenarios | Simulating behavior that cannot be kept faithful to the implementation |
| Learning-record writer | Recording demonstrated, decision-relevant understanding | Storing session logs or full explainers |
| Review scheduler | Retrieval timing and interleaving | Choosing the curriculum sequence |

## Canonical Data Model

### Lesson manifest

Add `curriculum/learning-flow.json` as the static curriculum graph and artifact contract.

Each lesson entry contains:

```json
{
  "0006-agent-loop-primitive": {
    "requires": [
      "0003-manual-tool-protocol",
      "0004-schema-validation",
      "0005-sandboxed-file-tools"
    ],
    "unlocks": ["0007-trace-logger"],
    "learning_goal": "Predict and explain harness control flow.",
    "implementation": {
      "targets": ["curriculum/phase-1/06_agent_loop/agent_loop.py"],
      "proof_command": [
        "uv",
        "run",
        "pytest",
        "curriculum/phase-1/06_agent_loop/tests_agent_loop.py"
      ],
      "first_proof": "test_submit_stops_loop"
    },
    "micro_world": {
      "decision": "required",
      "score": 9,
      "component": "agent-trace-lab",
      "scenario_source": "curriculum/traces/agent-loop",
      "learner_action": "predict_next_transition",
      "fallback": "annotated_static_trace",
      "rationale": "Harness decisions evolve through hidden, branching state."
    }
  }
}
```

Commands are arrays, not shell strings. The proof runner executes only commands declared in the manifest.

### Learner state

Replace the meaning carried by one coarse status with a phase plus explicit milestones:

```json
{
  "lesson_id": "0006-agent-loop-primitive",
  "phase": "implementing",
  "milestones": {
    "meaningful_practice_passed": true,
    "implementation_plan_ready": true,
    "proof_passed": false,
    "explainer_reviewed": false,
    "recall_passed": false,
    "learning_record_written": false
  },
  "evidence": {
    "practice_attempts": [],
    "proof_runs": [],
    "trace_paths": [],
    "explainer_path": null,
    "recall_attempts": [],
    "learning_record_path": null
  },
  "updated_at": "2026-07-12T00:00:00Z"
}
```

Phases are:

```text
not_started → studying → ready_to_implement → implementing
            → consolidating → learned
```

Review scheduling is orthogonal to phase. A learned lesson may be due for review without moving backward.

### Domain events

Persist an append-only, bounded event history for auditability:

```json
{
  "event_id": "uuid",
  "lesson_id": "0006-agent-loop-primitive",
  "type": "implementation.proof_passed",
  "occurred_at": "2026-07-12T00:00:00Z",
  "source": "prove-lesson",
  "evidence_refs": ["proof-run-id"],
  "transition": {
    "from": "implementing",
    "to": "consolidating"
  }
}
```

Events explain transitions; current state remains directly queryable. Limit retained operational events per lesson while preserving durable proof and recall evidence.

## Transition Rules and Automatic Hooks

### 1. `teach.session_started`

Triggered at the beginning of every `teach` invocation.

Dependencies:

- valid mission;
- lesson manifest;
- active learning records;
- local or synced learner state;
- due-review queue.

Actions:

1. Sync remote notes when configured.
2. Validate the manifest and learner-state schema.
3. Find overdue recall, an unfinished phase, and newly unlocked lessons in that order.
4. Produce a compact teaching context: assumed knowledge, current uncertainty, evidence already available, and one recommended next action.
5. Resume existing work before creating a new lesson unless the user overrides it.

It must not alter mastery state.

### 2. `lesson.meaningful_practice_passed`

Triggered by a reasoning task with deterministic or rubric-based feedback. Checkboxes and keyword-presence tests do not qualify.

Dependencies:

- lesson is in `studying`;
- attempt is recorded;
- feedback has been shown.

Actions:

- mark meaningful practice complete;
- preserve incorrect attempts as misconception candidates;
- reveal or enable the implementation-plan step;
- prefill the target and first proof from the manifest.

### 3. `lesson.ready_to_implement`

Triggered when the learner explicitly marks ready and all handoff fields are present:

- target artifact;
- smallest behavior;
- must-do boundary;
- must-not-do boundary;
- first executable proof;
- open question, which may explicitly be `none`.

Actions:

- move to `ready_to_implement`;
- create a compact implementation handoff;
- schedule a pre-implementation recall check;
- expose the handoff to the next `teach` session.

This transition does not create a learning record.

### 4. `implementation.started`

Triggered when `prove-lesson` is first invoked or when the teaching agent explicitly begins the configured implementation slice.

Dependencies:

- implementation handoff exists;
- configured lesson targets and proof command exist;
- prerequisites are learned or explicitly waived with a recorded reason.

Actions:

- move to `implementing`;
- record the repository baseline needed to calculate the relevant diff;
- surface the must-do, must-not-do, first proof, and open question.

### 5. `implementation.proof_completed`

Triggered by `tools/prove-lesson <lesson-id>`.

Actions:

1. Execute the manifest command without shell interpolation.
2. Capture exit code, structured test summary where available, timestamp, and relevant diff metadata.
3. Store failure output as diagnostic evidence without advancing phase.
4. On success, capture applicable traces and mark `proof_passed`.
5. Move to `consolidating` only after the declared proof passes.

### 6. `implementation.evidence_ready`

Triggered after proof success and required evidence collection.

Dependencies:

- passing proof;
- relevant diff or explicit no-diff explanation;
- required trace scenarios;
- learner's prior responses and misconception candidates.

Actions:

- generate an explainer under `curriculum/explainers/`;
- order code by causal explanation rather than filename;
- include background personalized from learning records;
- include intuition, happy path, failure path, unchanged boundaries, and evidence;
- generate two or three implementation-specific recall prompts;
- embed or link a micro-world only when the manifest decision permits it.

### 7. `consolidation.recall_passed`

Triggered after the learner answers from memory and receives feedback.

Passing requires evidence of causal understanding, not matching exact prose. The learner must be able to explain the invariant, interpret at least one implementation-specific scenario, and connect it to the proof.

Actions:

- mark recall passed;
- generate a concise learning-record candidate;
- require learner or teaching-agent confirmation that the candidate matches demonstrated understanding;
- write the next numbered learning record;
- mark the lesson `learned`;
- schedule long-term retention reviews;
- make dependent lessons eligible.

### 8. `review.completed`

Triggered after a due retrieval attempt.

Actions:

- store the answer before revealing source material;
- store the rating separately from objective or rubric feedback;
- update the 1, 3, 7, 14, and 30-day schedule;
- interleave a related prerequisite or dependent concept when useful;
- create a misconception candidate if the answer reveals a new error.

A weak review does not erase a learning record. It changes the next review interval and may recommend targeted reconsolidation.

## Micro-World Decision System

### Eligibility gate

A lesson is eligible only when all are true:

1. The goal is a mental model rather than fact recall.
2. Important behavior is hidden, dynamic, spatial, or branching.
3. Learner actions expose meaningful cause and effect.
4. The world can be grounded in real code, traces, schemas, or tests.

### Score

| Signal | Score |
|---|---:|
| State changes across multiple steps | +2 |
| Branches have meaningfully different consequences | +2 |
| Important internal behavior is hard to see in source | +2 |
| Interaction exposes a common misconception | +2 |
| Component is reusable in later lessons | +1 |
| Static annotation teaches the concept equally well | -3 |
| Simulation may drift from the implementation | -3 |

Decision thresholds:

- `6+`: micro-world;
- `3–5`: small playground or interactive figure;
- `0–2`: prose, static diagram, annotated trace, or quiz.

The manifest records `required`, `optional`, or `none`, plus score, rationale, data source, learner action, and static fallback. An author can override the computed recommendation only with a rationale.

### Initial Project 1A decisions

| Lesson | Teaching form |
|---|---|
| Model call | Annotated request/response |
| Message state | Small state timeline |
| Tool parsing | Input/output playground |
| Schema validation | Validation playground |
| Sandboxed file tools | Optional path-containment world |
| Agent loop | Full trace-driven micro-world |
| Trace logger | Reuse the agent-loop world with trace-field controls |
| Eval runner | Reuse scenarios with assertions and aggregate outcomes |

### Agent Trace Lab contract

Build one reusable `agent-trace-lab` component. Scenario data contains:

- initial messages;
- raw assistant output;
- parse and validation result;
- harness decision;
- tool result or rejection observation;
- updated message state;
- exit reason;
- source proof or trace reference.

Learner modes are layered rather than duplicated:

- agent-loop mode: predict the next harness decision;
- trace mode: identify the field that explains the decision;
- eval mode: decide whether the trajectory satisfies an assertion;
- review mode: diagnose a partially hidden trajectory.

Every scenario must have a static, printable fallback.

## Storage and Migration

### Local SQLite

Extend `curriculum/study_server.py` with additive migrations for:

- lesson phase;
- milestones;
- evidence records;
- bounded domain events;
- review kind (`pre_implementation` or `retention`).

Keep old `status` values readable during migration. Map them conservatively:

| Existing status | New phase |
|---|---|
| `not_started` | `not_started` |
| `studying` | `studying` |
| `ready_to_implement` | `ready_to_implement` |
| `review` | `studying`, with a review flag |

Do not infer proof, recall, or mastery milestones from old status values.

### Netlify state

Increment the remote schema version and migrate on read. Preserve existing lessons, responses, plans, reflections, and scheduled reviews. Use the same transition validation and sanitized payload shapes as the local store.

Extract shared transition fixtures, even if Python and JavaScript must retain separate implementations. Contract tests must feed identical fixtures into both paths.

### Generated and private artifacts

- `curriculum/explainers/`: generated or curated detailed explainers; commit only intentionally durable examples.
- `curriculum/traces/`: canonical, non-sensitive scenarios used by lessons and micro-worlds.
- `curriculum/data/`: private synced learner state and run evidence; ignored unless an existing fixture is intentionally tracked.
- `curriculum/learning-records/`: concise, confirmed durable understanding.

## `teach` Skill Integration

Add a repository-owned companion instruction such as `curriculum/TEACHING-ORCHESTRATION.md`, then update the local `teach` skill to require it when present.

The companion instruction should require the teaching agent to:

1. Run the session-start context command before selecting material.
2. Respect manifest prerequisites and phase transitions.
3. Use existing lesson assets before creating new ones.
4. Never infer mastery from coverage, confidence, or tests alone.
5. Use proof evidence and recall before proposing a learning record.
6. Apply the micro-world gate before creating interactive simulations.
7. Resume unfinished consolidation or due review before expanding scope.
8. Ask for confirmation before changing the mission.

The skill remains the pedagogical conductor. Transition logic lives in tested application code, not in prompt wording alone.

## Implementation Phases

### Phase 0 — Stabilize the current foundation

Scope:

- finish and test the in-progress review work;
- remove accidental duplicate asset injection in the site builder if it remains after current work is reconciled;
- document the current local/remote schema and API behavior;
- add baseline tests for build output and review scheduling.

Exit criteria:

- current unit tests pass;
- site build is deterministic;
- each generated page loads shared assets once;
- existing learner data survives a round trip;
- current review behavior has regression coverage.

### Phase 1 — Curriculum manifest and validation

Scope:

- create `curriculum/learning-flow.json` for all eight lessons;
- add a manifest loader and validator;
- validate lesson IDs, prerequisite references, cycles, target paths, proof commands, micro-world decisions, rationales, and fallbacks;
- make site generation fail clearly on an invalid manifest;
- derive suggested target and proof in `study.js` from generated manifest data instead of the hard-coded `LESSON_CONTEXT` object.

Exit criteria:

- all lessons have valid graph entries;
- graph is acyclic;
- referenced artifacts exist;
- the browser and teaching tools consume the same manifest;
- invalid fixtures produce useful errors.

### Phase 2 — Learner-state machine

Scope:

- implement phase, milestones, evidence, and event records locally and remotely;
- centralize transition preconditions;
- migrate existing records without inferring mastery;
- update progress UI to show the actionable phase;
- distinguish due review from lesson phase.

Exit criteria:

- illegal transitions are rejected;
- repeated events are idempotent;
- local and remote contract fixtures agree;
- legacy study records load without data loss;
- `ready_to_implement` no longer implies learned.

### Phase 3 — Teaching-session context and handoff

Scope:

- add `tools/study-context` to combine mission, manifest, learning records, synced state, and due reviews;
- emit human-readable and JSON output;
- add implementation-handoff generation;
- create `curriculum/TEACHING-ORCHESTRATION.md`;
- update the local `teach` skill to invoke the context workflow when this repository is the workspace.

Recommendation priority:

1. overdue retrieval that blocks reliable recall;
2. unfinished consolidation;
3. ready implementation handoff;
4. lesson in progress;
5. newly eligible lesson in the zone of proximal development.

Exit criteria:

- a new teaching session can answer “what should we do next and why?” with one command;
- it never recommends a locked lesson without explaining an override;
- it resumes saved plans and open questions;
- it does not mutate learner state during context calculation.

### Phase 4 — Proof runner and evidence capture

Scope:

- add `tools/prove-lesson`;
- execute only manifest-declared argument arrays;
- capture proof attempts, exit codes, relevant test results, baseline/diff metadata, and trace paths;
- make failed attempts available for feedback;
- trigger consolidation only on declared proof success.

Exit criteria:

- the agent-loop proof can be run by lesson ID;
- failures are preserved without advancing the learner;
- success creates complete, inspectable evidence;
- unrelated working-tree changes are excluded from the explainer input;
- no arbitrary command from learner state is executable.

### Phase 5 — Evidence-based explainer pipeline

Scope:

- define a structured explainer input and output contract;
- generate background from mission and active learning records;
- generate literate diffs from the relevant implementation slice;
- include traces, failures, unchanged boundaries, and proof results;
- generate implementation-specific recall prompts;
- render printable HTML and source Markdown;
- require explicit review before marking `explainer_reviewed`.

Exit criteria:

- the agent-loop submit slice produces a faithful explainer;
- every code claim links to diff or proof evidence;
- missing evidence is called out rather than invented;
- output prints cleanly and works on mobile;
- detailed explainers do not pollute learning records.

### Phase 6 — Trace Lab micro-world

Scope:

- define and validate canonical trace-scenario JSON;
- implement `agent-trace-lab.js` and shared styles;
- support predict, trace-diagnosis, eval, and review modes;
- add keyboard, screen-reader, reduced-motion, mobile, and print fallbacks;
- embed it first in the agent-loop lesson, then reuse it in trace and eval lessons;
- enforce the micro-world decision in the lesson build.

Initial scenarios:

1. valid tool request → observation → next call;
2. malformed JSON → rejection observation → bounded recovery;
3. `submit` → immediate internal stop;
4. unknown tool → structured rejection;
5. repeated requests → `max_steps`.

Exit criteria:

- every transition matches a real contract, test, or trace fixture;
- learners must predict before reveal;
- the same scenario data drives all modes;
- static fallback communicates the same causal sequence;
- lessons scored below the threshold do not load the full component.

### Phase 7 — Consolidation and learning records

Scope:

- present two or three recall questions derived from the learner's evidence;
- add rubric-based assessment for causal explanations;
- generate a learning-record candidate only after proof and recall;
- scan numbering and write the next concise record after confirmation;
- mark the lesson learned and unlock dependents.

Exit criteria:

- coverage alone cannot write a learning record;
- passing tests alone cannot write a learning record;
- records follow the skill's concise format;
- misconception corrections can supersede older records;
- future session context immediately reflects the new learning floor.

### Phase 8 — Spaced and interleaved review

Scope:

- split pre-implementation and retention review queues;
- preserve the existing 1, 3, 7, 14, and 30-day schedule;
- draw questions from invariant, failure, evidence, implementation, and trace understanding;
- interleave prerequisite concepts when a dependent lesson is active;
- feed new misconceptions back into consolidation recommendations.

Exit criteria:

- readiness schedules pre-implementation recall;
- learned status schedules retention review;
- self-rating and assessed correctness are stored separately;
- a weak answer shortens the interval without erasing mastery history;
- reminders link directly to the correct review type and lesson context.

### Phase 9 — Hardening and documentation

Scope:

- end-to-end tests for local and remote flows;
- accessibility and responsive browser tests;
- storage limits, sanitization, and sensitive trace guidance;
- failure recovery for interrupted saves and partially generated explainers;
- update study-workflow, remote-workspace, lesson-authoring, and contributor documentation;
- add analytics limited to pedagogically useful events, with no private answer leakage.

Exit criteria:

- the complete agent-loop path works locally and remotely;
- the flow survives refreshes and resumed sessions;
- learner answers and tokens remain private;
- generated artifacts expose their evidence sources;
- a contributor can add a lesson and receive manifest/micro-world guidance from validation errors.

## Test Strategy

### Unit tests

- manifest schema, graph cycles, references, and micro-world scoring;
- state transition preconditions and idempotency;
- local database migrations;
- Netlify state migrations and sanitization;
- review interval calculations;
- implementation-handoff completeness;
- proof-command allowlisting;
- explainer evidence completeness;
- trace-scenario validation.

### Contract tests

Store common JSON fixtures for:

- legacy learner records;
- valid and invalid transitions;
- readiness versus mastery;
- proof failure and success;
- two review kinds;
- micro-world recommendations and overrides.

Run equivalent fixtures against Python and JavaScript implementations.

### Integration tests

- study response → meaningful-practice milestone;
- ready plan → implementation handoff and pre-implementation review;
- proof runner failure → no phase advancement;
- proof runner success → explainer eligibility;
- successful recall → learning record and dependent unlock;
- learned lesson → retention schedule;
- remote export → local context command.

### Browser tests

- mobile study and review flows;
- saved/resumed lesson state;
- Trace Lab prediction and feedback;
- keyboard-only operation;
- screen-reader labels and live feedback;
- reduced-motion behavior;
- print fallback;
- no duplicate scripts or styles.

### Acceptance journey

Use `0006-agent-loop-primitive` as the vertical slice:

1. Learner predicts `submit` behavior and passes meaningful practice.
2. Study panel creates a complete submit-handling implementation handoff.
3. A later `teach` session resumes that handoff automatically.
4. `prove-lesson` records a failing attempt, then a passing attempt.
5. The system creates an explainer grounded in the diff, test, and submit trace.
6. Trace Lab asks the learner to predict the stop transition.
7. Learner explains why the registered `submit` callable is not executed.
8. The system writes a concise learning record after confirmation.
9. Trace Logger becomes eligible.
10. A retention question appears on schedule and updates its interval.

The vertical slice is complete only when this journey works without manually copying state between the browser, repository, and teaching agent.

## Delivery and Commit Boundaries

Use small commits that leave the current system runnable:

1. `docs(learning): define orchestration and state contracts`
2. `feat(curriculum): add validated learning-flow manifest`
3. `feat(study): add milestone-based learner state`
4. `feat(teach): add session context and implementation handoff`
5. `feat(evidence): add lesson proof runner`
6. `feat(explainers): generate evidence-grounded change explainers`
7. `feat(microworld): add trace-driven agent loop lab`
8. `feat(learning): consolidate recall into learning records`
9. `feat(review): separate readiness and retention review`
10. `test(learning): cover the end-to-end agent loop journey`

Do not combine schema migration, remote deployment behavior, and the first micro-world in one change.

## Deferred Scope

Do not add these until the vertical slice demonstrates value:

- general-purpose LLM lesson generation;
- arbitrary user-authored proof commands;
- a visual curriculum editor;
- collaborative multi-user classrooms;
- generalized simulation authoring;
- automatic learning-record publication without confirmation;
- analytics dashboards unrelated to teaching decisions;
- additional micro-worlds that do not pass the eligibility gate.

## Definition of Done

The learning system is complete for Project 1A when:

- every lesson has validated prerequisites, evidence, and teaching-form metadata;
- the study site and `teach` skill agree on the learner's next action;
- implementation plans cross from phone study to home coding automatically;
- configured proofs create inspectable evidence;
- explainers are grounded in actual work;
- micro-worlds appear only when the eligibility gate justifies them;
- learning records require both executable and conceptual evidence;
- spaced review distinguishes preparation from durable retention;
- the agent-loop vertical slice works locally and remotely;
- no manual state copying is necessary anywhere in the normal flow.
