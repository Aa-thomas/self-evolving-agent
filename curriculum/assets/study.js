const LESSON_CONTEXT = {
  "0001-model-call-primitive": { target: "call_model", proof: "Model call record test" },
  "0002-message-state-primitive": { target: "message state", proof: "Second-call message-state proof" },
  "0003-manual-tool-protocol": { target: "parse_tool_request", proof: "Valid and invalid request cases" },
  "0004-schema-validation": { target: "validate_tool_args", proof: "One validation gate test" },
  "0005-sandboxed-file-tools": { target: "read_file / write_file / list_files", proof: "Sandbox path test" },
  "0006-agent-loop-primitive": { target: "run_agent", proof: "test_submit_stops_loop" },
  "0007-trace-logger": { target: "trace event contract", proof: "One replayable trace case" },
  "0008-eval-runner": { target: "run_eval_suite", proof: "One local evaluation case" },
};

function lessonIdFromPage() {
  const match = window.location.pathname.match(/\/(\d{4}-[a-z0-9-]+)\.html$/);
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

function renderStudyPanel(lessonId) {
  const context = LESSON_CONTEXT[lessonId] || { target: "", proof: "" };
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
    <p class="study-intro">Notes sync to your private study record. No code is edited or run here.</p>
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
      <label for="jot-notes">Jot notes</label>
      <textarea id="jot-notes" data-response-id="jot_notes" placeholder="Raw fragments, keywords, examples, confusions, or copied error messages. Keep this messy."></textarea>
      <label for="one-sentence">In one sentence, what is this primitive?</label>
      <textarea id="one-sentence" data-response-id="one_sentence" placeholder="Explain it in your own words."></textarea>
      <label for="invariant">What must never happen?</label>
      <textarea id="invariant" data-response-id="invariant" placeholder="Name the boundary or invariant."></textarea>
      <label for="failure">What failure would this prevent?</label>
      <textarea id="failure" data-response-id="failure" placeholder="Describe a realistic bad outcome."></textarea>
      <label for="evidence">What evidence would prove the behavior?</label>
      <textarea id="evidence" data-response-id="evidence" placeholder="A test, trace, eval, or observable result."></textarea>
      <label for="understanding">How clear is this now?</label>
      <select id="understanding" data-response-assessment="one_sentence">
        <option value="unrated">Choose later</option>
        <option value="clear">Clear</option>
        <option value="needs_revision">Needs revision</option>
        <option value="fuzzy">Still fuzzy</option>
      </select>
    </section>
    <section data-study-view="plan" class="study-view">
      <p class="study-step">2 of 3 · Prepare the home session</p>
      <p class="study-context">Suggested target: <code>${context.target}</code><br>Suggested first proof: <code>${context.proof}</code></p>
      <label for="target-function">Function or artifact to work on</label>
      <input id="target-function" data-plan-field="target_function" placeholder="${context.target}">
      <label for="smallest-slice">Smallest behavior to implement</label>
      <textarea id="smallest-slice" data-plan-field="smallest_slice" placeholder="One narrow behavior, not the whole feature."></textarea>
      <label for="must-do">Must do</label>
      <textarea id="must-do" data-plan-field="must_do" placeholder="List the essential behavior."></textarea>
      <label for="must-not-do">Must not do</label>
      <textarea id="must-not-do" data-plan-field="must_not_do" placeholder="List scope boundaries and forbidden behavior."></textarea>
      <label for="first-proof">First proof to run at home</label>
      <input id="first-proof" data-plan-field="first_proof" placeholder="${context.proof}">
      <label for="open-question">One fuzzy question</label>
      <textarea id="open-question" data-plan-field="open_question" placeholder="Name what you need to check before coding."></textarea>
    </section>
    <section data-study-view="reflect" class="study-view">
      <p class="study-step">3 of 3 · Close the study session</p>
      <label for="feynman-explanation">Explain this to a smart 12-year-old</label>
      <textarea id="feynman-explanation" data-reflection-field="feynman_explanation" placeholder="Use plain language, one analogy, and no framework jargon."></textarea>
      <label for="feynman-limit">Where does that explanation break?</label>
      <textarea id="feynman-limit" data-reflection-field="feynman_limit" placeholder="Name one detail your simple explanation leaves out or risks oversimplifying."></textarea>
      <label for="mental-model">What changed in your mental model?</label>
      <textarea id="mental-model" data-reflection-field="mental_model" placeholder="Capture the correction or connection you want to remember."></textarea>
      <label for="next-step">Next smallest step when you are home</label>
      <textarea id="next-step" data-reflection-field="next_step" placeholder="Write a concrete, one-session action."></textarea>
      <div class="study-complete">
        <button type="button" data-mark-ready>Mark ready to implement</button>
        <p>Use the <a href="../study-workflow.html">Study Workflow</a> when you need the full method or a low-energy version.</p>
      </div>
    </section>
  `;
  document.body.append(panel);

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
    panel.querySelector("[data-study-status]").value = "ready_to_implement";
    scheduleSave(panel, lessonId, 0);
  });
  panel.querySelectorAll("[data-study-tab]").forEach((button) => {
    button.addEventListener("click", () => showStudyTab(panel, button.dataset.studyTab));
  });
  panel.querySelectorAll("textarea, input, select").forEach((field) => {
    field.addEventListener("input", () => scheduleSave(panel, lessonId));
    field.addEventListener("change", () => scheduleSave(panel, lessonId));
  });

  document.querySelectorAll(".practice textarea").forEach((textarea, index) => {
    const responseId = `lesson_practice_${index + 1}`;
    textarea.dataset.responseId = responseId;
    textarea.addEventListener("input", () => scheduleSave(panel, lessonId));
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
      if (!studyToken() && !connectStudy()) return setSaveState(panel, "Sync token required");
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
  const panel = renderStudyPanel(lessonId);
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
    const counts = { studying: 0, ready_to_implement: 0, review: 0 };
    lessonLinks.forEach((link) => {
      const lessonId = link.getAttribute("href").replace("lessons/", "").replace(".html", "");
      const state = byLesson.get(lessonId);
      if (!state || state.status === "not_started") return;
      counts[state.status] += 1;
      const badge = document.createElement("span");
      badge.className = `progress-badge ${state.status}`;
      badge.textContent = state.status.replaceAll("_", " ");
      link.append(badge);
    });
    progress.innerHTML = `<strong>${counts.studying} studying</strong><strong>${counts.ready_to_implement} ready to implement</strong><strong>${counts.review} marked for review</strong>`;
  } catch {
    progress.textContent = "Open a lesson and connect sync to track progress.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupLessonWorkspace();
  setupCourseHome();
});
