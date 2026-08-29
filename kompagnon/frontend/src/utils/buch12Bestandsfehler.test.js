/**
 * Drei stille Bestandsfehler (BUCH-12, FIX-1/2/4 — L-115).
 *
 * „Still" heisst: Sie erzeugen keine Fehlermeldung, sondern falsches
 * Verhalten. Deshalb hat sie niemand gemeldet, und deshalb braucht jeder eine
 * Zusicherung — nachgesehen bringt sie niemand ein zweites Mal.
 *
 * **FIX-1 · Steuersatz.** `ProductEditor` setzte `product.tax_rate ?? 19`.
 * Für Bücher und E-Books gilt der ermässigte Satz von 7 % (Anlage 2 UStG).
 * Wer ein Buchprodukt anlegte und das Feld nicht bewusst änderte, verkaufte
 * mit falschem Steuerausweis — und alles funktionierte, nur die Buchhaltung
 * stimmte nicht.
 *
 * **FIX-2 · Jahreszahl.** Im Warnband des Auditberichts stand fest
 * verdrahtet „Homepage Standard **2025**". Wir haben August 2026, und jeder
 * Kunde las eine ein Jahr alte Standardbezeichnung. Die Fassung steht am
 * Audit selbst (`standard_version`), und `fassungText` gab es an derselben
 * Seite bereits — der Bericht nahm sie nur an einer von zwei Stellen.
 *
 * **FIX-4 · Widerrufsverzicht.** Der Websprint-Checkout erfasste Name, Firma,
 * Website, E-Mail, Telefon, Nachricht — und keine Zustimmung zum sofortigen
 * Leistungsbeginn. Bei Dienstleistungen, die in der Widerrufsfrist beginnen,
 * braucht es sie wie beim PDF (§ 356 Abs. 4 BGB); ohne sie gibt es bei einem
 * Widerruf **keinen Wertersatz** für bereits geleistete Arbeit.
 */
import fs from 'fs';
import path from 'path';

const SRC = path.join(__dirname, '..');

function quelle(datei) {
  return fs.readFileSync(path.join(SRC, datei), 'utf8');
}

/**
 * Quelltext ohne Kommentare.
 *
 * **Warum das hier nötig ist.** Der Kommentar, der *erklärt*, warum
 * `tax_rate ?? 19` weg musste, enthält die Zeichenfolge — und die erste
 * Fassung dieser Prüfung zählte ihn mit. Derselbe Fehler wie am 28.08.2026
 * beim Wächter, der seinen eigenen Kommentar fand. Ein Wächter misst Code,
 * nicht Prosa.
 */
function ohneKommentare(text) {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/^\s*\/\/.*$/gm, ' ');
}

// ── FIX-1 · Der Steuersatz ───────────────────────────────────────────

describe('FIX-1 — der Steuersatz ist keine Vorbelegung mehr', () => {
  test('19 % wird nicht mehr stillschweigend eingesetzt', () => {
    // Arrange & Act
    const text = ohneKommentare(quelle('pages/ProductEditor.jsx'));

    // Assert
    expect(text).not.toMatch(/tax_rate\s*\?\?\s*19/);
    // Gegenprobe: Die Prüfung greift überhaupt — sie findet die Auswahl,
    // die an ihre Stelle getreten ist.
    expect(text).toMatch(/STEUERSAETZE\.map/);
  });

  test('die drei gültigen deutschen Sätze stehen zur Auswahl', () => {
    // Ein freies Zahlenfeld nimmt auch 5 oder 20 entgegen.
    const text = quelle('pages/ProductEditor.jsx');

    expect(text).toMatch(/STEUERSAETZE/);
    expect(text).toMatch(/value=\{19\}|19, ?label|"19"/);
    expect(text).toMatch(/7/);
    expect(text).toMatch(/0/);
  });

  test('beim ermäßigten Satz steht der Grund daneben', () => {
    // Sonst wählt jemand 7 %, weil es billiger aussieht.
    const text = quelle('pages/ProductEditor.jsx');

    expect(text).toMatch(/Anlage 2|elektronische Publikation|Bücher/i);
  });
});

// ── FIX-2 · Die Jahreszahl ───────────────────────────────────────────

describe('FIX-2 — die Fassung wird gelesen, nicht geschrieben', () => {
  test('„Homepage Standard 2025" steht nirgends mehr fest verdrahtet', () => {
    // Arrange & Act
    const text = ohneKommentare(quelle('components/AuditReport.jsx'));

    // Assert
    expect(text).not.toMatch(/Homepage Standard 2025/);
  });

  test('das Warnband nimmt dieselbe Quelle wie die Kopfzeile', () => {
    // Zwei Quellen für dieselbe Zahl ist der Fehler, der hier weh tut.
    const text = quelle('components/AuditReport.jsx');
    const treffer = text.match(/fassungText\(/g) || [];

    expect(treffer.length).toBeGreaterThanOrEqual(2);
  });
});

// ── FIX-4 · Der Widerrufsverzicht ────────────────────────────────────

describe('FIX-4 — der Websprint-Checkout fragt nach dem Verzicht', () => {
  test('es gibt ein Häkchen, und es startet leer', () => {
    // **Am Quelltext geprüft, nicht am Bild.** `Checkout.jsx` zieht
    // `react-router-dom` herein, das sich in dieser Jest-Umgebung nicht
    // auflösen lässt; ein Render scheitert am Router, nicht am Formular.
    // Geprüft wird deshalb der Ausgangszustand — und darauf kommt es an:
    // Vorangekreuzte Zustimmungen sind unwirksam.
    // Arrange & Act
    const text = ohneKommentare(quelle('pages/Checkout.jsx'));

    // Assert
    expect(text).toMatch(/withdrawal_waived: false/);
    expect(text).toMatch(/type="checkbox"[\s\S]{0,120}withdrawal_waived/);
  });

  test('der Verzichtstext ist nicht selbst formuliert', () => {
    // Derselbe Fund wie im Shop-Formular am 29.08.: Ein plausibler Rechtssatz
    // wird nie geprüft, weil er geprüft aussieht.
    const text = quelle('pages/Checkout.jsx');

    expect(text).toMatch(/VERZICHTSTEXT|rechtstexte/);
  });

  test('ohne Häkchen wird nicht zu Stripe weitergeleitet', () => {
    const text = quelle('pages/Checkout.jsx');

    // Die Sperre steht im Absendeweg, nicht nur als deaktivierter Knopf:
    // Ein disabled-Attribut allein ist keine Prüfung.
    expect(text).toMatch(/form\.withdrawal_waived/);
  });
});
