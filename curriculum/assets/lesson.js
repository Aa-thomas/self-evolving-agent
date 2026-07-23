const completedCases = new Map();
let revealId = 0;

function revealAnswer(button) {
  const targetId = button.getAttribute("data-target");
  const target = document.getElementById(targetId);
  if (!target) return;
  target.classList.toggle("visible");
  button.textContent = target.classList.contains("visible") ? "Hide answer" : "Reveal answer";
}

function feedbackFor(container) {
  return container.querySelector("[data-feedback]") || container.querySelector(".feedback");
}

function showFeedback(container, message, passed = false) {
  const feedback = feedbackFor(container);
  if (!feedback) return;
  feedback.textContent = message;
  feedback.className = passed ? "feedback good" : "feedback";
}

function setupLectureReveals() {
  const reveals = [...document.querySelectorAll("[data-lecture-reveal='after-prediction']")];
  if (!reveals.length) return;
  reveals.forEach((section) => {
    if (!section.id) {
      revealId += 1;
      section.id = `lecture-after-prediction-${revealId}`;
    }
  });
  const controlledIds = reveals.map((section) => section.id).join(" ");
  document.querySelectorAll("[data-prediction-submit]").forEach((button) => {
    button.setAttribute("aria-controls", controlledIds);
    button.setAttribute("aria-expanded", "false");
  });
}

function revealLectureAfterPrediction(prediction, button) {
  const reveals = [...document.querySelectorAll("[data-lecture-reveal='after-prediction']")];
  if (!reveals.length) return;

  reveals.forEach((section) => section.hidden = false);
  button.setAttribute("aria-expanded", "true");

  let status = prediction.querySelector("[data-lecture-reveal-status]");
  if (!status) {
    status = document.createElement("p");
    status.className = "lecture-reveal-status";
    status.dataset.lectureRevealStatus = "";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    prediction.append(status);
  }
  status.textContent = "Prediction committed. The next lecture explanation is now available.";

  const firstReveal = reveals[0];
  const heading = firstReveal.matches("h1, h2, h3, h4, h5, h6")
    ? firstReveal
    : firstReveal.querySelector("h1, h2, h3, h4, h5, h6");
  if (heading) {
    if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
    heading.focus();
  }
}

function checkKeywords(button) {
  const practice = button.closest(".practice");
  if (!practice) return;
  const input = practice.querySelector("textarea");
  const rawKeywords = button.getAttribute("data-keywords") || "";
  const keywords = rawKeywords.split(",").map((item) => item.trim().toLowerCase()).filter(Boolean);
  const text = (input?.value || "").toLowerCase();
  const found = keywords.filter((keyword) => text.includes(keyword));
  if (found.length === keywords.length) {
    showFeedback(practice, "Good. You named the required moving parts.", true);
    return;
  }
  showFeedback(practice, `Missing: ${keywords.filter((keyword) => !found.includes(keyword)).join(", ")}. Try again before revealing the answer.`);
}

function commitPrediction(button) {
  const prediction = button.closest("[data-prediction]") || button.parentElement;
  if (!prediction) return;
  const selected = prediction.querySelector("[data-prediction-choice]:checked, input[type='radio']:checked");
  const rationale = prediction.querySelector("[data-prediction-rationale]");
  if (!selected || !rationale?.value.trim()) {
    showFeedback(prediction, "Choose an action and write a short rationale before revealing the explanation.");
    return;
  }
  prediction.querySelectorAll("[data-prediction-answer]").forEach((answer) => answer.hidden = false);
  revealLectureAfterPrediction(prediction, button);
  button.disabled = true;
  showFeedback(prediction, "Prediction committed. Compare your reasoning with the evidence now.", true);
  document.dispatchEvent(new CustomEvent("learning:prediction-committed", {
    detail: { kind: "prediction", selected: selected.value, rationale: rationale.value.trim() },
  }));
}

function commitCase(button) {
  const practiceCase = button.closest("[data-case-id]");
  if (!practiceCase) return;
  const selected = practiceCase.querySelector("input[type='radio']:checked");
  const rationale = practiceCase.querySelector("[data-rationale]");
  const expected = practiceCase.getAttribute("data-answer");
  if (!selected || !rationale?.value.trim()) {
    showFeedback(practiceCase, "Choose a case answer and explain the boundary before checking feedback.");
    return;
  }
  const passed = selected.value === expected;
  const message = passed
    ? practiceCase.getAttribute("data-correct") || "Correct. Your rationale should name the responsible boundary."
    : practiceCase.getAttribute("data-incorrect") || "Not quite. Re-check the first boundary that can reject this case.";
  showFeedback(practiceCase, message, passed);
  completedCases.set(practiceCase.getAttribute("data-case-id"), passed);
  document.dispatchEvent(new CustomEvent("learning:case-attempt", {
    detail: {
      kind: "case",
      case_id: practiceCase.getAttribute("data-case-id"),
      selected: selected.value,
      expected,
      rationale: rationale.value.trim(),
      passed,
    },
  }));
  const set = practiceCase.closest("[data-case-set]");
  const allCases = set?.querySelectorAll("[data-case-id]") || [];
  if (allCases.length && [...allCases].every((item) => completedCases.has(item.getAttribute("data-case-id")))) {
    const score = [...allCases].filter((item) => completedCases.get(item.getAttribute("data-case-id"))).length / allCases.length;
    document.dispatchEvent(new CustomEvent("learning:practice-set-completed", {
      detail: { case_count: allCases.length, score },
    }));
  }
}

function checkChoice(button) {
  const practice = button.closest(".practice");
  if (!practice) return;
  const selected = practice.querySelector("input[type='radio']:checked");
  const expected = button.getAttribute("data-answer");
  if (!selected || !expected) {
    showFeedback(practice, "Choose an answer first, then check the feedback.");
    return;
  }
  const selectedValue = selected.value || "";
  const feedbackKey = `feedback${selectedValue.replace(/(^|-)([a-z])/g, (_, __, letter) => letter.toUpperCase())}`;
  const passed = selectedValue === expected;
  showFeedback(practice, button.dataset[feedbackKey] || (passed ? button.getAttribute("data-correct") : button.getAttribute("data-incorrect")) || "Re-check the invariant and failure case.", passed);
  // Legacy one-click questions provide feedback but never create a passing practice record.
  const caseRoot = practice.closest("[data-case-id]");
  if (caseRoot) commitCase(button);
}

function deterministicShuffleChoices() {
  document.querySelectorAll("[data-case-id][data-shuffle-choices]").forEach((practiceCase) => {
    const list = practiceCase.querySelector("[data-choice-list]");
    if (!list) return;
    const items = [...list.children];
    let state = [...(practiceCase.getAttribute("data-case-id") || "")].reduce((value, char) => value + char.charCodeAt(0), 0) || 1;
    for (let index = items.length - 1; index > 0; index -= 1) {
      state = (state * 1664525 + 1013904223) >>> 0;
      const swap = state % (index + 1);
      [items[index], items[swap]] = [items[swap], items[index]];
    }
    items.forEach((item) => list.append(item));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  deterministicShuffleChoices();
  setupLectureReveals();
});
document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;
  if (target.matches("[data-reveal]")) revealAnswer(target);
  if (target.matches("[data-check-keywords]")) checkKeywords(target);
  if (target.matches("[data-prediction-submit]")) commitPrediction(target);
  if (target.matches("[data-case-submit]")) commitCase(target);
  if (target.matches("[data-check-choice]")) checkChoice(target);
});
