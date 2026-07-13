# Learning System

The Project 1A curriculum uses one evidence-oriented loop from study through long-term recall.

```text
lesson practice → implementation handoff → configured proof
→ evidence explainer → recall → learning record → spaced review
```

## Sources of truth

- `curriculum/MISSION.md` defines the outcome that teaching serves.
- `curriculum/learning-flow.json` defines prerequisites, implementation targets, proofs, and micro-world decisions.
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

The Agent Trace Lab is shared by Agent Loop, Trace Logger, and Eval Runner. Its canonical scenarios live in `curriculum/traces/agent-loop-scenarios.json` and point back to the agent-loop tests.

## Adding or changing a lesson

1. Update the lesson HTML and `curriculum/learning-flow.json` together.
2. Reuse components in `curriculum/assets/`.
3. Run `python3 tools/build_lessons_site.py`; manifest or lesson mismatches fail the build.
4. Run `uv run pytest`.
5. Verify interactive changes in a real browser at desktop and mobile sizes.

The detailed delivery design and deferred scope remain in [Learning System Implementation Plan](learning-system-implementation-plan.md).
