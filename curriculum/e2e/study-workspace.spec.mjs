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

test("sandbox lesson gates its prediction and persists a capability-scoped study handoff", async ({ page }) => {
  await page.goto("/lessons/0005-sandboxed-file-tools.html");

  const prediction = page.locator("[data-prediction]");
  await expect(prediction.getByText("Repository decision:")).toBeHidden();
  await prediction.getByRole("radio", { name: /FORBIDDEN_PATH from the file tool/ }).check();
  await prediction.getByRole("textbox").fill(
    "Primitive 4 proves the string shape; the file tool owns the stricter path policy and resolved authority.",
  );
  await prediction.getByRole("button", { name: "Commit prediction" }).click();
  await expect(prediction.getByText("Repository decision:")).toBeVisible();
  await expect(page.locator("[data-case-id]")).toHaveCount(10);

  await openWorkspace(page);
  const workspace = page.getByRole("complementary", { name: "Lesson study workspace" });
  const context = workspace.getByRole("region", { name: "Lesson evidence context" });
  await expect(context).toContainText("05_sandboxed_file_tools_skeleton.py");
  await expect(context).toContainText("05_sandboxed_file_tools.py");
  await expect(context).toContainText("test_read_symlink_resolving_outside_sandbox_rejected");

  await workspace.getByRole("textbox", { name: "Jot notes" }).fill(
    "A valid path string is not yet an authorized filesystem capability.",
  );
  await workspace.getByRole("textbox", { name: "What has Primitive 4 actually proved?" }).fill(
    "The tool exists and path is a string; it does not prove the resolved resource is inside this sandbox.",
  );
  await workspace.getByRole("textbox", { name: "Where does this path stop?" }).fill(
    "An outside-pointing symlink stops at canonical containment with FORBIDDEN_PATH.",
  );

  await workspace.getByRole("button", { name: "Plan" }).click();
  await workspace.getByRole("textbox", { name: "Artifact to build or change" }).fill("validate_path");
  await workspace.getByRole("textbox", { name: "Smallest authorized behavior" }).fill(
    "Resolve one symlink and reject its outside target.",
  );
  await workspace.getByRole("textbox", { name: "Must preserve" }).fill(
    "Allowed nested paths and precise Ok/Err observations.",
  );
  await workspace.getByRole("textbox", { name: "Must not do" }).fill(
    "Inspect the outside target before authorization.",
  );
  await workspace.getByRole("textbox", { name: "First capability proof" }).fill(
    "test_read_symlink_resolving_outside_sandbox_rejected",
  );

  await workspace.getByRole("button", { name: "Reflect" }).click();
  await workspace.getByRole("textbox", { name: "Explain this to a smart 12-year-old" }).fill(
    "A folder key opens only that folder, even when a shortcut inside points somewhere else.",
  );
  await workspace.getByRole("textbox", { name: "Where does that explanation break?" }).fill(
    "It hides the difference between checking path spelling and resolving the real target.",
  );
  await expect(workspace.getByText("Saved", { exact: true })).toBeVisible();

  await page.reload();
  await openWorkspace(page);
  const reloaded = page.getByRole("complementary", { name: "Lesson study workspace" });
  await expect(reloaded.getByRole("textbox", { name: "Jot notes" })).toHaveValue(
    "A valid path string is not yet an authorized filesystem capability.",
  );
  await reloaded.getByRole("button", { name: "Plan" }).click();
  await expect(reloaded.getByRole("textbox", { name: "Artifact to build or change" })).toHaveValue("validate_path");
  await reloaded.getByRole("button", { name: "Reflect" }).click();
  await expect(reloaded.getByRole("textbox", { name: "Where does that explanation break?" })).toHaveValue(
    "It hides the difference between checking path spelling and resolving the real target.",
  );
});

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

test("diagnostic lecture stays gated until prediction commitment and exposes an accessible explanation", async ({ page }) => {
  await page.goto("/lessons/0007-trace-logger.html");

  const prediction = page.locator("[data-prediction]");
  const explanation = page.getByRole("heading", { name: "Record each fact where it becomes authoritative" });
  await expect(explanation).toBeHidden();

  await prediction.getByRole("button", { name: "Commit prediction" }).click();
  await expect(prediction.getByText("Choose an action and write a short rationale")).toBeVisible();
  await expect(explanation).toBeHidden();

  await prediction.getByRole("radio", { name: "What the model requested at each step." }).check();
  await prediction.getByRole("button", { name: "Commit prediction" }).click();
  await expect(explanation).toBeHidden();

  await prediction.getByRole("textbox").fill(
    "The model-call boundary first knows the assistant output, which distinguishes repeated valid work from rejected output.",
  );
  await prediction.getByRole("button", { name: "Commit prediction" }).click();

  await expect(explanation).toBeVisible();
  await expect(explanation).toBeFocused();
  await expect(prediction.getByRole("status")).toContainText("next lecture explanation is now available");
  await expect(prediction.getByRole("button", { name: "Commit prediction" })).toHaveAttribute("aria-expanded", "true");
});

test("print exposes the complete diagnostic lecture without requiring interaction", async ({ page }) => {
  await page.goto("/lessons/0007-trace-logger.html");
  const explanation = page.getByRole("heading", { name: "Record each fact where it becomes authoritative" });
  await expect(explanation).toBeHidden();

  await page.emulateMedia({ media: "print" });
  await expect(explanation).toBeVisible();
});

test("course identity and further reading remain readable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const firstLesson = page.getByRole("link", { name: /A model call is text in, text out, plus evidence/ });
  await expect(firstLesson).toContainText("Primitive 1 · Model-Call Boundary");
  await expect(page.getByRole("link", { name: /A trace is replayable evidence/ })).toContainText(
    "Primitive 7 · Trace Logger",
  );

  await page.goto("/lessons/0007-trace-logger.html");
  await expect(page).toHaveTitle("Project 1A · Trace Logger · A trace is replayable evidence");
  await expect(page.getByText("Lesson 7 of 8 · Trace Logger").first()).toBeVisible();
  await expect(page.locator("[data-further-reading] .source-card")).toHaveCount(3);

  const hasPageOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasPageOverflow).toBe(false);

  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const overlapsStudyLauncher = await page.evaluate(() => {
    const launcher = document.querySelector(".study-launcher");
    const links = document.querySelectorAll(".site-nav.bottom-nav a");
    if (!launcher || !links.length) return true;
    const launcherBox = launcher.getBoundingClientRect();
    return [...links].some((link) => {
      const linkBox = link.getBoundingClientRect();
      return !(
        linkBox.right <= launcherBox.left
        || linkBox.left >= launcherBox.right
        || linkBox.bottom <= launcherBox.top
        || linkBox.top >= launcherBox.bottom
      );
    });
  });
  expect(overlapsStudyLauncher).toBe(false);
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
