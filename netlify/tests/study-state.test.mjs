import assert from "node:assert/strict";
import test from "node:test";

import { deriveMilestones, emptyStudy, LOCKED_LESSONS, sanitizeLearning } from "../functions/study-state.mjs";
import { sanitizeStudy } from "../functions/study.mjs";

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

test("legacy milestone names migrate to evidence-derived milestones", () => {
  const existing = {
    ...emptyStudy(lessonId),
    phase: "consolidating",
    milestones: {
      meaningful_practice_passed: true,
      explainer_reviewed: true,
      implementation_plan_ready: true,
      proof_passed: true,
      recall_passed: false,
      learning_record_written: false,
    },
  };

  const learning = sanitizeLearning({
    lesson_id: lessonId,
    phase: "consolidating",
    milestones: existing.milestones,
    evidence: { proof_runs: [{ passed: true }] },
  }, existing, "studying", plan, {});

  assert.deepEqual(Object.keys(learning.milestones).sort(), Object.keys(emptyStudy(lessonId).milestones).sort());
  assert.equal(learning.milestones.proof_passed, true);
  assert.equal("meaningful_practice_passed" in learning.milestones, false);
  assert.equal("explainer_reviewed" in learning.milestones, false);
});

test("publication status is read from the lesson contract", () => {
  assert.equal(LOCKED_LESSONS.has("0007-trace-logger"), false);
  assert.equal(LOCKED_LESSONS.has("0008-eval-runner"), false);
});

test("study persistence retains the prediction-versus-evidence reflection", () => {
  const study = sanitizeStudy("0007-trace-logger", {
    status: "studying",
    reflection: {
      feynman_explanation: "The trace records the moves, not just the ending.",
      feynman_limit: "The analogy does not identify each responsible boundary.",
      prediction_vs_evidence: "Assistant output rules out guessing about an unseen request.",
    },
  }, emptyStudy("0007-trace-logger"));

  assert.equal(
    study.reflection.prediction_vs_evidence,
    "Assistant output rules out guessing about an unseen request.",
  );
});
