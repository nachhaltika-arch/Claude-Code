import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

/**
 * Die Schnellsuche im Hauptmenü (Wunsch David, 06.09.2026).
 *
 * **Der Befund: Es gab keine.** Wer einen Betrieb suchte, ging auf die
 * Betriebsliste; wer ein Projekt suchte, auf die Pipeline; wer einen Zugang
 * suchte, in die Benutzerverwaltung. Die Frage „wo ist Firma Müller?" hatte je
 * nach Gegenstand eine andere Antwort — und wer den Gegenstand nicht kannte,
 * suchte dreimal.
 *
 * **Was sie nicht tut: bei jedem Tastendruck fragen.** 300 ms Ruhe, und erst
 * ab zwei Zeichen. Eine Suche, die jedem Buchstaben hinterherläuft, erzeugt
 * fünf Abfragen über drei Tabellen für ein Wort.
 *
 * **Die Tastatur führt.** Pfeiltasten wählen, Enter springt, Escape schließt.
 * Wer sucht, hat die Hände auf der Tastatur; ihn zur Maus zu zwingen ist der
 * längere Weg.
 *
 * **Nur Innendienst.** Der Endpunkt weist Kunden ab; das Feld erscheint bei
 * ihnen gar nicht erst — ein Suchfeld, das immer „nicht erlaubt" sagt, ist
 * schlimmer als keines.
 */
export default function Schnellsuche() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [begriff, setBegriff] = useState('');
  const [treffer, setTreffer] = useState([]);
  const [hinweis, setHinweis] = useState('');
  const [offen, setOffen] = useState(false);
  const [aktiv, setAktiv] = useState(0);
  const feld = useRef(null);

  const suchen = useCallback(async (wort) => {
    if (!wort || wort.trim().length < 2) { setTreffer([]); setHinweis(''); return; }
    try {
      const res = await fetch(`${API_BASE_URL}/api/suche?q=${encodeURIComponent(wort)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setTreffer([]); return; }
      const d = await res.json();
      setTreffer(d.treffer || []);
      setHinweis(d.hinweis || '');
      setAktiv(0);
    } catch { /* Ein Netzfehler lässt die Liste leer, statt die Leiste zu kippen. */ }
  }, [token]);

  useEffect(() => {
    const t = setTimeout(() => suchen(begriff), 300);
    return () => clearTimeout(t);
  }, [begriff, suchen]);

  /* Strg+K bzw. Cmd+K — dieselbe Taste wie überall sonst. */
  useEffect(() => {
    const auf = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        feld.current?.focus();
        setOffen(true);
      }
    };
    window.addEventListener('keydown', auf);
    return () => window.removeEventListener('keydown', auf);
  }, []);

  if (user?.role === 'kunde') return null;

  const springen = (t) => {
    navigate(t.ziel);
    setBegriff(''); setTreffer([]); setOffen(false);
    feld.current?.blur();
  };

  const taste = (e) => {
    if (e.key === 'Escape') { setOffen(false); feld.current?.blur(); return; }
    if (!treffer.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setAktiv((i) => (i + 1) % treffer.length); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setAktiv((i) => (i - 1 + treffer.length) % treffer.length); }
    if (e.key === 'Enter') { e.preventDefault(); springen(treffer[aktiv]); }
  };

  return (
    <div style={S.rahmen}>
      <input
        ref={feld}
        value={begriff}
        onChange={(e) => { setBegriff(e.target.value); setOffen(true); }}
        onFocus={() => setOffen(true)}
        onKeyDown={taste}
        placeholder="Suchen … (⌘K)"
        aria-label="Betriebe, Projekte und Zugänge durchsuchen"
        style={S.feld}
      />

      {offen && (begriff.trim().length >= 2) && (
        <div style={S.liste} role="listbox">
          {treffer.length === 0 && (
            <p style={S.leer}>{hinweis || 'Nichts gefunden.'}</p>
          )}
          {treffer.map((t, i) => (
            <button key={`${t.art}-${t.ziel}-${t.titel}`}
                    onClick={() => springen(t)}
                    onMouseEnter={() => setAktiv(i)}
                    role="option" aria-selected={i === aktiv}
                    style={{ ...S.zeile, ...(i === aktiv ? S.zeileAktiv : {}) }}>
              {/* Die Art steht vorn — eine Liste aus Namen lässt offen, ob
                  „Müller" der Betrieb, das Projekt oder der Zugang ist. */}
              <span style={S.art}>{ART[t.art] || t.art}</span>
              <span style={S.mitte}>
                <span style={S.titel}>{t.titel}</span>
                {t.dazu && <span style={S.dazu}>{t.dazu}</span>}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const ART = { betrieb: 'Betrieb', projekt: 'Projekt', zugang: 'Zugang' };

const S = {
  rahmen: { position: 'relative', padding: '10px 12px 2px' },
  feld: { width: '100%', boxSizing: 'border-box', padding: '9px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.18)', background: 'rgba(255,255,255,0.08)', color: '#fff', fontSize: 13, fontFamily: 'inherit', outline: 'none' },
  liste: { position: 'absolute', left: 12, right: 12, top: '100%', zIndex: 40, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 8, boxShadow: '0 12px 32px rgba(0,0,0,.28)', maxHeight: 420, overflowY: 'auto', padding: 4 },
  zeile: { display: 'flex', gap: 10, alignItems: 'flex-start', width: '100%', padding: '9px 10px', background: 'none', border: 'none', borderRadius: 6, textAlign: 'left', font: 'inherit', color: 'var(--text-primary)', cursor: 'pointer' },
  zeileAktiv: { background: 'var(--bg-app)' },
  /* **12 px ist die Untergrenze, nicht eine Empfehlung** (L-17). Hier stand
     erst 10 px für die Art und 11 px für die Zeile darunter — `test_
     schriftgroessen.py` hat beides im selben Lauf gemeldet. Eine
     Trefferliste, die man zusammenkneifen muss, ist keine Hilfe; die Art
     bleibt trotzdem ruhig, weil sie in Großbuchstaben und gedämpft steht. */
  art: { flex: 'none', fontSize: 12, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-tertiary)', paddingTop: 2, minWidth: 62 },
  mitte: { display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 },
  titel: { fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' },
  dazu: { fontSize: 12, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  leer: { fontSize: 12, color: 'var(--text-tertiary)', padding: '10px 12px', margin: 0 },
};
