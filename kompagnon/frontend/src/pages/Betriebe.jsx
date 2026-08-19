// Die Betriebsliste — eine Liste, eine Zahl.
//
// Bis 2026-08-17 gab es zwei Bildschirme mit denselben Firmen:
// „Unternehmen" (/app/companies, Tabelle, Quellenfilter, Anlegen-Knopf) und
// „Kunden" (/app/customers, bessere Gestaltung, Kennzahlen, Statusfilter,
// aber ohne Menueeintrag). Sie zeigten 61 gegen 50 Eintraege.
//
// Der Grund war kein Filter: „Kunden" rief `/api/leads/` ohne `limit` auf und
// bekam die Voreinstellung des Servers — 50 (`routers/leads.py:249`). Elf
// Betriebe fehlten still, und **jede Kennzahl darueber war falsch**, weil sie
// ueber die abgeschnittene Liste gerechnet wurde. Eine abgeschnittene Zahl,
// die „Gesamt" heisst, ist schlimmer als gar keine.
//
// Uebrig bleibt dieser Bildschirm: die Gestaltung von „Kunden", die Funktionen
// von „Unternehmen", die Listenlogik in `utils/betriebeListe.js`.

import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import { apiRequest } from '../utils/apiRequest';
import EmptyState from '../components/ui/EmptyState';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import BetriebAnlegenModal from '../components/BetriebAnlegenModal';
import { leadStatusLabel, leadStatusVariant } from '../utils/leadStatus';
import { stufeFuerScore, stufeKurz } from '../utils/homepageStandard';
import {
  betriebeAufbereiten,
  betriebeStatistik,
  quellenAusBetrieben,
  BETRIEB_SORTIERUNGEN,
} from '../utils/betriebeListe';

// Wie viele Betriebe hoechstens geholt werden. Kein stiller Deckel: Kommen
// genau so viele zurueck, sagt die Seite es (siehe `amDeckel` unten).
const MAX_BETRIEBE = 1000;

/**
 * Farbe des Scores nach den Stufen des Homepage Standards.
 *
 * Vorher stand in „Kunden" eine eigene Staffelung 85/70/50/30 mit den Kuerzeln
 * Pt/Go/Si/Br im Kreis vor dem Namen. Das war die **zurueckgezogene** Skala:
 * `utils/homepageStandard.js` haelt fest, dass genau diese Staffelung gegen die
 * des Backends (95/85/70/50) getauscht wurde, weil derselbe Score im Bericht
 * „Silber" und im Widget „Gold" hiess. In dieser Liste hatte sie ueberlebt —
 * ein Betrieb mit 86 Punkten trug hier „Pt", waehrend sein Bericht „Homepage
 * Standard Gold" sagt.
 *
 * Die Kuerzel sind mit ihr entfallen: Zwei Buchstaben ohne Legende sind nicht
 * zu entschluesseln. Der Kreis zeigt jetzt den Anfangsbuchstaben des Betriebs
 * — wofuer ein solcher Kreis da ist —, die Stufe steht am Score.
 */
function scoreFarbe(score) {
  if (score >= 85) return 'var(--status-success-text)';
  if (score >= 50) return 'var(--status-warning-text)';
  return 'var(--status-danger-text)';
}

const domain = (url) => {
  if (!url) return '';
  try {
    return new URL(url.startsWith('http') ? url : `https://${url}`).hostname.replace('www.', '');
  } catch {
    return url;
  }
};

const SPALTEN = '2fr 1fr 120px 120px 40px';

export default function Betriebe() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { isMobile } = useScreenSize();

  const [betriebe, setBetriebe] = useState([]);
  const [laedt, setLaedt] = useState(true);
  const [ladefehler, setLadefehler] = useState(null);

  const [suche, setSuche] = useState('');
  const [status, setStatus] = useState('alle');
  // Wo im Trichter — getrennt vom Bearbeitungsstand. Der Status oben
  // beantwortete beides gleichzeitig (19.08.2026).
  const [phase, setPhase] = useState('alle');
  const [quelle, setQuelle] = useState('alle');
  const [sortierung, setSortierung] = useState('name');
  const [dialogOffen, setDialogOffen] = useState(false);

  const laden = useCallback(async () => {
    setLaedt(true);
    setLadefehler(null);
    try {
      // apiRequest statt loadJson: Ein Ladefehler darf hier nicht als leere
      // Liste erscheinen — „Noch keine Betriebe" waere dann eine Falschaussage.
      const daten = await apiRequest(`${API_BASE_URL}/api/leads/?limit=${MAX_BETRIEBE}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setBetriebe(Array.isArray(daten) ? daten : []);
    } catch (fehler) {
      setLadefehler(fehler.message);
    } finally {
      setLaedt(false);
    }
  }, [token]);

  useEffect(() => { laden(); }, [laden]);

  const gefiltert = useMemo(
    () => betriebeAufbereiten({ betriebe, suche, status, quelle, phase, sortierung }),
    [betriebe, suche, status, quelle, phase, sortierung],
  );
  const stat    = useMemo(() => betriebeStatistik(betriebe), [betriebe]);
  const quellen = useMemo(() => quellenAusBetrieben(betriebe), [betriebe]);

  const gefiltertWird = suche !== '' || status !== 'alle' || quelle !== 'alle';
  const amDeckel = betriebe.length === MAX_BETRIEBE;

  const filterZuruecksetzen = () => { setSuche(''); setStatus('alle'); setQuelle('alle'); };

  // ── Laden ────────────────────────────────────────────────────────────

  if (laedt) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 64 }} />)}
        </div>
        <div className="skeleton" style={{ height: 44 }} />
        {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton" style={{ height: 56 }} />)}
      </div>
    );
  }

  // ── Ladefehler ───────────────────────────────────────────────────────

  if (ladefehler) {
    return (
      <Card>
        <EmptyState
          icon="⚠️"
          title="Die Betriebe konnten nicht geladen werden"
          description={ladefehler}
          action={{ label: 'Erneut versuchen', onClick: laden }}
        />
      </Card>
    );
  }

  // ── Anzeige ──────────────────────────────────────────────────────────

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: '100%', minWidth: 0, overflowX: 'hidden' }}>

      {/* Kennzahlen — ueber alle Betriebe, nicht ueber die gefilterte Auswahl */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, minWidth: 0, width: '100%' }}>
        <MiniStat label="Betriebe" value={stat.gesamt} />
        <MiniStat label="Mit Score" value={stat.mitScore} />
        <MiniStat
          label="Ø Score"
          value={stat.durchschnittsScore || '—'}
          color={stat.durchschnittsScore >= 70 ? 'var(--status-success-text)' : stat.durchschnittsScore >= 50 ? 'var(--status-warning-text)' : undefined}
        />
        {stat.statusZaehler.slice(0, 3).map(s => (
          <MiniStat
            key={s.key} label={s.label} value={s.anzahl}
            onClick={() => setStatus(status === s.key ? 'alle' : s.key)}
            active={status === s.key}
          />
        ))}
      </div>

      {amDeckel && (
        <div style={{ fontSize: 11, color: 'var(--status-warning-text)' }}>
          Es werden höchstens {MAX_BETRIEBE} Betriebe geladen — diese Liste ist
          vollständig gefüllt und zeigt womöglich nicht alle.
        </div>
      )}

      {/* Suche, Filter, Sortierung, Anlegen */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
          <svg aria-hidden="true" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}>
            <circle cx="7" cy="7" r="5" /><path d="M11 11l3.5 3.5" />
          </svg>
          <input
            type="search" value={suche} onChange={e => setSuche(e.target.value)}
            aria-label="Betriebe durchsuchen"
            placeholder="Suchen nach Name, Ort, Gewerk, E-Mail…"
            style={{
              width: '100%', padding: '9px 12px 9px 34px',
              border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
              fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)',
              color: 'var(--text-primary)', outline: 'none', transition: 'border-color 0.15s',
            }}
            onFocus={e => { e.target.style.borderColor = 'var(--brand-primary-mid)'; }}
            onBlur={e => { e.target.style.borderColor = 'var(--border-light)'; }}
          />
        </div>

        {/* Quelle — nur die Quellen, die vorkommen */}
        <select
          value={quelle} onChange={e => setQuelle(e.target.value)}
          aria-label="Nach Quelle filtern"
          style={auswahlStil}
        >
          {quellen.map(q => (
            <option key={q.key} value={q.key}>{q.label} ({q.anzahl})</option>
          ))}
        </select>

        <select
          value={sortierung} onChange={e => setSortierung(e.target.value)}
          aria-label="Sortierung"
          style={auswahlStil}
        >
          {BETRIEB_SORTIERUNGEN.map(s => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>

        <button
          type="button" onClick={() => setDialogOffen(true)}
          style={{
            padding: '9px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
            border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap',
          }}
        >
          + Neuer Betrieb
        </button>
      </div>

      {/* Phasenfilter — wo im Trichter. „Phase offen" ist die Schaltflaeche
        * fuer Betriebe mit einem Status, den die Zuordnung nicht kennt: Ein
        * unbekannter Wert soll sich zeigen, nicht verschwinden. */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {[{ key: 'alle', label: 'Alle Phasen', anzahl: betriebe.length }, ...stat.phasenZaehler].map(p => {
          const aktiv = phase === p.key;
          return (
            <button
              key={p.key} type="button" onClick={() => setPhase(p.key)}
              aria-pressed={aktiv}
              style={{
                padding: '5px 10px', borderRadius: 'var(--radius-full)',
                border: `1px solid ${aktiv ? 'var(--border-medium)' : 'var(--border-light)'}`,
                background: aktiv ? 'var(--bg-active)' : 'transparent',
                color: aktiv ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                fontSize: 11, fontWeight: aktiv ? 500 : 400, cursor: 'pointer',
                fontFamily: 'var(--font-sans)', transition: 'all 0.1s', whiteSpace: 'nowrap',
              }}
            >
              {p.label}
              <span style={{ marginLeft: 4, opacity: 0.6 }}>{p.anzahl}</span>
            </button>
          );
        })}
      </div>

      {/* Statusfilter — aus den Daten, damit auch ein unbekannter Status
        * erreichbar ist und die Zahlen aufgehen */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {[{ key: 'alle', label: 'Alle', anzahl: betriebe.length }, ...stat.statusZaehler].map(s => {
          const aktiv = status === s.key;
          return (
            <button
              key={s.key} type="button" onClick={() => setStatus(s.key)}
              aria-pressed={aktiv}
              style={{
                padding: '5px 10px', borderRadius: 'var(--radius-full)',
                border: `1px solid ${aktiv ? 'var(--border-medium)' : 'var(--border-light)'}`,
                background: aktiv ? 'var(--bg-active)' : 'transparent',
                color: aktiv ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                fontSize: 11, fontWeight: aktiv ? 500 : 400, cursor: 'pointer',
                fontFamily: 'var(--font-sans)', transition: 'all 0.1s', whiteSpace: 'nowrap',
              }}
            >
              {s.label}
              <span style={{ marginLeft: 4, opacity: 0.6 }}>{s.anzahl}</span>
            </button>
          );
        })}
      </div>

      {/* Was gerade gezeigt wird — und warum es weniger sein kann */}
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        <span>
          {gefiltertWird
            ? `${gefiltert.length} von ${betriebe.length} Betrieben`
            : `${betriebe.length} ${betriebe.length === 1 ? 'Betrieb' : 'Betriebe'}`}
          {suche && ` · Suche: „${suche}"`}
          {status !== 'alle' && ` · Status: ${leadStatusLabel(status)}`}
          {quelle !== 'alle' && ` · Quelle: ${quellen.find(q => q.key === quelle)?.label || quelle}`}
        </span>
        {gefiltertWird && (
          <button
            type="button" onClick={filterZuruecksetzen}
            style={{
              background: 'none', border: 'none', padding: 0, cursor: 'pointer',
              fontSize: 11, color: 'var(--brand-primary)', fontFamily: 'var(--font-sans)',
              textDecoration: 'underline',
            }}
          >
            Filter zurücksetzen
          </button>
        )}
      </div>

      {/* Die Liste */}
      {gefiltert.length === 0 ? (
        <Card style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
          <EmptyState
            icon="🏢"
            title={gefiltertWird ? 'Kein Betrieb passt zu dieser Auswahl' : 'Noch keine Betriebe'}
            description={gefiltertWird
              ? 'Andere Suchbegriffe versuchen oder die Filter zurücksetzen.'
              : 'Betriebe aus einer Datei importieren oder von Hand anlegen.'}
            action={gefiltertWird
              ? { label: 'Filter zurücksetzen', onClick: filterZuruecksetzen }
              : { label: '+ Neuer Betrieb', onClick: () => setDialogOffen(true) }}
            secondaryAction={gefiltertWird
              ? undefined
              : { label: 'Domains importieren', onClick: () => navigate('/app/import') }}
          />
        </Card>
      ) : (
        <Card padding="sm" style={{ padding: 0, overflow: 'hidden', width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
          {!isMobile && (
            <div style={{
              display: 'grid', gridTemplateColumns: SPALTEN, gap: 16,
              padding: '10px 20px', borderBottom: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
            }}>
              {['Betrieb', 'Ort', 'Status', 'Score', ''].map((kopf, i) => (
                <span key={i} style={{
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: '0.04em', color: 'var(--text-tertiary)',
                }}>{kopf}</span>
              ))}
            </div>
          )}

          {gefiltert.map((betrieb, idx) => {
            const score = betrieb.analysis_score || 0;
            const name = betrieb.display_name || betrieb.company_name || 'Unbekannt';
            // Die Liste liefert keine Stufe vom Server (`routers/leads.py:263 ff.`),
            // nur den Score — also wird sie nachgerechnet. Die K.-o.-Regeln
            // (kein Impressum, kein TLS) kann sie damit nicht kennen; die volle
            // Wahrheit steht im Bericht des Betriebs.
            const stufe = score > 0 ? stufeFuerScore(score) : null;

            return (
              <div
                key={betrieb.id}
                onClick={() => navigate(`/app/betriebe/${betrieb.id}`)}
                style={{
                  display: isMobile ? 'flex' : 'grid',
                  gridTemplateColumns: isMobile ? undefined : SPALTEN,
                  flexDirection: isMobile ? 'column' : undefined,
                  gap: isMobile ? 6 : 16,
                  alignItems: isMobile ? 'stretch' : 'center',
                  padding: isMobile ? '12px 16px' : '10px 20px',
                  borderBottom: idx < gefiltert.length - 1 ? '1px solid var(--border-light)' : 'none',
                  cursor: 'pointer', transition: 'background 0.1s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
              >
                {/* Name */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                  <div
                    aria-hidden="true"
                    style={{
                      width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                      background: 'var(--brand-primary-light)',
                      color: 'var(--brand-primary)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, fontWeight: 600,
                    }}
                  >
                    {name[0] || '?'}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{
                      fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {name}
                    </div>
                    <div style={{
                      fontSize: 11, color: 'var(--text-tertiary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {betrieb.trade || ''}
                      {betrieb.trade && betrieb.website_url ? ' · ' : ''}
                      {domain(betrieb.website_url)}
                    </div>
                  </div>
                </div>

                {/* Ort */}
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', display: isMobile ? 'none' : 'block' }}>
                  {betrieb.city || '—'}
                </div>

                {/* Status */}
                <div style={isMobile ? { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } : {}}>
                  {isMobile && <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{betrieb.city}</span>}
                  <Badge variant={leadStatusVariant(betrieb.status)}>
                    {leadStatusLabel(betrieb.status)}
                  </Badge>
                </div>

                {/* Score */}
                <div>
                  {score > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }} title={stufe}>
                      <span style={{
                        fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-mono)',
                        color: scoreFarbe(score), minWidth: 22,
                      }}>
                        {score}
                      </span>
                      <div style={{ flex: 1, height: 4, background: 'var(--border-light)', borderRadius: 2, maxWidth: 50 }}>
                        <div style={{
                          width: `${Math.min(100, score)}%`, height: '100%', borderRadius: 2,
                          background: scoreFarbe(score),
                        }} />
                      </div>
                      {/* Welche Farbe welche Stufe bedeutet, stand vorher nur
                        * im `title` — also im Tooltip, den es auf einem
                        * Berührungsgerät gar nicht gibt (UX-28). */}
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>
                        {stufeKurz(score)}
                      </span>
                    </div>
                  ) : (
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Kein Audit</span>
                  )}
                </div>

                {/* Pfeil */}
                <div style={{ display: isMobile ? 'none' : 'flex', justifyContent: 'flex-end' }}>
                  <svg aria-hidden="true" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" strokeLinecap="round">
                    <path d="M6 4l4 4-4 4" />
                  </svg>
                </div>
              </div>
            );
          })}
        </Card>
      )}

      {dialogOffen && (
        <BetriebAnlegenModal
          token={token}
          onClose={() => setDialogOffen(false)}
          onCreated={(betrieb) => {
            setDialogOffen(false);
            if (betrieb?.id) navigate(`/app/betriebe/${betrieb.id}`);
            else laden();
          }}
        />
      )}
    </div>
  );
}

const auswahlStil = {
  padding: '8px 10px', border: '1px solid var(--border-light)',
  borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: 'var(--font-sans)',
  background: 'var(--bg-surface)', color: 'var(--text-secondary)',
  cursor: 'pointer', outline: 'none',
};

function MiniStat({ label, value, color, onClick, active }) {
  const Element = onClick ? 'button' : 'div';
  return (
    <Element
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      aria-pressed={onClick ? Boolean(active) : undefined}
      style={{
        background: active ? 'var(--bg-active)' : 'var(--bg-surface)',
        border: `1px solid ${active ? 'var(--border-medium)' : 'var(--border-light)'}`,
        borderRadius: 'var(--radius-md)', padding: '10px 12px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s', textAlign: 'left', font: 'inherit', width: '100%',
      }}
    >
      <div style={{
        fontSize: 20, fontWeight: 500, fontFamily: 'var(--font-sans)',
        color: color || (active ? 'var(--brand-primary)' : 'var(--text-primary)'),
        lineHeight: 1, marginBottom: 3,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>
    </Element>
  );
}
