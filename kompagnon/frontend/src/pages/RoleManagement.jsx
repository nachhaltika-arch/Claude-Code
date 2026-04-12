import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
import { apiCall } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';



const ROLE_META = {
  superadmin: { icon: '⚡', label: 'Superadmin', desc: 'Systemkritische Aktionen, KAS-Deploy', locked: true, bg: '#7c3aed', fg: '#fff' },
  admin: { icon: '👑', label: 'Admin', desc: 'Vollstaendige Systemrechte', locked: true, bg: 'var(--text-primary)', fg: '#fff' },
  auditor: { icon: '🔍', label: 'Auditor', desc: 'Zugriff auf Audit-Funktionen', locked: false, bg: '#2a5aa0', fg: '#fff' },
  nutzer: { icon: '👤', label: 'Nutzer', desc: 'Eingeschraenkter Zugriff', locked: false, bg: '#4a5a7a', fg: '#fff' },
  kunde: { icon: '🏢', label: 'Kunde', desc: 'Nur eigene Daten & Leistungen', locked: false, bg: '#2a7a3a', fg: '#fff' },
};

const PERM_LABELS = {
  view_dashboard: 'Dashboard einsehen',
  view_leads: 'Leads einsehen',
  create_leads: 'Leads erstellen',
  edit_leads: 'Leads bearbeiten',
  delete_leads: 'Leads loeschen',
  view_audits: 'Audits einsehen',
  create_audits: 'Audits erstellen',
  download_pdf: 'PDFs herunterladen',
  view_projects: 'Projekte einsehen',
  manage_projects: 'Projekte verwalten',
  view_users: 'Nutzer einsehen',
  manage_users: 'Nutzer verwalten',
  view_settings: 'Einstellungen sehen',
  manage_settings: 'Einstellungen aendern',
  view_billing: 'Rechnungen einsehen',
  manage_billing: 'Abonnement verwalten',
  deploy_kas_pages: 'KAS-Seiten live deployen',
  manage_system_settings: 'Systemkritische Einstellungen aendern',
};

export default function RoleManagement() {
  const { isMobile } = useScreenSize();
  const [roles, setRoles] = useState({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // role key
  const [editPerms, setEditPerms] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadRoles(); }, []);

  const loadRoles = async () => {
    setLoading(true);
    try {
      const res = await apiCall('/api/admin/roles');
      if (res.ok) setRoles(await res.json());
    } catch (e) { toast.error('Rollen konnten nicht geladen werden'); }
    finally { setLoading(false); }
  };

  const openEdit = (role) => {
    setEditing(role);
    setEditPerms({ ...roles[role] });
  };

  const savePerms = async () => {
    setSaving(true);
    try {
      const res = await apiCall(`/api/admin/roles/${editing}`, { method: 'PATCH', body: JSON.stringify({ permissions: editPerms }) });
      if (res.ok) {
        toast.success(`Berechtigungen fuer ${ROLE_META[editing]?.label} gespeichert`);
        setEditing(null);
        loadRoles();
      } else toast.error((await res.json()).detail || 'Fehler');
    } finally { setSaving(false); }
  };

  if (loading) return <div style={{ padding: 20, color: 'var(--text-secondary)' }}>Laden...</div>;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 4px' }}>Rollenverwaltung</h2>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>Definieren Sie Berechtigungen pro Rolle</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 16 }}>
        {Object.entries(ROLE_META).map(([key, meta]) => {
          const perms = roles[key] || {};
          return (
            <div key={key} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', overflow: 'hidden' }}>
              {/* Header */}
              <div style={{ background: meta.bg, color: meta.fg, padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 800 }}>{meta.icon} {meta.label}</div>
                  <div style={{ fontSize: 12, opacity: 0.8, marginTop: 2 }}>{meta.desc}</div>
                </div>
                {!meta.locked && (
                  <button onClick={() => openEdit(key)} style={{
                    background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 6,
                    color: '#fff', padding: '6px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  }}>
                    Bearbeiten
                  </button>
                )}
              </div>
              {/* Permissions list */}
              <div style={{ padding: '14px 18px' }}>
                {Object.entries(PERM_LABELS).map(([perm, label]) => {
                  const allowed = perms[perm] !== false;
                  return (
                    <div key={perm} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', fontSize: 13 }}>
                      <span style={{ color: allowed ? 'var(--status-success-text)' : 'var(--border-strong)', fontWeight: 700, width: 16 }}>{allowed ? '✓' : '—'}</span>
                      <span style={{ color: allowed ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{label}</span>
                    </div>
                  );
                })}
                {meta.locked && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8, fontStyle: 'italic' }}>Systemrolle — nicht editierbar</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Edit Modal */}
      {editing && createPortal(
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={(e) => { if (e.target === e.currentTarget) setEditing(null); }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 440, width: '100%', maxHeight: '80vh', overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 4px', fontSize: 18, color: 'var(--text-primary)' }}>
              {ROLE_META[editing]?.icon} {ROLE_META[editing]?.label} — Berechtigungen
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 20px' }}>Aktivieren oder deaktivieren Sie einzelne Berechtigungen</p>

            {Object.entries(PERM_LABELS).map(([perm, label]) => (
              <label key={perm} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 0', borderBottom: '1px solid var(--border-light)', cursor: 'pointer', fontSize: 14,
              }}>
                <span style={{ color: 'var(--text-primary)' }}>{label}</span>
                <input type="checkbox" checked={editPerms[perm] !== false}
                  onChange={(e) => setEditPerms((p) => ({ ...p, [perm]: e.target.checked }))}
                  style={{ width: 18, height: 18 }} />
              </label>
            ))}

            <div style={{ display: 'flex', gap: 8, marginTop: 20 }}>
              <button onClick={savePerms} disabled={saving} style={{
                flex: 1, background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                padding: '10px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44,
                opacity: saving ? 0.6 : 1,
              }}>
                {saving ? 'Speichern...' : 'Berechtigungen speichern'}
              </button>
              <button onClick={() => setEditing(null)} style={{
                background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)',
                padding: '10px 16px', fontSize: 14, cursor: 'pointer', minHeight: 44,
              }}>
                Abbrechen
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
