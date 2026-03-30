import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useScreenSize } from './utils/responsive';

import Dashboard from './pages/Dashboard';
import LeadPipeline from './pages/LeadPipeline';
import ProjectDetail from './pages/ProjectDetail';
import Checklists from './pages/Checklists';
import Customers from './pages/Customers';
import ContactImport from './pages/ContactImport';
import AuditTool from './pages/AuditTool';
import LeadProfile from './pages/LeadProfile';

import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

function AppContent() {
  const { isMobile } = useScreenSize();

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
        {!isMobile && <Sidebar />}
        <main style={{ flex: 1, minWidth: 0 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/leads" element={<LeadPipeline />} />
            <Route path="/leads/:leadId" element={<LeadProfile />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/checklists" element={<Checklists />} />
            <Route path="/checklists/:projectId" element={<Checklists />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/import" element={<ContactImport />} />
            <Route path="/audit" element={<AuditTool />} />
          </Routes>
        </main>
      </div>
      {isMobile && <BottomNav />}
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
    </div>
  );
}

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const items = [
    { icon: '🏠', label: 'Dashboard', path: '/' },
    { icon: '👥', label: 'Leads', path: '/leads' },
    { icon: '🔍', label: 'Audit', path: '/audit' },
    { icon: '📥', label: 'Import', path: '/import' },
    { icon: '👤', label: 'Kunden', path: '/customers' },
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
      <AppContent />
    </Router>
  );
}

export default App;
