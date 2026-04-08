import { useState } from 'react';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';
import WZSearch from './WZSearch';

const TEAL   = '#008EAA';
const STEPS  = [
  'Betrieb & Leistungen',
  'Zielgruppe & Kunden',
  'Alleinstellung & Mitbewerb',
  'Design & Stil',
  'Seiten & Assets',
  'Zusammenfassung',
];

const GEWERK_OPTIONS = [
  'Sanitär', 'Heizung', 'Elektro', 'Maler', 'Schreiner',
  'Dachdecker', 'Fliesenleger', 'Zimmerer', 'Kfz', 'Sonstige',
];
const ZIELGRUPPE_OPTIONS = ['Privatkunden', 'Gewerbekunden', 'Beides'];
const STIL_OPTIONS = [
  'Modern & Minimalistisch',
  'Klassisch & Seriös',
  'Frisch & Freundlich',
  'Industriell & Technisch',
  'Kein Vorzug',
];
const SEITEN_OPTIONS = [
  'Startseite', 'Über uns', 'Leistungen', 'Referenzen',
  'Kontakt', 'Blog / News', 'Stellenangebote', 'FAQ',
];

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
      <Field label="Gewerk / Branche" required hint="Tippen Sie den Anfang Ihres Gewerks ein und waehlen Sie aus der Liste.">
        <WZSearch value={data.gewerk} onChange={v => set('gewerk', v)} placeholder="Gewerk suchen, z.B. Sanitaer, Elektriker..." />
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

function Toggle({ value, onChange, labelOn = 'Ja', labelOff = 'Nein' }) {
  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {[true, false].map(opt => (
        <button
          key={String(opt)}
          type="button"
          onClick={() => onChange(opt)}
          style={{
            padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
            border: `1.5px solid ${value === opt ? TEAL : '#DDE4E8'}`,
            background: value === opt ? TEAL : '#fff',
            color: value === opt ? '#fff' : '#5A7080',
            cursor: 'pointer', transition: 'all 0.15s',
            fontFamily: 'var(--font-sans, system-ui)',
          }}
        >
          {opt ? labelOn : labelOff}
        </button>
      ))}
    </div>
  );
}

function SeitenCheckbox({ selected, onChange }) {
  const toggle = (page) => {
    if (selected.includes(page)) onChange(selected.filter(p => p !== page));
    else onChange([...selected, page]);
  };
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {SEITEN_OPTIONS.map(page => {
        const active = selected.includes(page);
        return (
          <button
            key={page}
            type="button"
            onClick={() => toggle(page)}
            style={{
              padding: '7px 14px', borderRadius: 8, fontSize: 13,
              border: `1.5px solid ${active ? TEAL : '#DDE4E8'}`,
              background: active ? '#E6F5F8' : '#FAFCFD',
              color: active ? TEAL : '#5A7080',
              fontWeight: active ? 700 : 400,
              cursor: 'pointer', transition: 'all 0.15s',
              fontFamily: 'var(--font-sans, system-ui)',
            }}
          >
            {active ? '✓ ' : ''}{page}
          </button>
        );
      })}
    </div>
  );
}

function Step4({ data, set }) {
  return (
    <>
      <Field label="Farbwünsche" hint="Welche Farben passen zu Ihrer Marke oder sollen verwendet werden?">
        <Input
          value={data.farben}
          onChange={v => set('farben', v)}
          placeholder="z.B. Blau & Weiß, Grün-Töne, keine Vorgabe …"
        />
      </Field>
      <Field label="Stil" required hint="Welcher Designstil soll Ihre Website prägen?">
        <Select value={data.stil} onChange={v => set('stil', v)} options={STIL_OPTIONS} />
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

function Step5({ data, set }) {
  return (
    <>
      <Field label="Gewünschte Seiten" hint="Welche Seiten soll Ihre neue Website enthalten?">
        <SeitenCheckbox
          selected={data.wunschseiten}
          onChange={v => set('wunschseiten', v)}
        />
      </Field>
      <Field label="Logo vorhanden?" hint="Haben Sie bereits ein Logo, das wir verwenden können?">
        <Toggle value={data.logo_vorhanden} onChange={v => set('logo_vorhanden', v)} />
      </Field>
      <Field label="Fotos / Bilder vorhanden?" hint="Haben Sie Fotos Ihres Betriebs, Teams oder Ihrer Arbeit?">
        <Toggle value={data.fotos_vorhanden} onChange={v => set('fotos_vorhanden', v)} />
      </Field>
      <Field label="Sonstige Hinweise" hint="Gibt es weitere Wünsche, Anforderungen oder wichtige Informationen?">
        <Textarea
          value={data.sonstige_hinweise}
          onChange={v => set('sonstige_hinweise', v)}
          placeholder="Weitere Hinweise, besondere Anforderungen …"
          rows={4}
        />
      </Field>
    </>
  );
}

function SummaryRow({ label, value }) {
  if (!value && value !== false) return null;
  const display = typeof value === 'boolean' ? (value ? 'Ja' : 'Nein')
    : Array.isArray(value) ? (value.length ? value.join(', ') : '–')
    : (value || '–');
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
      <div style={{ width: 160, flexShrink: 0, fontSize: 12, fontWeight: 700, color: '#5A7080', textTransform: 'uppercase', letterSpacing: '0.06em', paddingTop: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color: '#1A2C32', lineHeight: 1.5, flex: 1 }}>{display}</div>
    </div>
  );
}

function SummarySection({ title, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{
        background: TEAL, color: '#fff', fontWeight: 700, fontSize: 12,
        padding: '5px 10px', borderRadius: 6, marginBottom: 10,
        letterSpacing: '0.04em',
      }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function Step6({ data, saving, error, onSaveAndPdf }) {
  return (
    <>
      <div style={{ marginBottom: 16, fontSize: 13, color: '#5A7080' }}>
        Bitte prüfen Sie alle Angaben. Mit „Speichern & PDF" wird das Briefing gespeichert und als PDF heruntergeladen.
      </div>
      <SummarySection title="Betrieb & Leistungen">
        <SummaryRow label="Gewerk" value={data.gewerk} />
        <SummaryRow label="Leistungen" value={data.leistungen} />
        <SummaryRow label="Einzugsgebiet" value={data.einzugsgebiet} />
      </SummarySection>
      <SummarySection title="Zielgruppe & Kunden">
        <SummaryRow label="Zielgruppe" value={data.zielgruppe} />
        <SummaryRow label="Typischer Kunde" value={data.typischerKunde} />
        <SummaryRow label="Häufigste Anfrage" value={data.haeufigeAnfrage} />
      </SummarySection>
      <SummarySection title="Alleinstellung & Mitbewerb">
        <SummaryRow label="USP" value={data.usp} />
        <SummaryRow label="Mitbewerber" value={data.mitbewerber} />
      </SummarySection>
      <SummarySection title="Design & Stil">
        <SummaryRow label="Farbwünsche" value={data.farben} />
        <SummaryRow label="Stil" value={data.stil} />
        <SummaryRow label="Vorbilder" value={data.vorbilder} />
      </SummarySection>
      <SummarySection title="Seiten & Assets">
        <SummaryRow label="Gewünschte Seiten" value={data.wunschseiten} />
        <SummaryRow label="Logo vorhanden" value={data.logo_vorhanden} />
        <SummaryRow label="Fotos vorhanden" value={data.fotos_vorhanden} />
        <SummaryRow label="Sonstige Hinweise" value={data.sonstige_hinweise} />
      </SummarySection>
      {error && (
        <div style={{ background: '#FFF0F0', border: '1px solid #FFBDBD', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#C0392B', marginTop: 8 }}>
          {error}
        </div>
      )}
      <button
        onClick={onSaveAndPdf}
        disabled={saving}
        style={{
          width: '100%', marginTop: 12, padding: '13px 0', borderRadius: 10,
          border: 'none', background: saving ? '#DDE4E8' : TEAL,
          color: saving ? '#8A9BA8' : '#fff', fontSize: 15, fontWeight: 700,
          cursor: saving ? 'not-allowed' : 'pointer',
          fontFamily: 'var(--font-sans, system-ui)',
          transition: 'background 0.15s',
        }}
      >
        {saving ? 'Speichern …' : 'Briefing speichern & PDF herunterladen'}
      </button>
    </>
  );
}

// ── Wizard ───────────────────────────────────────────────────────────────────

export default function BriefingWizard({ leadId, leadData, onClose, onComplete }) {
  const { isMobile } = useScreenSize();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  const [data, setData] = useState({
    // Step 1
    gewerk:            leadData?.gewerk            || '',
    leistungen:        leadData?.leistungen        || '',
    einzugsgebiet:     leadData?.einzugsgebiet     || '',
    // Step 2
    zielgruppe:        leadData?.zielgruppe        || '',
    typischerKunde:    leadData?.typischerKunde    || '',
    haeufigeAnfrage:   leadData?.haeufigeAnfrage   || '',
    // Step 3
    usp:               leadData?.usp               || '',
    mitbewerber:       leadData?.mitbewerber       || '',
    vorbilder:         leadData?.vorbilder         || '',
    // Step 4
    farben:            leadData?.farben            || '',
    stil:              leadData?.stil              || '',
    // Step 5
    wunschseiten:      leadData?.wunschseiten
      ? (Array.isArray(leadData.wunschseiten)
          ? leadData.wunschseiten
          : leadData.wunschseiten.split(', ').filter(Boolean))
      : [],
    logo_vorhanden:    leadData?.logo_vorhanden    ?? false,
    fotos_vorhanden:   leadData?.fotos_vorhanden   ?? false,
    sonstige_hinweise: leadData?.sonstige_hinweise || '',
  });

  const set = (key, val) => setData(d => ({ ...d, [key]: val }));

  const canNext = () => {
    if (step === 0) return !!data.gewerk && !!data.leistungen.trim();
    if (step === 1) return !!data.zielgruppe;
    if (step === 2) return !!data.usp.trim();
    if (step === 3) return !!data.stil;
    if (step === 4) return data.wunschseiten.length > 0;
    return true;
  };

  const handleSaveAndPdf = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const token = localStorage.getItem('kompagnon_token');
      const payload = {
        gewerk:            data.gewerk,
        leistungen:        data.leistungen,
        einzugsgebiet:     data.einzugsgebiet,
        usp:               data.usp,
        mitbewerber:       data.mitbewerber,
        vorbilder:         data.vorbilder,
        farben:            data.farben,
        stil:              data.stil,
        wunschseiten:      data.wunschseiten.join(', '),
        logo_vorhanden:    data.logo_vorhanden,
        fotos_vorhanden:   data.fotos_vorhanden,
        sonstige_hinweise: data.sonstige_hinweise,
      };
      const res = await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      // Open PDF in new tab
      window.open(`${API_BASE_URL}/api/briefings/${leadId}/pdf`, '_blank');
      if (onComplete) onComplete(data);
    } catch (e) {
      setSaveError(e.message || 'Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
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
      case 3: return <Step4 data={data} set={set} />;
      case 4: return <Step5 data={data} set={set} />;
      case 5: return <Step6 data={data} saving={saving} error={saveError} onSaveAndPdf={handleSaveAndPdf} />;
      default: return null;
    }
  };

  return (
    /* Overlay */
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center',
      padding: isMobile ? 0 : '16px',
    }} onClick={e => e.target === e.currentTarget && onClose?.()}>

      {/* Panel */}
      <div style={{
        background: '#fff', borderRadius: isMobile ? '16px 16px 0 0' : 16,
        width: '100%', maxWidth: 700,
        maxHeight: isMobile ? '94vh' : '92vh',
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

          {step < STEPS.length - 1 && (
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
              Weiter →
            </button>
          )}
          {step === STEPS.length - 1 && (
            <div style={{ width: 120 }} />
          )}
        </div>
      </div>
    </div>
  );
}
