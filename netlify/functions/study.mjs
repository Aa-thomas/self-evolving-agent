import { getStore } from "@netlify/blobs";

const LESSON_ID = /^\d{4}-[a-z0-9-]+$/;
const STATUSES = new Set(["not_started", "studying", "ready_to_implement", "review"]);
const MAX_BODY_BYTES = 250_000;
const STORE_NAME = "study-workspace";
const STORE_KEY = "current";

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
  };
}

function sanitizeText(value, defaultValue = "") {
  if (value === undefined || value === null) return defaultValue;
  if (typeof value !== "string") throw new Error("Study fields must be text.");
  return value.slice(0, 12_000);
}

function sanitizeStudy(lessonId, payload) {
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
  const reflectionFields = ["mental_model", "next_step"];
  const cleanedPlan = Object.fromEntries(planFields.map((field) => [field, sanitizeText(plan[field])]));
  const cleanedReflection = Object.fromEntries(reflectionFields.map((field) => [field, sanitizeText(reflection[field])]));
  return {
    lesson_id: lessonId,
    status,
    updated_at: new Date().toISOString(),
    responses: cleanedResponses,
    plan: cleanedPlan,
    reflection: cleanedReflection,
  };
}

async function loadState(store) {
  const state = await store.get(STORE_KEY, { type: "json" });
  return state && typeof state === "object" && !Array.isArray(state)
    ? { schema_version: 1, lessons: state.lessons && typeof state.lessons === "object" ? state.lessons : {} }
    : { schema_version: 1, lessons: {} };
}

function lessonFromPath(path) {
  const match = path.match(/^\/lessons\/([^/]+)\/study$/);
  return match && LESSON_ID.test(match[1]) ? match[1] : null;
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
      .map(({ lesson_id, status, updated_at }) => ({ lesson_id, status, updated_at }))
      .sort((left, right) => left.lesson_id.localeCompare(right.lesson_id));
    return json({ lessons });
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
      const study = sanitizeStudy(lessonId, JSON.parse(body));
      const state = await loadState(store);
      state.lessons[lessonId] = study;
      await store.setJSON(STORE_KEY, state);
      return json(study);
    } catch (error) {
      return json({ error: error instanceof Error ? error.message : "Invalid study payload." }, 400);
    }
  }
  return json({ error: "Unknown study endpoint." }, 404);
};
