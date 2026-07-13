import { getStore } from "@netlify/blobs";

const LESSON_ID = /^\d{4}-[a-z0-9-]+$/;
const STATUSES = new Set(["not_started", "studying", "ready_to_implement", "review"]);
const PHASES = new Set(["not_started", "studying", "ready_to_implement", "implementing", "consolidating", "learned"]);
const MILESTONE_KEYS = [
  "meaningful_practice_passed", "implementation_plan_ready", "proof_passed",
  "explainer_reviewed", "recall_passed", "learning_record_written",
];
const PHASE_ORDER = ["not_started", "studying", "ready_to_implement", "implementing", "consolidating", "learned"];
const MAX_BODY_BYTES = 250_000;
const STORE_NAME = "study-workspace";
const STORE_KEY = "current";
const REVIEW_INTERVAL_DAYS = [1, 3, 7, 14, 30];
const REVIEW_QUESTION_TYPES = [
  ["one_sentence", "In one sentence, what is this primitive or concept?"],
  ["invariant", "What must never happen, and who enforces that boundary?"],
  ["failure", "What realistic failure does this prevent?"],
  ["evidence", "What test, trace, or observable result would prove it works?"],
];

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function requestPath(request) {
  const path = new URL(request.url).pathname;
  return path
    .replace(/^\/.netlify\/functions\/study/, "")
    .replace(/^\/api/, "");
}

function isAuthorized(request) {
  const expected = process.env.STUDY_ACCESS_TOKEN;
  return Boolean(expected) && request.headers.get("X-Study-Token") === expected;
}

function emptyStudy(lessonId) {
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
      practice_attempts: [], proof_runs: [], trace_paths: [], explainer_path: null,
      recall_attempts: [], learning_record_path: null,
    },
    events: [],
  };
}

function emptyReview(lessonId, kind = "retention") {
  return { lesson_id: lessonId, kind, due_at: null, interval_index: 0, last_reviewed_at: null, answers: {} };
}

function sanitizeText(value, defaultValue = "") {
  if (value === undefined || value === null) return defaultValue;
  if (typeof value !== "string") throw new Error("Study fields must be text.");
  return value.slice(0, 12_000);
}

function phaseForStatus(status) {
  return status === "ready_to_implement" ? status : status === "not_started" ? status : "studying";
}

function completePlan(plan) {
  return ["target_function", "smallest_slice", "must_do", "must_not_do", "first_proof"]
    .every((field) => typeof plan[field] === "string" && plan[field].trim());
}

function sanitizeLearning(payload, existing, status, plan) {
  const current = existing || emptyStudy(payload.lesson_id || "");
  let phase = payload.phase ?? phaseForStatus(status);
  if (!PHASES.has(phase)) throw new Error("Invalid lesson phase.");
  if (PHASE_ORDER.indexOf(phase) < PHASE_ORDER.indexOf(current.phase || "not_started")) phase = current.phase;
  const incomingMilestones = payload.milestones ?? {};
  if (!incomingMilestones || typeof incomingMilestones !== "object" || Array.isArray(incomingMilestones)) {
    throw new Error("Learning milestones have an invalid shape.");
  }
  if (Object.keys(incomingMilestones).some((key) => !MILESTONE_KEYS.includes(key))) {
    throw new Error("Learning milestones have an invalid shape.");
  }
  const milestones = { ...emptyStudy("").milestones, ...(current.milestones || {}), ...incomingMilestones };
  if (Object.values(milestones).some((value) => typeof value !== "boolean")) {
    throw new Error("Learning milestones must be booleans.");
  }
  if (phase === "ready_to_implement" && completePlan(plan)) milestones.implementation_plan_ready = true;
  if (phase === "ready_to_implement" && !milestones.implementation_plan_ready) {
    throw new Error("Phase ready_to_implement requires milestone implementation_plan_ready.");
  }
  if (phase === "consolidating" && !milestones.proof_passed) {
    throw new Error("Phase consolidating requires milestone proof_passed.");
  }
  if (phase === "learned" && !milestones.learning_record_written) {
    throw new Error("Phase learned requires milestone learning_record_written.");
  }
  const evidence = { ...emptyStudy("").evidence, ...(current.evidence || {}) };
  if (payload.evidence !== undefined) {
    if (!payload.evidence || typeof payload.evidence !== "object" || Array.isArray(payload.evidence)) {
      throw new Error("Learning evidence has an invalid shape.");
    }
    for (const [key, value] of Object.entries(payload.evidence)) {
      if (!(key in evidence)) throw new Error("Learning evidence has an invalid shape.");
      if (["practice_attempts", "proof_runs", "trace_paths", "recall_attempts"].includes(key)) {
        if (!Array.isArray(value)) throw new Error(`Evidence field ${key} must be a list.`);
        evidence[key] = value.slice(-50);
      } else if (value !== null && typeof value !== "string") {
        throw new Error(`Evidence field ${key} must be text or null.`);
      } else evidence[key] = value;
    }
  }
  const events = Array.isArray(current.events) ? current.events.slice(-49) : [];
  if (phase !== current.phase) {
    events.push({
      event_id: crypto.randomUUID(),
      lesson_id: payload.lesson_id,
      type: phase === "ready_to_implement" ? "lesson.ready_to_implement" : `lesson.${phase}`,
      occurred_at: new Date().toISOString(),
      source: sanitizeText(payload.event_source, "study-api").slice(0, 80),
      evidence_refs: [],
      transition: { from: current.phase || "not_started", to: phase },
    });
  }
  return { phase, milestones, evidence, events };
}

function sanitizeStudy(lessonId, payload, existing = null) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Study payload must be an object.");
  }
  const status = payload.status ?? "studying";
  if (!STATUSES.has(status)) throw new Error("Invalid lesson status.");
  const responses = payload.responses ?? {};
  const plan = payload.plan ?? {};
  const reflection = payload.reflection ?? {};
  if ([responses, plan, reflection].some((value) => !value || typeof value !== "object" || Array.isArray(value))) {
    throw new Error("Study data has an invalid shape.");
  }
  const cleanedResponses = {};
  for (const [promptId, response] of Object.entries(responses)) {
    if (!response || typeof response !== "object" || Array.isArray(response)) {
      throw new Error("Study response has an invalid shape.");
    }
    cleanedResponses[promptId.slice(0, 80)] = {
      answer: sanitizeText(response.answer),
      self_assessment: sanitizeText(response.self_assessment, "unrated").slice(0, 32),
    };
  }
  const planFields = ["target_function", "smallest_slice", "must_do", "must_not_do", "first_proof", "open_question"];
  const reflectionFields = ["feynman_explanation", "feynman_limit", "mental_model", "next_step"];
  const cleanedPlan = Object.fromEntries(planFields.map((field) => [field, sanitizeText(plan[field])]));
  const cleanedReflection = Object.fromEntries(reflectionFields.map((field) => [field, sanitizeText(reflection[field])]));
  const learning = sanitizeLearning({ ...payload, lesson_id: lessonId }, existing, status, cleanedPlan);
  return {
    lesson_id: lessonId,
    status,
    updated_at: new Date().toISOString(),
    responses: cleanedResponses,
    plan: cleanedPlan,
    reflection: cleanedReflection,
    ...learning,
  };
}

async function loadState(store) {
  const state = await store.get(STORE_KEY, { type: "json" });
  return state && typeof state === "object" && !Array.isArray(state)
    ? {
      schema_version: 3,
      lessons: state.lessons && typeof state.lessons === "object" ? state.lessons : {},
      reviews: state.reviews && typeof state.reviews === "object" ? state.reviews : {},
    }
    : { schema_version: 3, lessons: {}, reviews: {} };
}

function lessonFromPath(path) {
  const match = path.match(/^\/lessons\/([^/]+)\/study$/);
  return match && LESSON_ID.test(match[1]) ? match[1] : null;
}

function dueReviews(state, limit = 3) {
  const now = Date.now();
  return Object.values(state.reviews)
    .filter((review) => review && review.due_at && Date.parse(review.due_at) <= now)
    .sort((left, right) => Date.parse(left.due_at) - Date.parse(right.due_at))
    .slice(0, limit)
    .map((review, index) => {
      const question = REVIEW_QUESTION_TYPES[(review.interval_index + index) % REVIEW_QUESTION_TYPES.length];
      return { lesson_id: review.lesson_id, kind: review.kind || "retention", due_at: review.due_at, prompt_id: question[0], question: question[1] };
    });
}

function reviewKey(lessonId, kind) { return `${lessonId}:${kind}`; }

function scheduleReview(state, lessonId, study) {
  const kind = study.phase === "learned" ? "retention"
    : study.phase === "ready_to_implement" ? "pre_implementation" : null;
  if (!kind) return;
  const key = reviewKey(lessonId, kind);
  const existing = state.reviews[key];
  if (existing?.due_at) return;
  const due = new Date(Date.now() + REVIEW_INTERVAL_DAYS[0] * 86_400_000).toISOString();
  state.reviews[key] = { ...emptyReview(lessonId, kind), due_at: due };
}

function reviewFromPath(path) {
  const match = path.match(/^\/reviews\/([^/]+)(?:\/(pre_implementation|retention))?$/);
  return match && LESSON_ID.test(match[1])
    ? { lessonId: match[1], kind: match[2] || "retention" }
    : null;
}

export default async (request) => {
  if (!isAuthorized(request)) return json({ error: "Study sync token required." }, 401);

  const path = requestPath(request);
  const store = getStore(STORE_NAME);
  const lessonId = lessonFromPath(path);

  if (request.method === "GET" && path === "/export") {
    return json(await loadState(store));
  }
  if (request.method === "GET" && path === "/progress") {
    const state = await loadState(store);
    const lessons = Object.values(state.lessons)
      .map(({ lesson_id, status, phase, updated_at }) => ({ lesson_id, status, phase: phase || phaseForStatus(status), updated_at }))
      .sort((left, right) => left.lesson_id.localeCompare(right.lesson_id));
    return json({ lessons });
  }
  if (request.method === "GET" && path === "/reviews/due") {
    const state = await loadState(store);
    return json({ reviews: dueReviews(state) });
  }
  const reviewTarget = reviewFromPath(path);
  if (reviewTarget && request.method === "PUT") {
    try {
      const payload = JSON.parse(await request.text());
      const rating = payload?.rating;
      if (!new Set(["easy", "hard", "again"]).has(rating)) throw new Error("Invalid review rating.");
      const state = await loadState(store);
      const matchingKey = reviewKey(reviewTarget.lessonId, reviewTarget.kind);
      const legacyKey = Object.keys(state.reviews).find((key) =>
        state.reviews[key]?.lesson_id === reviewTarget.lessonId
        && (state.reviews[key]?.kind || "retention") === reviewTarget.kind
      );
      const storageKey = legacyKey || matchingKey;
      const review = state.reviews[storageKey] || emptyReview(reviewTarget.lessonId, reviewTarget.kind);
      const nextIndex = rating === "easy"
        ? Math.min(review.interval_index + 1, REVIEW_INTERVAL_DAYS.length - 1)
        : rating === "hard" ? Math.max(review.interval_index, 0) : 0;
      review.interval_index = nextIndex;
      review.last_reviewed_at = new Date().toISOString();
      review.due_at = new Date(Date.now() + REVIEW_INTERVAL_DAYS[nextIndex] * 86_400_000).toISOString();
      review.answers = { ...(payload.answers && typeof payload.answers === "object" ? payload.answers : {}) };
      state.reviews[matchingKey] = review;
      if (storageKey !== matchingKey) delete state.reviews[storageKey];
      await store.setJSON(STORE_KEY, state);
      return json(review);
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : "Invalid review payload." }, 400);
    }
  }
  if (lessonId && request.method === "GET") {
    const state = await loadState(store);
    return json(state.lessons[lessonId] || emptyStudy(lessonId));
  }
  if (lessonId && request.method === "PUT") {
    const body = await request.text();
    if (new TextEncoder().encode(body).byteLength > MAX_BODY_BYTES) {
      return json({ error: "Study payload is too large." }, 400);
    }
    try {
      const state = await loadState(store);
      const study = sanitizeStudy(lessonId, JSON.parse(body), state.lessons[lessonId] || emptyStudy(lessonId));
      state.lessons[lessonId] = study;
      scheduleReview(state, lessonId, study);
      await store.setJSON(STORE_KEY, state);
      return json(study);
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : "Invalid study payload." }, 400);
    }
  }
  return json({ error: "Unknown study endpoint." }, 404);
};
