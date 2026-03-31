import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
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
import Akademie from './pages/Akademie';
import SalesPipeline from './pages/SalesPipeline';

import AppLayout from './components/Layout/AppLayout';

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
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: 'var(--text-tertiary)' }}>
        Laden...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/app/dashboard" replace />;
  return children;
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
            <Route path="sales" element={<PrivateRoute roles={['admin', 'auditor']}><SalesPipeline /></PrivateRoute>} />
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
            <Route path="akademie" element={<Akademie />} />

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
              fontFamily: 'var(--font-sans)',
              fontSize: 13,
              borderRadius: 'var(--radius-md)',
            },
          }}
        />
      </AuthProvider>
    </Router>
  );
}

export default App;
