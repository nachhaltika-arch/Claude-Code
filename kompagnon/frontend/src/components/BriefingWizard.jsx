import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import API_BASE_URL from '../config';
import WZSearch from './WZSearch';
import { useScreenSize } from '../utils/responsive';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';

const TEAL   = 'var(--brand-primary)';
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

// ── Draft-Persistenz ──────────────────────────────────────────────────────────

const DRAFT_KEY = (leadId) => `briefing_draft_${leadId}`;

function saveDraft(leadId, data, step) {
  try { localStorage.setItem(DRAFT_KEY(leadId), JSON.stringify({ data, step, savedAt: new Date().toISOString() })); } catch { }
}

function loadDraft(leadId) {
  try { const raw = localStorage.getItem(DRAFT_KEY(leadId)); return raw ? JSON.parse(raw) : null; } catch { return null; }
}

function clearDraft(leadId) {
  try { localStorage.removeItem(DRAFT_KEY(leadId)); } catch { }
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

// ── Shared field components ──────────────────────────────────────────────────

function FieldLabel({ children, required, hasError }) {
  return (
    <label style={{
      display: 'block', fontSize: 11, fontWeight: 700,
      color: hasError ? 'var(--status-danger-text)' : 'var(--text-secondary)',
      textTransform: 'uppercase', letterSpacing: '0.07em',
      marginBottom: 6, transition: 'color 0.15s',
    }}>
      {children}{required && <span style={{ color: hasError ? 'var(--status-danger-text)' : TEAL, marginLeft: 2 }}>*</span>}
    </label>
  );
}

function FieldHint({ children }) {
  return (
    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

const inputBase = {
  width: '100%', padding: '10px 12px',
  border: '1.5px solid var(--border-light)', borderRadius: 8,
  fontSize: 14, fontFamily: 'var(--font-sans, system-ui)',
  color: 'var(--text-primary)', background: 'var(--bg-elevated)',
  outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};

function Input({ value, onChange, placeholder, onFocus, onBlur, hasError }) {
  return (
    <input
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{ ...inputBase, borderColor: hasError ? 'var(--status-danger-text)' : undefined, background: hasError ? 'var(--status-danger-bg)' : undefined }}
      onFocus={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL; if (onFocus) onFocus(e); }}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    />
  );
}

function Textarea({ value, onChange, placeholder, rows = 4, onBlur, hasError }) {
  return (
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      style={{ ...inputBase, resize: 'vertical', lineHeight: 1.6, borderColor: hasError ? 'var(--status-danger-text)' : undefined, background: hasError ? 'var(--status-danger-bg)' : undefined }}
      onFocus={e => e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    />
  );
}

function Select({ value, onChange, options, onBlur, hasError }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{ ...inputBase, cursor: 'pointer', appearance: 'none',
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238A9BA8' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center',
        paddingRight: 36,
        borderColor: hasError ? 'var(--status-danger-text)' : undefined,
        background: hasError ? 'var(--status-danger-bg)' : undefined,
      }}
      onFocus={e => e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    >
      <option value="">– bitte wählen –</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function Field({ label, required, hint, error, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <FieldLabel required={required} hasError={!!error}>{label}</FieldLabel>
      {children}
      {error ? (
        <div style={{ fontSize: 11, color: 'var(--status-danger-text)', marginTop: 5, display: 'flex', alignItems: 'center', gap: 4, lineHeight: 1.4 }}>
          <span style={{ fontSize: 12 }}>⚠</span>{error}
        </div>
      ) : hint ? <FieldHint>{hint}</FieldHint> : null}
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
              background: i <= step ? TEAL : 'var(--border-light)',
              transition: 'background 0.3s',
            }}
          />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: TEAL }}>
          Schritt {step + 1} von {STEPS.length}
        </span>
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          {STEPS[step]}
        </span>
      </div>
    </div>
  );
}

// ── Step screens ─────────────────────────────────────────────────────────────

function Step1({ data, set, firstRef, touch, fieldError }) {
  return (
    <div ref={firstRef}>
      <Field label="Gewerk / Branche" required hint="Wählen Sie die Hauptbranche Ihres Betriebs." error={fieldError('gewerk')}>
        <WZSearch
          value={data.wz_code ? { code: data.wz_code, title: data.wz_title } : null}
          onChange={(entry) => {
            set('wz_code', entry?.code || '');
            set('wz_title', entry?.title || '');
            set('gewerk', entry?.title || '');
          }}
          placeholder="Branche suchen, z.B. 'Elektro', 'Sanitär', 'Maler'..."
        />
      </Field>
      <Field label="Leistungen" required hint="Was bieten Sie an? Bitte alle Leistungen auflisten." error={fieldError('leistungen')}>
        <Textarea
          value={data.leistungen}
          onChange={v => set('leistungen', v)}
          onBlur={() => touch('leistungen')}
          hasError={!!fieldError('leistungen')}
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
    </div>
  );
}

function Step2({ data, set, firstRef, touch, fieldError }) {
  return (
    <div ref={firstRef}>
      <Field label="Zielgruppe" required hint="Wen sprechen Sie mit Ihrer Website hauptsächlich an?" error={fieldError('zielgruppe')}>
        <Select value={data.zielgruppe} onChange={v => set('zielgruppe', v)} onBlur={() => touch('zielgruppe')} hasError={!!fieldError('zielgruppe')} options={ZIELGRUPPE_OPTIONS} />
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
    </div>
  );
}

function Step3({ data, set, firstRef, touch, fieldError }) {
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const loadSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/website-templates/suggestions?gewerk=${encodeURIComponent(data.gewerk || '')}`,
        { headers: { Authorization: `Bearer ${localStorage.getItem('kompagnon_token') || localStorage.getItem('token') || ''}` } }
      );
      if (res.ok) {
        const d = await res.json();
        const list = d.suggestions || [];
        if (list[0]) set('inspiration_url_1', list[0]);
        if (list[1]) set('inspiration_url_2', list[1]);
        if (list[2]) set('inspiration_url_3', list[2]);
      }
    } catch (e) { /* ignore */ }
    setLoadingSuggestions(false);
  };

  const noneSet = !data.inspiration_url_1 && !data.inspiration_url_2 && !data.inspiration_url_3;

  return (
    <div ref={firstRef}>
      <Field label="Alleinstellungsmerkmal (USP)" required hint="Was macht Ihren Betrieb besonders? Warum sollte ein Kunde Sie wählen und nicht den Mitbewerb?" error={fieldError('usp')}>
        <Textarea
          value={data.usp}
          onChange={v => set('usp', v)}
          onBlur={() => touch('usp')}
          hasError={!!fieldError('usp')}
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
      <Field label="Inspirations-Website 1" hint="Welche Websites gefallen Ihnen?">
        <Input
          value={data.inspiration_url_1}
          onChange={v => set('inspiration_url_1', v)}
          placeholder="https://www.beispiel.de"
        />
      </Field>
      <Field label="Inspirations-Website 2">
        <Input
          value={data.inspiration_url_2}
          onChange={v => set('inspiration_url_2', v)}
          placeholder="https://www.anderes-beispiel.de"
        />
      </Field>
      <Field label="Inspirations-Website 3">
        <Input
          value={data.inspiration_url_3}
          onChange={v => set('inspiration_url_3', v)}
          placeholder="https://www.noch-eine.de"
        />
      </Field>
      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8, lineHeight: 1.6 }}>
        Keine Idee? Kein Problem — wir machen Vorschläge passend zu Ihrer Branche.
      </div>
      {noneSet && (
        <button
          type="button"
          onClick={loadSuggestions}
          disabled={loadingSuggestions}
          style={{
            marginTop: 10, padding: '9px 18px',
            background: 'var(--bg-app)', color: 'var(--brand-primary)',
            border: '1px solid var(--brand-primary)', borderRadius: 'var(--radius-md)',
            fontSize: 12, fontWeight: 600, cursor: loadingSuggestions ? 'wait' : 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {loadingSuggestions ? 'Lädt…' : 'Branchenpassende Vorschläge laden'}
        </button>
      )}
    </div>
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
            border: `1.5px solid ${value === opt ? 'var(--brand-primary)' : 'var(--border-light)'}`,
            background: value === opt ? 'var(--brand-primary)' : 'var(--bg-surface)',
            color: value === opt ? 'var(--text-inverse)' : 'var(--text-secondary)',
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
              border: `1.5px solid ${active ? 'var(--brand-primary)' : 'var(--border-light)'}`,
              background: active ? 'var(--brand-primary-light)' : 'var(--bg-elevated)',
              color: active ? 'var(--brand-primary)' : 'var(--text-secondary)',
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

function Step4({ data, set, firstRef, touch, fieldError }) {
  return (
    <div ref={firstRef}>
      <Field label="Farbwünsche" hint="Welche Farben passen zu Ihrer Marke oder sollen verwendet werden?">
        <Input
          value={data.farben}
          onChange={v => set('farben', v)}
          placeholder="z.B. Blau & Weiß, Grün-Töne, keine Vorgabe …"
        />
      </Field>
      <Field label="Stil" required hint="Welcher Designstil soll Ihre Website prägen?" error={fieldError('stil')}>
        <Select value={data.stil} onChange={v => set('stil', v)} onBlur={() => touch('stil')} hasError={!!fieldError('stil')} options={STIL_OPTIONS} />
      </Field>
      <Field label="Vorbilder / Inspiration" hint="Gibt es Websites, die Ihnen gefallen? URL(s) eintragen.">
        <Input
          value={data.vorbilder}
          onChange={v => set('vorbilder', v)}
          placeholder="z.B. https://www.beispiel.de, https://andereseite.de"
        />
      </Field>
    </div>
  );
}

function Step5({ data, set, firstRef }) {
  return (
    <div ref={firstRef}>
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
    </div>
  );
}

function SummaryRow({ label, value }) {
  if (!value && value !== false) return null;
  const display = typeof value === 'boolean' ? (value ? 'Ja' : 'Nein')
    : Array.isArray(value) ? (value.length ? value.join(', ') : '–')
    : (value || '–');
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
      <div style={{ width: 160, flexShrink: 0, fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', paddingTop: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5, flex: 1 }}>{display}</div>
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
      <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
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
        <div style={{ background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-border)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--status-danger-text)', marginTop: 8 }}>
          {error}
        </div>
      )}
      <button
        onClick={onSaveAndPdf}
        disabled={saving}
        style={{
          width: '100%', marginTop: 12, padding: '13px 0', borderRadius: 10,
          border: 'none', background: saving ? 'var(--border-light)' : TEAL,
          color: saving ? 'var(--text-tertiary)' : 'var(--text-inverse)', fontSize: 15, fontWeight: 700,
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
  const existingDraft = loadDraft(leadId);

  const [step, setStep] = useState(existingDraft?.step ?? 0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [draftBanner, setDraftBanner] = useState(existingDraft ? formatDraftAge(existingDraft.savedAt) : null);
  const firstFieldRef = useRef(null);

  // Esc schließt den Wizard
  useEscapeKey(onClose, true);

  // Auto-Focus auf erstes Feld bei Schritt-Wechsel
  useEffect(() => {
    const t = setTimeout(() => {
      if (firstFieldRef.current) {
        const el = firstFieldRef.current.querySelector('input,textarea,select');
        el?.focus();
      }
    }, 120);
    return () => clearTimeout(t);
  }, [step]);

  // Draft-Banner nach 5 Sekunden ausblenden
  useEffect(() => {
    if (!draftBanner) return;
    const t = setTimeout(() => setDraftBanner(null), 5000);
    return () => clearTimeout(t);
  }, [draftBanner]);

  const defaultData = {
    gewerk:            leadData?.gewerk            || '',
    wz_code:           leadData?.wz_code           || '',
    wz_title:          leadData?.wz_title          || '',
    leistungen:        leadData?.leistungen        || '',
    einzugsgebiet:     leadData?.einzugsgebiet     || '',
    zielgruppe:        leadData?.zielgruppe        || '',
    typischerKunde:    leadData?.typischerKunde    || '',
    haeufigeAnfrage:   leadData?.haeufigeAnfrage   || '',
    usp:               leadData?.usp               || '',
    mitbewerber:       leadData?.mitbewerber       || '',
    vorbilder:         leadData?.vorbilder         || '',
    inspiration_url_1: leadData?.inspiration_url_1 || '',
    inspiration_url_2: leadData?.inspiration_url_2 || '',
    inspiration_url_3: leadData?.inspiration_url_3 || '',
    farben:            leadData?.farben            || '',
    stil:              leadData?.stil              || '',
    wunschseiten:      leadData?.wunschseiten
      ? (Array.isArray(leadData.wunschseiten)
          ? leadData.wunschseiten
          : leadData.wunschseiten.split(', ').filter(Boolean))
      : [],
    logo_vorhanden:    leadData?.logo_vorhanden    ?? false,
    fotos_vorhanden:   leadData?.fotos_vorhanden   ?? false,
    sonstige_hinweise: leadData?.sonstige_hinweise || '',
  };

  const [data, setData] = useState(() => existingDraft?.data || defaultData);

  const set = (key, val) => setData(d => ({ ...d, [key]: val }));

  // Auto-Save Draft bei jeder Änderung
  useEffect(() => { saveDraft(leadId, data, step); }, [data, step, leadId]);

  const [touched, setTouched] = useState({});
  const touch = (field) => setTouched(prev => ({ ...prev, [field]: true }));
  const touchStep = (stepIndex) => {
    const fields = { 0: ['gewerk', 'leistungen'], 1: ['zielgruppe'], 2: ['usp'], 3: ['stil'], 4: [] };
    const toTouch = {};
    (fields[stepIndex] || []).forEach(f => { toTouch[f] = true; });
    setTouched(prev => ({ ...prev, ...toTouch }));
  };
  const fieldError = (field) => {
    if (!touched[field]) return null;
    const msgs = { gewerk: 'Bitte Branche auswählen', leistungen: 'Bitte Leistungen eintragen', zielgruppe: 'Bitte Zielgruppe auswählen', usp: 'Bitte USP eintragen', stil: 'Bitte Designstil auswählen' };
    const empty = { gewerk: !data.gewerk && !data.wz_code, leistungen: !data.leistungen?.trim(), zielgruppe: !data.zielgruppe, usp: !data.usp?.trim(), stil: !data.stil };
    return empty[field] ? (msgs[field] || 'Pflichtfeld') : null;
  };

  const canNext = () => {
    if (step === 0) return !!(data.gewerk || data.wz_code) && !!data.leistungen.trim();
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
        wz_code:           data.wz_code,
        wz_title:          data.wz_title,
        leistungen:        data.leistungen,
        einzugsgebiet:     data.einzugsgebiet,
        usp:               data.usp,
        mitbewerber:       data.mitbewerber,
        vorbilder:         data.vorbilder,
        inspiration_url_1: data.inspiration_url_1,
        inspiration_url_2: data.inspiration_url_2,
        inspiration_url_3: data.inspiration_url_3,
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
      // Additionally persist inspiration URLs on the lead itself
      try {
        await fetch(`${API_BASE_URL}/api/leads/${leadId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            inspiration_url_1: data.inspiration_url_1 || null,
            inspiration_url_2: data.inspiration_url_2 || null,
            inspiration_url_3: data.inspiration_url_3 || null,
          }),
        });
      } catch (_) { /* non-fatal */ }
      // Open PDF in new tab
      clearDraft(leadId);
      window.open(`${API_BASE_URL}/api/briefings/${leadId}/pdf`, '_blank');
      if (onComplete) onComplete(data);
    } catch (e) {
      setSaveError(e.message || 'Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  };

  const handleNext = () => {
    if (!canNext()) { touchStep(step); return; }
    if (step < STEPS.length - 1) setStep(s => s + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep(s => s - 1);
    else if (onClose) onClose();
  };

  const renderStep = () => {
    const p = { data, set, touch, fieldError, firstRef: firstFieldRef };
    switch (step) {
      case 0: return <Step1 {...p} />;
      case 1: return <Step2 {...p} />;
      case 2: return <Step3 {...p} />;
      case 3: return <Step4 {...p} />;
      case 4: return <Step5 {...p} />;
      case 5: return <Step6 data={data} saving={saving} error={saveError} onSaveAndPdf={handleSaveAndPdf} />;
      default: return null;
    }
  };

  const panelStyle = isMobile
    ? {
        position: 'fixed', left: 0, right: 0, bottom: 0,
        top: 'auto', transform: 'none',
        width: '100%', maxWidth: '100%', maxHeight: '92vh',
        borderRadius: '20px 20px 0 0',
        animation: 'bwSlideUpMobile 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      }
    : {
        position: 'fixed', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '100%', maxWidth: 680, maxHeight: '90vh',
        borderRadius: 20,
        animation: 'bwSlideUp 0.28s cubic-bezier(0.34, 1.56, 0.64, 1)',
      };

  return createPortal(
    <>
      {/* ── Overlay ── */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.55)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
          zIndex: 2000,
          animation: 'bwFadeIn 0.2s ease',
        }}
      />

      {/* ── Modal-Box ── */}
      <div
        onClick={e => e.stopPropagation()}
        style={{
          ...panelStyle,
          zIndex: 2001,
          background: 'var(--bg-surface)',
          boxShadow: '0 32px 80px rgba(0,0,0,0.25), 0 8px 24px rgba(0,0,0,0.12)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* ── Header ── */}
        <div style={{
          padding: '20px 28px 16px',
          borderBottom: '1px solid var(--border-light)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 16,
          background: 'var(--bg-surface)',
        }}>
          <div>
            <div style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.08em',
              color: TEAL,
              textTransform: 'uppercase',
              marginBottom: 4,
            }}>
              Website-Briefing · Lead #{leadId}
            </div>
            <div style={{
              fontSize: 20,
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.2,
            }}>
              {STEPS[step]}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              flexShrink: 0,
              width: 32, height: 32,
              borderRadius: 8,
              border: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-secondary)',
              fontSize: 18, lineHeight: 1,
              transition: 'background 0.15s',
              fontFamily: 'var(--font-sans)',
              padding: 0,
            }}
            title="Schließen"
          >
            ×
          </button>
        </div>

        {/* ── Stepper / Progress ── */}
        <div style={{
          padding: '12px 28px 14px',
          flexShrink: 0,
          borderBottom: '1px solid var(--border-light)',
          background: 'var(--bg-surface)',
        }}>
          <div style={{ display: 'flex', gap: 5, marginBottom: 10 }}>
            {STEPS.map((label, i) => (
              <div
                key={i}
                title={label}
                style={{
                  flex: 1,
                  height: 5,
                  borderRadius: 3,
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
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                flex: 1,
                minWidth: 0,
              }}>
                <div style={{
                  width: 22, height: 22,
                  borderRadius: '50%',
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
                  whiteSpace: 'nowrap',
                  maxWidth: 70,
                  textAlign: 'center',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
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
            background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-text)',
            borderRadius: 'var(--radius-md, 6px)', fontSize: 12,
            color: 'var(--status-warning-text)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
          }}>
            <span>Entwurf {draftBanner} wiederhergestellt{existingDraft?.step > 0 ? ` — Schritt ${existingDraft.step + 1}` : ''}</span>
            <button
              onClick={() => { clearDraft(leadId); setDraftBanner(null); setData(defaultData); setStep(0); }}
              style={{ background: 'none', border: 'none', fontSize: 11, fontWeight: 600, color: 'var(--status-warning-text)', cursor: 'pointer', textDecoration: 'underline', padding: 0, fontFamily: 'var(--font-sans)' }}
            >Verwerfen</button>
          </div>
        )}

        {/* ── Scrollbarer Formular-Bereich ── */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px 28px',
          background: 'var(--bg-app)',
          scrollbarWidth: 'thin',
          scrollbarColor: 'var(--border-light) transparent',
        }}>
          {renderStep()}
        </div>

        {/* ── Footer / Navigation ── */}
        <div style={{
          padding: '16px 28px',
          borderTop: '1px solid var(--border-light)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-surface)',
        }}>
          <button
            onClick={handleBack}
            style={{
              padding: '10px 20px',
              borderRadius: 10,
              border: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
              color: 'var(--text-secondary)',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              transition: 'all 0.15s',
            }}
          >
            {step === 0 ? 'Abbrechen' : '← Zurück'}
          </button>

          <span style={{
            fontSize: 13,
            color: 'var(--text-tertiary)',
            fontWeight: 500,
          }}>
            {step + 1} / {STEPS.length}
          </span>

          {step < STEPS.length - 1 ? (
            <button
              onClick={handleNext}
              style={{
                padding: '10px 24px',
                borderRadius: 10,
                border: 'none',
                background: canNext() ? TEAL : 'var(--border-medium)',
                color: 'var(--text-inverse)',
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
                transition: 'background var(--transition-fast)',
                opacity: canNext() ? 1 : 0.7,
              }}
            >
              Weiter →
            </button>
          ) : (
            <div style={{ width: 120 }} />
          )}
        </div>
      </div>

      {/* ── CSS Animationen ── */}
      <style>{`
        @keyframes bwFadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes bwSlideUp {
          from { opacity: 0; transform: translate(-50%, calc(-50% + 24px)); }
          to   { opacity: 1; transform: translate(-50%, -50%); }
        }
        @keyframes bwSlideUpMobile {
          from { transform: translateY(100%); }
          to   { transform: translateY(0); }
        }
      `}</style>
    </>,
    document.body
  );
}
