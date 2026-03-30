import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/app/dashboard', icon: '📊' },
  { label: 'Lead Pipeline', path: '/app/leads', icon: '👥', roles: ['admin', 'auditor'] },
  { label: 'Website Audit', path: '/app/audit', icon: '🔍' },
  { label: 'Kontakt-Import', path: '/app/import', icon: '📥', roles: ['admin', 'auditor'] },
  { label: 'Kunden', path: '/app/customers', icon: '👤' },
  { label: 'Projekte', path: '/app/projects', icon: '📁', roles: ['admin', 'auditor'] },
  { label: 'Checklisten', path: '/app/checklists', icon: '📋', roles: ['admin', 'auditor'] },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();

  const handleLogout = () => { logout(); navigate('/'); };

  const items = NAV_ITEMS.filter((item) => !item.roles || item.roles.some((r) => hasRole(r)));

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/app/dashboard')}>
          <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center">
            <span className="text-white font-black text-sm">HS</span>
          </div>
          <div>
            <div className="text-white font-bold text-sm tracking-wide">KOMPAGNON</div>
            <div className="text-kompagnon-300 text-xs">Automation System</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {items.map((item) => {
          const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
          return (
            <div key={item.path} onClick={() => navigate(item.path)} className={active ? 'nav-item-active' : 'nav-item'}>
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          );
        })}

        {/* Settings */}
        <div className="pt-4 mt-4 border-t border-white/10">
          <div
            onClick={() => navigate('/app/settings')}
            className={location.pathname.startsWith('/app/settings') ? 'nav-item-active' : 'nav-item'}
          >
            <span className="text-lg">⚙️</span>
            <span>Einstellungen</span>
          </div>
          {hasRole('admin') && (
            <div
              onClick={() => navigate('/app/settings/users')}
              className={location.pathname === '/app/settings/users' ? 'nav-item-active' : 'nav-item'}
            >
              <span className="text-lg">🧑‍💼</span>
              <span>Benutzerverwaltung</span>
            </div>
          )}
        </div>
      </nav>

      {/* User Footer */}
      <div className="px-3 py-4 border-t border-white/10">
        {user && (
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 mb-2">
            <div className="w-8 h-8 rounded-full bg-kompagnon-400 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {user.first_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-sm font-medium truncate">{user.first_name} {user.last_name}</div>
              <div className="text-kompagnon-300 text-xs truncate">{user.role}</div>
            </div>
          </div>
        )}
        <button onClick={handleLogout} className="w-full nav-item text-red-400 hover:bg-red-500/10 hover:text-red-300">
          <span>🚪</span>
          <span>Abmelden</span>
        </button>
      </div>
    </aside>
  );
}
