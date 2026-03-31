import React, { useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';

const N = '#0F1E3A';

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
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: N, marginBottom: 8 }}>Massen-Export</h1>
      <p style={{ color: '#4a5a7a', fontSize: 14, marginBottom: 24 }}>Alle Leads als CSV-Datei exportieren.</p>

      <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #eef0f8', padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: N, marginBottom: 8 }}>Lead-Export (CSV)</div>
        <p style={{ fontSize: 13, color: '#4a5a7a', marginBottom: 16 }}>
          Exportiert alle Leads mit Firmenname, Kontakt, Telefon, E-Mail, Website, Stadt, Gewerk, Status, Score und Quelle.
          Semikolon-getrennt, UTF-8 mit BOM.
        </p>
        <button onClick={exportCSV} disabled={exporting} style={{
          background: N, color: '#fff', border: 'none', borderRadius: 8, padding: '10px 24px',
          fontSize: 14, fontWeight: 700, cursor: exporting ? 'not-allowed' : 'pointer', minHeight: 44, opacity: exporting ? 0.6 : 1,
        }}>
          {exporting ? 'Wird exportiert...' : 'CSV herunterladen'}
        </button>
      </div>
    </div>
  );
}
