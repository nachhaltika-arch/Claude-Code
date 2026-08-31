/**
 * Die fuenf Schritte des Leistungsseiten-Assistenten und ihre Felder (L-25).
 *
 * Am 2026-08-30 aus `LeistungsseitenWizard.jsx` herausgeloest — 313 der damals
 * 970 Zeilen. Jeder Schritt war dort schon eine eigene Funktion.
 */
import React, { useId } from 'react';
import { KONTAKT_OPTIONS, TEAL, ZIELGRUPPE_OPTIONS, inputBase } from './leistungsseitenDaten';

export function Input({ value, onChange, placeholder, onBlur, hasError, id, type = 'text' }) {
  return (
    <input aria-label={placeholder}
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


export function Textarea({ value, onChange, placeholder, rows = 4, onBlur, hasError, maxLength, id }) {
  const len = (value || '').length;
  const tooLong = maxLength && len > maxLength;
  const counterColor = len === 0
    ? 'var(--text-tertiary)'
    : tooLong ? 'var(--status-danger-text)' : 'var(--text-tertiary)';
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
          position: 'absolute', bottom: 8, right: 10, fontSize: 12, fontWeight: 600,
          color: counterColor, pointerEvents: 'none', userSelect: 'none', transition: 'color 0.2s',
        }}>
          {len}/{maxLength}
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

export function ButtonGroup({ value, onChange, options }) {
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

export function Field({ label, required, hint, error, children }) {
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
          display: 'block', fontSize: 12, fontWeight: 700,
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
          fontSize: 12, color: 'var(--status-danger-text)', marginTop: 5,
          display: 'flex', alignItems: 'center', gap: 4, lineHeight: 1.4,
        }}>
          <span style={{ fontSize: 12 }}>⚠</span>{error}
        </div>
      ) : hint ? (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5 }}>
          {hint}
        </div>
      ) : null}
    </div>
  );
}

// ── Step-Screens ─────────────────────────────────────────────────────────────

export function Step1({ data, set, touch, fieldError }) {
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

export function Step2({ data, set, touch, fieldError }) {
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

export function Step3({ data, set, touch, fieldError }) {
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

export function Step4({ data, set }) {
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

export function Step5({ data, set, touch, fieldError }) {
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

