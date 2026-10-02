const {defineConfig, devices} = require("@playwright/test");
const port = Number(process.env.PLAYWRIGHT_PORT || 8765);

module.exports = defineConfig({
  testDir: "./tests/browser",
  timeout: 30_000,
  expect: {timeout: 7_500},
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    browserName: "chromium",
    headless: true,
    locale: "zh-TW",
    trace: "retain-on-failure"
  },
  webServer: {
    command: `python3 scripts/serve_test_site.py --port ${port} --directory site`,
    url: `http://127.0.0.1:${port}/`,
    reuseExistingServer: false,
    timeout: 30_000
  },
  projects: [{
    name: "chromium",
    use: {...devices["Desktop Chrome"]}
  }]
});
