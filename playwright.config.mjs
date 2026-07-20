import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./curriculum/e2e",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  outputDir: "output/playwright/test-results",
  use: {
    baseURL: "http://127.0.0.1:8125",
    browserName: "chromium",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "python3 -u curriculum/study_server.py --port 8125 --database /tmp/self-evolving-agent-study-e2e.sqlite3",
    url: "http://127.0.0.1:8125/api/health",
    reuseExistingServer: false,
  },
});
