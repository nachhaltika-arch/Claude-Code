import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  UserGroupIcon,
  FolderIcon,
  ChecklistIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

const menuItems = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Lead Pipeline', path: '/leads', icon: UserGroupIcon },
  { name: 'Projects', path: '/projects', icon: FolderIcon },
  { name: 'Checklists', path: '/checklists', icon: ChecklistIcon },
  { name: 'Customers', path: '/customers', icon: UsersIcon },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-48 flex-shrink-0">
      <nav className="space-y-1 bg-white rounded-lg p-4 shadow">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg font-medium text-sm transition-colors ${
                isActive
                  ? 'bg-kompagnon-100 text-kompagnon-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
