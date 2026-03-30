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

import Navbar from './components/Navbar';
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
    <div style={{ minHeight: '100vh', background: 'var(--kc-hell)' }}>
      <Navbar />
      <div
        style={{
          display: 'flex',
          gap: isMobile ? 0 : 'var(--kc-space-8)',
          maxWidth: 'var(--kc-container-xl)',
          margin: '0 auto',
          padding: isMobile ? 'var(--kc-space-4)' : 'var(--kc-space-8) var(--kc-space-6)',
          paddingBottom: isMobile ? 80 : undefined,
        }}
      >
        {!isMobile && user && <Sidebar />}
        <main style={{ flex: 1, minWidth: 0 }}>
          <Outlet />
        </main>
      </div>
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
