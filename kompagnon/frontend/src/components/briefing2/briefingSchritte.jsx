/**
 * Die sechs Schritte des Briefing-Assistenten samt Feldern und Entwurf (L-25).
 *
 * Am 2026-08-30 aus `BriefingWizard.jsx` herausgeloest — 519 der damals 1.261
 * Zeilen. Schritte, Feldbausteine, Auswahllisten und die drei Funktionen fuer
 * den lokalen Entwurf; jeder war dort schon eine eigene Funktion.
 */
import React, { useId } from 'react';
import WZSearch from '../WZSearch';

export function SuggestButton({ field, suggestions, onSuggest, onApply, set, currentValue }) {
  // Ohne Zusage kein Knopf — siehe `ohneVorschlaege` oben.
  if (!onSuggest) return null;
  const s = suggestions?.[field] || {};
  if (s.loading) return (
    <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ width: 10, height: 10, border: '1.5px solid #DDE4E8', borderTopColor: 'var(--kc-mid)', borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block' }} />
      <span style={{ fontSize: 11, color: '#8A9BA8' }}>Website wird analysiert...</span>
    </div>
  );
  if (s.value) return (
    <div style={{ marginTop: 8, background: '#E8F7FA', border: '1px solid #A8DDE8', borderRadius: 8, padding: '10px 12px' }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--kc-mid)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Vorschlag aus Website-Content</div>
      <div style={{ fontSize: 12, color: '#1a2e35', lineHeight: 1.6, marginBottom: 8, whiteSpace: 'pre-wrap' }}>{s.value}</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={() => { set(field, s.value); onApply(field); }}
          style={{ padding: '5px 12px', borderRadius: 6, border: 'none', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          Uebernehmen
        </button>
        <button type="button" onClick={() => { set(field, (currentValue ? currentValue + '\n' : '') + s.value); onApply(field); }}
          style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid var(--kc-mid)', background: 'transparent', color: 'var(--kc-mid)', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          + Ergaenzen
        </button>
        <button type="button" onClick={() => onApply(field)}
          style={{ padding: '5px 12px', borderRadius: 6, border: 'none', background: 'transparent', color: '#8A9BA8', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          Ablehnen
        </button>
      </div>
    </div>
  );
  if (s.error) return <div style={{ marginTop: 6, fontSize: 11, color: '#C0392B' }}>{s.error}</div>;
  return (
    <button type="button" onClick={() => onSuggest(field)}
      style={{ marginTop: 6, padding: '4px 10px', borderRadius: 6, border: '1px dashed #A8DDE8', background: 'transparent', color: 'var(--kc-mid)', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      Aus Website vorschlagen
    </button>
  );
}

export const TEAL   = 'var(--brand-primary)';
export const STEPS  = [
  'Betrieb & Leistungen',
  'Zielgruppe & Kunden',
  'Alleinstellung & Mitbewerb',
  'Design & Stil',
  'Seiten & Assets',
  'Zusammenfassung',
];

// Das Feld, über das der Assistent im jeweiligen Schritt spricht. Die Namen
// sind die des Regelwerks im Backend (services/assistant_rules.py), nicht die
// des Formulars — deshalb steht daneben der Formularschlüssel, in den ein
// übernommener Vorschlag geschrieben wird.
export const ASSISTENT_FELD = {
  0: { regel: 'leistungen',      formular: 'leistungen' },
  1: { regel: 'typischer_kunde', formular: 'typischerKunde' },
  2: { regel: 'usp',             formular: 'usp' },
  // Der Stil ist eine Auswahlliste — beraten ja, hineinschreiben nein.
  3: { regel: 'stil',            formular: '' },
  4: { regel: '',                formular: 'sonstige_hinweise' },
  5: { regel: '',                formular: 'sonstige_hinweise' },
};

export const GEWERK_OPTIONS = [
  'Sanitär', 'Heizung', 'Elektro', 'Maler', 'Schreiner',
  'Dachdecker', 'Fliesenleger', 'Zimmerer', 'Kfz', 'Sonstige',
];
export const ZIELGRUPPE_OPTIONS = ['Privatkunden', 'Gewerbekunden', 'Beides'];
export const STIL_OPTIONS = [
  'Modern & Minimalistisch',
  'Klassisch & Seriös',
  'Frisch & Freundlich',
  'Industriell & Technisch',
  'Kein Vorzug',
];
export const SEITEN_OPTIONS = [
  'Startseite', 'Über uns', 'Leistungen', 'Referenzen',
  'Kontakt', 'Blog / News', 'Stellenangebote', 'FAQ',
];

// ── Draft-Persistenz ──────────────────────────────────────────────────────────

export const DRAFT_KEY = (leadId) => `briefing_draft_${leadId}`;

// localStorage kann fehlschlagen (privater Modus, volles Kontingent). Das ist
// hier verkraftbar und bewusst still: der Entwurf ist nur eine Bequemlichkeit,
// die eigentliche Speicherung laeuft ueber autoSave gegen den Server.
export function saveDraft(leadId, data, step) {
  try { localStorage.setItem(DRAFT_KEY(leadId), JSON.stringify({ data, step, savedAt: new Date().toISOString() })); } catch { /* Entwurf ist optional, siehe oben */ }
}

export function loadDraft(leadId) {
  try { const raw = localStorage.getItem(DRAFT_KEY(leadId)); return raw ? JSON.parse(raw) : null; } catch { return null; }
}

export function clearDraft(leadId) {
  try { localStorage.removeItem(DRAFT_KEY(leadId)); } catch { /* Entwurf ist optional, siehe oben */ }
}

export function formatDraftAge(isoString) {
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

export function FieldLabel({ children, required, hasError }) {
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

export function FieldHint({ children }) {
  return (
    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

export const inputBase = {
  width: '100%', padding: '10px 12px',
  border: '1.5px solid var(--border-light)', borderRadius: 8,
  fontSize: 14, fontFamily: 'var(--font-sans, system-ui)',
  color: 'var(--text-primary)', background: 'var(--bg-elevated)',
  outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};

export function Input({ value, onChange, placeholder, onFocus, onBlur, hasError, id }) {
  return (
    <input aria-label={placeholder}
      id={id}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{ ...inputBase, borderColor: hasError ? 'var(--status-danger-text)' : undefined, background: hasError ? 'var(--status-danger-bg)' : undefined }}
      onFocus={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL; if (onFocus) onFocus(e); }}
      onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
    />
  );
}

export function Textarea({ value, onChange, placeholder, rows = 4, onBlur, hasError, minLength, maxLength, id }) {
  const len = (value || '').length;
  const tooLong = maxLength && len > maxLength;
  const tooShort = minLength && len > 0 && len < minLength;
  const counterColor = len === 0 ? 'var(--text-tertiary)' : tooLong ? 'var(--status-danger-text)' : !tooShort ? 'var(--status-success-text)' : 'var(--text-tertiary)';
  return (
    <div style={{ position: 'relative' }}>
      <textarea aria-label={placeholder}
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
          paddingBottom: (minLength || maxLength) ? 24 : undefined,
        }}
        onFocus={e => e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : TEAL}
        onBlur={e => { e.target.style.borderColor = hasError ? 'var(--status-danger-text)' : tooLong ? 'var(--status-warning-text)' : 'var(--border-light)'; if (onBlur) onBlur(e); }}
      />
      {(minLength || maxLength) && (
        <div style={{ position: 'absolute', bottom: 8, right: 10, fontSize: 10, fontWeight: 600, color: counterColor, pointerEvents: 'none', userSelect: 'none', transition: 'color 0.2s' }}>
          {len}{maxLength ? `/${maxLength}` : ''}{minLength && len < minLength ? ` (min. ${minLength})` : ''}
        </div>
      )}
    </div>
  );
}

export function Select({ value, onChange, options, onBlur, hasError, id }) {
  return (
    <select
      id={id}
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

export function Field({ label, required, hint, error, charInfo, children }) {
  const id = useId();
  const childWithId = React.Children.map(children, (child, i) => {
    if (i === 0 && React.isValidElement(child)) return React.cloneElement(child, { id });
    return child;
  });
  return (
    <div style={{ marginBottom: 20 }}>
      <label htmlFor={id} style={{
        display: 'block', fontSize: 11, fontWeight: 700,
        color: error ? 'var(--status-danger-text)' : 'var(--text-secondary)',
        textTransform: 'uppercase', letterSpacing: '0.07em',
        marginBottom: 6, cursor: 'pointer', transition: 'color 0.15s',
      }}>
        {label}{required && <span style={{ color: error ? 'var(--status-danger-text)' : TEAL, marginLeft: 2 }}>*</span>}
      </label>
      {childWithId}
      {error ? (
        <div style={{ fontSize: 11, color: 'var(--status-danger-text)', marginTop: 5, display: 'flex', alignItems: 'center', gap: 4, lineHeight: 1.4 }}>
          <span style={{ fontSize: 12 }}>⚠</span>{error}
        </div>
      ) : hint ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
          {hint}{charInfo && <span style={{ color: 'var(--brand-primary-mid)', marginLeft: 6 }}> · {charInfo}</span>}
        </div>
      ) : charInfo ? (
        <div style={{ fontSize: 11, color: 'var(--brand-primary-mid)', marginTop: 4 }}>{charInfo}</div>
      ) : null}
    </div>
  );
}

// ── Progress bar ─────────────────────────────────────────────────────────────

export function ProgressBar({ step }) {
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

export function Step1({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply }) {
  return (
    <div ref={firstRef}>
      <Field label="Gewerk / Branche" required hint="Waehlen Sie die Hauptbranche Ihres Betriebs." error={fieldError('gewerk')}>
        <WZSearch
          value={data.wz_code ? { code: data.wz_code, title: data.wz_title } : null}
          onChange={(entry) => {
            set('wz_code', entry?.code || '');
            set('wz_title', entry?.title || '');
            set('gewerk', entry?.title || '');
          }}
          placeholder="Branche suchen, z.B. 'Elektro', 'Sanitaer', 'Maler'..."
        />
        <SuggestButton field="gewerk" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.gewerk} />
      </Field>
      <Field label="Leistungen" required hint="Was bieten Sie an? Bitte alle Leistungen auflisten." error={fieldError('leistungen')} charInfo="Empfohlen: mind. 50 Zeichen">
        <Textarea
          value={data.leistungen}
          onChange={v => set('leistungen', v)}
          onBlur={() => touch('leistungen')}
          hasError={!!fieldError('leistungen')}
          minLength={50}
          placeholder={"z.B. Badsanierung, Rohrbruch-Notdienst, Heizungsinstallation"}
          rows={5}
        />
        <SuggestButton field="leistungen" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.leistungen} />
      </Field>
      <Field label="Einzugsgebiet" hint="In welcher Region arbeiten Sie?">
        <Input
          value={data.einzugsgebiet}
          onChange={v => set('einzugsgebiet', v)}
          placeholder="z.B. Koblenz und Umgebung, ca. 40 km Radius"
        />
        <SuggestButton field="einzugsgebiet" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.einzugsgebiet} />
      </Field>
    </div>
  );
}

export function Step2({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply }) {
  return (
    <div ref={firstRef}>
      <Field label="Zielgruppe" required hint="Wen sprechen Sie mit Ihrer Website an?" error={fieldError('zielgruppe')}>
        <Select value={data.zielgruppe} onChange={v => set('zielgruppe', v)} onBlur={() => touch('zielgruppe')} hasError={!!fieldError('zielgruppe')} options={ZIELGRUPPE_OPTIONS} />
        <SuggestButton field="zielgruppe" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.zielgruppe} />
      </Field>
      <Field label="Typischer Kunde" hint="Beschreiben Sie Ihren idealen Kunden." charInfo="Empfohlen: mind. 30 Zeichen">
        <Textarea
          value={data.typischerKunde}
          onChange={v => set('typischerKunde', v)}
          minLength={30}
          placeholder={"z.B. Eigenheimbesitzer, 40-60 Jahre, plant Badsanierung"}
          rows={4}
        />
        <SuggestButton field="typischerKunde" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.typischerKunde} />
      </Field>
      <Field label="Haeufigste Anfrage" hint="Was fragen Kunden am haeufigsten an?">
        <Input
          value={data.haeufigeAnfrage}
          onChange={v => set('haeufigeAnfrage', v)}
          placeholder="z.B. Kostenanfrage Heizungstausch, Notdienst Rohrbruch"
        />
        <SuggestButton field="haeufigeAnfrage" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.haeufigeAnfrage} />
      </Field>
    </div>
  );
}

export function Step3({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply }) {
  return (
    <div ref={firstRef}>
      <Field label="Alleinstellungsmerkmal (USP)" required hint="Was macht Ihren Betrieb besonders?" error={fieldError('usp')} charInfo="Empfohlen: 40-300 Zeichen">
        <Textarea
          value={data.usp}
          onChange={v => set('usp', v)}
          onBlur={() => touch('usp')}
          hasError={!!fieldError('usp')}
          minLength={40}
          maxLength={300}
          placeholder={"z.B. 25 Jahre Erfahrung, 24h-Notdienst, Festpreisgarantie"}
          rows={5}
        />
        <SuggestButton field="usp" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.usp} />
      </Field>
      <Field label="Mitbewerber" hint="Nennen Sie 2-3 Mitbewerber in Ihrer Region.">
        <Input
          value={data.mitbewerber}
          onChange={v => set('mitbewerber', v)}
          placeholder="z.B. Firma Mueller, Installateure Schmidt GmbH"
        />
        <SuggestButton field="mitbewerber" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.mitbewerber} />
      </Field>
    </div>
  );
}

export function Toggle({ value, onChange, labelOn = 'Ja', labelOff = 'Nein' }) {
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

export function SeitenCheckbox({ selected, onChange }) {
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

export function Step4({ data, set, firstRef, touch, fieldError, showErrors, suggestions, onSuggest, onApply }) {
  return (
    <div ref={firstRef}>
      <Field label="Farbwuensche" hint="Welche Farben passen zu Ihrer Marke?">
        <Input value={data.farben} onChange={v => set('farben', v)} placeholder="z.B. Blau & Weiss, Gruen-Toene, keine Vorgabe" />
        <SuggestButton field="farben" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.farben} />
      </Field>
      <Field label="Stil *" required hint="Welcher Designstil soll Ihre Website praegen?" error={fieldError('stil')}>
        <Select value={data.stil} onChange={v => set('stil', v)} onBlur={() => touch('stil')} hasError={!!fieldError('stil')} options={STIL_OPTIONS} />
        {showErrors && !data.stil && (
          <div style={{ fontSize: 11, color: '#C0392B', marginTop: 4, fontWeight: 600 }}>Bitte einen Stil auswaehlen um fortzufahren</div>
        )}
        <SuggestButton field="stil" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.stil} />
      </Field>
      <Field label="Vorbilder / Inspiration" hint="Gibt es Websites die Ihnen gefallen? URL(s) eintragen.">
        <Input value={data.vorbilder} onChange={v => set('vorbilder', v)} placeholder="z.B. https://www.beispiel.de" />
        <SuggestButton field="vorbilder" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.vorbilder} />
      </Field>
    </div>
  );
}

export function Step5({ data, set, firstRef }) {
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
      <Field label="Sonstige Hinweise" hint="Gibt es weitere Wünsche, Anforderungen oder wichtige Informationen?" charInfo="Max. 500 Zeichen">
        <Textarea
          value={data.sonstige_hinweise}
          onChange={v => set('sonstige_hinweise', v)}
          maxLength={500}
          placeholder="Weitere Hinweise, besondere Anforderungen …"
          rows={4}
        />
      </Field>
    </div>
  );
}

export function SummaryRow({ label, value }) {
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

export function SummarySection({ title, children }) {
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

export function Step6({ data, saving, error, onSaveAndPdf, onSaveOnly }) {
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
      <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
        <button onClick={onSaveOnly} disabled={saving}
          style={{ flex: 1, padding: '13px 0', borderRadius: 10, border: `1.5px solid ${TEAL}`, background: 'transparent', color: TEAL, fontSize: 14, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          {saving ? 'Speichert...' : 'Nur speichern'}
        </button>
        <button onClick={onSaveAndPdf} disabled={saving}
          style={{ flex: 2, padding: '13px 0', borderRadius: 10, border: 'none', background: saving ? 'var(--border-light)' : TEAL, color: saving ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          {saving ? 'Speichern...' : 'Speichern & PDF'}
        </button>
      </div>
    </>
  );
}

// ── Wizard ───────────────────────────────────────────────────────────────────

