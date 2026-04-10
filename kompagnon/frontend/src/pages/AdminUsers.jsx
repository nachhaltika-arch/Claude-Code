import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
import { parseApiError } from '../utils/apiError';
import { apiCall } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';



const ROLE_BADGES = {
  admin: { bg: 'var(--text-primary)', color: '#fff', label: 'Admin' },
  auditor: { bg: '#2a5aa0', color: '#fff', label: 'Auditor' },
  nutzer: { bg: '#4a5a7a', color: '#fff', label: 'Nutzer' },
  kunde: { bg: '#2a7a3a', color: '#fff', label: 'Kunde' },
};

export default function AdminUsers() {
  const { isMobile } = useScreenSize();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', first_name: '', last_name: '', role: 'nutzer', position: '' });
  const [creating, setCreating] = useState(false);
  const [tempPw, setTempPw] = useState('');

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await apiCall('/api/admin/users');
      if (res.ok) setUsers(await res.json());
    } catch (e) { toast.error('Benutzer konnten nicht geladen werden'); }
    finally { setLoading(false); }
  };

  const createUser = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await apiCall('/api/admin/users', { method: 'POST', body: JSON.stringify(newUser) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setTempPw(data.temp_password);
      toast.success(`Benutzer ${data.user.email} angelegt`);
      loadUsers();
    } catch (e) { toast.error(parseApiError(e)); }
    finally { setCreating(false); }
  };

  const toggleActive = async (userId, isActive) => {
    try {
      await apiCall(`/api/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify({ is_active: !isActive }) });
      loadUsers();
    } catch (e) { toast.error(parseApiError(e)); }
  };

  const deleteUser = async (userId, email) => {
    if (!window.confirm(`Benutzer ${email} wirklich loeschen?`)) return;
    try {
      const res = await apiCall(`/api/admin/users/${userId}`, { method: 'DELETE' });
      if (res.ok) { toast.success('Geloescht'); loadUsers(); }
      else throw new Error((await res.json()).detail);
    } catch (e) { toast.error(parseApiError(e)); }
  };

  const resetPw = async (userId, email) => {
    try {
      const res = await apiCall(`/api/admin/users/${userId}/reset-password`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Neues Passwort: ${data.temp_password}`);
        alert(`Neues temporaeres Passwort fuer ${email}:\n\n${data.temp_password}\n\nBitte sicher weitergeben.`);
      }
    } catch (e) { toast.error(parseApiError(e)); }
  };

  return (
    <div style={{ width: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>Benutzerverwaltung</h1>
        <button onClick={() => { setShowCreate(true); setTempPw(''); setNewUser({ email: '', first_name: '', last_name: '', role: 'nutzer', position: '' }); }} style={{
          background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44,
        }}>
          + Neuer Benutzer
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Laden...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {users.map((u) => {
            const badge = ROLE_BADGES[u.role] || ROLE_BADGES.nutzer;
            return (
              <div key={u.id} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: isMobile ? '12px 14px' : '14px 20px', minHeight: 44,
                display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: 12,
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                    {u.first_name} {u.last_name}
                    {!u.is_active && <span style={{ color: '#c03030', fontSize: 11, marginLeft: 8 }}>(deaktiviert)</span>}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{u.email}</div>
                </div>
                <span style={{ background: badge.bg, color: badge.color, fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 20 }}>
                  {badge.label}
                </span>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <SmallBtn onClick={() => toggleActive(u.id, u.is_active)} label={u.is_active ? 'Deaktivieren' : 'Aktivieren'} />
                  <SmallBtn onClick={() => resetPw(u.id, u.email)} label="PW Reset" />
                  <SmallBtn onClick={() => deleteUser(u.id, u.email)} label="X" danger />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create User Modal */}
      {showCreate && createPortal(
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowCreate(false); }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: '28px 32px', maxWidth: 440, width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 20 }}>Neuen Benutzer anlegen</h3>
            {tempPw ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 14, color: 'var(--status-success-text)', fontWeight: 700, marginBottom: 12 }}>Benutzer angelegt!</div>
                <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: 16, fontSize: 16, fontFamily: 'monospace', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
                  {tempPw}
                </div>
                <p style={{ fontSize: 12, color: '#c07820' }}>Bitte dieses temporaere Passwort sicher weitergeben.</p>
                <button onClick={() => setShowCreate(false)} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 24px', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 12, minHeight: 44 }}>
                  Schliessen
                </button>
              </div>
            ) : (
              <form onSubmit={createUser} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                  <input value={newUser.first_name} onChange={(e) => setNewUser((f) => ({ ...f, first_name: e.target.value }))} placeholder="Vorname" style={inpStyle} />
                  <input value={newUser.last_name} onChange={(e) => setNewUser((f) => ({ ...f, last_name: e.target.value }))} placeholder="Nachname" style={inpStyle} />
                </div>
                <input value={newUser.email} onChange={(e) => setNewUser((f) => ({ ...f, email: e.target.value }))} placeholder="E-Mail" type="email" required style={inpStyle} />
                <select value={newUser.role} onChange={(e) => setNewUser((f) => ({ ...f, role: e.target.value }))} style={inpStyle}>
                  <option value="nutzer">Nutzer</option>
                  <option value="auditor">Auditor</option>
                  <option value="admin">Admin</option>
                  <option value="kunde">Kunde</option>
                </select>
                {newUser.role === 'auditor' && (
                  <input value={newUser.position} onChange={(e) => setNewUser((f) => ({ ...f, position: e.target.value }))} placeholder="Position (z.B. Senior Auditor)" style={inpStyle} />
                )}
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button type="submit" disabled={creating} style={{ flex: 1, background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>
                    {creating ? 'Anlegen...' : 'Benutzer anlegen'}
                  </button>
                  <button type="button" onClick={() => setShowCreate(false)} style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 16px', fontSize: 14, cursor: 'pointer', minHeight: 44 }}>
                    Abbrechen
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

const inpStyle = {
  width: '100%', padding: '10px 12px',
  border: '1px solid var(--border-medium)',
  borderRadius: 'var(--radius-md)', fontSize: 16,
  boxSizing: 'border-box',
  background: 'var(--bg-elevated)',
  color: 'var(--text-primary)',
};

function SmallBtn({ onClick, label, danger }) {
  return (
    <button onClick={onClick} style={{
      background: danger ? 'var(--status-danger-bg)' : 'var(--bg-app)',
      color: danger ? 'var(--status-danger-text)' : 'var(--text-primary)',
      border: 'none', borderRadius: 6, padding: '5px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer', minHeight: 30,
    }}>
      {label}
    </button>
  );
}
