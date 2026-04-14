import React, { useState, useEffect, useRef, useId } from 'react';
import { createPortal } from 'react-dom';
import API_BASE_URL from '../config';
import WZSearch from './WZSearch';
import { useScreenSize } from '../utils/responsive';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { useAuth } from '../context/AuthContext';

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

function Input({ value, onChange, placeholder, onFocus, onBlur, hasError, id }) {
  return (
    <input
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

function Textarea({ value, onChange, placeholder, rows = 4, onBlur, hasError, minLength, maxLength, id }) {
  const len = (value || '').length;
  const tooLong = maxLength && len > maxLength;
  const tooShort = minLength && len > 0 && len < minLength;
  const counterColor = len === 0 ? 'var(--text-tertiary)' : tooLong ? 'var(--status-danger-text)' : !tooShort ? 'var(--status-success-text)' : 'var(--text-tertiary)';
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

function Select({ value, onChange, options, onBlur, hasError, id }) {
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

function Field({ label, required, hint, error, charInfo, kiFilled, children }) {
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
        {kiFilled && (
          <span
            title="Automatisch vorausgefüllt — bitte prüfen. Sobald du editierst, verschwindet das Badge."
            style={{
              marginLeft: 8, padding: '1px 7px', borderRadius: 10,
              background: '#E6F1FB', color: '#0C447C',
              fontSize: 9, fontWeight: 700,
              textTransform: 'none', letterSpacing: '0.02em',
              verticalAlign: 'middle',
            }}
          >🤖 KI</span>
        )}
      </label>
      {childWithId}
      {error ? (
        <div style={{ fontSize: 11, color: 'var(--status-danger-text)', marginTop: 5, display: 'flex', alignItems: 'center', gap: 4, lineHeight: 1.4 }}>
          <span style={{ fontSize: 12 }}>⚠</span>{error}
        </div>
      ) : hint ? (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
          {hint}{charInfo && <span style={{ color: 'var(--brand-primary)', marginLeft: 6 }}> · {charInfo}</span>}
        </div>
      ) : charInfo ? (
        <div style={{ fontSize: 11, color: 'var(--brand-primary)', marginTop: 4 }}>{charInfo}</div>
      ) : null}
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

function Step1({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply, isKiFilled = () => false }) {
  return (
    <div ref={firstRef}>
      <Field label="Gewerk / Branche" required hint="Waehlen Sie die Hauptbranche Ihres Betriebs." error={fieldError('gewerk')} kiFilled={isKiFilled('gewerk')}>
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
      <Field label="Leistungen" required hint="Was bieten Sie an? Bitte alle Leistungen auflisten." error={fieldError('leistungen')} charInfo="Empfohlen: mind. 50 Zeichen" kiFilled={isKiFilled('leistungen')}>
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
      <Field label="Einzugsgebiet" hint="In welcher Region arbeiten Sie?" kiFilled={isKiFilled('einzugsgebiet')}>
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

function Step2({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply }) {
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

function Step3({ data, set, firstRef, touch, fieldError, suggestions, onSuggest, onApply }) {
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

function Step4({ data, set, firstRef, touch, fieldError, showErrors, suggestions, onSuggest, onApply, isKiFilled = () => false }) {
  return (
    <div ref={firstRef}>
      <Field label="Farbwuensche" hint="Welche Farben passen zu Ihrer Marke?" kiFilled={isKiFilled('farben')}>
        <Input value={data.farben} onChange={v => set('farben', v)} placeholder="z.B. Blau & Weiss, Gruen-Toene, keine Vorgabe" />
        <SuggestButton field="farben" suggestions={suggestions} onSuggest={onSuggest} onApply={onApply} set={set} currentValue={data.farben} />
      </Field>
      <Field label="Stil *" required hint="Welcher Designstil soll Ihre Website praegen?" error={fieldError('stil')} kiFilled={isKiFilled('stil')}>
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

function Step5({ data, set, firstRef, isKiFilled = () => false }) {
  return (
    <div ref={firstRef}>
      <Field label="Gewünschte Seiten" hint="Welche Seiten soll Ihre neue Website enthalten?" kiFilled={isKiFilled('wunschseiten')}>
        <SeitenCheckbox
          selected={data.wunschseiten}
          onChange={v => set('wunschseiten', v)}
        />
      </Field>
      <Field label="Logo vorhanden?" hint="Haben Sie bereits ein Logo, das wir verwenden können?" kiFilled={isKiFilled('logo_vorhanden')}>
        <Toggle value={data.logo_vorhanden} onChange={v => set('logo_vorhanden', v)} />
      </Field>
      <Field label="Fotos / Bilder vorhanden?" hint="Haben Sie Fotos Ihres Betriebs, Teams oder Ihrer Arbeit?" kiFilled={isKiFilled('fotos_vorhanden')}>
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

function Step6({ data, saving, error, submitted, onSaveAndPdf, onSaveOnly, onSubmit }) {
  // Nach erfolgreichem Submit: Success-Screen statt Buttons.
  if (submitted) {
    return (
      <div style={{
        padding: '28px 24px', borderRadius: 12,
        background: '#EAF3DE', border: '1px solid #1D9E75',
        textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 10,
      }}>
        <div style={{ fontSize: 40, lineHeight: 1 }}>✓</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#0F5C43' }}>
          Briefing abgeschickt
        </div>
        <div style={{ fontSize: 13, color: '#27500A', lineHeight: 1.6, maxWidth: 480, margin: '0 auto' }}>
          Dein Briefing liegt jetzt beim Team zur Freigabe.
          Sobald es geprüft ist, starten wir automatisch mit der Sitemap und dem Content
          und du bekommst eine E-Mail-Benachrichtigung.
        </div>
        <div style={{ fontSize: 11, color: '#3D5F32', marginTop: 4 }}>
          Du kannst diesen Dialog jetzt schliessen.
        </div>
      </div>
    );
  }

  return (
    <>
      <div style={{ marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
        Bitte prüfen Sie alle Angaben. Mit „Abschicken" geht das Briefing zur Admin-Freigabe — danach startet die KI-Sitemap automatisch.
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
      <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
        <button onClick={onSaveOnly} disabled={saving}
          style={{ flex: '1 1 140px', padding: '13px 0', borderRadius: 10, border: `1.5px solid ${TEAL}`, background: 'transparent', color: TEAL, fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          {saving ? '…' : 'Entwurf speichern'}
        </button>
        <button onClick={onSaveAndPdf} disabled={saving}
          style={{ flex: '1 1 140px', padding: '13px 0', borderRadius: 10, border: `1.5px solid ${TEAL}`, background: 'transparent', color: TEAL, fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          {saving ? '…' : 'Speichern & PDF'}
        </button>
        <button onClick={onSubmit} disabled={saving}
          style={{ flex: '2 1 200px', padding: '13px 0', borderRadius: 10, border: 'none', background: saving ? 'var(--border-light)' : '#1D9E75', color: saving ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans, system-ui)', boxShadow: saving ? 'none' : '0 1px 3px rgba(0,0,0,0.12)' }}>
          {saving ? 'Wird übermittelt…' : '✓ Briefing abschicken'}
        </button>
      </div>
    </>
  );
}

// ── Wizard ───────────────────────────────────────────────────────────────────

export default function BriefingWizard({ leadId, leadData, onClose, onComplete, embedded = false }) {
  const { isMobile } = useScreenSize();
  const { token } = useAuth();
  const suggestHeaders = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const existingDraft = loadDraft(leadId);

  const [step, setStep] = useState(existingDraft?.step ?? 0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [draftBanner, setDraftBanner] = useState(existingDraft ? formatDraftAge(existingDraft.savedAt) : null);
  const [suggestions, setSuggestions] = useState({});
  const [showErrors, setShowErrors] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('');
  const firstFieldRef = useRef(null);

  const suggestField = async (field) => {
    setSuggestions(prev => ({ ...prev, [field]: { loading: true, value: null, error: null } }));
    try {
      const res = await fetch(`${API_BASE_URL}/api/briefings/${leadId}/suggest-field`, { method: 'POST', headers: suggestHeaders, body: JSON.stringify({ field }) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Fehler'); }
      const { suggestion } = await res.json();
      setSuggestions(prev => ({ ...prev, [field]: { loading: false, value: suggestion, error: null } }));
    } catch (e) {
      setSuggestions(prev => ({ ...prev, [field]: { loading: false, value: null, error: e.message } }));
    }
  };
  const applySuggestion = (field) => setSuggestions(prev => ({ ...prev, [field]: { ...prev[field], value: null } }));

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
    zielgruppe:        typeof leadData?.zielgruppe === 'string' ? leadData.zielgruppe : leadData?.zielgruppe?.primaer || '',
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

  // KI-Auto-Fill Tracking: welche Felder wurden vom Backend-ki-prefill
  // befuellt? Das Set wird beim Laden von leadData initialisiert und
  // schrumpft, sobald der Nutzer ein Feld editiert — dann verschwindet
  // das KI-Badge an diesem Feld.
  const KI_AUTOFILL_FIELDS = [
    'gewerk', 'leistungen', 'einzugsgebiet', 'farben', 'stil',
    'wunschseiten', 'logo_vorhanden', 'fotos_vorhanden',
  ];
  const [kiFilledFields, setKiFilledFields] = useState(() => new Set());
  const kiPrefilledAt = leadData?.ki_prefilled_at || null;
  const kiConfidence = leadData?.ki_confidence || '';
  const kiHinweise = leadData?.ki_hinweise || '';

  // Sync from leadData when it arrives (e.g. after async briefing load)
  useEffect(() => {
    if (!leadData) return;
    setData(prev => {
      // Only fill empty fields — don't overwrite user edits
      const hasUserInput = prev.gewerk || prev.leistungen || prev.usp;
      if (hasUserInput) return prev;
      const updated = { ...prev };
      for (const key of Object.keys(prev)) {
        if (!prev[key] && leadData[key]) {
          if (key === 'zielgruppe') {
            updated[key] = typeof leadData[key] === 'string' ? leadData[key] : leadData[key]?.primaer || '';
          } else if (key === 'wunschseiten') {
            updated[key] = Array.isArray(leadData[key]) ? leadData[key] : (leadData[key] || '').split(', ').filter(Boolean);
          } else {
            updated[key] = leadData[key];
          }
        }
      }
      return updated;
    });
  }, [leadData]); // eslint-disable-line

  // KI-Badges initialisieren, sobald ki_prefilled_at vom Backend kommt
  useEffect(() => {
    if (!kiPrefilledAt) return;
    const filled = new Set();
    for (const key of KI_AUTOFILL_FIELDS) {
      const val = leadData?.[key];
      const isSet = (
        (typeof val === 'string' && val.trim() !== '') ||
        (Array.isArray(val) && val.length > 0) ||
        (typeof val === 'boolean' && val === true)
      );
      if (isSet) filled.add(key);
    }
    setKiFilledFields(filled);
  }, [kiPrefilledAt]); // eslint-disable-line

  const set = (key, val) => {
    setData(d => ({ ...d, [key]: val }));
    // Sobald Nutzer ein Feld editiert: KI-Badge entfernen
    setKiFilledFields(prev => {
      if (!prev.has(key)) return prev;
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
  };

  // Auto-Save Draft bei jeder Änderung (nur wenn echte Daten vorhanden)
  useEffect(() => {
    if (data.gewerk || data.leistungen || data.usp || data.farben || data.stil) {
      saveDraft(leadId, data, step);
    }
  }, [data, step, leadId]);

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
      // Nach Fix 14 Phase 2 wird Auth ueber httpOnly-Cookie getragen — sessionStorage
      // ist leer. Wir verwenden den `token` aus useAuth() (siehe oben), der aus dem
      // AuthContext kommt, und lassen den monkey-patched fetch die Cookies anhaengen.
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
      // Open PDF in new tab (with auth)
      clearDraft(leadId);
      try {
        const pdfRes = await fetch(`${API_BASE_URL}/api/briefings/${leadId}/pdf`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (pdfRes.ok) {
          const blob = await pdfRes.blob();
          const url = URL.createObjectURL(blob);
          window.open(url, '_blank');
          setTimeout(() => URL.revokeObjectURL(url), 60000);
        }
      } catch (_) { /* PDF download non-fatal */ }
      if (onComplete) onComplete(data);
    } catch (e) {
      setSaveError(e.message || 'Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  };

  const buildPayload = () => ({
    gewerk: data.gewerk, wz_code: data.wz_code, wz_title: data.wz_title,
    leistungen: data.leistungen, einzugsgebiet: data.einzugsgebiet,
    usp: data.usp, mitbewerber: data.mitbewerber, vorbilder: data.vorbilder,
    farben: data.farben, stil: data.stil,
    wunschseiten: Array.isArray(data.wunschseiten) ? data.wunschseiten.join(', ') : data.wunschseiten || '',
    logo_vorhanden: data.logo_vorhanden, fotos_vorhanden: data.fotos_vorhanden,
    sonstige_hinweise: data.sonstige_hinweise,
  });

  const autoSave = async () => {
    setAutoSaveStatus('saving');
    try {
      // Token aus useAuth()-Context (oben destrukturiert). Nach Fix 14 Phase 2
      // wird der tatsaechliche Auth-Kontext via httpOnly-Cookie vom monkey-patched
      // fetch uebertragen — dieser Header ist nur noch eine Best-Effort-Beigabe.
      await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'POST', headers: suggestHeaders,
        body: JSON.stringify(buildPayload()),
      });
      setAutoSaveStatus('saved');
      setTimeout(() => setAutoSaveStatus(''), 2000);
    } catch { setAutoSaveStatus('error'); setTimeout(() => setAutoSaveStatus(''), 3000); }
  };

  const handleNext = async () => {
    if (!canNext()) { touchStep(step); setShowErrors(true); return; }
    setShowErrors(false);
    await autoSave();
    if (step < STEPS.length - 1) setStep(s => s + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep(s => s - 1);
    else if (onClose) onClose();
  };

  const handleSaveOnly = async () => {
    setSaving(true); setSaveError('');
    try {
      // Token aus useAuth()-Context; Cookie-Auth uebernimmt die eigentliche Pruefung.
      const res = await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'POST', headers: suggestHeaders,
        body: JSON.stringify(buildPayload()),
      });
      if (!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || 'Fehler');
      clearDraft(leadId);
      if (onComplete) onComplete(data);
    } catch (e) { setSaveError(e.message); }
    finally { setSaving(false); }
  };

  // Tor 1 — "Briefing abschicken" (Baustein 2 der Funnel-Automation)
  const [submitted, setSubmitted] = useState(false);
  const handleSubmit = async () => {
    setSaving(true);
    setSaveError('');
    try {
      // Schritt 1: letzten Stand speichern (damit der Submit-Check auf
      // aktuelle Werte greift — der Endpoint validiert gewerk/leistungen).
      const saveRes = await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, {
        method: 'POST', headers: suggestHeaders,
        body: JSON.stringify(buildPayload()),
      });
      if (!saveRes.ok) {
        const err = await saveRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Speichern fehlgeschlagen');
      }
      // Schritt 2: Submit-Endpoint triggern.
      const submitRes = await fetch(
        `${API_BASE_URL}/api/briefings/${leadId}/submit`,
        { method: 'POST', headers: suggestHeaders },
      );
      if (!submitRes.ok) {
        const err = await submitRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Abschicken fehlgeschlagen');
      }
      clearDraft(leadId);
      setSubmitted(true);
    } catch (e) {
      setSaveError(e.message || 'Abschicken fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  };

  const renderStep = () => {
    const suggestProps = { suggestions, onSuggest: suggestField, onApply: applySuggestion };
    const isKiFilled = (key) => kiFilledFields.has(key);
    const p = { data, set, touch, fieldError, firstRef: firstFieldRef, isKiFilled, ...suggestProps };
    switch (step) {
      case 0: return <Step1 {...p} />;
      case 1: return <Step2 {...p} />;
      case 2: return <Step3 {...p} />;
      case 3: return <Step4 {...p} showErrors={showErrors} />;
      case 4: return <Step5 {...p} />;
      case 5: return (
        <Step6
          data={data}
          saving={saving}
          error={saveError}
          submitted={submitted}
          onSaveAndPdf={handleSaveAndPdf}
          onSaveOnly={handleSaveOnly}
          onSubmit={handleSubmit}
        />
      );
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

  // ── Embedded: render inline without portal ──
  if (embedded) {
    return (
      <div style={{ borderRadius: 12, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', overflow: 'hidden', maxHeight: 600 }}>
        {/* Header */}
        <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-surface)', flexShrink: 0 }}>
          <div>
            <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '.08em', color: TEAL, textTransform: 'uppercase' }}>Schritt {step + 1} von {STEPS.length}</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>{STEPS[step]}</div>
            {leadData?.gewerk ? (
              <div style={{ fontSize: 11, color: '#1D9E75', marginTop: 2 }}>Bestehendes Briefing wird bearbeitet</div>
            ) : (
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Neues Briefing anlegen</div>
            )}
          </div>
        </div>
        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {renderStep()}
        </div>
        {/* Footer */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <button onClick={handleBack} style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            {step === 0 ? 'Abbrechen' : 'Zurueck'}
          </button>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
            {autoSaveStatus === 'saving' && (<><span style={{ width: 10, height: 10, border: '1.5px solid var(--border-light)', borderTopColor: TEAL, borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block' }} /><span>Speichert...</span></>)}
            {autoSaveStatus === 'saved' && <span style={{ color: '#1D9E75' }}>Gespeichert</span>}
            {autoSaveStatus === 'error' && <span style={{ color: '#C0392B' }}>Fehler</span>}
            {!autoSaveStatus && <span>{step + 1} / {STEPS.length}</span>}
          </div>
          {step < STEPS.length - 1 ? (
            <button onClick={handleNext} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', background: canNext() ? TEAL : 'var(--border-medium)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Weiter
            </button>
          ) : (
            <button onClick={handleSaveAndPdf} disabled={saving} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', background: saving ? 'var(--border-medium)' : '#059669', color: '#fff', fontSize: 13, fontWeight: 700, cursor: saving ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Speichert...' : 'Speichern'}
            </button>
          )}
        </div>
        {saveError && <div style={{ padding: '8px 20px', fontSize: 12, color: 'var(--status-danger-text)', background: 'var(--status-danger-bg)' }}>{saveError}</div>}
      </div>
    );
  }

  return createPortal(
    <>
      {/* ── Overlay ── */}
      <div
        onClick={async () => {
          const hasData = !!(data.gewerk || data.leistungen || data.usp);
          if (hasData && step > 0) { try { await autoSave(); } catch {} }
          onClose?.();
        }}
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
        {/* Drag Handle — Mobile only */}
        {isMobile && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0 2px', flexShrink: 0 }}>
            <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2 }} />
          </div>
        )}

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

        {/* KI-Prefill-Banner — erscheint wenn Backend das Briefing
            automatisch aus Crawler/Brand/Audit vorausgefuellt hat */}
        {kiPrefilledAt && (
          <div style={{
            margin: '10px 24px 0', padding: '10px 14px',
            background: '#E6F1FB', border: '1px solid #0C447C',
            borderRadius: 'var(--radius-md, 6px)', fontSize: 12,
            color: '#0C447C', lineHeight: 1.5,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: kiHinweise ? 4 : 0 }}>
              <span style={{ fontSize: 14 }}>🤖</span>
              <strong>Wir haben dein Briefing bereits aus deiner bisherigen Website vorausgefüllt.</strong>
              {kiConfidence && (
                <span style={{
                  marginLeft: 'auto', padding: '1px 8px', borderRadius: 10,
                  background: '#FFFFFFAA', fontSize: 10, fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>
                  {kiConfidence === 'high' ? 'Hohe Sicherheit'
                    : kiConfidence === 'medium' ? 'Mittlere Sicherheit'
                    : 'Niedrige Sicherheit'}
                </span>
              )}
            </div>
            <div>
              Bitte prüfe die Angaben und ergänze was fehlt. Felder mit <span style={{
                padding: '0 5px', borderRadius: 8, background: '#FFFFFF',
                fontSize: 9, fontWeight: 700,
              }}>🤖 KI</span> wurden automatisch erkannt.
            </div>
            {kiHinweise && (
              <div style={{ marginTop: 6, fontStyle: 'italic', color: '#3D5F86' }}>
                Hinweis: {kiHinweise}
              </div>
            )}
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

function SuggestButton({ field, suggestions, onSuggest, onApply, set, currentValue }) {
  const s = suggestions?.[field] || {};
  if (s.loading) return (
    <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ width: 10, height: 10, border: '1.5px solid #DDE4E8', borderTopColor: '#008EAA', borderRadius: '50%', animation: 'spin .7s linear infinite', display: 'inline-block' }} />
      <span style={{ fontSize: 11, color: '#8A9BA8' }}>Website wird analysiert...</span>
    </div>
  );
  if (s.value) return (
    <div style={{ marginTop: 8, background: '#E8F7FA', border: '1px solid #A8DDE8', borderRadius: 8, padding: '10px 12px' }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: '#008EAA', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Vorschlag aus Website-Content</div>
      <div style={{ fontSize: 12, color: '#1a2e35', lineHeight: 1.6, marginBottom: 8, whiteSpace: 'pre-wrap' }}>{s.value}</div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={() => { set(field, s.value); onApply(field); }}
          style={{ padding: '5px 12px', borderRadius: 6, border: 'none', background: '#008EAA', color: '#fff', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
          Uebernehmen
        </button>
        <button type="button" onClick={() => { set(field, (currentValue ? currentValue + '\n' : '') + s.value); onApply(field); }}
          style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #008EAA', background: 'transparent', color: '#008EAA', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)' }}>
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
      style={{ marginTop: 6, padding: '4px 10px', borderRadius: 6, border: '1px dashed #A8DDE8', background: 'transparent', color: '#008EAA', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans, system-ui)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      Aus Website vorschlagen
    </button>
  );
}
