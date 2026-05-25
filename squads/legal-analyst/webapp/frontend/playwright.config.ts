import { defineConfig, devices } from "@playwright/test";

const host = process.env.PLAYWRIGHT_HOST || "127.0.0.1";
const port = process.env.PLAYWRIGHT_PORT || "5173";
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://${host}:${port}`;

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
