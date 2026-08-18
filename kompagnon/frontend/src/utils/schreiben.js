// Ein schreibender Aufruf, der sich meldet, wenn er scheitert.
//
// Warum es das gibt: Am 18.08.2026 stellte sich heraus, dass sich in der
// Akademie **keine einzige Lektion anlegen liess** — der Endpunkt antwortete
// mit 500, seit es ihn gibt. Aufgefallen ist es niemandem, weil die Oberfläche
// so gebaut war:
//
//     const res = await fetch(…);
//     if (res.ok) { … }            // sonst: nichts
//     } catch (e) { console.error(e); }
//
// Ein Fehler, den niemand sieht, ist ein Fehler, der bleibt (dieselbe Bauart
// wie Lücke L-36 und wie die Kundenfreigabe vom 17.08.). Beide Fälle muss man
// abfangen: die geworfene Ausnahme **und** die Antwort, die nicht `ok` ist.

/** Aus einem Statuscode wird ein Satz, den man lesen kann. */
export function meldung(was, status, rumpf = '') {
  const nach = {
    401: 'Die Anmeldung ist abgelaufen — bitte neu anmelden.',
    403: 'Dafür fehlt die Berechtigung.',
    404: 'Das Ziel gibt es nicht (mehr).',
    409: 'Es gibt einen Konflikt mit dem gespeicherten Stand.',
    413: 'Der Inhalt ist zu gross.',
    422: 'Der Server hat die Eingabe abgelehnt.',
  }[status];

  if (nach) return `${was} nicht gespeichert. ${nach}`;
  if (status >= 500) {
    const detail = String(rumpf).slice(0, 160).trim();
    return `${was} nicht gespeichert — der Server meldet einen Fehler (${status}).`
      + (detail ? ` ${detail}` : '');
  }
  return `${was} nicht gespeichert (Status ${status}).`;
}

/**
 * Führt `aufruf` aus und liefert `{ ok, antwort }` oder `{ ok: false, fehler }`.
 * Der Aufrufer entscheidet, wo die Meldung erscheint — hier wird nichts
 * verschluckt und nichts angezeigt.
 */
export async function schreibe(aufruf, was = 'Die Änderung') {
  let antwort;
  try {
    antwort = await aufruf();
  } catch (fehler) {
    return {
      ok: false,
      fehler: `${was} nicht gespeichert — keine Verbindung zum Server.`
        + (fehler?.message ? ` (${fehler.message})` : ''),
    };
  }

  if (!antwort || !antwort.ok) {
    let rumpf = '';
    try {
      rumpf = await antwort.text();
    } catch {
      rumpf = '';
    }
    return { ok: false, fehler: meldung(was, antwort ? antwort.status : 0, rumpf) };
  }

  return { ok: true, antwort };
}
