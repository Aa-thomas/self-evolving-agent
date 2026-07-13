const TOKEN_KEY = "study-access-token";

function token() { return window.sessionStorage.getItem(TOKEN_KEY); }

function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token()) headers.set("X-Study-Token", token());
  return fetch(path, { ...options, headers });
}

function connect() {
  const value = window.prompt("Enter your study sync token. It is kept only for this browser session.");
  if (value) window.sessionStorage.setItem(TOKEN_KEY, value);
  return Boolean(value);
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

async function loadReviews() {
  const root = document.querySelector("#review-check");
  const response = await request("/api/reviews/due");
  if (response.status === 401) {
    root.innerHTML = '<p>Connect sync to load your private review queue.</p><button type="button" data-connect>Connect sync</button>';
    root.querySelector("[data-connect]").addEventListener("click", () => { if (connect()) loadReviews(); });
    return;
  }
  if (!response.ok) throw new Error("Could not load reviews");
  const { reviews } = await response.json();
  if (!reviews.length) {
    root.innerHTML = "<p>Nothing is due today. Your next retention check will appear here when it is ready.</p>";
    return;
  }
  root.innerHTML = reviews.map((review, index) => `
    <article class="review-card" data-lesson-id="${escapeHtml(review.lesson_id)}">
      <p class="review-lesson">Lesson ${escapeHtml(review.lesson_id)} · ${review.kind === "pre_implementation" ? "Before implementation" : "Retention"}</p>
      <h2>${index + 1}. ${escapeHtml(review.question)}</h2>
      <textarea placeholder="Answer from memory" data-answer></textarea>
      <fieldset><legend>How did that feel?</legend>
        <label><input type="radio" name="rating-${index}" value="easy" checked> Easy</label>
        <label><input type="radio" name="rating-${index}" value="hard"> Hard</label>
        <label><input type="radio" name="rating-${index}" value="again"> Again soon</label>
      </fieldset>
    </article>`).join("") + '<button type="button" class="submit-reviews" data-submit>Schedule next reviews</button>';
  root.querySelector("[data-submit]").addEventListener("click", () => saveReviews(reviews));
}

async function saveReviews(reviews) {
  const root = document.querySelector("#review-check");
  const cards = Array.from(root.querySelectorAll(".review-card"));
  const outcomes = await Promise.all(cards.map((card, index) => request(`/api/reviews/${reviews[index].lesson_id}/${reviews[index].kind || "retention"}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      rating: card.querySelector('input[type="radio"]:checked').value,
      answers: { [reviews[index].prompt_id]: card.querySelector("[data-answer]").value },
    }),
  })));
  if (outcomes.some((response) => !response.ok)) throw new Error("Could not save reviews");
  root.innerHTML = "<p>Saved. Your next questions are now scheduled from your ratings.</p>";
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("[data-connect]")?.addEventListener("click", () => { if (connect()) loadReviews(); });
  if (token()) loadReviews();
});
