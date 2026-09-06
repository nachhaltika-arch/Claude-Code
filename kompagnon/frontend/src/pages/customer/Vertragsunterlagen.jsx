import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import API_BASE_URL from '../../config';
import SeitenTitel from '../../components/ui/SeitenTitel';
import MeineDatenRechte from '../../components/kunde/MeineDatenRechte';

/**
 * „Vertragsunterlagen" — alles, was der Kunde unterschrieben hat (L-160 Rang 7).
 *
 * **Der Befund.** Angebot, AGB-Fassung und Auftragsbestätigung liegen im
 * System, und der Kunde kommt nicht heran: Der einzige Auslieferungsweg der
 * Auftragsbestätigung verlangt `require_admin`.
 *
 * **Was diese Seite nicht tut: etwas erfinden.** Wo eine Unterlage nicht
 * vorliegt, steht der Grund — und kein Link. Eine Liste mit fünf Zeilen, von
 * denen drei ins Leere führen, ist schlechter als eine mit zwei; der Kunde
 * klickt einmal, findet nichts und traut der Seite danach nicht mehr.
 *
 * **Die Gründe kommen aus der Antwort, nicht von hier.** Warum eine Unterlage
 * fehlt, ist eine Aussage über unsere Daten — sie gehört dorthin, wo die
 * Daten gelesen werden, nicht auf den Bildschirm.
 */
export default function Vertragsunterlagen() {
  const { token } = useAuth();
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');

  useEffect(() => {
    if (!token) return;
    fetch(`${API_BASE_URL}/api/portal/vertragsunterlagen`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(
        r.status === 403
          ? 'Ihr Zugang darf keine Vertragsunterlagen sehen.'
          : `Konnte nicht geladen werden (${r.status})`))))
      .then(setDaten)
      .catch(e => setFehler(e.message));
  }, [token]);

  /**
   * **Wie eine Unterlage geholt wird, sagt sie selbst** (`art`), statt dass
   * der Bildschirm es aus der Form der Adresse schließt.
   *
   * Die erste Fassung prüfte `adresse.startsWith('/api/')` — und der Wächter
   * `test_frontend_adressen.py` meldete prompt eine Adresse „/api", die es im
   * Backend nicht gibt: Er kann eine **Prüfung** auf ein Präfix nicht von
   * einem **Aufruf** unterscheiden. Er hatte im Ergebnis recht, wenn auch
   * aus einem anderen Grund: Der Abrufweg ist eine Eigenschaft der Unterlage
   * und gehört dorthin, wo die Daten entstehen.
   */
  const oeffnen = async (u) => {
    if (u.art !== 'pdf') { window.open(u.adresse, '_blank', 'noopener'); return; }
    /* Der Abruf trägt die Anmeldung im Kopf, nicht in der Adresse — ein
       Token in der URL landet im Verlauf und im Server-Protokoll. */
    const res = await fetch(`${API_BASE_URL}${u.adresse}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) { setFehler('Die Unterlage konnte nicht geladen werden.'); return; }
    const url = URL.createObjectURL(await res.blob());
    window.open(url, '_blank', 'noopener');
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  };

  return (
    <div style={S.seite}>
      <SeitenTitel>Vertragsunterlagen</SeitenTitel>
      <h1 style={S.h1}>Vertragsunterlagen</h1>
      <p style={S.unter}>
        Alles, was Sie unterschrieben haben — in der Fassung, die für Ihren
        Auftrag gilt.
      </p>

      {fehler && <p style={S.fehler}>{fehler}</p>}
      {!daten && !fehler && <p style={S.leise}>Wird geladen …</p>}

      {daten?.unterlagen?.map(u => (
        <article key={u.titel} style={S.karte}>
          <div style={S.kopf}>
            <span style={S.titel}>{u.titel}</span>
            {u.stand && <span style={S.stand}>{u.stand}</span>}
            {u.vorhanden ? (
              <button style={S.knopf} onClick={() => oeffnen(u)}>
                {u.art === 'pdf' ? 'PDF ansehen' : 'Ansehen'}
              </button>
            ) : (
              <span style={S.marke}>liegt nicht vor</span>
            )}
          </div>
          {/* Der Grund steht unter der Zeile, nicht in einem Hinweisfeld
              daneben: Er gehört zu dieser einen Unterlage. */}
          {!u.vorhanden && <p style={S.grund}>{u.grund}</p>}
        </article>
      ))}

      {/* **Auskunft und Löschung stehen hier** (L-160 Rang 5) — so wie im
          Entwurf `kundenkonto-neu`. Der Ort ist keine Verlegenheit: Wer seine
          Vertragsunterlagen ansieht, denkt ohnehin über das Verhältnis nach.
          Ein eigener Menüpunkt „Meine Rechte" stünde das ganze Jahr da und
          würde einmal gebraucht. */}
      <MeineDatenRechte token={token} />
    </div>
  );
}

const S = {
  seite: { maxWidth: 760, margin: '0 auto', padding: '0 0 40px' },
  h1: { fontSize: 22, fontWeight: 900, letterSpacing: '-.02em', color: 'var(--text-primary)', margin: '0 0 6px' },
  unter: { fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 22px', maxWidth: '62ch' },
  karte: { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '16px 20px', marginBottom: 12 },
  kopf: { display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' },
  titel: { fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', flex: '1 1 auto' },
  stand: { fontSize: 13, color: 'var(--text-tertiary)' },
  knopf: { fontWeight: 700, fontSize: 13, padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: 'var(--text-on-brand)' },
  marke: { fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 999, background: 'var(--bg-app)', color: 'var(--text-secondary)', boxShadow: 'inset 0 0 0 1px var(--border-light)' },
  grund: { fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '10px 0 0', maxWidth: '64ch' },
  fehler: { fontSize: 13, color: 'var(--status-danger-text)' },
  leise: { fontSize: 13, color: 'var(--text-tertiary)' },
};
