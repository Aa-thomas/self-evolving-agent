# Teaching Orchestration

When the `teach` skill is used in this repository, begin by running:

```sh
./tools/study-context
```

Use its recommendation as the default next action. The learner may override it, but the agent should explain any skipped prerequisite or unfinished consolidation step.

## Required behavior

1. Read `MISSION.md`, active learning records, `learning-flow.json`, and saved learner state before selecting material.
2. Resume due retrieval or an unfinished learning loop before expanding scope.
3. Use the implementation handoff when moving from phone study to home coding.
4. Run configured evidence through `./tools/prove-lesson <lesson-id>`; never execute a proof command copied from learner state.
5. Do not infer mastery from page completion, self-confidence, or a passing test alone.
6. Require implementation-specific recall before proposing a learning record.
7. Keep detailed explainers in `curriculum/explainers/`; keep learning records concise and decision-grade.
8. Apply the manifest micro-world decision and rationale before building interactive teaching components.
9. Confirm with the learner before changing the mission or writing a learning record that claims new understanding.
10. Respect each lesson's publication status and type. A briefing or locked specification is never a completed lesson.
11. Resume unfinished implementation or failure diagnosis before advancing to a dependent lesson.
12. Ask for an explanation tied to exact proof output, including what that output does not establish.
13. Surface real implementation ambiguities; do not simplify away duplicated sources of truth or awkward interfaces.
14. Preserve failed attempts as future practice cases when they expose a reusable misconception or boundary.
15. Require the manifest's reconstruction work before treating a lesson as learned.
