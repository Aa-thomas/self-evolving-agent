import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("study-access-token", "e2e-test-token");
  });
});

async function openWorkspace(page) {
  await page.getByRole("button", { name: "Study workspace", exact: true }).click();
  await expect(page.getByRole("complementary", { name: "Lesson study workspace" })).toBeVisible();
}

test("diagnostic workspace renders evidence, persists a handoff, and restores reflections", async ({ page }) => {
  await page.goto("/lessons/0007-trace-logger.html");
  await openWorkspace(page);

  const workspace = page.getByRole("complementary", { name: "Lesson study workspace" });
  await expect(workspace.getByRole("region", { name: "Lesson evidence context" })).toContainText("partial-run.json");
  await expect(workspace.getByRole("textbox", { name: "What can this run actually tell you?" })).toBeVisible();
  await expect(workspace.getByRole("textbox", { name: "Which tempting diagnosis must wait?" })).toBeVisible();

  await workspace.getByRole("textbox", { name: "Jot notes" }).fill("The final result cannot establish the first bad transition.");
  await workspace.getByRole("textbox", { name: "What is the next useful evidence?" }).fill(
    "Record assistant output where the loop receives it.",
  );

  await workspace.getByRole("button", { name: "Plan" }).click();
  await workspace.getByRole("textbox", { name: "Artifact to build or change" }).fill("TraceLogger and run_agent hooks");
  await workspace.getByRole("textbox", { name: "Smallest evidence slice" }).fill("Initial messages and one ordered causal step");
  await workspace.getByRole("textbox", { name: "Must preserve" }).fill("Existing loop behavior");
  await workspace.getByRole("textbox", { name: "Must not do" }).fill("Invent a trace after the run");
  await workspace.getByRole("textbox", { name: "First diagnostic proof" }).fill(
    "test_trace_logger_records_causal_fields_and_writes_replayable_json",
  );

  await workspace.getByRole("button", { name: "Reflect" }).click();
  await workspace.getByRole("textbox", { name: "Explain this to a smart 12-year-old" }).fill(
    "A score tells you the ending, but a trace tells you the moves that led there.",
  );
  await workspace.getByRole("textbox", { name: "Where does that explanation break?" }).fill(
    "It hides which boundary first owned each fact.",
  );
  const predictionEvidence = workspace.getByRole("textbox", { name: "What did the new trace confirm or rule out?" });
  await predictionEvidence.fill("Assistant output rules out guessing about an unseen request.");

  await expect(workspace.getByText("Saved", { exact: true })).toBeVisible();

  await page.reload();
  await openWorkspace(page);
  const reloaded = page.getByRole("complementary", { name: "Lesson study workspace" });
  await expect(reloaded.getByRole("textbox", { name: "Jot notes" })).toHaveValue(
    "The final result cannot establish the first bad transition.",
  );
  await reloaded.getByRole("button", { name: "Plan" }).click();
  await expect(reloaded.getByRole("textbox", { name: "Artifact to build or change" })).toHaveValue("TraceLogger and run_agent hooks");
  await reloaded.getByRole("button", { name: "Reflect" }).click();
  await expect(reloaded.getByRole("textbox", { name: "What did the new trace confirm or rule out?" })).toHaveValue(
    "Assistant output rules out guessing about an unseen request.",
  );
});

test("experiment workspace renders the measurement-specific prompts", async ({ page }) => {
  await page.goto("/lessons/0008-eval-runner.html");
  await openWorkspace(page);

  const workspace = page.getByRole("complementary", { name: "Lesson study workspace" });
  await expect(workspace.getByRole("region", { name: "Lesson evidence context" })).toContainText("eval-cases.json");
  await expect(workspace.getByRole("textbox", { name: "What are we actually claiming?" })).toBeVisible();
  await expect(workspace.getByRole("textbox", { name: "What must stay fixed?" })).toBeVisible();
  await expect(workspace.getByRole("textbox", { name: "What makes a failed case useful?" })).toBeVisible();

  await workspace.getByRole("button", { name: "Reflect" }).click();
  await expect(workspace.getByRole("textbox", { name: "What did the report confirm or weaken?" })).toBeVisible();
});
