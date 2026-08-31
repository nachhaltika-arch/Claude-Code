/**
 * Der Zugangs-Reiter des Betriebsblatts (L-25).
 *
 * Am 2026-08-31 aus `LeadProfile.jsx` herausgeloest — 105 Zeilen. **Der zweite
 * Anlauf.** Am 30.08. ist der erste an der Form gescheitert: Dieser Reiter ist
 * eine sofort aufgerufene Funktion, und ein Schnitt, der `&& (` annimmt,
 * zerreisst sie.
 *
 * Auch der zweite Anlauf brauchte einen Umweg — der Klammernzaehler, der bei
 * `CustomerDetail` traegt, fand hier keine schliessende Klammer. Geschnitten
 * wurde deshalb an den **Zeilen** zwischen zwei Reitermarken, nicht an der
 * Klammer. Wenn zwei Verfahren dasselbe messen sollen und eines aussteigt,
 * ist das Ergebnis des anderen zu pruefen, nicht zu glauben: Der Build und
 * das Oeffnen der Seite stehen hinter diesem Schnitt.
 */
import Card from '../ui/Card';
import Zugaenge from '../betrieb/Zugaenge';
import CredentialsSafe from '../CredentialsSafe';

export default function ReiterZugang({
  lead,
  leadId,
  token,
  isDesktop,
  loadQrCode,
  projectId,
  qrData,
  qrLoading,
  qrRefreshing,
  refreshQrCode,
}) {
      if (!qrData && !qrLoading) { loadQrCode(); }
      return (
        <div style={{ display: 'grid', gridTemplateColumns: isDesktop ? '320px 1fr' : '1fr', gap: 16, alignItems: 'flex-start' }}>
          <Card padding="md">
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>Kunden-Zugang QR-Code</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 16, lineHeight: 1.5 }}>
              Der Kunde scannt diesen Code und gelangt direkt zu seinen Daten.
            </div>
            {qrLoading ? (
              <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
              </div>
            ) : qrData ? (
              <>
                <div style={{ background: 'white', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, textAlign: 'center', marginBottom: 12 }}>
                  <img src={`data:image/png;base64,${qrData.qr_code_base64}`} alt="QR-Code" style={{ width: '100%', maxWidth: 220, height: 'auto', display: 'block', margin: '0 auto' }} />
                  <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, letterSpacing: '0.05em' }}>{lead.company_name?.toUpperCase()}</div>
                </div>
                <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '8px 10px', marginBottom: 12 }}>
                  <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Portal-Link</div>
                  <div style={{ fontSize: 10, color: 'var(--brand-primary-mid)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all', lineHeight: 1.4 }}>{qrData.portal_url}</div>
                </div>
                {lead.email && (
                  <div style={{ background: 'var(--status-info-bg)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: '8px 10px', marginBottom: 12, fontSize: 12, color: 'var(--status-info-text)', lineHeight: 1.5 }}>
                    🔐 Zugang via Domain <strong>@{lead.email.split('@')[1]}</strong>
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                    style={{ flex: 1, padding: 8, background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    ⬇ PNG laden
                  </button>
                  <button onClick={() => navigator.clipboard.writeText(qrData.portal_url)}
                    style={{ flex: 1, padding: 8, background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    📋 Link kopieren
                  </button>
                  <button onClick={refreshQrCode} disabled={qrRefreshing}
                    style={{ padding: '8px 10px', background: 'var(--bg-surface)', color: 'var(--status-danger-text)', border: '1px solid var(--status-danger-bg)', borderRadius: 'var(--radius-md)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                    title="Neuen Code generieren">🔄</button>
                </div>
                <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-tertiary)', textAlign: 'center' }}>Erstellt: {qrData.created_at}</div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-tertiary)', fontSize: 12 }}>QR-Code konnte nicht geladen werden</div>
            )}
          </Card>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Card padding="md">
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>So funktioniert der Kunden-Zugang</div>
              {[
                { icon: '📲', title: 'QR-Code scannen', desc: 'Kunde scannt den Code mit dem Smartphone — kein Login nötig.' },
                { icon: '✉️', title: 'E-Mail-Domain eingeben', desc: `Verifikation über @${lead.email?.split('@')[1] || 'ihredomain.de'}.` },
                { icon: '📊', title: 'Zugang zu Daten', desc: 'Audit-Ergebnisse, Scores und Handlungsempfehlungen.' },
                { icon: '🔒', title: 'Sicher & eindeutig', desc: 'Jeder Code ist einmalig — bei Bedarf neuen erstellen.' },
              ].map(item => (
                <div key={item.icon} style={{ display: 'flex', gap: 12, marginBottom: 14, alignItems: 'flex-start' }}>
                  <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-active)', color: 'var(--brand-primary-mid)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>{item.icon}</div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{item.title}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{item.desc}</div>
                  </div>
                </div>
              ))}
            </Card>
            <Card padding="md">
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>QR-Code versenden</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.6, marginBottom: 12 }}>
                Den QR-Code als PNG herunterladen und dem Kunden per E-Mail oder Brief zusenden.
              </div>
              {lead.email && qrData && (
                <a href={`mailto:${lead.email}?subject=Ihr persönlicher Zugang — KOMPAGNON&body=Sehr geehrte Damen und Herren,%0D%0A%0D%0AIhr persönlicher Kundenlink:%0D%0A${qrData.portal_url}`}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, textDecoration: 'none' }}>
                  ✉️ Per E-Mail senden
                </a>
              )}
            </Card>
            {/* Die Konten dieses Betriebs — seit dem 25.08.2026 koennen es
              * mehrere sein. Der Reiter hiess schon „Zugang"; er zeigte
              * bis dahin nur den QR-Einmallink, nicht die Menschen. */}
            <Zugaenge leadId={leadId} token={token} />

            {/* Der Safe fuer Hosting-, CMS- und Domainzugaenge (26.08.2026,
              * L-95). `CredentialsSafe.jsx` lag seit jeher im Quellbaum und
              * war von niemandem importiert — die Routen dahinter gibt es,
              * verschluesselt, samt `CREDENTIALS_KEY` in der
              * Wiederherstellungspruefung; nur keinen Bildschirm.
              *
              * **Warum hier und nicht im Projektbildschirm:** Dieser Reiter
              * sammelt, was mit Zugang zu tun hat — der Einmallink fuer den
              * Kunden, die Menschen mit Konto, und jetzt die Zugaenge zu
              * fremden Systemen. Drei Richtungen desselben Themas an einer
              * Stelle statt an dreien.
              *
              * Der Safe haengt am **Projekt**; ohne Projekt gibt es nichts
              * zu hinterlegen. */}
            {projectId && (
              <Card>
                <CredentialsSafe projectId={projectId} token={token} />
              </Card>
            )}
          </div>
        </div>
      );
}
