import React from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileSettings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isMobile } = useScreenSize();

  // Siehe MobileLeads: `navigate()` im Render leitet nicht um.
  if (!isMobile) return <Navigate to="/app/settings" replace />;

  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';
  const initials = ((user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')).toUpperCase() || 'U';

  return (
    <div style={{ background: 'var(--bg-app)', minHeight: '100%', paddingBottom: 24 }}>

      {/* User-Card */}
      <div style={{
        background: 'var(--brand-primary)',
        padding: '20px 16px 18px',
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{
          // Der Kreis stand auf --brand-primary — und die Karte darunter
          // ebenfalls: gleiche Farbe auf gleicher Farbe, also unsichtbar. Der
          // Umbau vom 18.08. hat ihn von --kc-mid dorthin gezogen; die Regel
          // „Markenflaeche traegt lesbare Tinte" war richtig, taugt aber
          // nicht, wo eine Flaeche sich von ihrer Nachbarflaeche abheben muss.
          width: 52, height: 52, borderRadius: '50%',
          background: 'var(--bg-surface)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 900, color: 'var(--brand-primary)',
          fontFamily: 'var(--font-sans)',
        }}>
          {initials}
        </div>
        <div>
          <div style={{
            fontSize: 19, fontWeight: 700, color: 'var(--text-on-brand)',
            textTransform: 'uppercase', fontFamily: 'var(--font-sans)',
          }}>
            {user?.first_name} {user?.last_name}
          </div>
          <div style={{
            fontSize: 10, fontWeight: 900, color: 'var(--kc-yellow)',
            textTransform: 'uppercase', letterSpacing: '.1em', marginTop: 2,
          }}>
            {user?.role || 'Nutzer'}
          </div>
        </div>
      </div>

      {/* Account */}
      <HubSectionLabel>Account</HubSectionLabel>
      <HubGrid>
        <HubButton icon="👤" label="Profil"      desc={`${user?.first_name || ''} ${user?.last_name || ''}`} path="/app/settings/profile" />
        <HubButton icon="🔐" label="Sicherheit"  desc="2FA & Passwort"                                       path="/app/settings/security" />
      </HubGrid>

      {isAdmin && (
        <>
          <HubSectionLabel>Team</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🧑‍💼" label="Benutzer" desc="Verwalten" path="/app/settings/users" />
            <HubButton icon="👥"  label="Rollen"    desc="Rechte je Rolle"  path="/app/settings/roles" />
          </HubGrid>

          <HubSectionLabel>System</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🔑" label="API-Keys"     desc="Konfigurieren"  path="/app/settings/system" />
            <HubButton icon="🌐" label="KAS Website"   desc="Seiten & Inhalte" path="/app/settings/kas-website" />
            <HubButton icon="🗂️" label="Templates"     desc="Vorlagen"       path="/app/settings/templates" />
            <HubButton icon="💳" label="Abonnement"    desc="Zahlung & Paket"   path="/app/settings/subscription" />
          </HubGrid>

          <HubSectionLabel>Produkt</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🛠️" label="Produktentw."  desc="Roadmap-Board"   path="/app/product" />
            <HubButton icon="✏️" label="Produkteditor"  desc="Pakete & Preise" path="/app/product-editor" />
          </HubGrid>
        </>
      )}

      <HubSectionLabel>Benachrichtigungen</HubSectionLabel>
      <div style={{ padding: '0 12px 10px' }}>
        <HubButton icon="🔔" label="Benachrichtigungen" desc="Einstellungen" path="/app/settings/notifications" />
      </div>

      {/* Abmelden */}
      <div style={{ padding: '4px 12px 8px' }}>
        <button
          onClick={() => { logout(); navigate('/'); }}
          style={{
            width: '100%', padding: '14px', border: 'none',
            background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)',
            borderRadius: 12, fontSize: 13, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
          }}
        >
          Abmelden
        </button>
      </div>
    </div>
  );
}
