import React, { useState, useEffect } from 'react';
import ModalSheet from '../components/ui/ModalSheet';
import toast from 'react-hot-toast';
import { parseApiError } from '../utils/apiError';
import { apiCall, useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import GeheimnisZeigen from '../components/ui/GeheimnisZeigen';



// Die alten Namen `auditor` und `nutzer` stehen hier weiter drin, obwohl
// niemand sie mehr vergibt (27.08.2026). Solange ein Konto im Bestand noch so
// gespeichert ist, soll die Liste es benennen koennen — sonst zeigt sie ein
// leeres Abzeichen und sieht aus wie ein Fehler.
const ROLE_BADGES = {
  superadmin: { bg: '#7c3aed', color: '#fff', label: 'Superadmin' },
  admin: { bg: 'var(--text-primary)', color: '#fff', label: 'Admin' },
  mitarbeiter: { bg: '#2a5aa0', color: '#fff', label: 'Mitarbeiter KOMPAGNON' },
  kunde: { bg: '#2a7a3a', color: '#fff', label: 'Kunde' },
  auditor: { bg: '#4a5a7a', color: '#fff', label: 'Auditor (alt)' },
  nutzer: { bg: '#4a5a7a', color: '#fff', label: 'Nutzer (alt)' },
};

export default function AdminUsers() {
  const { isMobile } = useScreenSize();
  const { isSuperadmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({ email: '', first_name: '', last_name: '', role: 'mitarbeiter', position: '', lead_id: null });
  const [creating, setCreating] = useState(false);
  const [tempPw, setTempPw] = useState('');
  // **Zu wem das Passwort gehoert, gehoert danebengeschrieben.** Wer zwei
  // Zuruecksetzungen hintereinander macht, verwechselt sie sonst.
  const [pwFuer, setPwFuer] = useState('');
  const [betriebe, setBetriebe] = useState([]);

  useEffect(() => { loadUsers(); loadBetriebe(); }, []);

  const loadBetriebe = async () => {
    try {
      const res = await apiCall('/api/admin/betriebe');
      if (res.ok) setBetriebe(await res.json());
    } catch { /* Ohne Liste bleibt die Zuordnung leer statt die Seite kaputt. */ }
  };

  const setzeBetrieb = async (userId, wert) => {
    try {
      const res = await apiCall(`/api/admin/users/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ lead_id: wert ? Number(wert) : null }),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      toast.success(wert ? 'Betrieb zugeordnet' : 'Zuordnung gelöst');
      loadUsers();
    } catch (e) { toast.error(parseApiError(e)); }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await apiCall('/api/admin/users');
      if (res.ok) setUsers(await res.json());
    } catch (e) { toast.error('Benutzerliste konnte nicht geladen werden — bitte Seite neu laden'); }
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
      setPwFuer(data.user.email);
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
      if (res.ok) { toast.success('Benutzer wurde gelöscht'); loadUsers(); }
      else throw new Error((await res.json()).detail);
    } catch (e) { toast.error(parseApiError(e)); }
  };

  const resetPw = async (userId, email) => {
    try {
      const res = await apiCall(`/api/admin/users/${userId}/reset-password`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        // **Kein `alert` mehr** (06.09.2026). Daraus liess sich das Passwort
        // je nach Browser nicht markieren, manche blocken den Dialog ganz,
        // und ein versehentliches „OK" verlor es endgueltig — gespeichert ist
        // nur der Hash. Jetzt steht es in einem Feld mit Kopieren-Knopf.
        setTempPw(data.temp_password);
        setPwFuer(email);
      }
    } catch (e) { toast.error(parseApiError(e)); }
  };

  return (
    <div style={{ width: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>Benutzerverwaltung</h1>
        <button onClick={() => { setShowCreate(true); setTempPw(''); setPwFuer(''); setNewUser({ email: '', first_name: '', last_name: '', role: 'mitarbeiter', position: '', lead_id: null }); }} style={{
          background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 20px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44,
        }}>
          + Neuer Benutzer
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>Laden...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {users.map((u) => {
            const badge = ROLE_BADGES[u.role] || ROLE_BADGES.mitarbeiter;
            return (
              <div key={u.id} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: isMobile ? '12px 14px' : '14px 20px', minHeight: 44,
                display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: 12,
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                    {u.first_name} {u.last_name}
                    {!u.is_active && <span style={{ color: '#c03030', fontSize: 12, marginLeft: 8 }}>(deaktiviert)</span>}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{u.email}</div>
                  {/* **Der Betrieb steht in der Zeile und ist dort aenderbar**
                      (Wunsch David, 06.09.2026). `users.lead_id` entscheidet
                      im Kundenkonto ueber alles — welchen Betrieb jemand
                      sieht, welche Mitwirkung, welche Rechnungen. Ueber die
                      Oberflaeche liess es sich bis heute weder setzen noch
                      aendern; es brauchte einen Datenbankzugriff. */}
                  {u.role === 'kunde' && (
                    <select value={u.lead_id || ''}
                            onChange={(e) => setzeBetrieb(u.id, e.target.value)}
                            aria-label={`Betrieb von ${u.email}`}
                            style={{ marginTop: 6, maxWidth: 280, padding: '5px 8px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: u.lead_id ? 'var(--text-primary)' : 'var(--text-tertiary)', fontSize: 12 }}>
                      <option value="">— kein Betrieb zugeordnet —</option>
                      {betriebe.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                    </select>
                  )}
                </div>
                <span style={{ background: badge.bg, color: badge.color, fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 20 }}>
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
      {/* Nach einem Zuruecksetzen steht das Passwort hier — nicht in einem
          Dialog, den ein Klick wegnimmt. */}
      {tempPw && !showCreate && (
        <GeheimnisZeigen
          titel={`Neues temporäres Passwort für ${pwFuer}`}
          wert={tempPw}
          onSchliessen={() => { setTempPw(''); setPwFuer(''); }}
        />
      )}


      {/* Create User Modal */}
      <ModalSheet open={showCreate} onClose={() => setShowCreate(false)} title={tempPw ? '✓ Benutzer angelegt' : 'Neuen Benutzer anlegen'} maxWidth={440}>
        {tempPw ? (
          <div>
            {/* **Kopierbar statt nur lesbar** (06.09.2026). Der Kasten hier
                zeigte das Passwort nur an; markieren ging, kopieren nicht auf
                Knopfdruck. Dasselbe Bauteil steht jetzt auch oben in der
                Liste, wenn ein Passwort zurueckgesetzt wird. */}
            <GeheimnisZeigen
              titel={`Temporäres Passwort für ${pwFuer}`}
              wert={tempPw}
              onSchliessen={() => { setTempPw(''); setPwFuer(''); setShowCreate(false); }}
            />
            <button onClick={() => { setTempPw(''); setPwFuer(''); setShowCreate(false); }}
                    style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', padding: '11px 22px', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}>
              Fertig
            </button>
          </div>
        ) : (
          <form onSubmit={createUser} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
              <input aria-label="Vorname" value={newUser.first_name} onChange={(e) => setNewUser((f) => ({ ...f, first_name: e.target.value }))} placeholder="Vorname" style={inpStyle} />
              <input aria-label="Nachname" value={newUser.last_name} onChange={(e) => setNewUser((f) => ({ ...f, last_name: e.target.value }))} placeholder="Nachname" style={inpStyle} />
            </div>
            <input aria-label="E-Mail" value={newUser.email} onChange={(e) => setNewUser((f) => ({ ...f, email: e.target.value }))} placeholder="E-Mail" type="email" required style={inpStyle} />
            <select aria-label="Rolle" value={newUser.role} onChange={(e) => setNewUser((f) => ({ ...f, role: e.target.value }))} style={inpStyle}>
              <option value="mitarbeiter">Mitarbeiter KOMPAGNON</option>
              <option value="admin">Admin</option>
              {isSuperadmin && isSuperadmin() && (
                <option value="superadmin">Superadmin</option>
              )}
              <option value="kunde">Kunde</option>
            </select>
            {/* **Der Betrieb gleich beim Anlegen** (06.09.2026). Nur bei
                der Rolle „Kunde": Ein Mitarbeiter gehoert zu KOMPAGNON, nicht
                zu einem Betrieb — die Auswahl dort waere eine Einladung zum
                Fehlgriff. */}
            {newUser.role === 'kunde' && (
              <select aria-label="Betrieb" value={newUser.lead_id || ''}
                      onChange={(e) => setNewUser((f) => ({ ...f, lead_id: e.target.value ? Number(e.target.value) : null }))}
                      style={{ padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontSize: 14 }}>
                <option value="">Betrieb wählen (kann später zugeordnet werden)</option>
                {betriebe.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            )}
            {newUser.role === 'mitarbeiter' && (
              <input aria-label="Position (erscheint im Audit-Bericht)" value={newUser.position} onChange={(e) => setNewUser((f) => ({ ...f, position: e.target.value }))} placeholder="Position (erscheint im Audit-Bericht)" style={inpStyle} />
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" disabled={creating} style={{ flex: 1, background: 'var(--brand-primary)', color: 'var(--text-inverse)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px', fontSize: 14, fontWeight: 700, cursor: 'pointer', minHeight: 44 }}>{creating ? 'Anlegen…' : 'Benutzer anlegen'}</button>
              <button type="button" onClick={() => setShowCreate(false)} style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px 16px', fontSize: 14, cursor: 'pointer', minHeight: 44 }}>Abbrechen</button>
            </div>
          </form>
        )}
      </ModalSheet>
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
      border: 'none', borderRadius: 6, padding: '5px 10px', fontSize: 12, fontWeight: 700, cursor: 'pointer', minHeight: 30,
    }}>
      {label}
    </button>
  );
}
