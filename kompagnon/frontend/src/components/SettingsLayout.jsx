import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const SETTINGS_NAV = [
  { label: 'Profil', path: '/app/settings/profile', icon: 'fa-user', roles: ['admin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Sicherheit', path: '/app/settings/security', icon: 'fa-shield-halved', roles: ['admin', 'auditor', 'nutzer', 'kunde'] },
  { label: 'Rollenverwaltung', path: '/app/settings/roles', icon: 'fa-users-gear', roles: ['admin'] },
  { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: 'fa-user-gear', roles: ['admin'] },
  { label: 'System', path: '/app/settings/system', icon: 'fa-server', roles: ['admin'] },
  { label: 'Benachrichtigungen', path: '/app/settings/notifications', icon: 'fa-bell', roles: ['admin', 'auditor'] },
  { label: 'Abonnement', path: '/app/settings/subscription', icon: 'fa-credit-card', roles: ['nutzer', 'kunde'] },
];

export default function SettingsLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const items = SETTINGS_NAV.filter(i => i.roles.includes(user?.role));

  return (
    <div className="row g-4">
      <div className="col-lg-3">
        <div className="card shadow-sm">
          <div className="card-header fw-semibold"><i className="fas fa-gear me-2"></i>Einstellungen</div>
          <div className="list-group list-group-flush">
            {items.map(item => (
              <button key={item.path} className={`list-group-item list-group-item-action d-flex align-items-center gap-2 ${location.pathname === item.path ? 'active' : ''}`} onClick={() => navigate(item.path)}>
                <i className={`fas ${item.icon}`}></i> {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="col-lg-9">
        <Outlet />
      </div>
    </div>
  );
}
