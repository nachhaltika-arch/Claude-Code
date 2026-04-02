import React, { useState } from 'react';

const SECURITY_CHECKS = [
  {
    area: 'Grundschutz', icon: '🔐', color: '#0369a1', bg: '#f0f9ff',
    items: [
      { id: 'ssl', label: 'SSL-Zertifikat (HTTPS)', desc: 'Verschluesselte Datenuebertragung — ohne SSL stuft Google die Seite als nicht sicher ein', tool: "Let's Encrypt", cost: 'Kostenlos', critical: true, auditField: 'si_ssl', maxScore: 3 },
      { id: 'passwords', label: 'Sichere Passwoerter & 2FA', desc: 'Min. 16 Zeichen + Zwei-Faktor-Authentifizierung. Brute-Force-Schutz.', tool: 'Bitwarden', cost: 'Kostenlos', critical: true, auditField: null, maxScore: null },
      { id: 'updates', label: 'WordPress & Plugins aktuell', desc: 'Veraltete Versionen haben bekannte Sicherheitsluecken die automatisch ausgenutzt werden', tool: 'Auto-Update', cost: 'Kostenlos', critical: true, auditField: null, maxScore: null },
    ],
  },
  {
    area: 'Zugangskontrolle', icon: '🧱', color: '#7c3aed', bg: '#faf5ff',
    items: [
      { id: 'login_url', label: 'Login-URL aendern', desc: 'Standard /wp-admin ist oeffentlich bekannt — umbenennen verhindert automatische Angriffe', tool: 'WPS Hide Login', cost: 'Kostenlos', critical: false, auditField: null, maxScore: null },
      { id: 'login_limit', label: 'Login-Versuche begrenzen', desc: 'Nach 3-5 falschen Versuchen wird die IP gesperrt — verhindert Brute-Force', tool: 'Limit Login Attempts', cost: 'Kostenlos', critical: true, auditField: null, maxScore: null },
      { id: 'user_roles', label: 'Benutzerrollen richtig vergeben', desc: 'Nur wer Admin sein muss bekommt Admin-Rechte. Grundsatz: so wenig wie moeglich.', tool: 'WordPress Rollen', cost: 'Kostenlos', critical: false, auditField: null, maxScore: null },
    ],
  },
  {
    area: 'Aktiver Schutz', icon: '🛡️', color: '#059669', bg: 'var(--status-success-bg)',
    items: [
      { id: 'waf', label: 'Web Application Firewall (WAF)', desc: 'Filtert boesartige Anfragen wie SQL-Injection bevor sie die Website erreichen', tool: 'Cloudflare', cost: 'Kostenlos', critical: true, auditField: 'si_header', maxScore: 3 },
      { id: 'security_plugin', label: 'Sicherheits-Plugin & Malware-Scan', desc: 'Scannt taeglich auf Schadsoftware und blockiert bekannte Angreifer automatisch', tool: 'Wordfence', cost: 'Kostenlos', critical: false, auditField: 'si_header', maxScore: 3 },
      { id: 'file_upload', label: 'Datei-Uploads eingeschraenkt', desc: 'Nur JPG, PDF, PNG erlauben — verhindert dass Schadcode hochgeladen wird', tool: 'WordPress Config', cost: 'Kostenlos', critical: false, auditField: 'si_formulare', maxScore: 1 },
    ],
  },
  {
    area: 'Backups', icon: '💾', color: '#d97706', bg: 'var(--status-warning-bg)',
    items: [
      { id: 'auto_backup', label: 'Taegliches automatisches Backup', desc: 'Backup ausserhalb des Servers speichern (Google Drive, Dropbox). Letzte Verteidigungslinie.', tool: 'UpdraftPlus', cost: 'Kostenlos', critical: true, auditField: 'ho_backup', maxScore: 3 },
      { id: 'hosting_backup', label: 'Hosting mit Backup-Infrastruktur', desc: 'Nur Hoster waehlen die taegliche Server-Backups inkludieren', tool: 'Raidboxes / All-Inkl.', cost: 'Im Hosting enthalten', critical: true, auditField: 'ho_backup', maxScore: 3 },
    ],
  },
];

function getStatus(field, data, max) {
  if (!field || !data) return 'unknown';
  const score = data[field];
  if (score == null) return 'unknown';
  const pct = score / max;
  if (pct >= 0.8) return 'ok';
  if (pct >= 0.4) return 'partial';
  return 'missing';
}

const S = {
  ok: { icon: '✓', color: '#059669', bg: 'var(--status-success-bg)', label: 'Umgesetzt' },
  partial: { icon: '~', color: '#d97706', bg: 'var(--status-warning-bg)', label: 'Teilweise' },
  missing: { icon: '✗', color: '#dc2626', bg: 'var(--status-danger-bg)', label: 'Fehlt' },
  unknown: { icon: '?', color: 'var(--text-tertiary)', bg: 'var(--status-neutral-bg)', label: 'Nicht geprueft' },
};

export default function SecurityChecklist({ auditData }) {
  const [openArea, setOpenArea] = useState(null);

  const totalItems = SECURITY_CHECKS.reduce((s, a) => s + a.items.length, 0);
  const okItems = SECURITY_CHECKS.reduce((s, a) => s + a.items.filter((i) => getStatus(i.auditField, auditData, i.maxScore) === 'ok').length, 0);
  const criticalMissing = SECURITY_CHECKS.reduce((s, a) => s + a.items.filter((i) => i.critical && getStatus(i.auditField, auditData, i.maxScore) === 'missing').length, 0);

  return (
    <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', overflow: 'hidden', marginBottom: 20 }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Website-Sicherheit</div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{auditData ? `${okItems} von ${totalItems} Massnahmen umgesetzt` : 'Noch kein Audit durchgefuehrt'}</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {criticalMissing > 0 && <span style={{ background: 'var(--status-danger-bg)', color: '#dc2626', borderRadius: 20, padding: '4px 10px', fontSize: 11, fontWeight: 700 }}>{criticalMissing} kritisch</span>}
          {auditData && okItems > 0 && <span style={{ background: 'var(--status-success-bg)', color: '#059669', borderRadius: 20, padding: '4px 10px', fontSize: 11, fontWeight: 700 }}>{okItems} umgesetzt</span>}
        </div>
      </div>

      {/* Areas */}
      {SECURITY_CHECKS.map((area) => {
        const isOpen = openArea === area.area;
        const areaOk = area.items.filter((i) => getStatus(i.auditField, auditData, i.maxScore) === 'ok').length;
        return (
          <div key={area.area}>
            <button onClick={() => setOpenArea(isOpen ? null : area.area)} style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 20px',
              background: isOpen ? area.bg : 'var(--bg-surface)', border: 'none', borderBottom: '1px solid var(--border-light)', cursor: 'pointer', textAlign: 'left',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18 }}>{area.icon}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: area.color }}>{area.area}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{areaOk}/{area.items.length} umgesetzt</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 60, height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: `${(areaOk / area.items.length) * 100}%`, height: '100%', background: area.color, borderRadius: 2 }} />
                </div>
                <span style={{ color: 'var(--text-tertiary)', fontSize: 12, transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'none' }}>▼</span>
              </div>
            </button>
            {isOpen && (
              <div style={{ borderBottom: '1px solid var(--border-light)' }}>
                {area.items.map((item, idx) => {
                  const status = getStatus(item.auditField, auditData, item.maxScore);
                  const cfg = S[status];
                  return (
                    <div key={item.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 20px', background: idx % 2 === 0 ? 'var(--bg-elevated)' : 'var(--bg-surface)', borderTop: idx > 0 ? '1px solid var(--border-light)' : 'none' }}>
                      <div style={{ width: 28, height: 28, borderRadius: '50%', background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 900, color: cfg.color, flexShrink: 0 }}>{cfg.icon}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3, flexWrap: 'wrap' }}>
                          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{item.label}</span>
                          {item.critical && <span style={{ fontSize: 10, fontWeight: 700, color: '#dc2626', background: 'var(--status-danger-bg)', padding: '1px 6px', borderRadius: 4 }}>KRITISCH</span>}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.4, marginBottom: 6 }}>{item.desc}</div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <span style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'var(--bg-hover)', padding: '2px 7px', borderRadius: 4, fontWeight: 600 }}>{item.tool}</span>
                          <span style={{ fontSize: 11, color: '#059669', background: 'var(--status-success-bg)', padding: '2px 7px', borderRadius: 4 }}>{item.cost}</span>
                        </div>
                      </div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: cfg.color, background: cfg.bg, padding: '3px 8px', borderRadius: 6, flexShrink: 0, whiteSpace: 'nowrap' }}>{cfg.label}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      <div style={{ padding: '12px 20px', background: 'var(--bg-app)', fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
        <span>ℹ️</span> Basierend auf BSI Grundschutz, DSGVO Art. 32 und OWASP Top 10. Stand: 2025.
      </div>
    </div>
  );
}
