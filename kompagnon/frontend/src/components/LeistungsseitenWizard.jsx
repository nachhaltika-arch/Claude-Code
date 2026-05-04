import React, { useState, useEffect, useRef, useId } from 'react';
import { createPortal } from 'react-dom';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';

// ── Konstanten ───────────────────────────────────────────────────────────────

const TEAL = 'var(--brand-primary)';

const STEPS = [
  'Leistung definieren',
  'Zielkunde & Problem',
  'USP & Preis',
  'Beweis & Vertrauen',
  'Kontakt & CTA',
];

const ZIELGRUPPE_OPTIONS = ['Privatkunden', 'Geschäftskunden', 'Beides'];
const KONTAKT_OPTIONS    = ['Telefon', 'WhatsApp', 'Kontaktformular', 'Alle drei'];

const DEFAULT_DATA = {
  // Step 1
  leistung: '',
  gebiet: '',
  zielgruppe: '',
  // Step 2
  idealer_kunde: '',
  problem: '',
  problem_folgen: '',
  // Step 3
  usp: '',
  einstiegspreis: '',
  inkludiert: '',
  // Step 4
  referenzen: '',
  projekt_anzahl: '',
  kundenstimmen: '',
  zertifikate: '',
  // Step 5
  kontakt_kanal: '',
  telefon: '',
  cta_text: '',
  dringlichkeit: '',
};

// ── Draft-Persistenz ─────────────────────────────────────────────────────────

const DRAFT_KEY = (projectId) => `leistungsseiten_draft_${projectId}`;

function saveDraft(projectId, data, step) {
  try {
    localStorage.setItem(
      DRAFT_KEY(projectId),
      JSON.stringify({ data, step, savedAt: new Date().toISOString() })
    );
  } catch {}
}

function loadDraft(projectId) {
  try {
    const raw = localStorage.getItem(DRAFT_KEY(projectId));
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function clearDraft(projectId) {
  try { localStorage.removeItem(DRAFT_KEY(projectId)); } catch {}
}

function formatDraftAge(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'gerade eben';
  if (min < 60) return `vor ${min} Minuten`;
  const h = Math.floor(min / 60);
  if (h < 24) return `vor ${h} Stunden`;
  return `vor ${Math.floor(h / 24)} Tagen`;
}

// ── Inline-Helper-Komponenten ────────────────────────────────────────────────

const inputBase = {
  width: '100%', padding: '10px 12px',
  border: '1.5px solid var(--border-light)', borderRadius: 8,
  fontSize: 14, fontFamily: 'var(--font-sans, system-ui)',
  color: 'var(--text-primary)', background: 'var(--bg-elevated)',
  outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};

function Input({ value, onChange, placeholder, onBlur, hasError, id, type = 'text' }) {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        ...inputBase,
        borderColor: hasError ? 'var(--status-danger-text)' : undefined,
        background: hasError ? 'var(--status-danger-bg)' : undefined,
      }}
      onFocus={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL; }}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    />
  );
}

function Textarea({ value, onChange, placeholder, rows = 4, onBlur, hasError, maxLength, id }) {
  const len = (value || '').length;
  const tooLong = maxLength && len > maxLength;
  const counterColor = len === 0
    ? 'var(--text-tertiary)'
    : tooLong ? 'var(--status-danger-text)' : 'var(--text-tertiary)';
  return (
    <div style={{ position: 'relative' }}>
      <textarea
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        maxLength={maxLength ? maxLength + 50 : undefined}
        style={{
          ...inputBase, resize: 'vertical', lineHeight: 1.6,
          borderColor: hasError ? 'var(--status-danger-text)' : tooLong ? 'var(--status-warning-text)' : undefined,
          background: hasError ? 'var(--status-danger-bg)' : undefined,
          paddingBottom: maxLength ? 24 : undefined,
        }}
        onFocus={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL; }}
        onBlur={e => {
          e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : tooLong ? 'var(--status-warning-text)' : 'var(--border-light)';
          if (onBlur) onBlur(e);
        }}
      />
      {maxLength && (
        <div style={{
          position: 'absolute', bottom: 8, right: 10, fontSize: 10, fontWeight: 600,
          color: counterColor, pointerEvents: 'none', userSelect: 'none', transition: 'color 0.2s',
        }}>
          {len}/{maxLength}
        </div>
      )}
    </div>
  );
}

function Select({ value, onChange, options, onBlur, hasError, id }) {
  return (
    <select
      id={id}
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        ...inputBase, cursor: 'pointer', appearance: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238A9BA8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center',
        paddingRight: 36,
        borderColor: hasError ? 'var(--status-danger-text)' : undefined,
        background: hasError ? 'var(--status-danger-bg)' : undefined,
      }}
      onFocus={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL; }}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    >
      <option value="">– bitte wählen –</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function ButtonGroup({ value, onChange, options }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {options.map(opt => {
        const active = value === opt;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            style={{
              padding: '9px 16px', borderRadius: 8, fontSize: 13, fontWeight: active ? 700 : 500,
              border: `1.5px solid ${active ? 'var(--brand-primary)' : 'var(--border-light)'}`,
              background: active ? 'var(--brand-primary)' : 'var(--bg-elevated)',
              color: active ? 'var(--text-inverse)' : 'var(--text-secondary)',
              cursor: 'pointer', transition: 'all 0.15s',
              fontFamily: 'var(--font-sans, system-ui)',
            }}
          >
            {active ? '✓ ' : ''}{opt}
          </button>
        );
      })}
    </div>
  );
}

function Field({ label, required, hint, error, children }) {
  const id = useId();
  const childWithId = React.Children.map(children, (child, i) => {
    if (i === 0 && React.isValidElement(child)) return React.cloneElement(child, { id });
    return child;
  });
  return (
    <div style={{ marginBottom: 20 }}>
      <label
        htmlFor={id}
        style={{
          display: 'block', fontSize: 11, fontWeight: 700,
          color: error ? 'var(--status-danger-text)' : 'var(--text-secondary)',
          textTransform: 'uppercase', letterSpacing: '0.07em',
          marginBottom: 6, cursor: 'pointer', transition: 'color 0.15s',
        }}
      >
        {label}{required && (
          <span style={{ color: error ? 'var(--status-danger-text)' : TEAL, marginLeft: 2 }}>*</span>
        )}
      </label>
      {childWithId}
      {error ? (
        <div style={{
          fontSize: 11, color: 'var(--status-danger-text)', marginTop: 5,
          display: 'flex', alignItems: 'center', gap: 4, lineHeight: 1.4,
        }}>
          <span style={{ fontSize: 12 }}>⚠</span>{error}
        </div>
      ) : hint ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
          {hint}
        </div>
      ) : null}
    </div>
  );
}

// ── Step-Screens ─────────────────────────────────────────────────────────────

function Step1({ data, set, touch, fieldError }) {
  return (
    <div>
      <Field label="Welche Leistung soll diese Seite vermarkten?" required error={fieldError('leistung')}>
        <Input
          value={data.leistung}
          onChange={v => set('leistung', v)}
          onBlur={() => touch('leistung')}
          hasError={!!fieldError('leistung')}
          placeholder="z.B. Badsanierung, Heizungsnotdienst"
        />
      </Field>
      <Field label="In welchem Gebiet?" required error={fieldError('gebiet')}>
        <Input
          value={data.gebiet}
          onChange={v => set('gebiet', v)}
          onBlur={() => touch('gebiet')}
          hasError={!!fieldError('gebiet')}
          placeholder="z.B. Koblenz und Umgebung"
        />
      </Field>
      <Field label="Für wen?" required error={fieldError('zielgruppe')}>
        <Select
          value={data.zielgruppe}
          onChange={v => set('zielgruppe', v)}
          onBlur={() => touch('zielgruppe')}
          hasError={!!fieldError('zielgruppe')}
          options={ZIELGRUPPE_OPTIONS}
        />
      </Field>
    </div>
  );
}

function Step2({ data, set, touch, fieldError }) {
  return (
    <div>
      <Field label="Wer ist dein idealer Kunde?" required error={fieldError('idealer_kunde')}>
        <Textarea
          value={data.idealer_kunde}
          onChange={v => set('idealer_kunde', v)}
          onBlur={() => touch('idealer_kunde')}
          hasError={!!fieldError('idealer_kunde')}
          maxLength={300}
          rows={3}
          placeholder="z.B. Eigenheimbesitzer 40-65 Jahre mit Altbau, die energetisch sanieren wollen"
        />
      </Field>
      <Field label="Welches Problem löst du?" required error={fieldError('problem')}>
        <Textarea
          value={data.problem}
          onChange={v => set('problem', v)}
          onBlur={() => touch('problem')}
          hasError={!!fieldError('problem')}
          maxLength={300}
          rows={3}
          placeholder="z.B. Veraltete Heizung, hohe Energiekosten, fehlende Förderungsübersicht"
        />
      </Field>
      <Field label="Was passiert, wenn das Problem nicht gelöst wird?" hint="Optional — hilft Dringlichkeit zu erzeugen.">
        <Textarea
          value={data.problem_folgen}
          onChange={v => set('problem_folgen', v)}
          maxLength={200}
          rows={2}
          placeholder="z.B. Weiter steigende Energiekosten, Ausfallrisiko im Winter"
        />
      </Field>
    </div>
  );
}

function Step3({ data, set, touch, fieldError }) {
  return (
    <div>
      <Field label="Was macht dich besser als die Konkurrenz?" required error={fieldError('usp')}>
        <Textarea
          value={data.usp}
          onChange={v => set('usp', v)}
          onBlur={() => touch('usp')}
          hasError={!!fieldError('usp')}
          maxLength={400}
          rows={4}
          placeholder="z.B. 30 Jahre Erfahrung, Festpreisgarantie, Meisterbetrieb, 24h-Notdienst"
        />
      </Field>
      <Field label="Einstiegspreis oder Paket?" hint="Optional — wenn du mit einem Richtpreis einsteigen möchtest.">
        <Input
          value={data.einstiegspreis}
          onChange={v => set('einstiegspreis', v)}
          placeholder="z.B. ab 2.500 € · Pauschalpaket ab 4.990 €"
        />
      </Field>
      <Field label="Was ist inbegriffen?" hint="Optional — Leistungsumfang, Garantien, Extras.">
        <Textarea
          value={data.inkludiert}
          onChange={v => set('inkludiert', v)}
          maxLength={300}
          rows={3}
          placeholder="z.B. Beratung vor Ort, Material, Montage, Entsorgung, 5 Jahre Garantie"
        />
      </Field>
    </div>
  );
}

function Step4({ data, set }) {
  return (
    <div>
      <Field label="Referenzen oder abgeschlossene Projekte?" hint="Optional — wenn du konkrete Beispiele nennen möchtest.">
        <Textarea
          value={data.referenzen}
          onChange={v => set('referenzen', v)}
          maxLength={400}
          rows={3}
          placeholder="z.B. Bad-Komplettsanierung Familie Meier / Heizungsmodernisierung EFH Bj. 1985"
        />
      </Field>
      <Field label="Wie viele solcher Projekte?" hint="Optional — eine Zahl reicht.">
        <Input
          value={data.projekt_anzahl}
          onChange={v => set('projekt_anzahl', v)}
          placeholder="z.B. 150 seit 2015"
        />
      </Field>
      <Field label="Kundenstimmen oder Bewertungen?" hint="Optional — Zitat, Google-Score, ProvenExpert.">
        <Textarea
          value={data.kundenstimmen}
          onChange={v => set('kundenstimmen', v)}
          maxLength={300}
          rows={2}
          placeholder={'z.B. "Schnell, sauber, fair" — Google-Score 4,9 / 5'}
        />
      </Field>
      <Field label="Zertifikate oder Auszeichnungen?" hint="Optional — Meisterbrief, Innungszugehörigkeit, TÜV, Fachbetrieb.">
        <Input
          value={data.zertifikate}
          onChange={v => set('zertifikate', v)}
          placeholder="z.B. Meisterbetrieb der HWK, SHK-Innung, VDI 6023 zertifiziert"
        />
      </Field>
    </div>
  );
}

function Step5({ data, set, touch, fieldError }) {
  return (
    <div>
      <Field label="Wie soll der Kunde Kontakt aufnehmen?" required error={fieldError('kontakt_kanal')}>
        <ButtonGroup
          value={data.kontakt_kanal}
          onChange={v => { set('kontakt_kanal', v); touch('kontakt_kanal'); }}
          options={KONTAKT_OPTIONS}
        />
      </Field>
      <Field label="Telefonnummer" hint="Optional — falls Telefon oder WhatsApp gewählt.">
        <Input
          value={data.telefon}
          onChange={v => set('telefon', v)}
          placeholder="z.B. +49 261 1234567"
        />
      </Field>
      <Field label="CTA-Button-Text" hint="Optional — Button-Beschriftung auf der Seite.">
        <Input
          value={data.cta_text}
          onChange={v => set('cta_text', v)}
          placeholder="Jetzt kostenlos anfragen"
        />
      </Field>
      <Field label="Dringlichkeit oder Angebot?" hint="Optional — Aktionszeitraum, Rabatt, Reaktionszeit.">
        <Textarea
          value={data.dringlichkeit}
          onChange={v => set('dringlichkeit', v)}
          maxLength={200}
          rows={2}
          placeholder="z.B. Bis 31.12. 10 % Rabatt — Rückruf innerhalb 24 h"
        />
      </Field>
    </div>
  );
}

// ── Haupt-Komponente ─────────────────────────────────────────────────────────

export default function LeistungsseitenWizard({
  projectId,
  leadId,
  token,
  onClose,
  onSave,
  brandData,  // eslint-disable-line no-unused-vars
}) {
  const { isMobile } = useScreenSize();

  const existingDraft = loadDraft(projectId);
  const [data, setData] = useState(() => existingDraft?.data || DEFAULT_DATA);
  const [step, setStep] = useState(() => existingDraft?.step || 0);
  const [touched, setTouched] = useState({});
  const [showErrors, setShowErrors] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [draftBanner, setDraftBanner] = useState(
    existingDraft?.savedAt ? formatDraftAge(existingDraft.savedAt) : null
  );

  const scrollRef = useRef(null);

  useEscapeKey(() => { onClose?.(); });

  const set = (key, val) => setData(d => ({ ...d, [key]: val }));
  const touch = (field) => setTouched(prev => ({ ...prev, [field]: true }));

  const touchStep = (stepIndex) => {
    const fields = {
      0: ['leistung', 'gebiet', 'zielgruppe'],
      1: ['idealer_kunde', 'problem'],
      2: ['usp'],
      3: [],
      4: ['kontakt_kanal'],
    };
    const toTouch = {};
    (fields[stepIndex] || []).forEach(f => { toTouch[f] = true; });
    setTouched(prev => ({ ...prev, ...toTouch }));
  };

  // Auto-Save Draft
  useEffect(() => {
    const hasContent = data.leistung || data.gebiet || data.idealer_kunde || data.problem || data.usp;
    if (hasContent) saveDraft(projectId, data, step);
  }, [data, step, projectId]);

  // Reset Scroll bei Step-Wechsel
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [step]);

  const fieldError = (field) => {
    if (!touched[field] && !showErrors) return null;
    const msgs = {
      leistung:      'Bitte Leistung eintragen',
      gebiet:        'Bitte Gebiet eintragen',
      zielgruppe:    'Bitte Zielgruppe auswählen',
      idealer_kunde: 'Bitte idealen Kunden beschreiben',
      problem:       'Bitte Problem beschreiben',
      usp:           'Bitte USP eintragen',
      kontakt_kanal: 'Bitte Kontakt-Kanal wählen',
    };
    const empty = {
      leistung:      !data.leistung?.trim(),
      gebiet:        !data.gebiet?.trim(),
      zielgruppe:    !data.zielgruppe,
      idealer_kunde: !data.idealer_kunde?.trim(),
      problem:       !data.problem?.trim(),
      usp:           !data.usp?.trim(),
      kontakt_kanal: !data.kontakt_kanal,
    };
    return empty[field] ? (msgs[field] || 'Pflichtfeld') : null;
  };

  const canNext = () => {
    if (step === 0) return !!data.leistung?.trim() && !!data.gebiet?.trim() && !!data.zielgruppe;
    if (step === 1) return !!data.idealer_kunde?.trim() && !!data.problem?.trim();
    if (step === 2) return !!data.usp?.trim();
    if (step === 3) return true;
    if (step === 4) return !!data.kontakt_kanal;
    return true;
  };

  const handleNext = () => {
    if (!canNext()) { touchStep(step); setShowErrors(true); return; }
    setShowErrors(false);
    setStep(s => Math.min(s + 1, STEPS.length - 1));
  };

  const handleBack = () => {
    if (step === 0) { onClose?.(); return; }
    setShowErrors(false);
    setStep(s => Math.max(s - 1, 0));
  };

  const handleSubmit = async () => {
    if (!canNext()) { touchStep(step); setShowErrors(true); return; }
    setSubmitting(true);
    setSubmitError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/leistungsseiten`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
      });
      if (res.status === 404) {
        setSubmitError('Backend folgt in Teil 2 — deine Angaben sind lokal gesichert.');
        return;
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const json = await res.json().catch(() => ({}));
      clearDraft(projectId);
      onSave?.(json);
      onClose?.();
    } catch (e) {
      // Netzwerkfehler oder 5xx: Daten bleiben im Draft, freundlicher Hinweis
      setSubmitError(
        e?.message?.includes('Failed to fetch')
          ? 'Backend folgt in Teil 2 — deine Angaben sind lokal gesichert.'
          : (e.message || 'Speichern fehlgeschlagen.')
      );
    } finally {
      setSubmitting(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 0: return <Step1 data={data} set={set} touch={touch} fieldError={fieldError} />;
      case 1: return <Step2 data={data} set={set} touch={touch} fieldError={fieldError} />;
      case 2: return <Step3 data={data} set={set} touch={touch} fieldError={fieldError} />;
      case 3: return <Step4 data={data} set={set} />;
      case 4: return <Step5 data={data} set={set} touch={touch} fieldError={fieldError} />;
      default: return null;
    }
  };

  const panelStyle = isMobile
    ? {
        position: 'fixed', left: 0, right: 0, bottom: 0,
        top: 'auto', transform: 'none',
        width: '100%', maxWidth: '100%', maxHeight: '92vh',
        borderRadius: '20px 20px 0 0',
        animation: 'lswSlideUpMobile 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }
    : {
        position: 'fixed', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '100%', maxWidth: 680, maxHeight: '90vh',
        borderRadius: 20,
        animation: 'lswSlideUp 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      };

  const isLastStep = step === STEPS.length - 1;

  return createPortal(
    <>
      {/* Overlay */}
      <div
        onClick={() => onClose?.()}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0, 0, 0, 0.55)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          zIndex: 2000,
          animation: 'lswFadeIn 0.2s ease',
        }}
      />

      {/* Modal-Box */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          ...panelStyle,
          zIndex: 2001,
          background: 'var(--bg-surface)',
          boxShadow: '0 32px 80px rgba(0,0,0,0.25), 0 8px 24px rgba(0,0,0,0.12)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}
      >
        {isMobile && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0 2px', flexShrink: 0 }}>
            <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2 }} />
          </div>
        )}

        {/* Header */}
        <div style={{
          padding: '20px 28px 16px',
          borderBottom: '1px solid var(--border-light)',
          flexShrink: 0,
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
          gap: 16, background: 'var(--bg-surface)',
        }}>
          <div>
            <div style={{
              fontSize: 11, fontWeight: 600, letterSpacing: '0.08em',
              color: TEAL, textTransform: 'uppercase', marginBottom: 4,
            }}>
              Leistungsseite · Projekt #{projectId}{leadId ? ` · Lead #${leadId}` : ''}
            </div>
            <div style={{
              fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2,
            }}>
              {STEPS[step]}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              flexShrink: 0, width: 32, height: 32, borderRadius: 8,
              border: '1px solid var(--border-light)', background: 'var(--bg-app)',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-secondary)', fontSize: 18, lineHeight: 1,
              transition: 'background 0.15s', fontFamily: 'var(--font-sans)', padding: 0,
            }}
            title="Schließen"
          >
            ×
          </button>
        </div>

        {/* Stepper */}
        <div style={{
          padding: '12px 28px 14px', flexShrink: 0,
          borderBottom: '1px solid var(--border-light)', background: 'var(--bg-surface)',
        }}>
          <div style={{ display: 'flex', gap: 5, marginBottom: 10 }}>
            {STEPS.map((label, i) => (
              <div
                key={i}
                title={label}
                style={{
                  flex: 1, height: 5, borderRadius: 3,
                  background: i <= step ? TEAL : 'var(--border-light)',
                  opacity: i <= step ? 1 : 0.5,
                  transition: 'background 0.3s, opacity 0.3s',
                }}
              />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            {STEPS.map((label, i) => (
              <div key={i} style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                gap: 3, flex: 1, minWidth: 0,
              }}>
                <div style={{
                  width: 22, height: 22, borderRadius: '50%',
                  background: i <= step ? TEAL : 'var(--border-light)',
                  color: i <= step ? '#fff' : 'var(--text-tertiary)',
                  fontSize: 10, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.3s',
                }}>
                  {i < step ? '✓' : i + 1}
                </div>
                <span style={{
                  fontSize: 9,
                  color: i === step ? TEAL : 'var(--text-tertiary)',
                  fontWeight: i === step ? 600 : 400,
                  whiteSpace: 'nowrap', maxWidth: 80,
                  textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis',
                }}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Draft-Banner */}
        {draftBanner && (
          <div style={{
            margin: '10px 24px 0', padding: '8px 14px',
            background: 'var(--status-warning-bg)',
            border: '1px solid var(--status-warning-text)',
            borderRadius: 6, fontSize: 12,
            color: 'var(--status-warning-text)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
          }}>
            <span>Entwurf {draftBanner} wiederhergestellt{existingDraft?.step > 0 ? ` — Schritt ${existingDraft.step + 1}` : ''}</span>
            <button
              onClick={() => {
                clearDraft(projectId);
                setDraftBanner(null);
                setData(DEFAULT_DATA);
                setStep(0);
              }}
              style={{
                background: 'none', border: 'none', fontSize: 11, fontWeight: 600,
                color: 'var(--status-warning-text)', cursor: 'pointer',
                textDecoration: 'underline', padding: 0, fontFamily: 'var(--font-sans)',
              }}
            >Verwerfen</button>
          </div>
        )}

        {/* Scrollbarer Inhalt */}
        <div
          ref={scrollRef}
          style={{
            flex: 1, overflowY: 'auto', padding: '24px 28px',
            background: 'var(--bg-app)',
            scrollbarWidth: 'thin',
            scrollbarColor: 'var(--border-light) transparent',
          }}
        >
          {renderStep()}

          {submitError && (
            <div style={{
              marginTop: 12, padding: '10px 14px',
              background: 'var(--status-warning-bg)',
              border: '1px solid var(--status-warning-text)',
              borderRadius: 8, fontSize: 12,
              color: 'var(--status-warning-text)',
            }}>
              {submitError}
            </div>
          )}
        </div>

        {/* Footer / Navigation */}
        <div style={{
          padding: '16px 28px', borderTop: '1px solid var(--border-light)',
          flexShrink: 0, display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', background: 'var(--bg-surface)',
        }}>
          <button
            onClick={handleBack}
            disabled={submitting}
            style={{
              padding: '10px 20px', borderRadius: 10,
              border: '1px solid var(--border-light)', background: 'var(--bg-app)',
              color: 'var(--text-secondary)', fontSize: 14, fontWeight: 500,
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)', transition: 'all 0.15s',
              opacity: submitting ? 0.6 : 1,
            }}
          >
            {step === 0 ? 'Abbrechen' : '← Zurück'}
          </button>

          <span style={{ fontSize: 13, color: 'var(--text-tertiary)', fontWeight: 500 }}>
            {step + 1} / {STEPS.length}
          </span>

          {isLastStep ? (
            <button
              onClick={handleSubmit}
              disabled={submitting || !canNext()}
              style={{
                padding: '10px 22px', borderRadius: 10, border: 'none',
                background: (canNext() && !submitting) ? TEAL : 'var(--border-medium)',
                color: 'var(--text-inverse)',
                fontSize: 14, fontWeight: 700,
                cursor: (canNext() && !submitting) ? 'pointer' : 'not-allowed',
                fontFamily: 'var(--font-sans)', transition: 'background 0.15s',
                opacity: (canNext() && !submitting) ? 1 : 0.7,
                display: 'inline-flex', alignItems: 'center', gap: 8,
              }}
            >
              {submitting && (
                <span style={{
                  width: 12, height: 12,
                  border: '2px solid rgba(255,255,255,0.4)',
                  borderTopColor: '#fff',
                  borderRadius: '50%',
                  animation: 'lswSpin 0.7s linear infinite',
                  display: 'inline-block',
                }} />
              )}
              {submitting ? 'Speichert…' : 'Leistungsseite generieren →'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              style={{
                padding: '10px 24px', borderRadius: 10, border: 'none',
                background: canNext() ? TEAL : 'var(--border-medium)',
                color: 'var(--text-inverse)',
                fontSize: 14, fontWeight: 700, cursor: 'pointer',
                fontFamily: 'var(--font-sans)', transition: 'background 0.15s',
                opacity: canNext() ? 1 : 0.7,
              }}
            >
              Weiter →
            </button>
          )}
        </div>
      </div>

      {/* CSS Animationen */}
      <style>{`
        @keyframes lswFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes lswSlideUp {
          from { opacity: 0; transform: translate(-50%, calc(-50% + 24px)); }
          to   { opacity: 1; transform: translate(-50%, -50%); }
        }
        @keyframes lswSlideUpMobile {
          from { transform: translateY(100%); }
          to   { transform: translateY(0); }
        }
        @keyframes lswSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </>,
    document.body
  );
}

// ── Inline-Launcher fuer die Einbettung im ProzessFlow ───────────────────────
//
// Der Wizard selbst ist ein Fullscreen-Modal. Fuer die Einbettung in den
// ProzessFlow (StepBody rendert inline) brauchen wir einen kleinen Launcher,
// der den Fragebogen auf Klick oeffnet und die bereits angelegten
// Leistungsseiten als Liste anzeigt.

function parseLeistungsseiten(confirmed) {
  if (!confirmed) return [];
  let obj = confirmed;
  if (typeof confirmed === 'string') {
    try { obj = JSON.parse(confirmed); } catch { return []; }
  }
  const list = obj?.leistungsseiten;
  return Array.isArray(list) ? list : [];
}

export function LeistungsseitenStep({
  projectId,
  leadId,
  token,
  brandData,
  confirmedSteps,
  onSave,
}) {
  const [open, setOpen] = useState(false);
  const [localList, setLocalList] = useState(() => parseLeistungsseiten(confirmedSteps));

  // Wenn der Parent neue confirmedSteps liefert, Liste synchronisieren
  useEffect(() => {
    setLocalList(parseLeistungsseiten(confirmedSteps));
  }, [confirmedSteps]);

  const handleSave = (resp) => {
    // Optimistisches Update — falls der Parent erst spaeter reloaded
    if (resp?.leistung) {
      setLocalList(prev => [...prev, {
        leistung: resp.leistung,
        saved_at: new Date().toISOString(),
      }]);
    }
    onSave?.(resp);
  };

  return (
    <div style={{ padding: '20px 24px' }}>
      <div style={{
        fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 16,
      }}>
        Pro Leistung eine eigene Seite: Zielgruppe, Problem, USP, Beweise und CTA
        in einem 5-Schritte-Fragebogen. Die Antworten fliessen in die
        KI-Generierung der Leistungsseite.
      </div>

      {localList.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: '0.07em',
            color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 8,
          }}>
            Bereits angelegt ({localList.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {localList.map((entry, i) => (
              <div
                key={i}
                style={{
                  padding: '10px 14px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-light)',
                  borderRadius: 8,
                  fontSize: 13,
                  color: 'var(--text-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                }}
              >
                <span style={{ fontWeight: 600 }}>
                  {entry.leistung || `Leistungsseite ${i + 1}`}
                </span>
                {entry.gebiet && (
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {entry.gebiet}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen(true)}
        style={{
          padding: '10px 22px', borderRadius: 10, border: 'none',
          background: TEAL, color: 'var(--text-inverse)',
          fontSize: 14, fontWeight: 700, cursor: 'pointer',
          fontFamily: 'var(--font-sans)', transition: 'opacity 0.15s',
        }}
      >
        {localList.length === 0 ? 'Fragebogen starten →' : '+ Weitere Leistungsseite anlegen'}
      </button>

      {open && (
        <LeistungsseitenWizard
          projectId={projectId}
          leadId={leadId}
          token={token}
          brandData={brandData}
          onClose={() => setOpen(false)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
