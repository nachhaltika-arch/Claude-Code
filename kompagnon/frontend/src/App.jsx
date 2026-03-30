import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
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

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: 'var(--kc-mittel)' }}>
        Laden...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function AppContent() {
  const { isMobile } = useScreenSize();
  const { user, loading } = useAuth();

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
          <Routes>
            {/* Protected app routes */}
            <Route path="/app" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/leads" element={<ProtectedRoute roles={['admin', 'auditor']}><LeadPipeline /></ProtectedRoute>} />
            <Route path="/leads/:leadId" element={<ProtectedRoute roles={['admin', 'auditor']}><LeadProfile /></ProtectedRoute>} />
            <Route path="/projects/:id" element={<ProtectedRoute roles={['admin', 'auditor']}><ProjectDetail /></ProtectedRoute>} />
            <Route path="/checklists" element={<ProtectedRoute roles={['admin', 'auditor']}><Checklists /></ProtectedRoute>} />
            <Route path="/checklists/:projectId" element={<ProtectedRoute roles={['admin', 'auditor']}><Checklists /></ProtectedRoute>} />
            <Route path="/customers" element={<ProtectedRoute roles={['admin', 'auditor']}><Customers /></ProtectedRoute>} />
            <Route path="/import" element={<ProtectedRoute roles={['admin', 'auditor']}><ContactImport /></ProtectedRoute>} />
            <Route path="/audit" element={<ProtectedRoute><AuditTool /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/2fa-setup" element={<ProtectedRoute><TwoFactorSetup /></ProtectedRoute>} />
            <Route path="/admin/users" element={<ProtectedRoute roles={['admin']}><AdminUsers /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
      {isMobile && user && <BottomNav />}
    </div>
  );
}

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { hasRole } = useAuth();
  const items = [
    { icon: '🏠', label: 'Dashboard', path: '/app' },
    ...(hasRole('admin', 'auditor') ? [{ icon: '👥', label: 'Leads', path: '/leads' }] : []),
    { icon: '🔍', label: 'Audit', path: '/audit' },
    ...(hasRole('admin', 'auditor') ? [{ icon: '📥', label: 'Import', path: '/import' }] : []),
    { icon: '👤', label: 'Profil', path: '/profile' },
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

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public pages — no app chrome */}
          <Route path="/" element={<Landing />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/checkout/:package" element={<Checkout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* App pages — with Navbar, Sidebar, BottomNav */}
          <Route path="/*" element={<AppContent />} />
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
