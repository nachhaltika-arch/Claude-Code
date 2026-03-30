import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  HomeIcon,
  UserGroupIcon,
  FolderIcon,
  ClipboardDocumentListIcon,
  UserIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

const menuItems = [
  { name: 'Dashboard', path: '/app/dashboard', icon: HomeIcon },
  { name: 'Lead Pipeline', path: '/app/leads', icon: UserGroupIcon },
  { name: 'Projekte', path: '/app/projects', icon: FolderIcon },
  { name: 'Checklisten', path: '/app/checklists', icon: ClipboardDocumentListIcon },
  { name: 'Website Audit', path: '/app/audit', icon: MagnifyingGlassCircleIcon },
  { name: 'Kontakt-Import', path: '/app/import', icon: ArrowUpTrayIcon },
  { name: 'Kunden', path: '/app/customers', icon: UserIcon },
  { name: 'Einstellungen', path: '/app/settings', icon: Cog6ToothIcon },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <aside style={{ width: '200px', flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
      <nav className="kc-card" style={{ padding: 'var(--kc-space-3)', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <div style={{ marginBottom: 'var(--kc-space-3)', padding: '0 var(--kc-space-3)' }}>
          <span className="kc-eyebrow" style={{ marginBottom: 0 }}>Navigation</span>
        </div>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'flex', alignItems: 'center', gap: 'var(--kc-space-3)',
                padding: 'var(--kc-space-2) var(--kc-space-3)', borderRadius: 'var(--kc-radius-md)',
                fontWeight: isActive ? 700 : 500, fontSize: 'var(--kc-text-sm)', textDecoration: 'none',
                color: isActive ? 'var(--kc-rot)' : 'var(--kc-text-sekundaer)',
                background: isActive ? 'var(--kc-rot-subtle)' : 'transparent',
                transition: 'all var(--kc-transition-fast)',
                borderLeft: isActive ? '3px solid var(--kc-rot)' : '3px solid transparent',
              }}
            >
              <Icon style={{ width: '18px', height: '18px' }} />
              {item.name}
            </Link>
          );
        })}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* User info + Logout */}
        <div style={{ borderTop: '1px solid var(--kc-rand)', paddingTop: 'var(--kc-space-3)', marginTop: 'var(--kc-space-3)' }}>
          {user && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '6px var(--kc-space-3)', marginBottom: 'var(--kc-space-2)',
            }}>
              <div style={{
                width: 30, height: 30, borderRadius: '50%', background: '#D4A017',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: '#0F1E3A', flexShrink: 0,
              }}>
                {user.first_name?.[0] || 'U'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--kc-text-primaer)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user.first_name} {user.last_name}
                </div>
                <div style={{ fontSize: 10, color: 'var(--kc-mittel)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user.email}
                </div>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px var(--kc-space-3)', borderRadius: 'var(--kc-radius-md)',
              cursor: 'pointer', color: '#e74c3c', fontSize: 'var(--kc-text-sm)', fontWeight: 600,
              background: 'rgba(231,76,60,0.08)', border: 'none', textAlign: 'left',
            }}
          >
            Abmelden
          </button>
        </div>
      </nav>
    </aside>
  );
}
