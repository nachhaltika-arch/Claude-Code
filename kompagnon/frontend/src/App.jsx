import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import Dashboard from './pages/Dashboard';
import LeadPipeline from './pages/LeadPipeline';
import ProjectDetail from './pages/ProjectDetail';
import Checklists from './pages/Checklists';
import Customers from './pages/Customers';
import ContactImport from './pages/ContactImport';

import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', background: 'var(--kc-hell)' }}>
        <Navbar />
        <div
          style={{
            display: 'flex',
            gap: 'var(--kc-space-8)',
            maxWidth: 'var(--kc-container-xl)',
            margin: '0 auto',
            padding: 'var(--kc-space-8) var(--kc-space-6)',
          }}
        >
          <Sidebar />
          <main style={{ flex: 1, minWidth: 0 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/leads" element={<LeadPipeline />} />
              <Route path="/projects/:id" element={<ProjectDetail />} />
              <Route path="/checklists" element={<Checklists />} />
              <Route path="/checklists/:projectId" element={<Checklists />} />
              <Route path="/customers" element={<Customers />} />
              <Route path="/import" element={<ContactImport />} />
            </Routes>
          </main>
        </div>
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
    </Router>
  );
}

export default App;
