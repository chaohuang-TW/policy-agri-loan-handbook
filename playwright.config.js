const {defineConfig, devices} = require("@playwright/test");

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
    baseURL: "http://127.0.0.1:8765",
    browserName: "chromium",
    headless: true,
    locale: "zh-TW",
    trace: "retain-on-failure"
  },
  webServer: {
    command: "python3 -m http.server 8765 --directory site --bind 127.0.0.1",
    url: "http://127.0.0.1:8765/",
    reuseExistingServer: false,
    timeout: 30_000
  },
  projects: [{
    name: "chromium",
    use: {...devices["Desktop Chrome"]}
  }]
});
