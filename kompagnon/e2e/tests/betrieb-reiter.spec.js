const { test, expect } = require('@playwright/test');
const { anmelden } = require('./helpers');

/**
 * Die vier Reiter hinter „Mehr" muessen sichtbar aufklappen.
 *
 * **Der Fehler, der diesen Test erzwungen hat (25.08.2026).** Die Reiterleiste
 * bekam am 22.08. `overflow-x: auto`, damit sie sich auf dem Handy wischen
 * laesst. Damit wurde auch `overflow-y` zu `auto` — und das Klappmenue haengt
 * unterhalb der 47 Pixel hohen Leiste. Der Scroll-Container schnitt es
 * vollstaendig ab: Der Knopf reagierte, der Zustand kippte, das Menue stand im
 * DOM — und niemand sah es. **Vier Reiter waren drei Tage lang unerreichbar**
 * (Deals, Akademie, Zugang, E-Mails), ohne eine einzige Fehlermeldung.
 *
 * **Warum `toBeVisible()` hier nicht genuegt:** Playwright nennt ein Element
 * sichtbar, wenn es ein nicht-leeres Rechteck hat und nicht auf `hidden`
 * steht. Ein vom Elternteil weggeschnittenes Element erfuellt beides — der
 * Test waere gruen geblieben. Gefragt ist, was an dieser Stelle wirklich
 * obenauf liegt: `elementFromPoint`. Das ist genau die Frage „sieht der
 * Mensch es und kann er es treffen".
 */
const HINTER_MEHR = ['Deals', 'Akademie', 'Zugang', 'E-Mails'];

test.describe('Betriebsansicht — die Reiter hinter „Mehr"', () => {
  test('das Klappmenue ist wirklich zu sehen, nicht nur im DOM', async ({ page }) => {
    await anmelden(page);
    await page.goto('/app/betriebe/1');

    await page.getByRole('button', { name: /^Mehr/ }).click();

    for (const name of HINTER_MEHR) {
      const eintrag = page.getByRole('button', { name: new RegExp(name) }).last();
      await expect(eintrag, `„${name}" fehlt im Menue`).toBeVisible();

      // Liegt an der Mitte des Eintrags auch wirklich der Eintrag?
      const obenauf = await eintrag.evaluate((el) => {
        const r = el.getBoundingClientRect();
        const treffer = document.elementFromPoint(r.left + r.width / 2,
                                                  r.top + r.height / 2);
        return treffer === el || el.contains(treffer);
      });
      expect(obenauf, `„${name}" steht im DOM, ist aber verdeckt oder ` +
        `vom Scroll-Container abgeschnitten`).toBe(true);
    }
  });

  /**
   * Der Weg bis in den Reiter. **Dieser Test allein wuerde nicht reichen:**
   * Gegen den kaputten Stand am 25.08. blieb er gruen. Playwright scrollt vor
   * jedem Klick von sich aus ins Sichtfeld — dabei scrollt es den
   * Scroll-Container, und der Klick trifft. Genau darum steht der Test oben
   * daneben; er misst, was ein Mensch sieht, nicht was ein Roboter erreicht.
   */
  test('ein Eintrag aus dem Menue oeffnet seinen Reiter', async ({ page }) => {
    await anmelden(page);
    await page.goto('/app/betriebe/1');

    await page.getByRole('button', { name: /^Mehr/ }).click();
    await page.getByRole('button', { name: /Zugang/ }).last().click();

    await expect(page.getByText('Zugänge dieses Betriebs')).toBeVisible();
  });
});
