// Dialog „Neuen Betrieb anlegen".
//
// Lag bis 2026-08-17 unten in `pages/Companies.jsx`. Beim Zusammenlegen der
// beiden Listen musste er mitwandern — als eigene Datei, damit die Seite die
// Liste zeigt und der Dialog das Anlegen macht.

import { useState } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const GEWERKE = [
  'Heizung', 'Sanitär', 'Elektriker', 'Klempner',
  'Dachdecker', 'Maler', 'Schreiner', 'Fliesenleger', 'Sonstiges',
];

const LEER = {
  company_name: '',
  website_url: '',
  contact_name: '',
  email: '',
  phone: '',
  city: '',
  trade: '',
};

/** Hängt `https://` an, wenn der Nutzer nur die Domain getippt hat. */
function adresseVervollstaendigen(eingabe) {
  const wert = eingabe.trim();
  if (!wert) return '';
  return wert.startsWith('http') ? wert : `https://${wert}`;
}

export default function BetriebAnlegenModal({ token, onClose, onCreated }) {
  const [form, setForm] = useState(LEER);
  const [speichert, setSpeichert] = useState(false);

  const set = (feld) => (e) => setForm((f) => ({ ...f, [feld]: e.target.value }));

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (speichert) return;
    if (!form.company_name.trim()) {
      toast.error('Firmenname ist Pflichtfeld');
      return;
    }

    setSpeichert(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          company_name: form.company_name.trim(),
          website_url: adresseVervollstaendigen(form.website_url) || undefined,
          contact_name: form.contact_name.trim() || undefined,
          email: form.email.trim() || undefined,
          phone: form.phone.trim() || undefined,
          city: form.city.trim() || undefined,
          trade: form.trade || undefined,
          status: 'new',
          lead_source: 'manual',
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const meldung = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(meldung);
      }
      toast.success(`„${form.company_name}" angelegt`);
      onCreated(body);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSpeichert(false);
    }
  };

  const inp = {
    width: '100%', boxSizing: 'border-box', padding: '9px 12px',
    border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-surface)', color: 'var(--text-primary)',
    fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
  };
  const lbl = {
    display: 'block', fontSize: 11, fontWeight: 600,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 4,
  };

  return createPortal(
    <div
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(0,0,0,0.55)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <form
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          width: '100%', maxWidth: 520,
          maxHeight: 'calc(100vh - 32px)', overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
        }}
      >
        {/* Kopf */}
        <div style={{
          padding: '18px 22px 14px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
              Neuen Betrieb anlegen
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
              Von Hand angelegt — kann später für Audit und Projekt genutzt werden
            </div>
          </div>
          <button
            type="button" onClick={onClose}
            style={{
              background: 'none', border: 'none', fontSize: 20,
              cursor: 'pointer', color: 'var(--text-tertiary)',
              lineHeight: 1, padding: '0 2px',
            }}
            aria-label="Schließen"
          >
            ×
          </button>
        </div>

        {/* Felder */}
        <div style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={lbl} htmlFor="betrieb-firmenname">Firmenname *</label>
            <input aria-label="Firmenname"
              id="betrieb-firmenname"
              value={form.company_name} onChange={set('company_name')}
              placeholder="z.B. Müller Haustechnik GmbH"
              style={inp} autoFocus
            />
          </div>
          <div>
            <label style={lbl} htmlFor="betrieb-website">Website / Domain</label>
            <input aria-label="Website / Domain"
              id="betrieb-website"
              value={form.website_url} onChange={set('website_url')}
              placeholder="z.B. mueller-haustechnik.de"
              style={inp} autoComplete="url"
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl} htmlFor="betrieb-ansprechpartner">Ansprechpartner</label>
              <input aria-label="Ansprechpartner"
                id="betrieb-ansprechpartner"
                value={form.contact_name} onChange={set('contact_name')}
                placeholder="Vor- und Nachname" style={inp}
              />
            </div>
            <div>
              <label style={lbl} htmlFor="betrieb-telefon">Telefon</label>
              <input aria-label="Telefon"
                id="betrieb-telefon"
                type="tel" value={form.phone} onChange={set('phone')}
                placeholder="+49 …" style={inp}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl} htmlFor="betrieb-email">E-Mail</label>
              <input aria-label="E-Mail"
                id="betrieb-email"
                type="email" value={form.email} onChange={set('email')}
                placeholder="info@firma.de" style={inp}
              />
            </div>
            <div>
              <label style={lbl} htmlFor="betrieb-stadt">Stadt</label>
              <input aria-label="Stadt"
                id="betrieb-stadt"
                value={form.city} onChange={set('city')}
                placeholder="Boppard" style={inp}
              />
            </div>
          </div>
          <div>
            <label style={lbl} htmlFor="betrieb-gewerk">Gewerk</label>
            <select aria-label="Gewerk"
              id="betrieb-gewerk"
              value={form.trade} onChange={set('trade')}
              style={{ ...inp, cursor: 'pointer' }}
            >
              <option value="">Bitte wählen…</option>
              {GEWERKE.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
        </div>

        {/* Fuß */}
        <div style={{
          padding: '14px 22px',
          borderTop: '1px solid var(--border-light)',
          display: 'flex', justifyContent: 'flex-end', gap: 10,
        }}>
          <button
            type="button" onClick={onClose}
            style={{
              padding: '9px 18px',
              background: 'var(--bg-app)',
              border: '1px solid var(--border-light)',
              color: 'var(--text-secondary)',
              borderRadius: 'var(--radius-md)',
              fontSize: 13, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            Abbrechen
          </button>
          <button
            type="submit" disabled={speichert}
            style={{
              padding: '9px 22px',
              background: 'var(--brand-primary)', opacity: speichert ? 0.5 : 1,
              color: 'var(--text-on-brand)', border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 13, fontWeight: 600,
              cursor: speichert ? 'wait' : 'pointer',
              fontFamily: 'var(--font-sans)',
              opacity: speichert ? 0.6 : 1,
            }}
          >
            {speichert ? 'Anlegen…' : '✓ Betrieb anlegen'}
          </button>
        </div>
      </form>
    </div>,
    document.body,
  );
}
