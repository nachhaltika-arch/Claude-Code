/**
 * Auswahllisten und Feldstile des Leistungsseiten-Assistenten (L-25).
 *
 * Am 2026-08-30 aus `LeistungsseitenWizard.jsx` herausgeloest. Der Assistent
 * und seine fuenf Schritte brauchen sie gleichermassen.
 */

export const inputBase = {
  width: '100%', padding: '10px 12px',
  border: '1.5px solid var(--border-light)', borderRadius: 8,
  fontSize: 14, fontFamily: 'var(--font-sans, system-ui)',
  color: 'var(--text-primary)', background: 'var(--bg-elevated)',
  outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.15s',
};

export const KONTAKT_OPTIONS    = ['Telefon', 'WhatsApp', 'Kontaktformular', 'Alle drei'];

export const TEAL = 'var(--brand-primary)';

export const ZIELGRUPPE_OPTIONS = ['Privatkunden', 'Geschäftskunden', 'Beides'];
