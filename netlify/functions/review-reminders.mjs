import { getStore } from "@netlify/blobs";

const STORE_NAME = "study-workspace";
const STORE_KEY = "current";
const QUESTION_TYPES = [
  "In one sentence, what is this primitive or concept?",
  "What must never happen, and who enforces that boundary?",
  "What realistic failure does this prevent?",
  "What test, trace, or observable result would prove it works?",
];

export const config = { schedule: "0 13 * * *" };

export default async () => {
  const recipient = process.env.REVIEW_EMAIL_TO;
  const sender = process.env.REVIEW_EMAIL_FROM;
  const apiKey = process.env.RESEND_API_KEY;
  const siteUrl = process.env.REVIEW_SITE_URL || process.env.URL;
  if (!recipient || !sender || !apiKey || !siteUrl) {
    return new Response("Review reminders are not configured.", { status: 204 });
  }

  const store = getStore(STORE_NAME);
  const state = await store.get(STORE_KEY, { type: "json" }) || {};
  const reviews = Object.values(state.reviews || {})
    .filter((review) => review?.due_at && Date.parse(review.due_at) <= Date.now())
    .sort((left, right) => Date.parse(left.due_at) - Date.parse(right.due_at))
    .slice(0, 3);
  if (!reviews.length) return new Response("No reviews are due.", { status: 204 });

  const questions = reviews.map((review, index) =>
    `<li><strong>${review.lesson_id}</strong> (${review.kind === "pre_implementation" ? "before implementation" : "retention"}) — ${QUESTION_TYPES[(review.interval_index + index) % QUESTION_TYPES.length]}</li>`
  ).join("");
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: sender,
      to: [recipient],
      subject: "Three questions from your agent lessons",
      html: `<p>Answer these from memory before reopening the lessons:</p><ol>${questions}</ol><p><a href="${siteUrl}/review.html">Open your retention check</a></p>`,
    }),
  });
  if (!response.ok) return new Response("Email delivery failed.", { status: 502 });
  return new Response("Review reminder sent.");
};
