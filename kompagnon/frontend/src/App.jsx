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
import Academy from './pages/Academy';
import AcademyCourseNew from './pages/AcademyCourse';   // neue 2-Spalten-Version (.js)
import AcademyLesson from './pages/AcademyLesson';
import AcademyAdmin from './pages/AcademyAdmin';
import AcademyAdminCourse from './pages/AcademyAdminCourse';
import AcademyAdminLesson from './pages/AcademyAdminLesson';
import AcademyEdit from './pages/AcademyEdit';
import AcademyModuleEdit from './pages/AcademyModuleEdit';
import AcademyCertificate from './pages/AcademyCertificate';
import SalesPipeline from './pages/SalesPipeline';
import Companies from './pages/Companies';
import CustomerDashboard from './pages/CustomerDashboard';
import Courses from './pages/Courses';
import DomainImport from './pages/DomainImport';
import CustomerPortal from './pages/CustomerPortal';
import CustomerDetail from './pages/CustomerDetail';
import KundenPortal from './pages/KundenPortal';
import PackageStarter from './pages/PackageStarter';
import PackageKompagnon from './pages/PackageKompagnon';
import PackagePremium from './pages/PackagePremium';
import KampagneLandingPage from './pages/KampagneLandingPage';

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
  // Kunde role: redirect to own card if they try to access restricted pages
  if (user.role === 'kunde' && roles && !roles.includes('kunde')) {
    return <Navigate to={user.lead_id ? `/app/usercards/${user.lead_id}` : '/app/dashboard'} replace />;
  }
  if (roles && !roles.includes(user.role)) return <Navigate to="/app/dashboard" replace />;
  return children;
}

// ── Dashboard: redirect Kunde to /app/usercards/:id, else regular Dashboard ──

function DashboardRoute() {
  const { user } = useAuth();
  if (user?.role === 'kunde') {
    if (user.lead_id) return <Navigate to={`/app/usercards/${user.lead_id}`} replace />;
    // Kunde without linked card
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', gap: 16, textAlign: 'center', padding: 24 }}>
        <div style={{ fontSize: 32 }}>📋</div>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kartei noch nicht verknüpft</h2>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 400, margin: 0 }}>
          Ihre Kundenkartei wurde noch nicht verknüpft. Bitte kontaktieren Sie KOMPAGNON.
        </p>
        <a href="mailto:info@kompagnon.eu" style={{ background: 'var(--brand-primary)', color: 'white', padding: '10px 24px', borderRadius: 'var(--radius-md)', textDecoration: 'none', fontSize: 14, fontWeight: 600 }}>
          Kontakt aufnehmen
        </a>
      </div>
    );
  }
  return <Dashboard />;
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
          <Route path="/portal/:token" element={<CustomerPortal />} />
          <Route path="/paket/starter" element={<PackageStarter />} />
          <Route path="/paket/kompagnon" element={<PackageKompagnon />} />
          <Route path="/paket/premium" element={<PackagePremium />} />
          <Route path="/checkout/:package" element={<Checkout />} />
          <Route path="/academy/certificate/:code" element={<AcademyCertificate />} />
          <Route path="/kampagne/:slug" element={<KampagneLandingPage />} />

          {/* App — authenticated, with Navbar/Sidebar */}
          <Route path="/app" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardRoute />} />
            <Route path="usercards/:id" element={<PrivateRoute><CustomerDashboard /></PrivateRoute>} />
            <Route path="sales" element={<PrivateRoute roles={['admin', 'auditor']}><SalesPipeline /></PrivateRoute>} />
            <Route path="companies" element={<PrivateRoute roles={['admin', 'auditor']}><Companies /></PrivateRoute>} />
            <Route path="leads" element={<PrivateRoute roles={['admin', 'auditor']}><LeadPipeline /></PrivateRoute>} />
            <Route path="leads/:leadId" element={<PrivateRoute roles={['admin', 'auditor']}><LeadProfile /></PrivateRoute>} />
            <Route path="projects" element={<PrivateRoute roles={['admin', 'auditor']}><CustomerProjects /></PrivateRoute>} />
            <Route path="projects/:id" element={<PrivateRoute roles={['admin', 'auditor']}><ProjectDetail /></PrivateRoute>} />
            <Route path="checklists" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="checklists/:projectId" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="customers" element={<PrivateRoute><Customers /></PrivateRoute>} />
            <Route path="customers/:customerId" element={<PrivateRoute roles={['admin']}><CustomerDetail /></PrivateRoute>} />
            <Route path="import" element={<PrivateRoute roles={['admin', 'auditor']}><DomainImport /></PrivateRoute>} />
            <Route path="export" element={<PrivateRoute roles={['admin', 'auditor']}><MassExport /></PrivateRoute>} />
            <Route path="audit" element={<PrivateRoute><AuditTool /></PrivateRoute>} />
            <Route path="profile" element={<Profile />} />
            <Route path="2fa-setup" element={<TwoFactorSetup />} />
            <Route path="admin/users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />
            <Route path="tickets" element={<PrivateRoute roles={['admin', 'auditor']}><Tickets /></PrivateRoute>} />
            <Route path="product" element={<PrivateRoute roles={['admin']}><ProductDevelopment /></PrivateRoute>} />
            {/* Academy — neue Routen */}
            <Route path="courses" element={<PrivateRoute roles={['admin', 'auditor']}><Courses /></PrivateRoute>} />
            <Route path="portal" element={<PrivateRoute roles={['kunde']}><KundenPortal /></PrivateRoute>} />
            <Route path="academy" element={<Academy />} />
            <Route path="academy/:id" element={<AcademyCourseNew />} />
            <Route path="academy/admin" element={<PrivateRoute roles={['admin']}><AcademyAdmin /></PrivateRoute>} />
            <Route path="academy/admin/course/new" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="academy/admin/course/:courseId" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="academy/admin/lesson/new" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            <Route path="academy/admin/lesson/:lessonId" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            {/* Legacy-Routen (Rückwärtskompatibilität) */}
            <Route path="akademie" element={<Academy />} />
            <Route path="akademie/kurs/:kursId" element={<AcademyCourseNew />} />
            <Route path="akademie/lektion/:lessonId" element={<AcademyLesson />} />
            <Route path="akademie/admin" element={<PrivateRoute roles={['admin']}><AcademyAdmin /></PrivateRoute>} />
            <Route path="akademie/admin/course/new" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="akademie/admin/course/:courseId" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="akademie/admin/lesson/new" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            <Route path="akademie/admin/lesson/:lessonId" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            <Route path="akademie/admin/neu" element={<PrivateRoute roles={['admin']}><AcademyEdit /></PrivateRoute>} />
            <Route path="akademie/admin/:courseId" element={<PrivateRoute roles={['admin']}><AcademyEdit /></PrivateRoute>} />
            <Route path="akademie/admin/modul/:moduleId" element={<PrivateRoute roles={['admin']}><AcademyModuleEdit /></PrivateRoute>} />

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
