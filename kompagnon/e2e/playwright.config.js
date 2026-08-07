const { defineConfig, devices } = require('@playwright/test');

/**
 * Browser-Tests gegen eine laufende Anwendung.
 *
 * Lokal:  bash scripts/dev.sh   (Backend 8000, Frontend 3000), dann `npm test`
 * CI:     beide Dienste werden im Workflow gestartet, E2E_BASE_URL zeigt darauf
 *
 * Bewusst nur Chromium: Die Tests sollen Regressionen in der Anwendung finden,
 * nicht Browser-Unterschiede. Drei Engines verdreifachen die Laufzeit ohne
 * zusaetzlichen Erkenntnisgewinn fuer ein internes Werkzeug.
 */
module.exports = defineConfig({
  testDir: './tests',
  timeout: 45_000,
  expect: { timeout: 10_000 },

  // In der CI kein Wiederholen bei Flakiness — ein instabiler Test soll
  // auffallen, nicht durch Wiederholung verschwinden.
  retries: 0,
  workers: 1,
  forbidOnly: !!process.env.CI,

  reporter: process.env.CI ? [['github'], ['list']] : [['list']],

  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    actionTimeout: 15_000,
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
