import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  UserGroupIcon,
  FolderIcon,
  ClipboardDocumentListIcon,
  UserIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassCircleIcon,
} from '@heroicons/react/24/outline';

const menuItems = [
  { name: 'Dashboard', path: '/app/dashboard', icon: HomeIcon },
  { name: 'Lead Pipeline', path: '/app/leads', icon: UserGroupIcon },
  { name: 'Projekte', path: '/app/projects', icon: FolderIcon },
  { name: 'Checklisten', path: '/app/checklists', icon: ClipboardDocumentListIcon },
  { name: 'Website Audit', path: '/app/audit', icon: MagnifyingGlassCircleIcon },
  { name: 'Kontakt-Import', path: '/app/import', icon: ArrowUpTrayIcon },
  { name: 'Kunden', path: '/app/customers', icon: UserIcon },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside style={{ width: '200px', flexShrink: 0 }}>
      <nav className="kc-card" style={{ padding: 'var(--kc-space-3)' }}>
        <div
          style={{
            marginBottom: 'var(--kc-space-3)',
            padding: '0 var(--kc-space-3)',
          }}
        >
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
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--kc-space-3)',
                padding: 'var(--kc-space-2) var(--kc-space-3)',
                borderRadius: 'var(--kc-radius-md)',
                fontWeight: isActive ? 700 : 500,
                fontSize: 'var(--kc-text-sm)',
                textDecoration: 'none',
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
      </nav>
    </aside>
  );
}
