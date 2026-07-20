# Learning System

The Project 1A curriculum uses one evidence-oriented loop from study through long-term recall.

```text
lesson practice → implementation handoff → configured proof
→ evidence explainer → recall → learning record → spaced review
```

## Sources of truth

- `curriculum/MISSION.md` defines the outcome that teaching serves.
- `curriculum/learning-flow.json` defines publication status, prerequisites, starting artifacts, target artifacts, proof artifacts, practice, reconstruction, micro-world decisions, and the selected episode pattern. `foundation_build` teaches isolated Project 1A primitives (Lessons 1–5); `integration_build` teaches composed behavior across real components and currently governs Agent Loop. Both record explanation, walkthrough, tradeoff, intervention scope, proof limits, and transfer without changing study-state milestones.
- `curriculum/learning-records/` defines understanding that future teaching may assume.
- The local or remote learner store defines the current phase, milestones, evidence references, and review schedule.
- Tests, diffs, and canonical traces provide executable evidence.

Detailed explainers are generated under `curriculum/explainers/generated/` and remain local by default. They are not learning records.

## Normal workflow

1. Run `./tools/study-context` when a teaching session starts.
2. Complete prediction and meaningful practice in the lesson.
3. Fill the implementation handoff and mark it ready.
4. At home, run `./tools/prove-lesson <lesson-id>`. When `STUDY_SITE_URL` and `STUDY_ACCESS_TOKEN` are set, proof and consolidation tools update the same remote record used by the phone; otherwise they use local SQLite.
5. Review the generated explainer and answer its questions from memory.
6. After the teacher and learner agree the recall demonstrates understanding, run `./tools/record-learning` with the assessed explanation and `--confirm`.
7. Complete scheduled pre-implementation and retention reviews from memory.

`prove-lesson` executes only argument arrays committed in the learning-flow manifest. Learner notes cannot introduce executable commands.

## Learner phases

```text
not_started → studying → ready_to_implement → implementing
            → consolidating → learned
```

Phase and review are independent. A learned lesson can be due for review. A weak later review changes its schedule and can trigger reconsolidation; it does not erase the historical learning record.

## Micro-world gate

Every lesson manifest entry records `required`, `optional`, or `none`, a score, a rationale, a real scenario source, and a static fallback. Full micro-worlds require a score of at least six and must expose hidden, dynamic, or branching behavior through grounded cause and effect.

The Agent Trace Lab is shared by the Agent Loop and its canonical scenarios live in `curriculum/traces/agent-loop-scenarios.json`. Trace Logger and Eval Runner are learner-build labs: they begin with a real incomplete-run or composed-workflow fixture, then produce their own evidence artifacts.

## Adding or changing a lesson

1. Identify a real learner decision or failure.
2. Create the evidence packet, separating existing starting artifacts from target and proof artifacts.
3. Implement or locate the runnable artifact.
4. Make the configured proof pass. For a learner-build lab, commit the real starter source and intentionally red proof first; the learner makes that same proof pass during the lesson.
5. Design learner actions around the real artifact.
6. Write the lesson.
7. Add its manifest contracts, including the applicable episode-pattern teaching contract.
8. Run `python3 tools/lint_lessons.py`.
9. Run the configured proof.
10. Review instructional quality with the authoring rubric.
11. Test the full study → implement → prove → explain path, including the milestone gates.
12. Publish only after every gate passes. The exception is a learner-build lab whose explicit starting gate is a real failing implementation proof; it may be published as unfinished learner work, but never recorded as complete until that proof passes.

`python3 tools/build_lessons_site.py` runs the lesson linter before generating `site/`. It builds only published lessons into the active course, presents locked specifications separately as upcoming work, and never allows a locked lesson to unlock later learning.

The detailed delivery design and deferred scope remain in [Learning System Implementation Plan](learning-system-implementation-plan.md).
