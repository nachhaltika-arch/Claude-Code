import React, { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import { useScreenSize } from '../utils/responsive';

const TRADE_OPTIONS = [
  'Elektriker',
  'Klempner',
  'Maler',
  'Schreiner',
  'Dachdecker',
  'Heizung',
  'Sanitär',
  'Fliesenleger',
  'Sonstiges',
];

export default function ContactImport() {
  const [activeTab, setActiveTab] = useState('csv');
  const tabs = [
    { key: 'csv', label: 'CSV Upload' },
    { key: 'manual', label: 'Manuell eingeben' },
    { key: 'template', label: 'CSV-Vorlage' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      <div className="kc-section-header">
        <span className="kc-eyebrow">Datenimport</span>
        <h1>Kontakt-Import</h1>
      </div>

      <div className="kc-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`kc-tab ${activeTab === tab.key ? 'kc-tab--active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'csv' && <CsvUploadTab />}
      {activeTab === 'manual' && <ManualEntryTab />}
      {activeTab === 'template' && <TemplateTab />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Tab 1: CSV Upload
// ═══════════════════════════════════════════════════════════

function CsvUploadTab() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f) return;
    if (!f.name.endsWith('.csv')) {
      toast.error('Nur CSV-Dateien erlaubt.');
      return;
    }
    setFile(f);
    setResult(null);

    // Parse preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter((l) => l.trim());
      const headers = lines[0];
      const rows = lines.slice(1, 6); // First 5 data rows
      setPreview({ headers: headers.split(/[,;]\s*/), rows: rows.map((r) => r.split(/[,;]\s*/)) });
    };
    reader.readAsText(f);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    handleFile(f);
  }, [handleFile]);

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API_BASE_URL}/api/leads/import/csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setResult(res.data);
      if (res.data.imported > 0) {
        toast.success(`${res.data.imported} Kontakte importiert`);
      }
      if (res.data.errors > 0) {
        toast.error(`${res.data.errors} Zeilen fehlerhaft`);
      }
    } catch (error) {
      const msg = error.response?.data?.detail || 'Import fehlgeschlagen';
      toast.error(msg);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-6)' }}>
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? 'var(--kc-rot)' : 'var(--kc-rand)'}`,
          borderRadius: 'var(--kc-radius-lg)',
          padding: 'var(--kc-space-12)',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragOver ? 'var(--kc-rot-subtle)' : 'var(--kc-weiss)',
          transition: 'all var(--kc-transition-fast)',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <div style={{ fontSize: 'var(--kc-text-3xl)', marginBottom: 'var(--kc-space-2)' }}>
          {file ? '✅' : '📄'}
        </div>
        <p style={{ fontWeight: 600, color: 'var(--kc-text-primaer)', fontSize: 'var(--kc-text-lg)' }}>
          {file ? file.name : 'CSV-Datei hierher ziehen'}
        </p>
        <p style={{ color: 'var(--kc-text-subtil)', fontSize: 'var(--kc-text-sm)' }}>
          {file ? `${(file.size / 1024).toFixed(1)} KB` : 'oder klicken zum Auswählen'}
        </p>
      </div>

      {/* Preview Table */}
      {preview && (
        <div className="kc-card" style={{ padding: 0, overflow: 'auto' }}>
          <div style={{ padding: 'var(--kc-space-3) var(--kc-space-4)', borderBottom: '1px solid var(--kc-rand)' }}>
            <span className="kc-eyebrow" style={{ marginBottom: 0 }}>
              Vorschau ({preview.rows.length} von {preview.rows.length}+ Zeilen)
            </span>
          </div>
          <table className="kc-table">
            <thead>
              <tr>
                {preview.headers.map((h, i) => (
                  <th key={i}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row, ri) => (
                <tr key={ri}>
                  {row.map((cell, ci) => (
                    <td key={ci}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Import Button */}
      {file && !result && (
        <div>
          <button
            className="kc-btn-primary"
            onClick={handleImport}
            disabled={importing}
            style={{ opacity: importing ? 0.6 : 1 }}
          >
            {importing ? 'Importiere...' : 'Importieren'}
          </button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div
          className={`kc-alert ${result.errors > 0 ? 'kc-alert--warning' : 'kc-alert--info'}`}
        >
          <strong>{result.message}</strong>
          {result.error_details && result.error_details.length > 0 && (
            <ul style={{ marginTop: 'var(--kc-space-3)', paddingLeft: 'var(--kc-space-6)', fontSize: 'var(--kc-text-sm)' }}>
              {result.error_details.map((err, i) => (
                <li key={i}>Zeile {err.row}: {err.error}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Tab 2: Manual Entry
// ═══════════════════════════════════════════════════════════

const EMPTY_FORM = {
  company_name: '',
  contact_name: '',
  phone: '',
  email: '',
  website_url: '',
  city: '',
  trade: '',
};

function ManualEntryTab() {
  const { isMobile } = useScreenSize();
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company_name.trim()) {
      toast.error('Firmenname ist Pflichtfeld.');
      return;
    }

    setSaving(true);
    try {
      await axios.post(`${API_BASE_URL}/api/leads/import/manual`, form);
      toast.success(`"${form.company_name}" gespeichert`);
      setForm({ ...EMPTY_FORM });
    } catch (error) {
      const msg = error.response?.data?.detail || 'Speichern fehlgeschlagen';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: 'var(--kc-space-3) var(--kc-space-4)',
    border: '1.5px solid var(--kc-rand)',
    borderRadius: 'var(--kc-radius-md)',
    fontSize: 'var(--kc-text-base)',
    fontFamily: 'var(--kc-font-body)',
    transition: 'border-color var(--kc-transition-fast)',
    background: 'var(--kc-weiss)',
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    fontSize: 'var(--kc-text-sm)',
    fontWeight: 600,
    color: 'var(--kc-text-sekundaer)',
    marginBottom: 'var(--kc-space-1)',
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="kc-card"
      style={{ maxWidth: isMobile ? '100%' : '640px', display: 'flex', flexDirection: 'column', gap: 'var(--kc-space-4)' }}
    >
      <div>
        <label style={labelStyle}>
          Firmenname <span style={{ color: 'var(--kc-rot)' }}>*</span>
        </label>
        <input
          type="text"
          value={form.company_name}
          onChange={set('company_name')}
          placeholder="z.B. Müller Sanitär GmbH"
          required
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 'var(--kc-space-4)' }}>
        <div>
          <label style={labelStyle}>Ansprechpartner</label>
          <input type="text" value={form.contact_name} onChange={set('contact_name')} placeholder="Vor- und Nachname" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Telefon</label>
          <input type="tel" value={form.phone} onChange={set('phone')} placeholder="+49 261 ..." style={inputStyle} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 'var(--kc-space-4)' }}>
        <div>
          <label style={labelStyle}>E-Mail</label>
          <input type="email" value={form.email} onChange={set('email')} placeholder="info@firma.de" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Website URL</label>
          <input type="url" value={form.website_url} onChange={set('website_url')} placeholder="https://www.firma.de" style={inputStyle} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 'var(--kc-space-4)' }}>
        <div>
          <label style={labelStyle}>Stadt</label>
          <input type="text" value={form.city} onChange={set('city')} placeholder="z.B. Koblenz" style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>Gewerk</label>
          <select value={form.trade} onChange={set('trade')} style={inputStyle}>
            <option value="">Bitte wählen...</option>
            {TRADE_OPTIONS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ paddingTop: 'var(--kc-space-2)' }}>
        <button
          type="submit"
          className="kc-btn-primary"
          disabled={saving}
          style={{ opacity: saving ? 0.6 : 1 }}
        >
          {saving ? 'Speichere...' : 'Kontakt speichern'}
        </button>
      </div>
    </form>
  );
}

// ═══════════════════════════════════════════════════════════
// Tab 3: Template Download
// ═══════════════════════════════════════════════════════════

function TemplateTab() {
  const { isMobile } = useScreenSize();
  return (
    <div className="kc-card" style={{ maxWidth: isMobile ? '100%' : '640px' }}>
      <span className="kc-eyebrow">Vorlage</span>
      <h2 style={{ fontSize: 'var(--kc-text-2xl)', marginBottom: 'var(--kc-space-4)' }}>
        CSV-Vorlage herunterladen
      </h2>

      <p style={{ color: 'var(--kc-text-sekundaer)', fontSize: 'var(--kc-text-sm)', marginBottom: 'var(--kc-space-6)', lineHeight: 'var(--kc-leading-normal)' }}>
        Laden Sie die Vorlage herunter, f&uuml;llen Sie sie mit Ihren Kontaktdaten
        und importieren Sie sie anschlie&szlig;end &uuml;ber den Tab &bdquo;CSV Upload&ldquo;.
        Die Datei enth&auml;lt 3 Beispiel-Eintr&auml;ge als Orientierung.
      </p>

      <div style={{ background: 'var(--kc-hell)', borderRadius: 'var(--kc-radius-md)', padding: 'var(--kc-space-4)', marginBottom: 'var(--kc-space-6)', fontSize: 'var(--kc-text-sm)' }}>
        <strong>Pflicht-Spalten:</strong> company_name, contact_name, email, city, trade<br />
        <strong>Optionale Spalten:</strong> phone, website_url<br />
        <strong>Trennzeichen:</strong> Komma oder Semikolon<br />
        <strong>Kodierung:</strong> UTF-8
      </div>

      <a
        href="/kontakte-vorlage.csv"
        download="kontakte-vorlage.csv"
        className="kc-btn-primary"
        style={{ textDecoration: 'none' }}
      >
        CSV-Vorlage herunterladen
      </a>
    </div>
  );
}
