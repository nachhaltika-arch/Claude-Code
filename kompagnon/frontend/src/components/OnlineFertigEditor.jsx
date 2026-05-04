/**
 * OnlineFertigEditor — Container der die neue 4-View-Architektur (Step E) +
 * KASSidebar (Step F) zu einem nutzbaren Editor verheiratet (Step G).
 *
 * Side-by-Side mit dem bestehenden ProzessFlowV3 — der Legacy-Editor bleibt
 * unter /app/projects/:id, der neue Editor läuft unter
 * /app/projects/:id/online-fertig.
 *
 * Verantwortlich für:
 *   - Project-Daten laden
 *   - wireframe_data laden + persistieren (Backend-Schritt-D-Endpoints)
 *   - View-Switching (KASSidebar ↔ aktive View-Komponente)
 *   - Step-Status-Berechnung (für die Sidebar-Dots)
 *   - Gates: Style-Guide-Approval entsperrt Design-View
 *   - KI-Wireframe-Generator triggern + Polling
 *   - Onclick-Callbacks an die Views (Approval, GrapesJS, Netlify-Deploy)
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import KASSidebar, { SCHRITTE } from './KASSidebar';
import SitemapView from './views/SitemapView';
import WireframeView from './views/WireframeView';
import StyleGuideView from './views/StyleGuideView';
import DesignView from './views/DesignView';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

export default function OnlineFertigEditor() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const [project, setProject] = useState(null);
  const [loadingProject, setLoadingProject] = useState(true);
  const [wireframeData, setWireframeData] = useState({ pages: [] });
  const [activeView, setActiveView] = useState('sitemap');
  const [activeStep, setActiveStep] = useState('sitemap-ki');
  const [generateStatus, setGenerateStatus] = useState(null); // null | 'running' | { error } | 'done'
  const pollTimerRef = useRef(null);

  // ── Initial load: Project + Wireframe ──────────────────────────────────────

  useEffect(() => {
    if (!projectId || !token) return;
    let cancelled = false;
    setLoadingProject(true);
    Promise.all([
      fetch(`${API_BASE_URL}/api/projects/${projectId}`, { headers }).then((r) =>
        r.ok ? r.json() : null,
      ),
      fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe`, { headers }).then((r) =>
        r.ok ? r.json() : { pages: [] },
      ),
    ])
      .then(([proj, wf]) => {
        if (cancelled) return;
        setProject(proj);
        setWireframeData(wf || { pages: [] });
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoadingProject(false));
    return () => {
      cancelled = true;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [projectId, token, headers]);

  // ── Persistierung des wireframe_data ───────────────────────────────────────

  const persistWireframe = useCallback(
    async (next) => {
      try {
        await fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe`, {
          method: 'POST',
          headers,
          body: JSON.stringify(next),
        });
      } catch {
        // Silent — Frontend behält den State, beim Reload wird neu geladen
      }
    },
    [projectId, headers],
  );

  // ── Handlers für die Views ─────────────────────────────────────────────────

  const handleViewChange = (view) => {
    setActiveView(view);
    // Korrespondenz: View → erster passender Step in der Sidebar
    const matching = SCHRITTE.find((s) => s.view === view);
    if (matching) setActiveStep(matching.id);
  };

  const handleStepClick = (stepId) => {
    setActiveStep(stepId);
    const step = SCHRITTE.find((s) => s.id === stepId);
    if (step?.view) setActiveView(step.view);
  };

  const handleWireframeChange = (next) => {
    setWireframeData(next);
    // WireframeView persistiert schon selbst — wir aktualisieren nur lokal
  };

  const handleStyleGuideChange = (sg) => {
    const next = { ...wireframeData, style_guide: sg };
    setWireframeData(next);
    persistWireframe(next);
  };

  const handleStyleGuideApprove = () => {
    const next = { ...wireframeData, style_guide_approved: true };
    setWireframeData(next);
    persistWireframe(next);
    // Brevo-Mail-Trigger ist later work — heute nur das Flag setzen
  };

  const handleRegenerateSitemap = async () => {
    if (!project?.lead_id) return;
    try {
      await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/generate`, {
        method: 'POST',
        headers,
      });
    } catch {
      // SitemapView lädt sich selbst neu beim nächsten Mount/Update
    }
  };

  const handleGenerateWireframe = async () => {
    setGenerateStatus('running');
    try {
      const startRes = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/wireframe/generate`,
        { method: 'POST', headers },
      );
      if (!startRes.ok) throw new Error(`HTTP ${startRes.status}`);
      const { job_id } = await startRes.json();
      if (!job_id) throw new Error('keine job_id');

      // Poll alle 3s, max ~5 Min
      const start = Date.now();
      const poll = async () => {
        if (Date.now() - start > 300_000) {
          setGenerateStatus({ error: 'Timeout (5 Min) — Job noch nicht fertig' });
          return;
        }
        try {
          const r = await fetch(
            `${API_BASE_URL}/api/projects/wireframe-jobs/${job_id}`,
            { headers },
          );
          if (r.status === 404) {
            // Job bereits abgeholt — wirefraem-Daten neu laden
            const wf = await fetch(
              `${API_BASE_URL}/api/projects/${projectId}/wireframe`,
              { headers },
            ).then((rr) => (rr.ok ? rr.json() : { pages: [] }));
            setWireframeData(wf);
            setGenerateStatus('done');
            return;
          }
          const data = await r.json();
          if (data.status === 'done') {
            const wf = await fetch(
              `${API_BASE_URL}/api/projects/${projectId}/wireframe`,
              { headers },
            ).then((rr) => (rr.ok ? rr.json() : { pages: [] }));
            setWireframeData(wf);
            setGenerateStatus('done');
            return;
          }
          if (data.status === 'error') {
            setGenerateStatus({ error: data.error || 'Unbekannter Fehler' });
            return;
          }
          pollTimerRef.current = setTimeout(poll, 3000);
        } catch (e) {
          setGenerateStatus({ error: e.message || 'Polling fehlgeschlagen' });
        }
      };
      poll();
    } catch (e) {
      setGenerateStatus({ error: e.message || 'Job-Start fehlgeschlagen' });
    }
  };

  const handleOpenGrapesJS = () => {
    // ProzessFlowV3 / DesignStudio enthält den GrapesEditor — wir nehmen den
    // Legacy-Pfad bis das in Step G+ integriert ist.
    navigate(`/app/projects/${projectId}`);
  };

  const handleNetlifyDeploy = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/netlify/deploy`, {
        method: 'POST',
        headers,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Reload project so Netlify-status appears in the UI
      const proj = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, { headers }).then(
        (r) => (r.ok ? r.json() : null),
      );
      if (proj) setProject(proj);
    } catch (e) {
      // eslint-disable-next-line no-alert
      alert(`Netlify-Deploy fehlgeschlagen: ${e.message || 'unbekannt'}`);
    }
  };

  // ── Step-Status für die Sidebar-Dots ──────────────────────────────────────

  const stepStatus = useMemo(
    () => computeStepStatus(project, wireframeData),
    [project, wireframeData],
  );

  // ── Rendering ──────────────────────────────────────────────────────────────

  if (loadingProject) {
    return (
      <div style={{ padding: 60, textAlign: 'center', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        Projekt wird geladen…
      </div>
    );
  }

  if (!project) {
    return (
      <div style={{ padding: 60, textAlign: 'center', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>⚠️</div>
        <div style={{ fontSize: 15, fontWeight: 700, color: KC_DARK, marginBottom: 6 }}>
          Projekt nicht gefunden
        </div>
        <button
          type="button"
          onClick={() => navigate('/app/projects')}
          style={{
            background: KC_MID, color: '#fff', border: 'none', borderRadius: 8,
            padding: '10px 18px', fontSize: 13, fontWeight: 700, cursor: 'pointer',
            marginTop: 16,
          }}
        >
          Zur Projektübersicht
        </button>
      </div>
    );
  }

  const styleGuide = wireframeData.style_guide || null;
  const approved = !!wireframeData.style_guide_approved;
  const activeStepDef = SCHRITTE.find((s) => s.id === activeStep);
  const showStepDetail = activeStepDef && !activeStepDef.view;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        zIndex: 50,
        background: '#f8fafc',
        fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)',
      }}
    >
      <KASSidebar
        activeView={activeView}
        onViewChange={handleViewChange}
        activeStep={activeStep}
        onStepClick={handleStepClick}
        stepStatus={stepStatus}
      />

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Topbar mit Quick-Switch zum Legacy-Editor */}
        <header
          style={{
            height: 44,
            flexShrink: 0,
            background: '#fff',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            padding: '0 16px',
            gap: 12,
          }}
        >
          <button
            type="button"
            onClick={() => navigate('/app/dashboard')}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 12 }}
          >
            ← Dashboard
          </button>
          <span style={{ color: '#cbd5e1' }}>·</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: KC_DARK, textTransform: 'uppercase', letterSpacing: '-0.01em' }}>
            {project.company_name || `Projekt #${project.id}`}
          </span>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            {generateStatus === 'running' && (
              <span style={{ fontSize: 11, color: KC_MID, fontWeight: 700 }}>
                ⚙️ KI-Wireframe wird erstellt…
              </span>
            )}
            {generateStatus === 'done' && (
              <span style={{ fontSize: 11, color: '#1D9E75', fontWeight: 700 }}>
                ✓ Wireframe fertig
              </span>
            )}
            {generateStatus?.error && (
              <span style={{ fontSize: 11, color: '#dc2626', fontWeight: 700 }}>
                ✗ {generateStatus.error.slice(0, 60)}
              </span>
            )}
            <button
              type="button"
              onClick={() => navigate(`/app/projects/${projectId}`)}
              style={{
                background: 'transparent',
                color: '#64748b',
                border: '1px solid #cbd5e1',
                borderRadius: 6,
                padding: '5px 12px',
                fontSize: 11,
                fontWeight: 700,
                cursor: 'pointer',
              }}
              title="Zurück zum Legacy-Editor mit allen 12 Schritten"
            >
              → Legacy-Editor
            </button>
          </div>
        </header>

        {/* Aktiver View oder Step-Detail */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          {showStepDetail ? (
            <StepDetailPanel step={activeStepDef} project={project} projectId={projectId} navigate={navigate} />
          ) : activeView === 'sitemap' ? (
            <SitemapView
              projectId={projectId}
              leadId={project.lead_id}
              wireframeData={wireframeData}
              onGenerateWireframe={handleGenerateWireframe}
              onNavigateToWireframe={() => handleViewChange('wireframe')}
              onRegenerateSitemap={handleRegenerateSitemap}
            />
          ) : activeView === 'wireframe' ? (
            <WireframeView
              projectId={projectId}
              leadId={project.lead_id}
              wireframeData={wireframeData}
              onWireframeChange={handleWireframeChange}
              onNavigateToStyleGuide={() => handleViewChange('styleguide')}
            />
          ) : activeView === 'styleguide' ? (
            <StyleGuideView
              styleGuide={styleGuide}
              onChange={handleStyleGuideChange}
              onApprove={handleStyleGuideApprove}
              approved={approved}
            />
          ) : activeView === 'design' ? (
            <DesignView
              projectId={projectId}
              wireframeData={wireframeData}
              styleGuide={styleGuide}
              approved={approved}
              onOpenGrapesJS={handleOpenGrapesJS}
              onNetlifyDeploy={handleNetlifyDeploy}
            />
          ) : null}
        </div>
      </main>
    </div>
  );
}

// ── Step-Detail-Panel für Schritte ohne eigene View ─────────────────────────

function StepDetailPanel({ step, project, projectId, navigate }) {
  const status = step.gate ? 'Gate' : step.optional ? 'Optional' : 'Workflow';
  return (
    <div style={{ padding: 40, maxWidth: 720, margin: '0 auto', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
        Phase {step.phase} · Schritt {step.nr} · {status}
      </div>
      <h1 style={{ fontSize: 28, fontWeight: 900, color: KC_DARK, textTransform: 'uppercase', margin: '0 0 16px', letterSpacing: '-0.02em' }}>
        {step.name}
      </h1>
      <div style={{
        background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12,
        padding: 24, fontSize: 14, color: '#475569', lineHeight: 1.7,
      }}>
        <p style={{ marginTop: 0 }}>
          Dieser Schritt ist Teil des Online-Fertig-Workflows, hat aber noch keine eigene Editor-View
          im neuen 4-View-Modus. Die Bearbeitung erfolgt aktuell über den Legacy-ProzessFlowV3.
        </p>
        <button
          type="button"
          onClick={() => navigate(`/app/projects/${projectId}`)}
          style={{
            background: KC_MID, color: '#fff', border: 'none',
            borderRadius: 8, padding: '10px 18px', fontSize: 13, fontWeight: 700,
            cursor: 'pointer', marginTop: 12,
          }}
        >
          Im Legacy-Editor öffnen →
        </button>
      </div>
    </div>
  );
}

// ── Step-Status berechnen ───────────────────────────────────────────────────

function computeStepStatus(project, wireframeData) {
  if (!project) return {};
  const status = {};

  // Phase 1 — Analyse
  // Wir haben keine direkten boolean-Flags fürs Briefing/Audit hier — heuristisch
  status['briefing-unternehmen'] = project.has_briefing ? 'completed' : 'pending';
  status['audit'] = project.audit_score ? 'completed' : 'pending';
  status['content-vollanalyse'] = project.scrape_full_at ? 'completed' : 'pending';
  status['briefing-website'] = project.has_briefing ? 'completed' : 'pending';
  status['zugangsdaten'] = 'pending'; // optional, kein eindeutiges Signal

  // Phase 2 — Sitemap + Wireframe
  // Sitemap-Pages werden separat geladen, hier prüfen wir nur den wireframe
  const hasWireframe = Array.isArray(wireframeData?.pages) && wireframeData.pages.length > 0;
  status['sitemap-ki'] = hasWireframe ? 'completed' : 'pending';
  status['wireframe-ki'] = hasWireframe ? 'completed' : 'pending';

  // Phase 3 — Style Guide + Design
  status['style-guide'] = wireframeData?.style_guide_approved ? 'completed' : (wireframeData?.style_guide ? 'active' : 'pending');
  status['finales-design'] = project.netlify_deploy_id ? 'completed' : 'pending';

  // Phase 4 — Produktion
  status['ki-content'] = 'pending'; // braucht Content-Generation-Tracking
  status['netlify-deploy'] = project.netlify_site_id ? 'completed' : 'pending';

  // Phase 5 — Go Live
  status['dns'] = project.netlify_domain_status === 'active' ? 'completed' : 'pending';
  status['qa'] = project.qa_score && project.qa_score >= 70 ? 'completed' : 'pending';
  status['abnahme'] = project.customer_approved_at ? 'completed' : 'pending';

  // Phase 6 — Post-Launch
  status['umami'] = 'pending';
  status['heatmap'] = 'pending';
  status['monats-report'] = 'pending';

  return status;
}
