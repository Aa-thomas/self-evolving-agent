function revealAnswer(button) {
  const targetId = button.getAttribute("data-target");
  const target = document.getElementById(targetId);
  if (!target) return;
  target.classList.toggle("visible");
  button.textContent = target.classList.contains("visible") ? "Hide answer" : "Reveal answer";
}

function checkKeywords(button) {
  const practice = button.closest(".practice");
  if (!practice) return;

  const input = practice.querySelector("textarea");
  const feedback = practice.querySelector(".feedback");
  const rawKeywords = button.getAttribute("data-keywords") || "";
  const keywords = rawKeywords.split(",").map((item) => item.trim().toLowerCase()).filter(Boolean);
  const text = (input?.value || "").toLowerCase();
  const found = keywords.filter((keyword) => text.includes(keyword));

  if (!feedback) return;

  if (found.length === keywords.length) {
    feedback.textContent = "Good. You named the required moving parts.";
    feedback.className = "feedback good";
    return;
  }

  const missing = keywords.filter((keyword) => !found.includes(keyword));
  feedback.textContent = `Missing: ${missing.join(", ")}. Try again before revealing the answer.`;
  feedback.className = "feedback";
}

function checkChoice(button) {
  const practice = button.closest(".practice");
  if (!practice) return;

  const feedback = practice.querySelector(".feedback");
  const expected = button.getAttribute("data-answer");
  const selected = practice.querySelector("input[type='radio']:checked");
  if (!feedback || !expected) return;

  if (!selected) {
    feedback.textContent = "Choose an answer first, then check the feedback.";
    feedback.className = "feedback";
    return;
  }

  const selectedValue = selected.getAttribute("value") || "";
  const feedbackKey = `feedback${selectedValue.replace(/(^|-)([a-z])/g, (_, __, letter) => letter.toUpperCase())}`;
  const optionFeedback = button.dataset[feedbackKey];

  if (selectedValue === expected) {
    feedback.textContent = optionFeedback || button.getAttribute("data-correct") || "Correct. Your choice preserves the lesson invariant.";
    feedback.className = "feedback good";
    document.dispatchEvent(new CustomEvent("learning:practice-attempt", {
      detail: { passed: true, selected: selectedValue, expected, kind: "choice" },
    }));
    return;
  }

  feedback.textContent = optionFeedback || button.getAttribute("data-incorrect") || "Not quite. Re-check the invariant and the failure case.";
  feedback.className = "feedback";
  document.dispatchEvent(new CustomEvent("learning:practice-attempt", {
    detail: { passed: false, selected: selectedValue, expected, kind: "choice" },
  }));
}

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;

  if (target.matches("[data-reveal]")) {
    revealAnswer(target);
  }

  if (target.matches("[data-check-keywords]")) {
    checkKeywords(target);
  }

  if (target.matches("[data-check-choice]")) {
    checkChoice(target);
  }
});
