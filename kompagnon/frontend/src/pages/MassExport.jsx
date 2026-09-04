import React, { useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import AuditExportWahl from '../components/AuditExportWahl';
import { useAuth } from '../context/AuthContext';

/**
 * Die weiteren Exporte — und welche davon es wirklich gibt.
 *
 * **Nachgemessen am 29.08.2026 (BUCH-12, FIX-3).** Hier trugen **alle sechs**
 * Kacheln „Bald verfügbar". Zwei davon gab es längst und wurden im
 * Auditwerkzeug produktiv benutzt; BUCH-12 nannte nur eine von beiden. Eine
 * Funktion nicht anzubieten, die man hat, ist verschenkter Nutzen — und lässt
 * das Werkzeug unfertiger wirken, als es ist.
 *
 * **Die anderen vier bleiben markiert, weil sie wirklich fehlen:** Für Excel,
 * WordPress-Theme, Serienbrief und Auswertung gibt es keinen Endpunkt —
 * gesucht wurde nach dem, was **aufruft**, nicht nach dem Wort.
 *
 * `art` verbindet die Kachel mit `AuditExportWahl`; `null` heißt „gibt es
 * noch nicht".
 */
const EXPORTE = [
  { icon: '📄', title: 'Angebots-PDF', art: 'angebot',
    desc: 'Persönliches Angebot als PDF für den Kunden exportieren' },
  { icon: '📊', title: 'Audit-Bericht PDF', art: 'pdf',
    desc: 'Vollständiger Homepage Standard Bericht als PDF' },
  { icon: '📋', title: 'Lead-Liste Excel', art: null,
    desc: 'Alle Leads mit Kontaktdaten als Excel-Datei' },
  { icon: '🌐', title: 'WordPress Theme', art: null,
    desc: 'Fertiges WordPress-Theme aus Kundendaten generieren' },
  { icon: '📮', title: 'Serienbrief', art: null,
    desc: 'DIN 5008 Anschreiben für mehrere Leads gleichzeitig' },
  { icon: '📈', title: 'Auswertung', art: null,
    desc: 'Score-Entwicklung und Pipeline-Statistiken exportieren' },
];

export default function MassExport() {
  const [exporting, setExporting] = useState(false);
  const [wahl, setWahl] = useState(null);
  const { token } = useAuth();
  const h = { Authorization: `Bearer ${token}` };

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
      <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Massen-Export</h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>Alle Leads als CSV-Datei exportieren.</p>

      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Lead-Export (CSV)</div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Exportiert alle Leads mit Firmenname, Kontakt, Telefon, E-Mail, Website, Stadt, Gewerk, Status, Score und Quelle.
          Semikolon-getrennt, UTF-8 mit BOM.
        </p>
        <button onClick={exportCSV} disabled={exporting} style={{
          background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 24px',
          fontSize: 14, fontWeight: 700, cursor: exporting ? 'not-allowed' : 'pointer', minHeight: 44, opacity: exporting ? 0.6 : 1,
        }}>
          {exporting ? 'Wird exportiert...' : 'CSV herunterladen'}
        </button>
      </div>

      {/* Weitere Exporte */}
      <div style={{ marginTop: 32 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
          Weitere Exporte
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {EXPORTE.map((item) => {
            const vorhanden = Boolean(item.art);
            const inhalt = (
              <>
                {!vorhanden && (
                  <div style={{ position: 'absolute', top: 10, right: 10, background: 'var(--status-neutral-bg)', color: 'var(--status-neutral-text)', borderRadius: 'var(--radius-full)', padding: '2px 8px', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Bald verfügbar
                  </div>
                )}
                <div style={{ fontSize: 28, marginBottom: 10 }}>{item.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 5 }}>{item.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{item.desc}</div>
              </>
            );
            const flaeche = {
              background: 'var(--bg-surface)',
              border: vorhanden ? '1px solid var(--border-light)' : '1px dashed var(--border-medium)',
              borderRadius: 'var(--radius-lg)', padding: '18px 16px',
              opacity: vorhanden ? 1 : 0.65,
              position: 'relative', overflow: 'hidden',
            };

            // Vorhandene Kacheln sind Schaltflaechen, keine Kaesten: Sie sind
            // mit der Tastatur erreichbar und tragen einen lesbaren Namen.
            return vorhanden ? (
              <button key={item.title} type="button"
                      onClick={() => setWahl(item.art)}
                      style={{ ...flaeche, textAlign: 'left', cursor: 'pointer', font: 'inherit', minHeight: 44 }}>
                {inhalt}
              </button>
            ) : (
              <div key={item.title} style={flaeche}>{inhalt}</div>
            );
          })}
        </div>

        {wahl && (
          <AuditExportWahl art={wahl} kopfzeilen={h}
                           onSchliessen={() => setWahl(null)} />
        )}
      </div>
    </div>
  );
}
