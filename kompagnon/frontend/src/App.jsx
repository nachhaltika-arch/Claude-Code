import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useScreenSize } from './utils/responsive';
import { AuthProvider, useAuth } from './context/AuthContext';

import Dashboard from './pages/Dashboard';
import LeadPipeline from './pages/LeadPipeline';
import ProjectDetail from './pages/ProjectDetail';
import Checklists from './pages/Checklists';
import Customers from './pages/Customers';
import ContactImport from './pages/ContactImport';
import MassExport from './pages/MassExport';
import Tickets from './pages/Tickets';
import CustomerProjects from './pages/CustomerProjects';
import ProductDevelopment from './pages/ProductDevelopment';
import FeedbackButton from './components/FeedbackButton';
import AuditTool from './pages/AuditTool';
import LeadProfile from './pages/LeadProfile';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AdminUsers from './pages/AdminUsers';
import TwoFactorSetup from './pages/TwoFactorSetup';
import Landing from './pages/Landing';
import Checkout from './pages/Checkout';
import CheckoutSuccess from './pages/CheckoutSuccess';
import Settings from './pages/Settings';
import RoleManagement from './pages/RoleManagement';
import SettingsLayout from './components/SettingsLayout';
import Impressum from './pages/Impressum';
import Datenschutz from './pages/Datenschutz';
import ResetPassword from './pages/ResetPassword';

import Sidebar from './components/Sidebar';

// ── Route Guards ──

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/app/dashboard" replace />;
  return children;
}

function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: 'var(--kc-mittel)' }}>
        Laden...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/app/dashboard" replace />;
  return children;
}

// ── App Layout (Navbar + Sidebar + Outlet) ──

function AppLayout() {
  const { isMobile } = useScreenSize();
  const { user } = useAuth();

  return (
    <div className="flex h-screen bg-slate-50">
      {!isMobile && user && <Sidebar />}
      <main className={`flex-1 overflow-y-auto overflow-x-hidden ${!isMobile && user ? 'ml-64' : ''}`} style={{ paddingBottom: isMobile ? 80 : undefined, minWidth: 0 }}>
        {isMobile && user && <MobileHeader />}
        <div style={{ padding: isMobile ? 16 : '24px 32px', width: '100%', maxWidth: '100%' }}>
          <Outlet />
        </div>
      </main>
      {isMobile && user && <BottomNav />}
    </div>
  );
}

// ── Mobile Header (sticky top bar + hamburger menu) ──

const MOBILE_NAV = [
  { icon: '📊', label: 'Dashboard', path: '/app/dashboard' },
  { icon: '👥', label: 'Lead Pipeline', path: '/app/leads', roles: ['admin', 'auditor'] },
  { icon: '🔍', label: 'Website Audit', path: '/app/audit' },
  { icon: '📥', label: 'Kontakt-Import', path: '/app/import', roles: ['admin', 'auditor'] },
  { icon: '👤', label: 'Kunden', path: '/app/customers' },
  { icon: '📁', label: 'Projekte', path: '/app/projects', roles: ['admin', 'auditor'] },
  { icon: '⚙️', label: 'Einstellungen', path: '/app/settings' },
];

function MobileHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const items = MOBILE_NAV.filter((i) => !i.roles || i.roles.some((r) => hasRole(r)));

  return (
    <>
      <header style={{
        background: '#0F1E3A', padding: '12px 16px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: '#D4A017', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#0F1E3A', fontWeight: 900, fontSize: 11 }}>HS</span>
          </div>
          <span style={{ color: '#fff', fontWeight: 800, fontSize: 16 }}>KOMPAGNON</span>
        </div>
        <button onClick={() => setMenuOpen(!menuOpen)} style={{
          background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: '8px 12px',
          color: '#fff', cursor: 'pointer', fontSize: 18, minWidth: 44, minHeight: 44,
        }}>
          {menuOpen ? '✕' : '☰'}
        </button>
      </header>
      {menuOpen && (
        <div style={{ position: 'fixed', top: 56, left: 0, right: 0, bottom: 0, background: '#0F1E3A', zIndex: 49, padding: 16, overflowY: 'auto' }}>
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 16, background: 'rgba(255,255,255,0.05)', borderRadius: 12, marginBottom: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: '50%', background: '#D4A017', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#0F1E3A' }}>
                {user.first_name?.[0] || 'U'}
              </div>
              <div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: 15 }}>{user.first_name} {user.last_name}</div>
                <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12 }}>{user.role}</div>
              </div>
            </div>
          )}
          {items.map((item) => (
            <button key={item.path} onClick={() => { navigate(item.path); setMenuOpen(false); }} style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
              background: 'none', border: 'none', color: 'rgba(255,255,255,0.85)', fontSize: 16,
              fontWeight: 500, cursor: 'pointer', borderRadius: 10, textAlign: 'left', minHeight: 52,
            }}>
              <span style={{ fontSize: 22 }}>{item.icon}</span> {item.label}
            </button>
          ))}
          <button onClick={() => { logout(); navigate('/'); }} style={{
            width: '100%', display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
            background: 'rgba(231,76,60,0.1)', border: 'none', color: '#ff6b6b', fontSize: 16,
            fontWeight: 600, cursor: 'pointer', borderRadius: 10, textAlign: 'left', marginTop: 16, minHeight: 52,
          }}>
            🚪 Abmelden
          </button>
        </div>
      )}
    </>
  );
}

// ── Bottom Nav (Mobile) ──

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { hasRole } = useAuth();
  const items = [
    { icon: '🏠', label: 'Dashboard', path: '/app/dashboard' },
    ...(hasRole('admin', 'auditor') ? [{ icon: '👥', label: 'Leads', path: '/app/leads' }] : []),
    { icon: '🔍', label: 'Audit', path: '/app/audit' },
    ...(hasRole('admin', 'auditor') ? [{ icon: '📥', label: 'Import', path: '/app/import' }] : []),
    { icon: '👤', label: 'Profil', path: '/app/profile' },
  ];

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: '#0F1E3A', display: 'flex', justifyContent: 'space-around',
      padding: '8px 0 calc(8px + env(safe-area-inset-bottom))',
      zIndex: 100, boxShadow: '0 -2px 12px rgba(0,0,0,0.2)',
    }}>
      {items.map((item) => (
        <button
          key={item.path}
          onClick={() => navigate(item.path)}
          style={{
            background: 'none', border: 'none',
            color: location.pathname === item.path ? '#D4A017' : 'rgba(255,255,255,0.8)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
            cursor: 'pointer', padding: '4px 12px', minWidth: 44, minHeight: 44,
          }}
        >
          <span style={{ fontSize: 20 }}>{item.icon}</span>
          <span style={{ fontSize: 10, fontWeight: 600 }}>{item.label}</span>
        </button>
      ))}
    </div>
  );
}

// ── Main App ──

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public pages — no app chrome */}
          <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/checkout/success" element={<CheckoutSuccess />} />
          <Route path="/impressum" element={<Impressum />} />
          <Route path="/datenschutz" element={<Datenschutz />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/checkout/:package" element={<Checkout />} />

          {/* App — authenticated, with Navbar/Sidebar */}
          <Route path="/app" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="leads" element={<PrivateRoute roles={['admin', 'auditor']}><LeadPipeline /></PrivateRoute>} />
            <Route path="leads/:leadId" element={<PrivateRoute roles={['admin', 'auditor']}><LeadProfile /></PrivateRoute>} />
            <Route path="projects" element={<PrivateRoute roles={['admin', 'auditor']}><CustomerProjects /></PrivateRoute>} />
            <Route path="projects/:id" element={<PrivateRoute roles={['admin', 'auditor']}><ProjectDetail /></PrivateRoute>} />
            <Route path="checklists" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="checklists/:projectId" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="customers" element={<PrivateRoute><Customers /></PrivateRoute>} />
            <Route path="import" element={<PrivateRoute roles={['admin', 'auditor']}><ContactImport /></PrivateRoute>} />
            <Route path="export" element={<PrivateRoute roles={['admin', 'auditor']}><MassExport /></PrivateRoute>} />
            <Route path="audit" element={<PrivateRoute><AuditTool /></PrivateRoute>} />
            <Route path="profile" element={<Profile />} />
            <Route path="2fa-setup" element={<TwoFactorSetup />} />
            <Route path="admin/users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />
            <Route path="tickets" element={<PrivateRoute roles={['admin', 'auditor']}><Tickets /></PrivateRoute>} />
            <Route path="product" element={<PrivateRoute roles={['admin']}><ProductDevelopment /></PrivateRoute>} />

            {/* Settings with sub-navigation */}
            <Route path="settings" element={<SettingsLayout />}>
              <Route index element={<Navigate to="/app/settings/profile" replace />} />
              <Route path="profile" element={<Settings tab="profile" />} />
              <Route path="security" element={<Settings tab="security" />} />
              <Route path="roles" element={<PrivateRoute roles={['admin']}><RoleManagement /></PrivateRoute>} />
              <Route path="users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />
              <Route path="system" element={<PrivateRoute roles={['admin']}><Settings tab="system" /></PrivateRoute>} />
              <Route path="notifications" element={<Settings tab="notifications" />} />
              <Route path="subscription" element={<PrivateRoute roles={['admin']}><Settings tab="subscription" /></PrivateRoute>} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <FeedbackButton />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              fontFamily: 'var(--kc-font-body)',
              fontSize: 'var(--kc-text-sm)',
              borderRadius: 'var(--kc-radius-md)',
            },
          }}
        />
      </AuthProvider>
    </Router>
  );
}

export default App;
