/**
 * Was auf der Kundenübersicht steht — die Entscheidungen, ohne die Darstellung.
 *
 * **Warum eine eigene Datei (04.09.2026, L-161).** Die vier Funktionen saßen
 * in `pages/CustomerDashboard.jsx`. Sie zu prüfen hieß, die Seite zu laden —
 * und die zieht über `react-router-dom` eine Kette herein, an der der
 * Testlauf abbricht: „Cannot find module 'react-router/dom'".
 *
 * Dieselbe Überlegung wie bei `schrittkette.js` und `freigabeStand.js`, und
 * beide Male ging es um dasselbe: Eine Entscheidung, die den Kunden Tage
 * kosten kann, darf nicht ungeprüft bleiben, weil ihre Nachbarn schwer zu
 * laden sind. Hier ist es die Frage, **welchen** Schritt der Kunde sieht —
 * zeigt die Seite ihm sein Guthaben, während wir auf seine Texte warten,
 * verliert er Tage und wir die Frist.
 *
 * **Diese Datei gibt Daten zurück, kein Markup.** Der hervorgehobene Teil
 * eines Satzes steht als eigenes Feld (`hervor`) daneben, statt als JSX. So
 * lässt sich prüfen, *was* dasteht, ohne zu prüfen, *wie* es aussieht.
 */
import { offeneFreigaben } from './freigabeStand';
import { euroAusCent } from './geld';

// ── Die Lage in einem Satz ───────────────────────────────────────────────
//
// Drei Zustände, wie im abgenommenen Entwurf — abgeleitet aus den Daten,
// nicht geschaltet: vor dem Baubeginn, während des Baus, nach dem Go-live.
export function lageBestimmen({ profil, mitwirkung }) {
  const projekt = (profil?.projects || [])[0] || null;
  const offen = mitwirkung?.offen ?? 0;
  const live = projekt?.status === 'phase_4' || projekt?.status === 'completed';

  if (live) {
    return {
      zustand: 'nach',
      satz: 'Ihre Website ist online.',
      dazu: projekt?.target_go_live
        ? `Seit dem ${datum(projekt.target_go_live)}.`
        : 'Wir halten sie für Sie aktuell.',
    };
  }
  if (offen > 0) {
    return {
      zustand: 'vor',
      satz: `Wir warten auf ${zahlwort(offen)} ${offen === 1 ? 'Angabe' : 'Angaben'} von Ihnen.`,
      dazu: `Sie haben ${mitwirkung.erledigt} von ${mitwirkung.gesamt} Punkten erledigt. `
          + 'Sobald alles da ist, starten wir am nächsten Werktag.',
    };
  }
  if (projekt) {
    return {
      zustand: 'bau',
      satz: 'Wir bauen. Bei Ihnen liegt gerade nichts.',
      dazu: projekt.target_go_live
        ? `Geplante Fertigstellung: ${datum(projekt.target_go_live)}.`
        : 'Wir melden uns, sobald es etwas freizugeben gibt.',
    };
  }
  return {
    zustand: 'vor',
    satz: 'Willkommen bei KOMPAGNON.',
    dazu: 'Sobald Ihr Auftrag angelegt ist, steht hier, woran wir gerade arbeiten.',
  };
}

// ── Der nächste Schritt ──────────────────────────────────────────────────
//
// **Immer einer, und immer nur einer.** Der Kunde soll beim Anmelden lesen,
// was als Nächstes geschieht — auch dann, wenn es gerade nichts von ihm
// braucht (Wunsch David, 04.09.2026). Zwei gleichrangige Aufforderungen sind
// keine Aufforderung mehr, sondern eine Auswahl, und die trifft niemand.
//
// Die Reihenfolge ist die der Dringlichkeit, nicht die der Datenquellen:
//
//   1. offene Angaben   — sie halten die Bauzeit an, alles andere wartet
//   2. offene Freigaben — sie halten sie ebenfalls an (M7/M8), aber erst,
//                         wenn die Angaben vollständig sind
//   3. freies Guthaben  — nach dem Go-live das Einzige, was er tun *kann*
//   4. die laufende Phase — nichts zu tun, aber es geschieht etwas
//
// Der vierte Fall ist der wichtigste für das Vertrauen: „Bei Ihnen liegt
// nichts" ist eine Auskunft, aber keine Antwort auf „und was passiert
// gerade?".
export function aufgabeBestimmen({ lage, mitwirkung, inhalt, projekt, portal }) {
  const offeneAngaben = mitwirkung?.offen ?? 0;
  if (offeneAngaben > 0) {
    const naechster = (mitwirkung.punkte || []).find((p) => !p.erledigt);
    return {
      vorspann: 'Als Nächstes: ',
      hervor: naechster ? naechster.titel : 'Ihre offenen Angaben',
      dazu: offeneAngaben === 1
        ? 'Danach beginnt die Bauzeit.'
        : `Noch ${offeneAngaben} von ${mitwirkung.gesamt} Punkten — danach beginnt die Bauzeit.`,
      knopf: 'Weiter',
      ziel: '/app/was-wir-brauchen',
    };
  }

  const offen = offeneFreigaben(projekt?.content_freigaben);
  if (offen.length > 0) {
    return {
      vorspann: 'Als Nächstes: ',
      hervor: 'Ihre Freigabe',
      dazu: `${offen.length} ${offen.length === 1 ? 'Seite wartet' : 'Seiten warten'} auf Sie — ein Klick je Zeile.`,
      knopf: 'Zu den Freigaben',
      ziel: '/app/freigaben',
    };
  }

  const rest = inhalt?.guthaben?.rest_minuten ?? 0;
  if (lage.zustand === 'nach' && rest > 0) {
    return {
      vorspann: 'Sie haben ',
      hervor: `${rest} Minuten`,
      nachspann: ' Änderungen frei in diesem Monat.',
      dazu: 'Sagen Sie uns, was sich ändern soll — wir setzen es um.',
      knopf: 'Änderung anfordern',
      ziel: '/app/inhaltsaenderungen',
    };
  }

  // Nichts liegt beim Kunden. Dann sagt der Streifen, woran **wir** sind —
  // benannt aus den Phasen, die das Portal ohnehin führt, statt aus einem
  // freundlichen Satz ohne Inhalt.
  const phasen = portal?.phases || [];
  const laufend = phasen.find((p) => p.state === 'active') || null;
  if (laufend) {
    const nummer = laufend.number || (phasen.indexOf(laufend) + 1);
    return {
      vorspann: 'Wir arbeiten an: ',
      hervor: laufend.label,
      dazu: [laufend.description, `Schritt ${nummer} von ${phasen.length}`]
        .filter(Boolean).join(' · '),
      knopf: null,
      ziel: null,
    };
  }
  return null;
}

// ── Drei Kacheln ─────────────────────────────────────────────────────────
export function kachelnBauen({ profil, mitwirkung, inhalt, zahlungen, lage }) {
  const kacheln = [];

  if (lage.zustand === 'vor' && mitwirkung) {
    kacheln.push({
      was: 'Bei Ihnen', zahl: String(mitwirkung.offen), klein: 'offen',
      sagt: `von ${mitwirkung.gesamt} Angaben`, hin: 'Was wir brauchen →',
      betont: mitwirkung.offen > 0, ziel: '/app/was-wir-brauchen',
    });
  } else if (inhalt?.guthaben) {
    const g = inhalt.guthaben;
    kacheln.push({
      was: 'Ihr Guthaben', zahl: String(g.rest_minuten), klein: `von ${g.kontingent_minuten} Min.`,
      sagt: 'frei in diesem Monat', hin: 'Inhaltsänderungen →',
      betont: true, ziel: '/app/inhaltsaenderungen',
    });
  }

  const punkte = profil?.current_score;
  kacheln.push({
    was: 'Letzter Bericht',
    zahl: punkte != null ? String(punkte) : '—',
    klein: punkte != null ? '/100' : '',
    sagt: (profil?.current_level || '').replace('Homepage Standard ', '') || 'noch nicht geprüft',
    hin: 'Bericht ansehen →', gut: punkte != null && punkte >= 70, ziel: '/app/mein-bericht',
  });

  const abo = (zahlungen?.abos || []).find((a) => a.laeuft);
  const offeneRechnung = (zahlungen?.rechnungen || []).find((r) => r.status === 'offen');
  if (offeneRechnung) {
    kacheln.push({
      was: 'Offene Rechnung',
      zahl: String(Math.round(Number(offeneRechnung.amount_gross || 0))), klein: '€',
      sagt: offeneRechnung.due_date ? `fällig am ${datum(offeneRechnung.due_date)}` : 'zur Zahlung',
      hin: 'Rechnungen →', ziel: '/app/rechnungen',
    });
  } else if (abo) {
    kacheln.push({
      was: 'Ihr Vertrag', zahl: euroAusCent(abo.brutto_cent).replace(/\s?€/, ''), klein: '€/Monat',
      sagt: abo.produkt === 'ABO-PRO' ? 'Pflege Pro' : 'Pflege Basic',
      hin: 'Rechnungen und Zahlung →', ziel: '/app/rechnungen',
    });
  }

  return kacheln.slice(0, 3);
}

// ── Was zuletzt geschah ──────────────────────────────────────────────────
//
// Aus den Quellen, die einen Zeitpunkt führen. Bewusst kurz: Der Verlauf
// beruhigt („es geschieht etwas"), er ist kein Archiv.
export function verlaufBauen({ inhalt, zahlungen, profil }) {
  const zeilen = [];

  (inhalt?.guthaben?.eintraege || []).forEach((e) => zeilen.push({
    was: `${e.taetigkeit} — ${e.minuten} Min.`, zeit: e.erfasst_am,
  }));
  (zahlungen?.rechnungen || []).filter((r) => r.paid_at).forEach((r) => zeilen.push({
    was: `${r.line_item || 'Rechnung'} bezahlt`, zeit: r.paid_at,
  }));
  const audit = (profil?.audits || [])[0];
  if (audit?.created_at) zeilen.push({ was: 'Ihre Website geprüft', zeit: audit.created_at });

  return zeilen
    .filter((z) => z.zeit)
    .sort((a, b) => String(b.zeit).localeCompare(String(a.zeit)))
    .slice(0, 4)
    .map((z) => ({ was: z.was, wann: datum(z.zeit) }));
}

// ── Kleinkram ────────────────────────────────────────────────────────────

function datum(wert) {
  if (!wert) return '';
  const d = new Date(wert);
  return Number.isNaN(d.getTime()) ? String(wert)
    : d.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' });
}

const ZAHLWORT = ['null', 'eine', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht', 'neun'];
function zahlwort(n) { return ZAHLWORT[n] ?? String(n); }
