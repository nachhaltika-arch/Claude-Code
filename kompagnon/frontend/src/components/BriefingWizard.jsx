import { useState } from 'react';

const TEAL   = '#008EAA';
const STEPS  = [
  'Betrieb & Leistungen',
  'Zielgruppe & Kunden',
  'Alleinstellung & Mitbewerb',
  'Design & Wünsche',
  'Seiten & Assets',
  'Zusammenfassung',
];

const GEWERK_OPTIONS = [
  'Sanitär', 'Heizung', 'Elektro', 'Maler', 'Schreiner',
  'Dachdecker', 'Fliesenleger', 'Zimmerer', 'Kfz', 'Sonstige',
];
const ZIELGRUPPE_OPTIONS = ['Privatkunden', 'Gewerbekunden', 'Beides'];

// ── Shared field components ──────────────────────────────────────────────────

function FieldLabel({ children, required }) {
  return (
    <label style={{
      display: 'block', fontSize: 11, fontWeight: 700,
      color: '#5A7080', textTransform: 'uppercase', letterSpacing: '0.07em',
      marginBottom: 6,
    }}>
      {children}{required && <span style={{ color: TEAL, marginLeft: 2 }}>*</span>}
    </label>
  );
}

function FieldHint({ children }) {
  return (
    <div style={{ fontSize: 11, color: '#8A9BA8', marginTop: 4, lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

const inputBase = {
  width: '100%', padding: '10px 12px',
  border: '1.5px solid #DDE4E8', borderRadius: 8,
  fontSize: 14, fontFamily: 'var(--font-sans, system-ui)',
  color: '#1A2C32', background: '#FAFCFD',
  outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};

function Input({ value, onChange, placeholder, onFocus, onBlur }) {
  return (
    <input
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={inputBase}
      onFocus={e => { e.target.style.borderColor = TEAL; if (onFocus) onFocus(e); }}
      onBlur={e => { e.target.style.borderColor = '#DDE4E8'; if (onBlur) onBlur(e); }}
    />
  );
}

function Textarea({ value, onChange, placeholder, rows = 4 }) {
  return (
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      style={{ ...inputBase, resize: 'vertical', lineHeight: 1.6 }}
      onFocus={e => e.target.style.borderColor = TEAL}
      onBlur={e => e.target.style.borderColor = '#DDE4E8'}
    />
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{ ...inputBase, cursor: 'pointer', appearance: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238A9BA8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center',
        paddingRight: 36,
      }}
      onFocus={e => e.target.style.borderColor = TEAL}
      onBlur={e => e.target.style.borderColor = '#DDE4E8'}
    >
      <option value="">– bitte wählen –</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function Field({ label, required, hint, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <FieldLabel required={required}>{label}</FieldLabel>
      {children}
      {hint && <FieldHint>{hint}</FieldHint>}
    </div>
  );
}

// ── Progress bar ─────────────────────────────────────────────────────────────

function ProgressBar({ step }) {
  return (
    <div style={{ padding: '16px 24px 0' }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
        {STEPS.map((label, i) => (
          <div
            key={i}
            title={label}
            style={{
              flex: 1, height: 4, borderRadius: 2,
              background: i <= step ? TEAL : '#DDE4E8',
              transition: 'background 0.3s',
            }}
          />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: TEAL }}>
          Schritt {step + 1} von {STEPS.length}
        </span>
        <span style={{ fontSize: 12, color: '#8A9BA8' }}>
          {STEPS[step]}
        </span>
      </div>
    </div>
  );
}

// ── Step screens ─────────────────────────────────────────────────────────────

function Step1({ data, set }) {
  return (
    <>
      <Field label="Gewerk / Branche" required hint="Wählen Sie die Hauptbranche Ihres Betriebs.">
        <Select value={data.gewerk} onChange={v => set('gewerk', v)} options={GEWERK_OPTIONS} />
      </Field>
      <Field label="Leistungen" required hint="Was bieten Sie an? Bitte alle Leistungen auflisten.">
        <Textarea
          value={data.leistungen}
          onChange={v => set('leistungen', v)}
          placeholder={"z.B. Badsanierung, Rohrbruch-Notdienst, Heizungsinstallation …"}
          rows={5}
        />
      </Field>
      <Field label="Einzugsgebiet" hint="In welcher Region arbeiten Sie?">
        <Input
          value={data.einzugsgebiet}
          onChange={v => set('einzugsgebiet', v)}
          placeholder="z.B. Koblenz und Umgebung, ca. 40 km Radius"
        />
      </Field>
    </>
  );
}

function Step2({ data, set }) {
  return (
    <>
      <Field label="Zielgruppe" required hint="Wen sprechen Sie mit Ihrer Website hauptsächlich an?">
        <Select value={data.zielgruppe} onChange={v => set('zielgruppe', v)} options={ZIELGRUPPE_OPTIONS} />
      </Field>
      <Field label="Typischer Kunde" hint="Beschreiben Sie Ihren idealen Kunden.">
        <Textarea
          value={data.typischerKunde}
          onChange={v => set('typischerKunde', v)}
          placeholder={"z.B. Eigenheimbesitzer, 40–60 Jahre, plant Badsanierung im nächsten Jahr …"}
          rows={4}
        />
      </Field>
      <Field label="Häufigste Anfrage" hint="Was fragen Kunden am häufigsten an?">
        <Input
          value={data.haeufigeAnfrage}
          onChange={v => set('haeufigeAnfrage', v)}
          placeholder="z.B. Kostenanfrage Heizungstausch, Notdienst Rohrbruch …"
        />
      </Field>
    </>
  );
}

function Step3({ data, set }) {
  return (
    <>
      <Field label="Alleinstellungsmerkmal (USP)" required hint="Was macht Ihren Betrieb besonders? Warum sollte ein Kunde Sie wählen und nicht den Mitbewerb?">
        <Textarea
          value={data.usp}
          onChange={v => set('usp', v)}
          placeholder={"z.B. 25 Jahre Erfahrung, 24h-Notdienst, Festpreisgarantie, familiengeführt …"}
          rows={5}
        />
      </Field>
      <Field label="Mitbewerber" hint="Nennen Sie 2–3 Mitbewerber in Ihrer Region.">
        <Input
          value={data.mitbewerber}
          onChange={v => set('mitbewerber', v)}
          placeholder="z.B. Firma Müller, Installateure Schmidt GmbH …"
        />
      </Field>
      <Field label="Vorbilder / Inspiration" hint="Gibt es Websites, die Ihnen gefallen? URL(s) eintragen.">
        <Input
          value={data.vorbilder}
          onChange={v => set('vorbilder', v)}
          placeholder="z.B. https://www.beispiel.de, https://andereseite.de"
        />
      </Field>
    </>
  );
}

// Placeholder steps (4–6 to be implemented)
function StepPlaceholder({ step }) {
  return (
    <div style={{ textAlign: 'center', padding: '40px 0', color: '#8A9BA8' }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>🚧</div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>{STEPS[step]}</div>
      <div style={{ fontSize: 12, marginTop: 6 }}>Wird in Teil 4 implementiert</div>
    </div>
  );
}

// ── Wizard ───────────────────────────────────────────────────────────────────

export default function BriefingWizard({ leadId, leadData, onClose, onComplete }) {
  const [step, setStep] = useState(0);

  const [data, setData] = useState({
    // Step 1
    gewerk:          leadData?.gewerk          || '',
    leistungen:      leadData?.leistungen      || '',
    einzugsgebiet:   leadData?.einzugsgebiet   || '',
    // Step 2
    zielgruppe:      leadData?.zielgruppe      || '',
    typischerKunde:  leadData?.typischerKunde  || '',
    haeufigeAnfrage: leadData?.haeufigeAnfrage || '',
    // Step 3
    usp:             leadData?.usp             || '',
    mitbewerber:     leadData?.mitbewerber     || '',
    vorbilder:       leadData?.vorbilder       || '',
  });

  const set = (key, val) => setData(d => ({ ...d, [key]: val }));

  const canNext = () => {
    if (step === 0) return !!data.gewerk && !!data.leistungen.trim();
    if (step === 1) return !!data.zielgruppe;
    if (step === 2) return !!data.usp.trim();
    return true;
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
    else if (onComplete) onComplete(data);
  };

  const handleBack = () => {
    if (step > 0) setStep(s => s - 1);
    else if (onClose) onClose();
  };

  const renderStep = () => {
    switch (step) {
      case 0: return <Step1 data={data} set={set} />;
      case 1: return <Step2 data={data} set={set} />;
      case 2: return <Step3 data={data} set={set} />;
      default: return <StepPlaceholder step={step} />;
    }
  };

  return (
    /* Overlay */
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '16px',
    }} onClick={e => e.target === e.currentTarget && onClose?.()}>

      {/* Panel */}
      <div style={{
        background: '#fff', borderRadius: 16,
        width: '100%', maxWidth: 700,
        maxHeight: '92vh',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 24px 80px rgba(0,0,0,0.25)',
        overflow: 'hidden',
      }}>

        {/* Header */}
        <div style={{
          borderBottom: '1px solid #EEF2F4',
          paddingBottom: 16,
          flexShrink: 0,
        }}>
          <div style={{
            display: 'flex', alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px 12px',
          }}>
            <div>
              <div style={{ fontSize: 11, color: '#8A9BA8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>
                Website-Briefing
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#1A2C32' }}>
                {leadData?.company_name || `Lead #${leadId}`}
              </div>
            </div>
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#8A9BA8', lineHeight: 1, padding: 4 }}
            >
              ×
            </button>
          </div>
          <ProgressBar step={step} />
        </div>

        {/* Body — scrollable */}
        <div style={{
          flex: 1, overflowY: 'auto',
          padding: '24px 24px 8px',
        }}>
          <div style={{
            fontSize: 18, fontWeight: 700, color: '#1A2C32',
            marginBottom: 20,
          }}>
            {STEPS[step]}
          </div>
          {renderStep()}
        </div>

        {/* Footer */}
        <div style={{
          borderTop: '1px solid #EEF2F4',
          padding: '16px 24px',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          background: '#FAFCFD',
        }}>
          <button
            onClick={handleBack}
            style={{
              padding: '10px 20px', borderRadius: 8,
              border: '1.5px solid #DDE4E8',
              background: '#fff', color: '#5A7080',
              fontSize: 14, fontWeight: 500,
              cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)',
            }}
          >
            {step === 0 ? 'Abbrechen' : '← Zurück'}
          </button>

          <div style={{ fontSize: 12, color: '#8A9BA8' }}>
            {step + 1} / {STEPS.length}
          </div>

          <button
            onClick={handleNext}
            disabled={!canNext()}
            style={{
              padding: '10px 24px', borderRadius: 8,
              border: 'none',
              background: canNext() ? TEAL : '#DDE4E8',
              color: canNext() ? '#fff' : '#8A9BA8',
              fontSize: 14, fontWeight: 600,
              cursor: canNext() ? 'pointer' : 'not-allowed',
              fontFamily: 'var(--font-sans, system-ui)',
              transition: 'background 0.15s',
            }}
          >
            {step === STEPS.length - 1 ? 'Fertigstellen ✓' : 'Weiter →'}
          </button>
        </div>
      </div>
    </div>
  );
}
