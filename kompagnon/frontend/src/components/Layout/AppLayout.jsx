import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/app/dashboard', icon: 'fas fa-gauge-high' },
  { label: 'Vertriebspipeline', path: '/app/sales', icon: 'fas fa-bars-progress' },
  { label: 'Projektpipeline', path: '/app/leads', icon: 'fas fa-diagram-project' },
  { label: 'Domain Import', path: '/app/import', icon: 'fas fa-cloud-arrow-up' },
  { label: 'Export', path: '/app/export', icon: 'fas fa-file-export' },
  { label: 'Website Audit', path: '/app/audit', icon: 'fas fa-magnifying-glass-chart' },
  { label: 'Kontaktkartei', path: '/app/customers', icon: 'fas fa-address-book' },
  { label: 'Kundenprojekte', path: '/app/projects', icon: 'fas fa-folder-open' },
  { label: 'Support Tickets', path: '/app/tickets', icon: 'fas fa-ticket' },
  { label: 'Einstellungen', path: '/app/settings', icon: 'fas fa-gear' },
];

const ADMIN_ITEMS = [
  { label: 'Benutzerverwaltung', path: '/app/settings/users', icon: 'fas fa-users-gear' },
  { label: 'Produktentwicklung', path: '/app/product', icon: 'fas fa-screwdriver-wrench' },
];

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  const handleNav = (path) => {
    navigate(path);
    // Close mobile menu
    const collapse = document.getElementById('navbarMain');
    if (collapse && collapse.classList.contains('show')) {
      const bsCollapse = window.bootstrap?.Collapse?.getInstance(collapse);
      if (bsCollapse) bsCollapse.hide();
    }
  };

  return (
    <>
      {/* Bootstrap Navbar */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark fixed-top shadow-sm">
        <div className="container-fluid">
          <span className="navbar-brand fw-bold" style={{ cursor: 'pointer', letterSpacing: '-0.5px' }} onClick={() => handleNav('/app/dashboard')}>
            KOMPAGNON
          </span>

          <button className="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMain" aria-controls="navbarMain" aria-expanded="false" aria-label="Navigation">
            <span className="navbar-toggler-icon"></span>
          </button>

          <div className="collapse navbar-collapse" id="navbarMain">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              {NAV_ITEMS.map(item => (
                <li className="nav-item" key={item.path}>
                  <button
                    className={`nav-link btn btn-link text-decoration-none ${isActive(item.path) ? 'active fw-semibold' : ''}`}
                    onClick={() => handleNav(item.path)}
                  >
                    <i className={`${item.icon} me-1`}></i> {item.label}
                  </button>
                </li>
              ))}
              {hasRole('admin') && ADMIN_ITEMS.map(item => (
                <li className="nav-item" key={item.path}>
                  <button
                    className={`nav-link btn btn-link text-decoration-none ${isActive(item.path) ? 'active fw-semibold' : ''}`}
                    onClick={() => handleNav(item.path)}
                  >
                    <i className={`${item.icon} me-1`}></i> {item.label}
                  </button>
                </li>
              ))}
            </ul>

            {user && (
              <div className="d-flex align-items-center gap-3">
                <span className="text-light small">
                  <i className="fas fa-user me-1"></i>
                  {user.first_name} {user.last_name}
                  <span className="badge bg-secondary ms-1">{user.role}</span>
                </span>
                <button
                  className="btn btn-outline-light btn-sm"
                  onClick={() => { logout(); navigate('/'); }}
                >
                  <i className="fas fa-right-from-bracket me-1"></i> Abmelden
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container-fluid py-3">
        <Outlet />
      </main>
    </>
  );
}
