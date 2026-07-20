const DEFAULT_STUDY_CONTRACT = {
  objective: "Form a usable model, plan one narrow implementation slice, and interpret the evidence honestly.",
  context_cards: ["starting_artifacts", "target_artifacts", "proof_artifacts", "failure_contract"],
  think: {
    jot_notes: { label: "Jot notes", placeholder: "Raw fragments, questions, examples, and evidence. Keep this messy." },
    prompts: [
      { id: "model", label: "What is the model?", prompt: "Explain the central boundary or invariant in your own words.", kind: "explanation" },
      { id: "decision", label: "What decision matters?", prompt: "Name the decision this lesson asks you to make.", kind: "judgment" },
      { id: "evidence", label: "What evidence would matter?", prompt: "Name the test, trace, or output that could support the claim.", kind: "evidence" },
    ],
  },
  plan: {
    intro: "Prepare one bounded implementation handoff.",
    fields: {
      target_function: { label: "Function or artifact to work on", placeholder: "One target artifact." },
      smallest_slice: { label: "Smallest behavior to implement", placeholder: "One narrow behavior, not the whole feature." },
      must_do: { label: "Must do", placeholder: "List the essential behavior." },
      must_not_do: { label: "Must not do", placeholder: "List scope boundaries and forbidden behavior." },
      first_proof: { label: "First proof to run at home", placeholder: "One executable proof." },
      open_question: { label: "One fuzzy question", placeholder: "Name what you need to check before coding." },
    },
  },
  reflect: {
    feynman: { label: "Explain this to a smart 12-year-old", subject: "the mechanism you just studied", placeholder: "Use plain language and one analogy." },
    feynman_limit: { label: "Where does that explanation break?", prompt: "Name one important detail the simple explanation hides." },
    prediction_vs_evidence: { label: "What did the evidence change?", prompt: "Compare your prediction with the result." },
    mental_model: { label: "What changed in your mental model?", prompt: "Capture the correction or connection you want to remember." },
    next_step: { label: "Next smallest step when you are home", prompt: "Write a concrete, one-session action." },
  },
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

function studyContractFor(lesson) {
  return lesson?.study_contract || DEFAULT_STUDY_CONTRACT;
}

async function loadLessonContext(lessonId) {
  try {
    const response = await fetch("../learning-flow.json");
    if (!response.ok) throw new Error("Manifest unavailable");
    const lesson = (await response.json()).lessons?.[lessonId];
    return {
      lesson,
      study: studyContractFor(lesson),
      target: lesson?.target_artifacts?.source_files?.join(", ") || "No implementation target yet",
      proof: lesson?.proof_artifacts?.proof_command?.join(" ") || "No proof configured yet",
    };
  } catch {
    return {
      lesson: null,
      study: DEFAULT_STUDY_CONTRACT,
      target: "Check the lesson implementation target",
      proof: "Choose one executable proof",
    };
  }
}

function listEntries(label, values) {
  if (!Array.isArray(values) || !values.length) return [];
  return values.map((value) => `${label}: ${value}`);
}

function contextEntries(lesson, cardName) {
  if (!lesson) return [];
  if (cardName === "starting_artifacts") {
    const artifacts = lesson.starting_artifacts || {};
    return [
      ...listEntries("Source", artifacts.source_files),
      ...listEntries("Symbol", artifacts.symbols),
      ...listEntries("Test", artifacts.tests),
      ...listEntries("Fixture or trace", artifacts.scenario_sources),
    ];
  }
  if (cardName === "target_artifacts") {
    const artifacts = lesson.target_artifacts || {};
    return [
      ...listEntries("Source", artifacts.source_files),
      ...listEntries("Test", artifacts.tests),
      ...(artifacts.expected_artifact ? [`Expected result: ${artifacts.expected_artifact}`] : []),
    ];
  }
  if (cardName === "proof_artifacts") {
    const artifacts = lesson.proof_artifacts || {};
    return [
      ...(artifacts.proof_command?.length ? [`Command: ${artifacts.proof_command.join(" ")}`] : []),
      ...listEntries("Assertion", artifacts.assertions),
      ...listEntries("Trace or output", artifacts.traces_or_output),
    ];
  }
  if (cardName === "failure_contract") {
    const failure = lesson.failure_contract || {};
    return [
      ...(failure.source ? [`Source: ${failure.source}`] : []),
      ...(failure.symptom ? [`Symptom: ${failure.symptom}`] : []),
      ...(failure.responsible_boundary ? [`Responsible boundary: ${failure.responsible_boundary}`] : []),
      ...(failure.regression_target ? [`Regression target: ${failure.regression_target}`] : []),
    ];
  }
  return [];
}

function contextTitle(cardName) {
  return {
    starting_artifacts: "Starting artifacts",
    target_artifacts: "Target artifacts",
    proof_artifacts: "Proof artifacts",
    failure_contract: "Failure to explain",
  }[cardName] || "Lesson context";
}

function renderContextCards(lesson, cards) {
  const rendered = cards.map((cardName) => {
    const entries = contextEntries(lesson, cardName);
    if (!entries.length) return "";
    return `<section class="study-context-card"><h3>${escapeHtml(contextTitle(cardName))}</h3><ul>${entries.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul></section>`;
  }).join("");
  return rendered ? `<section class="study-context-cards" aria-label="Lesson evidence context">${rendered}</section>` : "";
}

function lessonIdFromPage() {
  const match = window.location.pathname.match(/\/(\d{4}-[a-z0-9-]+)(?:\.html)?$/);
  return match ? match[1] : null;
}

function apiPath(lessonId) {
  return `/api/lessons/${lessonId}/study`;
}

const STUDY_TOKEN_KEY = "study-access-token";

function studyToken() {
  return window.sessionStorage.getItem(STUDY_TOKEN_KEY);
}

function requestStudy(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = studyToken();
  if (token) headers.set("X-Study-Token", token);
  return fetch(path, { ...options, headers });
}

function connectStudy() {
  const token = window.prompt("Enter your study sync token. It is kept only for this browser session.");
  if (!token) return false;
  window.sessionStorage.setItem(STUDY_TOKEN_KEY, token);
  return true;
}

const PLAN_FIELD_ORDER = ["target_function", "smallest_slice", "must_do", "must_not_do", "first_proof", "open_question"];

function renderThink(study) {
  const jot = study.think.jot_notes;
  const prompts = study.think.prompts.map((prompt) => {
    const id = `study-think-${prompt.id}`;
    return `
      <label for="${escapeHtml(id)}">${escapeHtml(prompt.label)}</label>
      <p class="study-field-hint">${escapeHtml(prompt.prompt)}</p>
      <textarea id="${escapeHtml(id)}" data-response-id="${escapeHtml(prompt.id)}" placeholder="Write your own answer before reopening the solution."></textarea>
    `;
  }).join("");
  return `
    <label for="jot-notes">${escapeHtml(jot.label)}</label>
    <textarea id="jot-notes" data-response-id="jot_notes" placeholder="${escapeHtml(jot.placeholder)}"></textarea>
    ${prompts}
  `;
}

function renderPlan(study, context) {
  const fields = PLAN_FIELD_ORDER.map((fieldName) => {
    const field = study.plan.fields[fieldName];
    const id = fieldName.replaceAll("_", "-");
    const element = fieldName === "target_function" || fieldName === "first_proof" ? "input" : "textarea";
    const fallback = fieldName === "target_function" ? context.target : fieldName === "first_proof" ? context.proof : "";
    const placeholder = field.placeholder || fallback;
    const input = element === "input"
      ? `<input id="${id}" data-plan-field="${fieldName}" placeholder="${escapeHtml(placeholder)}">`
      : `<textarea id="${id}" data-plan-field="${fieldName}" placeholder="${escapeHtml(placeholder)}"></textarea>`;
    return `<label for="${id}">${escapeHtml(field.label)}</label>${input}`;
  }).join("");
  return `<p class="study-plan-intro">${escapeHtml(study.plan.intro)}</p>${fields}`;
}

function renderReflect(study) {
  const reflect = study.reflect;
  return `
    <label for="feynman-explanation">${escapeHtml(reflect.feynman.label)}</label>
    <p class="study-field-hint">Explain ${escapeHtml(reflect.feynman.subject)}.</p>
    <textarea id="feynman-explanation" data-reflection-field="feynman_explanation" placeholder="${escapeHtml(reflect.feynman.placeholder)}"></textarea>
    <label for="feynman-limit">${escapeHtml(reflect.feynman_limit.label)}</label>
    <p class="study-field-hint">${escapeHtml(reflect.feynman_limit.prompt)}</p>
    <textarea id="feynman-limit" data-reflection-field="feynman_limit" placeholder="Write the important limit in your own words."></textarea>
    <label for="prediction-vs-evidence">${escapeHtml(reflect.prediction_vs_evidence.label)}</label>
    <p class="study-field-hint">${escapeHtml(reflect.prediction_vs_evidence.prompt)}</p>
    <textarea id="prediction-vs-evidence" data-reflection-field="prediction_vs_evidence" placeholder="Connect one prediction to one observed result."></textarea>
    <label for="mental-model">${escapeHtml(reflect.mental_model.label)}</label>
    <p class="study-field-hint">${escapeHtml(reflect.mental_model.prompt)}</p>
    <textarea id="mental-model" data-reflection-field="mental_model" placeholder="Capture the correction or connection you want to remember."></textarea>
    <label for="next-step">${escapeHtml(reflect.next_step.label)}</label>
    <p class="study-field-hint">${escapeHtml(reflect.next_step.prompt)}</p>
    <textarea id="next-step" data-reflection-field="next_step" placeholder="Write a concrete, one-session action."></textarea>
  `;
}

function renderStudyPanel(lessonId, context) {
  const study = context.study;
  const panel = document.createElement("aside");
  panel.className = "study-panel";
  panel.id = "study-workspace";
  panel.setAttribute("aria-label", "Lesson study workspace");
  panel.innerHTML = `
    <div class="study-panel-header">
      <div>
        <p class="study-kicker">Your study workspace</p>
        <h2>Make the lesson usable later</h2>
      </div>
      <button class="icon-button" type="button" data-study-close aria-label="Close study workspace">Close</button>
    </div>
    <p class="study-intro">${escapeHtml(study.objective)} Notes sync to your private study record; no code is edited or run here.</p>
    <div class="study-status-row">
      <label for="lesson-status">Session</label>
      <select id="lesson-status" data-study-status>
        <option value="not_started">Not started</option>
        <option value="studying">Studying</option>
        <option value="ready_to_implement">Ready to implement</option>
        <option value="review">Review later</option>
      </select>
      <span class="save-state" data-save-state>Loading</span>
      <button class="text-button" type="button" data-study-connect>Connect sync</button>
    </div>
    <nav class="study-tabs" aria-label="Study workspace steps">
      <button type="button" data-study-tab="think" class="active">Think</button>
      <button type="button" data-study-tab="plan">Plan</button>
      <button type="button" data-study-tab="reflect">Reflect</button>
    </nav>
    <section data-study-view="think" class="study-view active">
      <p class="study-step">1 of 3 · Before revisiting the prose</p>
      ${renderContextCards(context.lesson, study.context_cards)}
      ${renderThink(study)}
    </section>
    <section data-study-view="plan" class="study-view">
      <p class="study-step">2 of 3 · Prepare the home session</p>
      ${renderPlan(study, context)}
    </section>
    <section data-study-view="reflect" class="study-view">
      <p class="study-step">3 of 3 · Close the study session</p>
      ${renderReflect(study)}
      <div class="study-complete">
        <button type="button" data-mark-ready>Mark ready to implement</button>
        <p>Use the <a href="../study-workflow.html">Study Workflow</a> when you need the full method or a low-energy version.</p>
      </div>
    </section>
  `;
  document.body.append(panel);
  panel.learningState = {
    phase: "not_started",
    milestones: {},
    evidence: { practice_attempts: [], artifact_inspections: [], proof_runs: [], trace_paths: [], failure_explanations: [], regression_paths: [], reconstruction_attempts: [], recall_attempts: [] },
  };

  const launcher = document.createElement("button");
  launcher.className = "study-launcher";
  launcher.type = "button";
  launcher.textContent = "Study workspace";
  launcher.setAttribute("aria-expanded", "false");
  launcher.setAttribute("aria-controls", panel.id);
  document.body.append(launcher);

  launcher.addEventListener("click", () => setPanelOpen(panel, launcher, true));
  panel.querySelector("[data-study-close]").addEventListener("click", () => setPanelOpen(panel, launcher, false));
  panel.querySelector("[data-study-connect]").addEventListener("click", async () => {
    if (connectStudy()) await loadStudy(panel, lessonId);
  });
  panel.querySelector("[data-mark-ready]").addEventListener("click", () => {
    const plan = valuesFor(panel, "[data-plan-field]", "planField");
    const missing = ["target_function", "smallest_slice", "must_do", "must_not_do", "first_proof"]
      .filter((field) => !plan[field]?.trim());
    if (missing.length) {
      setSaveState(panel, "Complete the implementation handoff first");
      showStudyTab(panel, "plan");
      return;
    }
    panel.querySelector("[data-study-status]").value = "ready_to_implement";
    panel.learningState.phase = "ready_to_implement";
    scheduleSave(panel, lessonId, 0);
  });
  panel.querySelectorAll("[data-study-tab]").forEach((button) => {
    button.addEventListener("click", () => showStudyTab(panel, button.dataset.studyTab));
  });
  panel.querySelectorAll("textarea, input, select").forEach((field) => {
    const beginStudying = () => {
      if (field.matches("[data-study-status]") || panel.learningState.phase !== "not_started") return;
      panel.learningState.phase = "studying";
      panel.querySelector("[data-study-status]").value = "studying";
    };
    field.addEventListener("input", () => { beginStudying(); scheduleSave(panel, lessonId); });
    field.addEventListener("change", () => { beginStudying(); scheduleSave(panel, lessonId); });
  });
  panel.querySelector("[data-study-status]").addEventListener("change", (event) => {
    const value = event.target.value;
    if (value === "ready_to_implement") {
      event.target.value = panel.learningState.phase === "ready_to_implement" ? value : "studying";
      if (event.target.value !== value) setSaveState(panel, "Use Mark ready after completing the plan");
      return;
    }
    if (value === "not_started" || value === "studying") panel.learningState.phase = value;
  });

  document.querySelectorAll(".practice textarea").forEach((textarea, index) => {
    const responseId = `lesson_practice_${index + 1}`;
    textarea.dataset.responseId = responseId;
    textarea.addEventListener("input", () => scheduleSave(panel, lessonId));
  });

  document.addEventListener("learning:prediction-committed", (event) => {
    const attempt = { ...event.detail, occurred_at: new Date().toISOString() };
    panel.learningState.evidence.practice_attempts = [
      ...(panel.learningState.evidence.practice_attempts || []), attempt,
    ].slice(-50);
    if (panel.querySelector("[data-study-status]").value === "not_started") {
      panel.querySelector("[data-study-status]").value = "studying";
      panel.learningState.phase = "studying";
    }
    scheduleSave(panel, lessonId, 0);
  });
  document.addEventListener("learning:case-attempt", (event) => {
    const attempt = { ...event.detail, occurred_at: new Date().toISOString() };
    panel.learningState.evidence.practice_attempts = [
      ...(panel.learningState.evidence.practice_attempts || []), attempt,
    ].slice(-50);
    scheduleSave(panel, lessonId, 0);
  });

  return panel;
}

function setPanelOpen(panel, launcher, isOpen) {
  panel.classList.toggle("open", isOpen);
  launcher.setAttribute("aria-expanded", String(isOpen));
  document.body.classList.toggle("study-panel-open", isOpen);
  if (isOpen) panel.querySelector("textarea, input")?.focus();
}

function showStudyTab(panel, tabName) {
  panel.querySelectorAll("[data-study-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.studyTab === tabName);
  });
  panel.querySelectorAll("[data-study-view]").forEach((view) => {
    view.classList.toggle("active", view.dataset.studyView === tabName);
  });
}

function hydrate(panel, data) {
  panel.querySelector("[data-study-status]").value = data.status || "not_started";
  panel.querySelectorAll("[data-response-id]").forEach((field) => {
    const response = data.responses?.[field.dataset.responseId];
    field.value = response?.answer || "";
  });
  panel.querySelectorAll("[data-response-assessment]").forEach((field) => {
    const response = data.responses?.[field.dataset.responseAssessment];
    field.value = response?.self_assessment || "unrated";
  });
  panel.querySelectorAll("[data-plan-field]").forEach((field) => {
    field.value = data.plan?.[field.dataset.planField] || "";
  });
  panel.querySelectorAll("[data-reflection-field]").forEach((field) => {
    field.value = data.reflection?.[field.dataset.reflectionField] || "";
  });
  panel.learningState = {
    phase: data.phase || "not_started",
    milestones: data.milestones || {},
    evidence: data.evidence || { practice_attempts: [], artifact_inspections: [], proof_runs: [], trace_paths: [], failure_explanations: [], regression_paths: [], reconstruction_attempts: [], recall_attempts: [] },
  };
}

function collectStudyData(panel) {
  const responses = {};
  panel.querySelectorAll("[data-response-id]").forEach((field) => {
    responses[field.dataset.responseId] = { answer: field.value, self_assessment: "unrated" };
  });
  panel.querySelectorAll("[data-response-assessment]").forEach((field) => {
    const responseId = field.dataset.responseAssessment;
    responses[responseId] = responses[responseId] || { answer: "", self_assessment: "unrated" };
    responses[responseId].self_assessment = field.value;
  });
  document.querySelectorAll(".practice textarea[data-response-id]").forEach((field) => {
    responses[field.dataset.responseId] = { answer: field.value, self_assessment: "unrated" };
  });
  return {
    status: panel.querySelector("[data-study-status]").value,
    responses,
    plan: valuesFor(panel, "[data-plan-field]", "planField"),
    reflection: valuesFor(panel, "[data-reflection-field]", "reflectionField"),
    phase: panel.learningState.phase,
    milestones: panel.learningState.milestones,
    evidence: panel.learningState.evidence,
    event_source: "lesson-site",
  };
}

function valuesFor(panel, selector, datasetKey) {
  return Array.from(panel.querySelectorAll(selector)).reduce((values, field) => {
    values[field.dataset[datasetKey]] = field.value;
    return values;
  }, {});
}

let saveTimer;
function scheduleSave(panel, lessonId, delay = 550) {
  window.clearTimeout(saveTimer);
  setSaveState(panel, "Saving");
  saveTimer = window.setTimeout(async () => {
    try {
      if (!studyToken()) return setSaveState(panel, "Connect sync to save notes");
      const response = await requestStudy(apiPath(lessonId), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectStudyData(panel)),
      });
      if (response.status === 401) {
        window.sessionStorage.removeItem(STUDY_TOKEN_KEY);
        return setSaveState(panel, "Sync token required");
      }
      if (!response.ok) throw new Error("Save failed");
      setSaveState(panel, "Saved");
    } catch {
      setSaveState(panel, "Could not save");
    }
  }, delay);
}

function setSaveState(panel, state) {
  panel.querySelector("[data-save-state]").textContent = state;
}

async function loadStudy(panel, lessonId) {
  try {
    const response = await requestStudy(apiPath(lessonId));
    if (response.status === 401) return setSaveState(panel, "Connect sync to load notes");
    if (!response.ok) throw new Error("Load failed");
    hydrate(panel, await response.json());
    setSaveState(panel, "Synced");
  } catch {
    setSaveState(panel, "Connect sync to save notes");
  }
}

async function setupLessonWorkspace() {
  const lessonId = lessonIdFromPage();
  if (!lessonId) return;
  const panel = renderStudyPanel(lessonId, await loadLessonContext(lessonId));
  await loadStudy(panel, lessonId);
  document.querySelectorAll(".site-nav").forEach((nav) => {
    if (!nav.querySelector("[data-workflow-link]")) {
      const link = document.createElement("a");
      link.href = "../study-workflow.html";
      link.dataset.workflowLink = "";
      link.textContent = "Study workflow";
      nav.insertBefore(link, nav.firstChild);
    }
  });
}

async function setupCourseHome() {
  const progress = document.querySelector("#study-progress");
  if (!progress) return;
  try {
    const response = await requestStudy("/api/progress");
    if (response.status === 401) {
      progress.textContent = "Open a lesson and connect sync to see your progress.";
      return;
    }
    if (!response.ok) throw new Error("Progress failed");
    const data = await response.json();
    const byLesson = new Map(data.lessons.map((item) => [item.lesson_id, item]));
    const lessonLinks = Array.from(document.querySelectorAll(".lesson-index a"));
    const counts = { studying: 0, ready_to_implement: 0, implementing: 0, consolidating: 0, learned: 0 };
    lessonLinks.forEach((link) => {
      const lessonId = link.getAttribute("href").replace("lessons/", "").replace(".html", "");
      const state = byLesson.get(lessonId);
      if (!state || state.phase === "not_started") return;
      const phase = state.phase || state.status;
      counts[phase] = (counts[phase] || 0) + 1;
      const badge = document.createElement("span");
      badge.className = `progress-badge ${phase}`;
      badge.textContent = phase.replaceAll("_", " ");
      link.append(badge);
    });
    progress.innerHTML = `<strong>${counts.studying} studying</strong><strong>${counts.ready_to_implement + counts.implementing} building</strong><strong>${counts.consolidating} consolidating</strong><strong>${counts.learned} learned</strong>`;
  } catch {
    progress.textContent = "Open a lesson and connect sync to track progress.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupLessonWorkspace();
  setupCourseHome();
});
