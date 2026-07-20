import manifest from "../../curriculum/learning-flow.json" with { type: "json" };

export const MILESTONE_KEYS = [
  "prediction_committed", "case_set_passed", "artifact_inspected",
  "implementation_plan_ready", "proof_passed", "failure_explained",
  "regression_added", "reconstruction_passed", "recall_passed", "learning_record_written",
];

export const LOCKED_LESSONS = new Set(
  Object.entries(manifest.lessons)
    .filter(([, lesson]) => lesson.publication.status === "locked")
    .map(([lessonId]) => lessonId),
);

export const PRACTICE_CONTRACTS = Object.fromEntries(
  Object.entries(manifest.lessons).map(([lessonId, lesson]) => [lessonId, {
    minimumCases: lesson.practice_contract.minimum_cases,
    threshold: lesson.practice_contract.passing_threshold,
    reconstruction: lesson.reconstruction_contract.mode !== "none",
  }]),
);

const PHASES = new Set(["not_started", "studying", "ready_to_implement", "implementing", "consolidating", "learned"]);
const PHASE_ORDER = ["not_started", "studying", "ready_to_implement", "implementing", "consolidating", "learned"];

export function emptyStudy(lessonId) {
  return {
    lesson_id: lessonId,
    status: "not_started",
    updated_at: null,
    responses: {},
    plan: {},
    reflection: {},
    phase: "not_started",
    milestones: Object.fromEntries(MILESTONE_KEYS.map((key) => [key, false])),
    evidence: {
      practice_attempts: [], artifact_inspections: [], proof_runs: [], trace_paths: [],
      explainer_path: null, failure_explanations: [], regression_paths: [],
      reconstruction_attempts: [], recall_attempts: [], learning_record_path: null,
    },
    events: [],
  };
}

export function sanitizeText(value, defaultValue = "") {
  if (value === undefined || value === null) return defaultValue;
  if (typeof value !== "string") throw new Error("Study fields must be text.");
  return value.slice(0, 12_000);
}

export function phaseForStatus(status) {
  return status === "ready_to_implement" ? status : status === "not_started" ? status : "studying";
}

function completePlan(plan) {
  return ["target_function", "smallest_slice", "must_do", "must_not_do", "first_proof"]
    .every((field) => typeof plan[field] === "string" && plan[field].trim());
}

function hasTextEvidence(entries, key = null) {
  return Array.isArray(entries) && entries.some((entry) => {
    if (typeof entry === "string") return Boolean(entry.trim());
    return entry && typeof entry === "object" && typeof (key ? entry[key] : Object.values(entry).find((value) => typeof value === "string")) === "string";
  });
}

export function deriveMilestones(lessonId, plan, reflection, evidence) {
  const contract = PRACTICE_CONTRACTS[lessonId] || { minimumCases: 6, threshold: 0.8, reconstruction: false };
  const attempts = Array.isArray(evidence.practice_attempts) ? evidence.practice_attempts : [];
  const predictionCommitted = attempts.some((attempt) => attempt?.kind === "prediction" && typeof attempt.selected === "string" && attempt.selected.trim() && typeof attempt.rationale === "string" && attempt.rationale.trim());
  const cases = new Map();
  for (const attempt of attempts) {
    if (attempt?.kind === "case" && typeof attempt.case_id === "string" && typeof attempt.passed === "boolean") cases.set(attempt.case_id, attempt.passed);
  }
  const score = cases.size ? [...cases.values()].filter(Boolean).length / cases.size : 0;
  const proofPassed = Array.isArray(evidence.proof_runs) && evidence.proof_runs.some((run) => run?.passed === true);
  const reconstructionPassed = !contract.reconstruction || (Array.isArray(evidence.reconstruction_attempts) && evidence.reconstruction_attempts.some((attempt) => attempt?.passed === true));
  const recallPassed = Array.isArray(evidence.recall_attempts) && evidence.recall_attempts.some((attempt) => attempt?.assessed_as === "passed");
  return {
    prediction_committed: predictionCommitted,
    case_set_passed: cases.size >= contract.minimumCases && score >= contract.threshold,
    artifact_inspected: hasTextEvidence(evidence.artifact_inspections),
    implementation_plan_ready: completePlan(plan),
    proof_passed: proofPassed,
    failure_explained: hasTextEvidence(evidence.failure_explanations, "explanation") || Boolean(reflection.feynman_explanation?.trim() && reflection.feynman_limit?.trim()),
    regression_added: hasTextEvidence(evidence.regression_paths),
    reconstruction_passed: reconstructionPassed,
    recall_passed: recallPassed,
    learning_record_written: typeof evidence.learning_record_path === "string" && Boolean(evidence.learning_record_path.trim()),
  };
}

export function sanitizeLearning(payload, existing, status, plan, reflection) {
  const current = existing || emptyStudy(payload.lesson_id || "");
  let phase = payload.phase ?? phaseForStatus(status);
  if (!PHASES.has(phase)) throw new Error("Invalid lesson phase.");
  if (PHASE_ORDER.indexOf(phase) < PHASE_ORDER.indexOf(current.phase || "not_started")) phase = current.phase;
  const incomingMilestones = payload.milestones ?? {};
  if (!incomingMilestones || typeof incomingMilestones !== "object" || Array.isArray(incomingMilestones)) throw new Error("Learning milestones have an invalid shape.");
  if (Object.keys(incomingMilestones).some((key) => !MILESTONE_KEYS.includes(key))) throw new Error("Learning milestones have an invalid shape.");
  if (Object.values(incomingMilestones).some((value) => typeof value !== "boolean")) throw new Error("Learning milestones must be booleans.");
  const evidence = { ...emptyStudy("").evidence, ...(current.evidence || {}) };
  if (payload.evidence !== undefined) {
    if (!payload.evidence || typeof payload.evidence !== "object" || Array.isArray(payload.evidence)) throw new Error("Learning evidence has an invalid shape.");
    for (const [key, value] of Object.entries(payload.evidence)) {
      if (!(key in evidence)) throw new Error("Learning evidence has an invalid shape.");
      if (["practice_attempts", "artifact_inspections", "proof_runs", "trace_paths", "failure_explanations", "regression_paths", "reconstruction_attempts", "recall_attempts"].includes(key)) {
        if (!Array.isArray(value)) throw new Error(`Evidence field ${key} must be a list.`);
        evidence[key] = value.slice(-50);
      } else if (value !== null && typeof value !== "string") throw new Error(`Evidence field ${key} must be text or null.`);
      else evidence[key] = value;
    }
  }
  const milestones = deriveMilestones(payload.lesson_id, plan, reflection, evidence);
  if (LOCKED_LESSONS.has(payload.lesson_id) && phase === "learned") throw new Error("Locked specifications cannot be marked learned.");
  const required = phase === "ready_to_implement"
    ? ["prediction_committed", "case_set_passed", "implementation_plan_ready"]
    : phase === "consolidating" ? ["proof_passed"]
      : phase === "learned" ? ["failure_explained", "recall_passed", "learning_record_written", "reconstruction_passed"] : [];
  const missing = required.filter((key) => !milestones[key]);
  if (missing.length) throw new Error(`Phase ${phase} requires evidence for: ${missing.join(", ")}.`);
  const events = Array.isArray(current.events) ? current.events.slice(-49) : [];
  if (phase !== current.phase) {
    events.push({
      event_id: crypto.randomUUID(), lesson_id: payload.lesson_id,
      type: phase === "ready_to_implement" ? "lesson.ready_to_implement" : `lesson.${phase}`,
      occurred_at: new Date().toISOString(), source: sanitizeText(payload.event_source, "study-api").slice(0, 80),
      evidence_refs: [], transition: { from: current.phase || "not_started", to: phase },
    });
  }
  return { phase, milestones, evidence, events };
}
