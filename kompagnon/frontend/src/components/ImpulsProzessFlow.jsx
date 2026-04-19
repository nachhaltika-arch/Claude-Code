import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';

// KOMPAGNON Brand Tokens
const PRIMARY = '#004F59';
const ACCENT  = '#FAE600';

// ── IMPULS Prozessschritte (aus ISB-158 Projektfahrplan) ──────────────────────
const IMPULS_PHASEN = [
  {
    id: 'vorbereitung',
    label: 'Vorbereitung & Antrag',
    icon: '📋',
    farbe: PRIMARY,
    schritte: [
      { id: 'erstgespraech',   nr: 1,  label: 'Erstgespräch',         desc: 'Förderfähigkeit prüfen, Paket festlegen', felder: ['isb_antrag_datum'] },
      { id: 'isb_antrag',      nr: 2,  label: 'ISB-Antrag stellen',   desc: 'Gemeinsam bei der ISB einreichen — vor Beratungsbeginn', felder: ['isb_antrag_datum'] },
      { id: 'bewilligung',     nr: 3,  label: 'Bewilligung abwarten', desc: 'ISB prüft und bestätigt den Förderantrag', felder: ['isb_bewilligung_datum'] },
    ],
  },
  {
    id: 'analyse',
    label: 'Phase 1 — Analyse',
    icon: '🔍',
    farbe: '#1D5F6A',
    schritte: [
      { id: 'ist_analyse',     nr: 4,  label: 'Unternehmens-Ist-Analyse',          desc: 'Umsatz, Kosten, Prozesse, Personal — vollständiges Unternehmensprofil' },
      { id: 'swot',            nr: 5,  label: 'SWOT & Benchmark',                  desc: 'Stärken, Schwächen, Chancen, Risiken — vollständige Matrix' },
      { id: 'finanzanalyse',   nr: 6,  label: 'Finanzanalyse',                     desc: 'Kostenstruktur, Deckungsbeitrag, Liquidität, Rentabilität' },
      { id: 'zielgruppen',     nr: 7,  label: 'Zielgruppen & Kundensegmentierung', desc: 'Wer sind die profitabelsten Kunden? ABC-Analyse' },
    ],
  },
  {
    id: 'strategie',
    label: 'Phase 2 — Strategie & Marketing',
    icon: '🎯',
    farbe: '#1A6B4A',
    schritte: [
      { id: 'unternehmensstrategie', nr: 8,  label: 'Unternehmensstrategie & Vision', desc: 'Strategisches Leitbild, Wachstumsrichtung 3–5 Jahre' },
      { id: 'positionierung',        nr: 9,  label: 'USP & Positionierung',            desc: 'Was macht das Unternehmen einzigartig? Klares Positionierungsstatement' },
      { id: 'marketingstrategie',    nr: 10, label: 'Marketing & Vertriebsstrategie',  desc: 'Kanalstrategie, Content-Plan, Pricing, Vertriebsroadmap' },
    ],
  },
  {
    id: 'digitalisierung',
    label: 'Phase 3 — Digitalisierung & KI',
    icon: '💻',
    farbe: '#3B5998',
    schritte: [
      { id: 'digital_status',  nr: 11, label: 'Digitalisierungscheck',   desc: 'Status quo: Welche Tools, welche Lücken?' },
      { id: 'ki_potenziale',   nr: 12, label: 'KI-Potenzialanalyse',     desc: 'Wo kann KI Prozesse verbessern oder automatisieren?' },
      { id: 'digital_roadmap', nr: 13, label: 'Digitale Roadmap',        desc: 'Priorisierter Umsetzungsplan mit Werkzeugen und Budgets' },
    ],
  },
  {
    id: 'design',
    label: 'Phase 6 — Kommunikationsdesign',
    icon: '🎨',
    farbe: '#6B2D8B',
    schritte: [
      { id: 'ci_check',        nr: 14, label: 'CI-Analyse & Brand Check', desc: 'Logo, Farbwelt, Typografie, Tonalität — Stärken/Schwächen' },
      { id: 'kommunikation',   nr: 15, label: 'Kommunikationskonzept',    desc: 'Zielgruppengerechte Kommunikationsstrategie, Designleitfaden' },
      { id: 'umsetzung',       nr: 16, label: 'Umsetzungsbegleitung',     desc: 'Website, Broschüre, Social Media Templates' },
    ],
  },
  {
    id: 'abschluss',
    label: 'Abschluss & Portal',
    icon: '🏁',
    farbe: '#1D7A5F',
    schritte: [
      { id: 'massnahmenplan',    nr: 17, label: 'Maßnahmenpläne & KPI-System', desc: 'Terminierte Maßnahmen, KPI-Set, Controlling-Framework' },
      { id: 'ergebnis_portal',   nr: 18, label: 'Ergebnis-Portal erstellen',   desc: 'Alle Beratungsergebnisse passwortgeschützt dokumentiert' },
      { id: 'leasing_abschluss', nr: 19, label: 'Leasing & ISB-Abrechnung',    desc: 'MMV Leasing abschließen, ISB-Verwendungsnachweis einreichen' },
    ],
  },
];

export default function ImpulsProzessFlow({ project, lead, token }) {
  const { user } = useAuth() || {};
  const isAdmin   = user?.role === 'admin' || user?.role === 'superadmin';
  const headers   = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [aktivePhase,  setAktivePhase]  = useState(null);
  const [aktiverSchritt, setAktiverSchritt] = useState(null);
  const [notizen,      setNotizen]      = useState({});
  const [erledigt,     setErledigt]     = useState({});

  // Fortschritt aus Projekt laden
  useEffect(() => {
    if (!project) return;
    const gespeichert = project.impuls_fortschritt
      ? (typeof project.impuls_fortschritt === 'string'
          ? (() => { try { return JSON.parse(project.impuls_fortschritt); } catch { return {}; } })()
          : project.impuls_fortschritt)
      : {};
    setErledigt(gespeichert.erledigt || {});
    setNotizen(gespeichert.notizen || {});
  }, [project?.id]);

  const gesamtSchritte   = IMPULS_PHASEN.flatMap(p => p.schritte).length;
  const erledigtAnzahl   = Object.values(erledigt).filter(Boolean).length;
  const fortschrittPct   = Math.round((erledigtAnzahl / gesamtSchritte) * 100);

  const persist = async (nextErledigt, nextNotizen) => {
    try {
      await fetch(`${API_BASE_URL}/api/projects/${project.id}`, {
        method: 'PUT', headers,
        body: JSON.stringify({
          impuls_fortschritt: JSON.stringify({ erledigt: nextErledigt, notizen: nextNotizen }),
        }),
      });
    } catch { toast.error('Speichern fehlgeschlagen'); }
  };

  const toggleErledigt = useCallback(async (schrittId) => {
    if (!isAdmin) return;
    const neu = { ...erledigt, [schrittId]: !erledigt[schrittId] };
    setErledigt(neu);
    persist(neu, notizen);
  }, [erledigt, notizen, project?.id, isAdmin]);

  const speichereNotiz = useCallback(async (schrittId, text) => {
    const neu = { ...notizen, [schrittId]: text };
    setNotizen(neu);
    persist(erledigt, neu);
  }, [erledigt, notizen, project?.id]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: 16, overflow: 'auto' }}>

      {/* Header Karte mit Projektstatus */}
      <div style={{ background: PRIMARY, borderRadius: 12, padding: '20px 24px', color: '#fff' }}>
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
          IMPULS by KOMPAGNON · ISB-158
        </div>
        <div style={{ fontSize: 20, fontWeight: 900, marginBottom: 12 }}>
          {lead?.company_name || lead?.display_name || 'Projekt'}
        </div>

        {/* Fortschrittsbalken */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ flex: 1, height: 6, background: 'rgba(255,255,255,0.2)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ width: `${fortschrittPct}%`, height: '100%', background: ACCENT, borderRadius: 3, transition: 'width 0.5s ease' }} />
          </div>
          <span style={{ fontSize: 12, fontWeight: 700, color: ACCENT, whiteSpace: 'nowrap' }}>
            {erledigtAnzahl} / {gesamtSchritte}
          </span>
        </div>

        {/* ISB-Eckdaten */}
        <div style={{ display: 'flex', gap: 20, marginTop: 14, flexWrap: 'wrap' }}>
          {[
            { label: 'Tagewerke', value: `${project?.tagewerke_verbraucht || 0} / ${project?.tagewerke_gesamt || 20} TW` },
            { label: 'Förderung', value: project?.isb_foerdersumme ? `${(project.isb_foerdersumme / 2).toLocaleString('de-DE')} €` : '—' },
            { label: 'Leasingrate', value: project?.mmv_leasingrate ? `~${Math.round(project.mmv_leasingrate)} €/Monat` : '—' },
          ].map(k => (
            <div key={k.label}>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{k.label}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', marginTop: 2 }}>{k.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Phasen */}
      {IMPULS_PHASEN.map(phase => {
        const phaseErledigt = phase.schritte.filter(s => erledigt[s.id]).length;
        const phaseOffen    = phase.schritte.length - phaseErledigt;
        const istAktiv      = aktivePhase === phase.id;

        return (
          <div key={phase.id} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 12, overflow: 'hidden' }}>

            {/* Phasen-Header */}
            <div
              onClick={() => setAktivePhase(istAktiv ? null : phase.id)}
              style={{ padding: '14px 18px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: istAktiv ? `${phase.farbe}10` : 'transparent', borderLeft: `4px solid ${phase.farbe}` }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 18 }}>{phase.icon}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{phase.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {phaseErledigt}/{phase.schritte.length} abgeschlossen
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {phaseOffen === 0 && (
                  <span style={{ fontSize: 11, background: '#1D9E7520', color: '#1D9E75', padding: '2px 8px', borderRadius: 20, fontWeight: 700 }}>✓ Fertig</span>
                )}
                <span style={{ color: 'var(--text-tertiary)', fontSize: 18 }}>{istAktiv ? '▾' : '▸'}</span>
              </div>
            </div>

            {/* Schritte (aufklappbar) */}
            {istAktiv && (
              <div style={{ padding: '8px 0' }}>
                {phase.schritte.map(schritt => {
                  const istFertig  = !!erledigt[schritt.id];
                  const istOffen   = aktiverSchritt === schritt.id;

                  return (
                    <div key={schritt.id} style={{ borderTop: '1px solid var(--border-light)' }}>
                      <div
                        onClick={() => setAktiverSchritt(istOffen ? null : schritt.id)}
                        style={{ padding: '10px 18px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12, background: istOffen ? 'var(--bg-app)' : 'transparent' }}
                      >
                        {/* Checkbox */}
                        <div
                          onClick={e => { e.stopPropagation(); toggleErledigt(schritt.id); }}
                          style={{ width: 20, height: 20, borderRadius: 5, border: `2px solid ${istFertig ? phase.farbe : 'var(--border-medium)'}`, background: istFertig ? phase.farbe : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: isAdmin ? 'pointer' : 'not-allowed', flexShrink: 0 }}
                        >
                          {istFertig && <span style={{ color: '#fff', fontSize: 12, lineHeight: 1 }}>✓</span>}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: istFertig ? 'var(--text-tertiary)' : 'var(--text-primary)', textDecoration: istFertig ? 'line-through' : 'none' }}>
                            {schritt.nr}. {schritt.label}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{schritt.desc}</div>
                        </div>
                        <span style={{ color: 'var(--text-tertiary)', fontSize: 14 }}>{istOffen ? '▾' : '▸'}</span>
                      </div>

                      {/* Notizfeld */}
                      {istOffen && isAdmin && (
                        <div style={{ padding: '10px 18px 14px 52px', background: 'var(--bg-app)' }}>
                          <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 5 }}>
                            Notizen / Ergebnisse
                          </label>
                          <textarea
                            value={notizen[schritt.id] || ''}
                            onChange={e => speichereNotiz(schritt.id, e.target.value)}
                            placeholder={`Ergebnisse zu ${schritt.label} dokumentieren...`}
                            rows={3}
                            style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 8, fontSize: 13, fontFamily: 'inherit', resize: 'vertical', outline: 'none', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' }}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
