import assert from "node:assert/strict";
import test from "node:test";

import { deriveMilestones, emptyStudy, LOCKED_LESSONS, sanitizeLearning } from "../functions/study-state.mjs";

const lessonId = "0006-agent-loop-primitive";
const plan = {
  target_function: "run_agent",
  smallest_slice: "Stop after submit.",
  must_do: "Return the submitted answer.",
  must_not_do: "Execute a tool after submit.",
  first_proof: "test_submit_stops_loop",
  open_question: "When is the tool observation appended?",
};

function attempts(caseCount = 6) {
  return [
    { kind: "prediction", selected: "harness", rationale: "The harness owns execution." },
    ...Array.from({ length: caseCount }, (_, index) => ({
      kind: "case", case_id: `case-${index}`, passed: true, rationale: "The evidence identifies the boundary.",
    })),
  ];
}

test("a single correct click cannot complete a case set", () => {
  const milestones = deriveMilestones(lessonId, plan, {}, {
    ...emptyStudy(lessonId).evidence,
    practice_attempts: attempts(1),
  });

  assert.equal(milestones.prediction_committed, true);
  assert.equal(milestones.case_set_passed, false);
});

test("forged milestone flags cannot advance consolidation", () => {
  assert.throws(() => sanitizeLearning({
    lesson_id: lessonId,
    phase: "consolidating",
    milestones: { proof_passed: true },
    evidence: { practice_attempts: attempts(), proof_runs: [] },
  }, emptyStudy(lessonId), "studying", plan, {}), /proof_passed/);
});

test("publication status is read from the lesson contract", () => {
  assert.equal(LOCKED_LESSONS.has("0007-trace-logger"), false);
  assert.equal(LOCKED_LESSONS.has("0008-eval-runner"), false);
});
