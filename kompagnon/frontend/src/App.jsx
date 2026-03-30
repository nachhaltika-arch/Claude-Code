import React from 'react';
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
import AuditTool from './pages/AuditTool';
import LeadProfile from './pages/LeadProfile';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AdminUsers from './pages/AdminUsers';
import TwoFactorSetup from './pages/TwoFactorSetup';
import Landing from './pages/Landing';
import Checkout from './pages/Checkout';
import Settings from './pages/Settings';
import RoleManagement from './pages/RoleManagement';
import SettingsLayout from './components/SettingsLayout';
import Impressum from './pages/Impressum';
import Datenschutz from './pages/Datenschutz';

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
      <main className={`flex-1 overflow-y-auto ${!isMobile && user ? 'ml-64' : ''}`} style={{ paddingBottom: isMobile ? 80 : undefined }}>
        <div className="max-w-7xl mx-auto p-4 lg:p-8">
          <Outlet />
        </div>
      </main>
      {isMobile && user && <BottomNav />}
    </div>
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
            color: location.pathname === item.path ? '#D4A017' : 'rgba(255,255,255,0.6)',
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
          <Route path="/impressum" element={<Impressum />} />
          <Route path="/datenschutz" element={<Datenschutz />} />
          <Route path="/checkout/:package" element={<Checkout />} />

          {/* App — authenticated, with Navbar/Sidebar */}
          <Route path="/app" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="leads" element={<PrivateRoute roles={['admin', 'auditor']}><LeadPipeline /></PrivateRoute>} />
            <Route path="leads/:leadId" element={<PrivateRoute roles={['admin', 'auditor']}><LeadProfile /></PrivateRoute>} />
            <Route path="projects/:id" element={<PrivateRoute roles={['admin', 'auditor']}><ProjectDetail /></PrivateRoute>} />
            <Route path="checklists" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="checklists/:projectId" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="customers" element={<PrivateRoute><Customers /></PrivateRoute>} />
            <Route path="import" element={<PrivateRoute roles={['admin', 'auditor']}><ContactImport /></PrivateRoute>} />
            <Route path="audit" element={<PrivateRoute><AuditTool /></PrivateRoute>} />
            <Route path="profile" element={<Profile />} />
            <Route path="2fa-setup" element={<TwoFactorSetup />} />
            <Route path="admin/users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />

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
