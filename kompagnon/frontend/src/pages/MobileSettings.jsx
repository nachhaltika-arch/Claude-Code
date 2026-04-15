import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import { HubGrid, HubButton, HubSectionLabel } from '../components/MobileHub';

export default function MobileSettings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isMobile } = useScreenSize();

  useEffect(() => {
    if (!isMobile) navigate('/app/settings', { replace: true });
  }, [isMobile, navigate]);

  if (!isMobile) return null;

  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin';

  return (
    <div style={{ background: '#F0F4F5', minHeight: '100%', fontFamily: 'var(--font-sans)' }}>

      {/* User-Card */}
      <div style={{
        background: '#004F59',
        padding: '20px 16px 18px',
        display: 'flex', alignItems: 'center', gap: 14,
      }}>
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: '#008EAA',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 900, color: '#fff',
          fontFamily: 'var(--font-sans)',
          flexShrink: 0,
        }}>
          {((user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')) || 'U'}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{
            fontFamily: "'Barlow Condensed', var(--font-sans)",
            fontSize: 19, fontWeight: 700, color: '#fff',
            textTransform: 'uppercase',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {user?.first_name} {user?.last_name}
          </div>
          <div style={{
            fontSize: 10, fontWeight: 900, color: '#FAE600',
            textTransform: 'uppercase', letterSpacing: '.1em',
            marginTop: 2,
          }}>
            {user?.role || 'Nutzer'}
          </div>
        </div>
      </div>

      {/* Account */}
      <HubSectionLabel>Account</HubSectionLabel>
      <HubGrid>
        <HubButton icon="👤" label="Profil"     desc={`${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'Anzeigen'} path="/app/settings/profile" />
        <HubButton icon="🔐" label="Sicherheit" desc="2FA & Passwort" path="/app/settings/security" />
      </HubGrid>

      {/* Team — nur Admin */}
      {isAdmin && (
        <>
          <HubSectionLabel>Team</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🧑‍💼" label="Benutzer" desc="Verwalten" path="/app/settings/users" />
            <HubButton icon="👥"  label="Rollen"   desc="5 Rollen"  path="/app/settings/roles" />
          </HubGrid>
        </>
      )}

      {/* System — nur Admin */}
      {isAdmin && (
        <>
          <HubSectionLabel>System</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🔑"  label="API-Keys"   desc="Konfigurieren" path="/app/settings/system" />
            <HubButton icon="🌐"  label="KAS Website" desc="2 Seiten live" path="/app/settings/kas-website" />
            <HubButton icon="🗂️"  label="Templates"   desc="Vorlagen"      path="/app/settings/templates" />
            <HubButton icon="💳"  label="Abonnement"  desc="Professional"  path="/app/settings/subscription" />
          </HubGrid>
        </>
      )}

      {/* Produkt — nur Admin */}
      {isAdmin && (
        <>
          <HubSectionLabel>Produkt</HubSectionLabel>
          <HubGrid>
            <HubButton icon="🛠️" label="Produktentw."  desc="Roadmap-Board"   path="/app/product" />
            <HubButton icon="✏️" label="Produkteditor" desc="Pakete & Preise" path="/app/product-editor" />
          </HubGrid>
        </>
      )}

      {/* Benachrichtigungen — voll-breit, weil einzeln */}
      <HubSectionLabel>Benachrichtigungen</HubSectionLabel>
      <div style={{ padding: '0 12px 12px' }}>
        <HubButton icon="🔔" label="Benachrichtigungen" desc="Einstellungen" path="/app/settings/notifications" />
      </div>

      {/* Abmelden */}
      <div style={{ padding: '4px 12px 24px' }}>
        <button
          onClick={() => { logout(); navigate('/'); }}
          style={{
            width: '100%', padding: '14px', border: 'none',
            background: '#FDECEA', color: '#C0392B',
            borderRadius: 12, fontSize: 13, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            textTransform: 'uppercase', letterSpacing: '.04em',
          }}
        >
          Abmelden
        </button>
      </div>
    </div>
  );
}
