import React, { useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';



export default function MassExport() {
  const [exporting, setExporting] = useState(false);

  const exportCSV = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/export/csv`);
      if (!res.ok) throw new Error('Export fehlgeschlagen');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads-export-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('CSV-Export heruntergeladen');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ width: '100%', boxSizing: 'border-box' }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Massen-Export</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>Alle Leads als CSV-Datei exportieren.</p>

      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Lead-Export (CSV)</div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Exportiert alle Leads mit Firmenname, Kontakt, Telefon, E-Mail, Website, Stadt, Gewerk, Status, Score und Quelle.
          Semikolon-getrennt, UTF-8 mit BOM.
        </p>
        <button onClick={exportCSV} disabled={exporting} style={{
          background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 24px',
          fontSize: 14, fontWeight: 700, cursor: exporting ? 'not-allowed' : 'pointer', minHeight: 44, opacity: exporting ? 0.6 : 1,
        }}>
          {exporting ? 'Wird exportiert...' : 'CSV herunterladen'}
        </button>
      </div>

      {/* Weitere Exporte */}
      <div style={{ marginTop: 32 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
          Weitere Exporte
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {[
            { icon: '📄', title: 'Angebots-PDF', desc: 'Persönliches Angebot als PDF für den Kunden exportieren', badge: 'Bald verfügbar' },
            { icon: '📊', title: 'Audit-Bericht PDF', desc: 'Vollständiger Homepage Standard Bericht als PDF', badge: 'Bald verfügbar' },
            { icon: '📋', title: 'Lead-Liste Excel', desc: 'Alle Leads mit Kontaktdaten als Excel-Datei', badge: 'Bald verfügbar' },
            { icon: '🌐', title: 'WordPress Theme', desc: 'Fertiges WordPress-Theme aus Kundendaten generieren', badge: 'Bald verfügbar' },
            { icon: '📮', title: 'Serienbrief', desc: 'DIN 5008 Anschreiben für mehrere Leads gleichzeitig', badge: 'Bald verfügbar' },
            { icon: '📈', title: 'Auswertung', desc: 'Score-Entwicklung und Pipeline-Statistiken exportieren', badge: 'Bald verfügbar' },
          ].map((item) => (
            <div key={item.title} style={{ background: 'var(--bg-surface)', border: '1px dashed var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: '18px 16px', opacity: 0.65, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 10, right: 10, background: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)', borderRadius: 'var(--radius-full)', padding: '2px 8px', fontSize: 9, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {item.badge}
              </div>
              <div style={{ fontSize: 28, marginBottom: 10 }}>{item.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 5 }}>{item.title}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
