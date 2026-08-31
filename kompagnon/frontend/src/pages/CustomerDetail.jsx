import React, { useState, useEffect } from 'react';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import { loadJson, saveJson } from '../utils/apiRequest';
import WebsiteDesigner from '../components/WebsiteDesigner';
import GrapesEditor from '../components/GrapesEditor';
import { aufTaste } from '../utils/tastaturBedienung';
// Am 30.08.2026 herausgeloest (L-25): `CustomerDetail.jsx` trug 2.512 Zeilen
// und darin fuenf eigenstaendige Abschnitte. Jeder war dort schon eine eigene
// Funktion — der Schnitt verschiebt sie nur dorthin, wo man sie sucht.
import AuditHistorySection from '../components/betrieb/AuditHistorySection';
import CmsConnectionSection from '../components/betrieb/CmsConnectionSection';
import LinkedProjectSection from '../components/betrieb/LinkedProjectSection';
import PageSpeedSection from '../components/betrieb/PageSpeedSection';
import ProjectFilesSection from '../components/betrieb/ProjectFilesSection';
// Am 31.08.2026 herausgeloest (L-25): die drei Reiter, die als sofort
// aufgerufene Funktionen in der Rueckgabe standen.
import ReiterAkademie from '../components/betrieb/ReiterAkademie';
import ReiterSitemap from '../components/betrieb/ReiterSitemap';
import ReiterDesignseiten from '../components/betrieb/ReiterDesignseiten';
import ReiterMarkendesign from '../components/betrieb/ReiterMarkendesign';

// ── PageSpeed helpers ──────────────────────────────────────────

export default function CustomerDetail() {
  const { customerId } = useParams();
  const navigate       = useNavigate();
  const { token }      = useAuth();
  const { isMobile }   = useScreenSize();
  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [customer, setCustomer]           = useState(null);
  const [loadingCustomer, setLoadingCustomer] = useState(true);
  const [activeTab, setActiveTab]          = useState('dateien');
  // lead_id for PageSpeed — loaded from project, falls back to customerId
  const [leadId, setLeadId] = useState(customerId);
  const [projectId, setProjectId] = useState(null);

  // ── Sitemap state ──────────────────────────────────────────────
  const [sitemapPages, setSitemapPages]   = useState([]);
  const [sitemapLoading, setSitemapLoading] = useState(false);
  const [sitemapLoaded, setSitemapLoaded]  = useState(false);
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [editingPage, setEditingPage]      = useState(null);
  // Add page inline form
  const [addPageOpen, setAddPageOpen]      = useState(false);
  const [addPageForm, setAddPageForm]      = useState({ page_name: '', page_type: 'info', parent_id: '' });
  const [addPageSaving, setAddPageSaving]  = useState(false);
  // Edit page modal
  const [editPageModal, setEditPageModal]  = useState(null); // page object
  const [editPageForm, setEditPageForm]    = useState({});
  const [editPageSaving, setEditPageSaving] = useState(false);
  // KI generation
  const [kiGenerating, setKiGenerating]    = useState(false);
  const [kiConfirm, setKiConfirm]          = useState(false);
  // Design state
  const [designRunning, setDesignRunning]  = useState(false);
  const [designSlow, setDesignSlow]        = useState(false);
  const [designResult, setDesignResult]    = useState(null);
  const [designError, setDesignError]      = useState('');
  // Design — per-page workflow
  const [activeDesignPage, setActiveDesignPage] = useState(null);
  const [pageVersions, setPageVersions]         = useState({});

  // Academy state
  const [assigned, setAssigned]     = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loadingAcademy, setLoadingAcademy] = useState(true);
  const [showModal, setShowModal]   = useState(false);

  // **Escape schliesst die beiden Modale — WCAG 2.1.1 (30.08.2026, L-17).**
  // Mit der Tastatur gab es aus ihnen keinen Weg heraus ausser dem Suchen des
  // Abbrechen-Knopfes.
  //
  // **Der Aufruf steht hinter beiden `useState`-Zeilen, und das ist der
  // Punkt.** Erst stand er unter der Signatur, dann hinter `editPageModal`
  // (Z. 1147) — und las trotzdem `showModal`, das erst hier entsteht:
  // „Cannot access 'showModal' before initialization", die Seite rendert
  // **gar nicht**. Keiner der 558 Tests rendert `CustomerDetail`; gefunden
  // hat es erst der Aufruf der Seite im Browser.
  useEscapeKey(() => { setEditPageModal(null); setShowModal(false); },
               Boolean(editPageModal) || showModal);
  const [assigning, setAssigning]   = useState(null);
  const [removing, setRemoving]     = useState(null);
  const [isDesignerOpen, setIsDesignerOpen] = useState(false);
  // Brand Design
  const [brandData, setBrandData]   = useState(null);
  const [brandLoaded, setBrandLoaded] = useState(false);
  const [scraping, setScraping]     = useState(false);
  const [analyzing, setAnalyzing]   = useState(false);
  const [scanRunning, setScanRunning] = useState(false);
  const [scanStep, setScanStep] = useState(-1);
  const [scanResults, setScanResults] = useState([]);

  useEffect(() => {
    loadJson(`${API_BASE_URL}/api/leads/${customerId}`, { headers: h }, { context: 'Kunde', emptyOn: [] })
      .then(data => { if (data) setCustomer(data); })
      .finally(() => setLoadingCustomer(false));
    // Try to resolve the real lead_id via the linked project
    loadJson(`${API_BASE_URL}/api/projects/?limit=200`, { headers: h }, { context: 'Projektzuordnung', fallback: [] })
      .then(projects => {
        const linked = Array.isArray(projects)
          ? projects.find(p => String(p.lead_id) === String(customerId))
          : null;
        if (linked?.lead_id) setLeadId(linked.lead_id);
        if (linked?.id) setProjectId(linked.id);
      });
  }, [customerId]); // eslint-disable-line

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/academy/courses`, { headers: h }).then(r => r.json()),
    ])
      .then(([assignedData, coursesData]) => {
        setAssigned(Array.isArray(assignedData) ? assignedData : []);
        setAllCourses(Array.isArray(coursesData) ? coursesData : []);
      })
      .catch(console.error)
      .finally(() => setLoadingAcademy(false));
  }, [customerId]); // eslint-disable-line

  // ── Sitemap helpers ────────────────────────────────────────────
  const loadSitemapPages = async (lid = leadId) => {
    if (!lid) return;
    setSitemapLoading(true);
    const pages = await loadJson(`${API_BASE_URL}/api/sitemap/${lid}`, { headers: h }, { context: 'Sitemap' });
    if (pages) {
      setSitemapPages(pages);
      setSitemapLoaded(true);
      if (!selectedPageId && pages.length > 0) {
        const content = pages.filter(p => !p.ist_pflichtseite);
        const start = content.find(p => p.page_type === 'startseite') || content[0];
        if (start) setSelectedPageId(start.id);
      }
    }
    setSitemapLoading(false);
  };

  const downloadSitemapPdf = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('PDF konnte nicht geladen werden');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'sitemap.pdf'; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { alert('PDF Fehler: ' + e.message); }
  };

  const deleteSitemapPage = async (pageId) => {
    if (!window.confirm('Seite wirklich löschen?')) return;
    await fetch(`${API_BASE_URL}/api/sitemap/pages/${pageId}`, { method: 'DELETE', headers: h });
    setSitemapPages(prev => prev.filter(p => p.id !== pageId));
  };

  const generateKI = async () => {
    setKiConfirm(false);
    setKiGenerating(true);
    const data = await loadJson(
      `${API_BASE_URL}/api/sitemap/${leadId}/generate`,
      { method: 'POST', headers: h },
      { context: 'Sitemap-Vorschlag', emptyOn: [] }
    );
    if (data) {
      setSitemapPages(data.pages || []);
      setSelectedPageId(null);
    }
    setKiGenerating(false);
  };

  const saveEditPage = async () => {
    if (!editPageModal) return;
    setEditPageSaving(true);
    const updated = await loadJson(
      `${API_BASE_URL}/api/sitemap/pages/${editPageModal.id}`,
      { method: 'PUT', headers: h, body: JSON.stringify(editPageForm) },
      { context: 'Seite speichern', emptyOn: [] }
    );
    if (updated) {
      setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p));
      setEditPageModal(null);
    }
    setEditPageSaving(false);
  };

  const createPage = async () => {
    if (!addPageForm.page_name.trim()) return;
    setAddPageSaving(true);
    const body = {
      page_name: addPageForm.page_name,
      page_type: addPageForm.page_type,
      parent_id: addPageForm.parent_id ? Number(addPageForm.parent_id) : null,
      position: sitemapPages.filter(p => !p.ist_pflichtseite).length,
    };
    const page = await loadJson(
      `${API_BASE_URL}/api/sitemap/${leadId}/pages`,
      { method: 'POST', headers: h, body: JSON.stringify(body) },
      { context: 'Seite anlegen', emptyOn: [] }
    );
    if (page) {
      setSitemapPages(prev => [...prev, page]);
      setAddPageForm({ page_name: '', page_type: 'info', parent_id: '' });
      setAddPageOpen(false);
    }
    setAddPageSaving(false);
  };

  const loadVersionsForPage = async (pageId) => {
    if (!pageId) return;
    const data = await loadJson(
      `${API_BASE_URL}/api/designs/${leadId}?page_id=${pageId}`,
      { headers: h },
      { context: 'Entwurfsversionen' }
    );
    if (data) setPageVersions(prev => ({ ...prev, [pageId]: Array.isArray(data) ? data : [] }));
  };

  const saveVersion = async (html) => {
    if (!activeDesignPage || !leadId) return;
    const versionName = `v${(pageVersions[activeDesignPage.id]?.length || 0) + 1} — ${new Date().toLocaleDateString('de-DE')}`;
    // Ohne Prüfung war eine verlorene Version nicht von einer gespeicherten zu
    // unterscheiden — die Liste blieb einfach unverändert.
    const saved = await saveJson(
      `${API_BASE_URL}/api/designs/${leadId}`,
      {
        method: 'POST', headers: h,
        body: JSON.stringify({
          sitemap_page_id: activeDesignPage.id,
          page_name: activeDesignPage.page_name,
          version_name: versionName,
          html_content: html,
        }),
      },
      { context: 'Version speichern' }
    );
    if (saved) loadVersionsForPage(activeDesignPage.id);
  };

  const loadPageContext = async (lid, pageId) => {
    const results = await Promise.allSettled([
      fetch(`${API_BASE_URL}/api/audit/lead/${lid}`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/leads/${lid}/pagespeed`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/crawler/${lid}`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/briefings/${lid}`, { headers: h }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/branddesign/${lid}`, { headers: h }).then(r => r.json()),
    ]);
    const [audits, pagespeed, crawler, briefing, brand] = results.map(r =>
      r.status === 'fulfilled' ? r.value : null
    );
    const latestAudit = Array.isArray(audits) ? audits[0] : null;
    return {
      audit_score:          latestAudit?.total_score || null,
      audit_problems:       latestAudit?.top_problems || [],
      audit_summary:        latestAudit?.ai_summary || '',
      pagespeed_mobile:     pagespeed?.mobile_score || null,
      pagespeed_desktop:    pagespeed?.desktop_score || null,
      crawler_pages:        Array.isArray(crawler) ? crawler.length : 0,
      crawler_titles:       Array.isArray(crawler) ? crawler.slice(0, 5).map(p => p.title).filter(Boolean) : [],
      briefing_usp:         briefing?.usp || '',
      briefing_leistungen:  briefing?.leistungen || '',
      briefing_zielgruppe:  briefing?.zielgruppe || '',
      brand_primary_color:  brand?.primary_color || null,
      brand_secondary_color: brand?.secondary_color || null,
      brand_font_primary:   brand?.font_primary || null,
      brand_design_style:   brand?.design_style || null,
    };
  };

  const generateDesign = async () => {
    if (!projectId || !activeDesignPage) return;
    setDesignRunning(true);
    setDesignSlow(false);
    setDesignError('');
    setDesignResult(null);
    const slowTimer = setTimeout(() => setDesignSlow(true), 20000);
    try {
      const [bRes, ctx] = await Promise.all([
        fetch(`${API_BASE_URL}/api/briefings/${leadId}`, { headers: h }),
        loadPageContext(leadId, activeDesignPage.id),
      ]);
      const briefing = bRes.ok ? await bRes.json() : null;

      let contentFields = {};
      try {
        const cRes = await fetch(`${API_BASE_URL}/api/content/page/${activeDesignPage.id}`, { headers: h });
        if (cRes.ok) {
          const cData = await cRes.json();
          (cData.sections || []).forEach(s => {
            const text = s.inhalt_final || s.inhalt_ki || '';
            if (text) contentFields[`content_${s.slot_typ}`] = text;
          });
        }
      } catch { /* optional */ }

      const payload = {
        company_name:       String(customer?.company_name || ''),
        city:               String(briefing?.einzugsgebiet || customer?.city || ''),
        trade:              String(briefing?.gewerk || customer?.trade || ''),
        usp:                String(briefing?.usp || ''),
        services:           Array.isArray(briefing?.leistungen)
                              ? briefing.leistungen.map(String)
                              : typeof briefing?.leistungen === 'string'
                                ? briefing.leistungen.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
                                : [],
        target_audience:    String(briefing?.zielgruppe || ''),
        page_name:          String(activeDesignPage.page_name || 'Startseite'),
        zweck:              String(activeDesignPage.zweck || ''),
        ziel_keyword:       String(activeDesignPage.ziel_keyword || ''),
        cta_text:           String(activeDesignPage.cta_text || ''),
        audit_score:        ctx.audit_score,
        audit_problems:     ctx.audit_problems,
        pagespeed_mobile:   ctx.pagespeed_mobile,
        crawler_titles:     ctx.crawler_titles,
        briefing_usp:       ctx.briefing_usp,
        briefing_leistungen: ctx.briefing_leistungen,
        briefing_zielgruppe:  ctx.briefing_zielgruppe,
        brand_primary_color:  ctx.brand_primary_color,
        brand_secondary_color: ctx.brand_secondary_color,
        brand_font_primary:   ctx.brand_font_primary,
        brand_design_style:   ctx.brand_design_style,
        ...contentFields,
      };

      const startRes = await fetch(`${API_BASE_URL}/api/agents/${projectId}/content`, {
        method: 'POST', headers: h, body: JSON.stringify(payload),
      });
      if (!startRes.ok) {
        const err = await startRes.json().catch(() => ({}));
        const detail = err.detail;
        throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : `Fehler ${startRes.status}`);
      }
      const { job_id } = await startRes.json();

      let result = null;
      const deadline = Date.now() + 120_000;
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 2000));
        const pollRes = await fetch(`${API_BASE_URL}/api/agents/jobs/${job_id}`, { headers: h });
        if (!pollRes.ok) throw new Error('Job-Status konnte nicht abgerufen werden');
        const job = await pollRes.json();
        if (job.status === 'done') {
          result = job.result_html || (typeof job.result === 'string' ? job.result : null);
          break;
        }
        if (job.status === 'error') throw new Error(job.error || 'KI-Generierung fehlgeschlagen');
      }
      if (!result) throw new Error('Zeitüberschreitung — bitte erneut versuchen');
      setDesignResult(result);

      // Auto-save version + update sitemap page
      const html = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
      saveVersion(html);
      saveJson(
        `${API_BASE_URL}/api/sitemap/pages/${activeDesignPage.id}`,
        { method: 'PUT', headers: h, body: JSON.stringify({ ...activeDesignPage, mockup_html: html }) },
        { context: 'Entwurf sichern' }
      );
      setSitemapPages(prev => prev.map(p => p.id === activeDesignPage.id ? { ...p, mockup_html: html } : p));
    } catch (e) {
      setDesignError(e?.message || String(e) || 'Generierung fehlgeschlagen.');
    } finally {
      clearTimeout(slowTimer);
      setDesignRunning(false);
      setDesignSlow(false);
    }
  };

  const handleAssign = async (courseId) => {
    setAssigning(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}/assign`, { method: 'POST', headers: h });
      if (res.ok) {
        const data = await res.json();
        setAssigned(prev => [...prev, { ...data, progress_pct: 0, total_lessons: 0, completed: 0, certificate_code: null }]);
      }
    } catch (e) { console.error(e); }
    setAssigning(null);
    setShowModal(false);
  };

  const handleRemove = async (courseId) => {
    setRemoving(courseId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/academy/customer/${customerId}/courses/${courseId}`, { method: 'DELETE', headers: h });
      if (res.ok) setAssigned(prev => prev.filter(a => a.course_id !== courseId));
    } catch (e) { console.error(e); }
    setRemoving(null);
  };

  const assignedIds = new Set(assigned.map(a => a.course_id));
  const available   = allCourses.filter(c => {
    const aud = c.target_audience || c.audience;
    return !assignedIds.has(c.id) && (aud === 'customer' || aud === 'both');
  });

  if (loadingCustomer) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
      <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
    </div>
  );

  return (
    // SCHRITT 8 — bottom nav clearance on mobile
    <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? 16 : 24, paddingBottom: isMobile ? 80 : 0 }}>

      {/* ── SCHRITT 2 — Header ── */}
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'flex-start' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? 8 : 12,
      }}>
        {/* Back + name */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0, flex: 1 }}>
          <button
            onClick={() => navigate(-1)}
            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', fontSize: 13, fontFamily: 'var(--font-sans)', padding: 0, display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}
          >← Zurück</button>
          <span style={{ color: 'var(--border-medium)' }}>·</span>
          <h1 style={{ fontSize: isMobile ? 17 : 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {customer?.contact_name || customer?.company_name || `Kunde #${customerId}`}
          </h1>
        </div>

        {/* Aktionsleiste */}
        <div style={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          gap: 8,
          marginBottom: 16,
          flexWrap: 'wrap',
        }}>
          <button onClick={() => setActiveTab('dateien')} style={{
            flex: isMobile ? 'none' : 1,
            padding: '9px 14px',
            background: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 500,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', gap: 6,
            justifyContent: 'center',
          }}>✏️ Projektdaten bearbeiten</button>

          <button onClick={() => setActiveTab('sitemap')} style={{
            flex: isMobile ? 'none' : 1,
            padding: '9px 14px',
            background: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 500,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', gap: 6,
            justifyContent: 'center',
          }}>📋 Briefing starten</button>

          <button onClick={() => setIsDesignerOpen(true)} style={{
            flex: isMobile ? 'none' : 1,
            padding: '9px 14px',
            background: 'var(--brand-primary)',
            color: 'var(--text-on-brand)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            display: 'flex', alignItems: 'center', gap: 6,
            justifyContent: 'center',
          }}>🌐 Website erstellen</button>
        </div>
      </div>

      {/* ── Verknüpftes Projekt ── */}
      <LinkedProjectSection leadId={customerId} headers={h} navigate={navigate} />

      {/* ── Tab navigation ── */}
      <div className="kc-tab-nav" style={{ display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 4, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        {[
          { id: 'dateien',     label: 'Dateien',     icon: '📎' },
          { id: 'audits',      label: 'Audits',      icon: '📋' },
          { id: 'sitemap',     label: 'Sitemap',     icon: '🗺️' },
          { id: 'design',      label: 'Design',      icon: '🎨' },
          { id: 'branddesign', label: 'Branddesign', icon: '🎨' },
          { id: 'pagespeed',   label: 'PageSpeed',   icon: '⚡' },
          { id: 'akademy',     label: 'Akademie',     icon: '🎓' },
          { id: 'cms',         label: 'CMS',         icon: '🔌' },
        ].map(({ id, label, icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{ flex: isMobile ? '0 0 auto' : 1, flexShrink: 0, padding: isMobile ? '7px 14px' : '8px 12px', borderRadius: 'var(--radius-md)', border: 'none', background: activeTab === id ? 'var(--bg-active)' : 'transparent', color: activeTab === id ? 'var(--brand-primary)' : 'var(--text-tertiary)', fontSize: 12, fontWeight: activeTab === id ? 500 : 400, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, whiteSpace: 'nowrap', transition: 'all 0.15s' }}
          >
            <span>{icon}</span>{label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      {activeTab === 'dateien'   && <ProjectFilesSection customerId={customerId} token={token} />}
      {activeTab === 'audits'    && <AuditHistorySection customerId={customerId} customer={customer} headers={h} />}

      {/* ── SITEMAP TAB ── */}
      {activeTab === 'sitemap' && (
        <ReiterSitemap
          isMobile={isMobile}
          addPageForm={addPageForm}
          addPageOpen={addPageOpen}
          addPageSaving={addPageSaving}
          createPage={createPage}
          downloadSitemapPdf={downloadSitemapPdf}
          editPageForm={editPageForm}
          editPageModal={editPageModal}
          editPageSaving={editPageSaving}
          generateKI={generateKI}
          kiConfirm={kiConfirm}
          kiGenerating={kiGenerating}
          leadId={leadId}
          loadSitemapPages={loadSitemapPages}
          saveEditPage={saveEditPage}
          setActiveDesignPage={setActiveDesignPage}
          setActiveTab={setActiveTab}
          setAddPageForm={setAddPageForm}
          setAddPageOpen={setAddPageOpen}
          setEditPageForm={setEditPageForm}
          setEditPageModal={setEditPageModal}
          setEditingPage={setEditingPage}
          setKiConfirm={setKiConfirm}
          sitemapLoaded={sitemapLoaded}
          sitemapLoading={sitemapLoading}
          sitemapPages={sitemapPages}
        />
      )}

      {/* ── DESIGN TAB ── */}
      {activeTab === 'design' && (
        <ReiterDesignseiten
          activeDesignPage={activeDesignPage}
          designError={designError}
          designResult={designResult}
          designRunning={designRunning}
          designSlow={designSlow}
          generateDesign={generateDesign}
          h={h}
          loadSitemapPages={loadSitemapPages}
          loadVersionsForPage={loadVersionsForPage}
          pageVersions={pageVersions}
          projectId={projectId}
          setActiveDesignPage={setActiveDesignPage}
          setActiveTab={setActiveTab}
          setDesignResult={setDesignResult}
          setPageVersions={setPageVersions}
          sitemapLoaded={sitemapLoaded}
          sitemapLoading={sitemapLoading}
          sitemapPages={sitemapPages}
        />
      )}
      {activeTab === 'pagespeed' && (
        leadId
          ? <PageSpeedSection leadId={leadId} headers={h} />
          : <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Lade Projektdaten…</div>
      )}

      {/* ── BRAND DESIGN TAB ── */}
      {activeTab === 'branddesign' && (
        <ReiterMarkendesign
          customerId={customerId}
          token={token}
          isMobile={isMobile}
          analyzing={analyzing}
          brandData={brandData}
          brandLoaded={brandLoaded}
          h={h}
          leadId={leadId}
          scanResults={scanResults}
          scanRunning={scanRunning}
          scanStep={scanStep}
          scraping={scraping}
          setAnalyzing={setAnalyzing}
          setBrandData={setBrandData}
          setBrandLoaded={setBrandLoaded}
          setScanResults={setScanResults}
          setScanRunning={setScanRunning}
          setScanStep={setScanStep}
          setScraping={setScraping}
        />
      )}

      {activeTab === 'cms'       && <CmsConnectionSection customerId={customerId} headers={h} />}
      {activeTab === 'akademy' && (
        <ReiterAkademie
          isMobile={isMobile}
          activeTab={activeTab}
          assigned={assigned}
          handleRemove={handleRemove}
          loadingAcademy={loadingAcademy}
          removing={removing}
          setShowModal={setShowModal}
        />
      )}

      {/* ── SCHRITT 6 — Assign Modal ── */}
      {showModal && (
        <>
          {/* Backdrop */}
          <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setShowModal(false))}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }}
            onClick={() => setShowModal(false)}
          />

          {/* Modal — slides from bottom on mobile, centered on desktop */}
          <div style={isMobile ? {
            position: 'fixed', bottom: 0, left: 0, right: 0,
            background: 'var(--bg-surface)',
            borderRadius: '16px 16px 0 0',
            boxShadow: '0 -8px 32px rgba(0,0,0,0.18)',
            maxHeight: '80vh',
            display: 'flex', flexDirection: 'column', zIndex: 101,
          } : {
            position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-xl)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.18)',
            width: 480, maxWidth: '90vw', maxHeight: '70vh',
            display: 'flex', flexDirection: 'column', zIndex: 101,
          }}>
            {/* Drag handle (mobile only) */}
            {isMobile && (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '12px 0 0' }}>
                <div style={{ width: 36, height: 4, background: 'var(--border-medium)', borderRadius: 2 }} />
              </div>
            )}

            <div style={{ padding: isMobile ? '14px 16px' : '18px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Kurs zuweisen</span>
              <button onClick={() => setShowModal(false)} style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
              {available.length === 0 ? (
                <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Alle verfügbaren Kurse wurden bereits zugewiesen.
                </div>
              ) : available.map(course => (
                <button
                  key={course.id}
                  onClick={() => handleAssign(course.id)}
                  disabled={assigning === course.id}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                    padding: isMobile ? '14px 12px' : '12px 14px',
                    background: 'transparent', border: 'none',
                    borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'left',
                    transition: 'background 0.1s', opacity: assigning === course.id ? 0.6 : 1,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: 'var(--radius-md)', flexShrink: 0,
                    background: course.thumbnail_url ? `url(${course.thumbnail_url}) center/cover` : 'linear-gradient(135deg, var(--brand-primary), var(--brand-primary-deeper))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                  }}>
                    {!course.thumbnail_url && '🎓'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{course.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{course.description}</div>
                  </div>
                  <span style={{ fontSize: 12, color: 'var(--brand-primary-mid)', fontWeight: 600, flexShrink: 0 }}>
                    {assigning === course.id ? '…' : '+ Zuweisen'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {isDesignerOpen && (
        <WebsiteDesigner
          customerId={customerId}
          customerName={customer?.contact_name || customer?.company_name}
          onClose={() => setIsDesignerOpen(false)}
        />
      )}

      {/* GrapesJS Editor Modal */}
      {editingPage && (
        <GrapesEditor
          key={editingPage.id}
          pageId={editingPage.id}
          pageName={editingPage.page_name}
          initialHtml={editingPage.gjs_html || editingPage.mockup_html || ''}
          onClose={() => setEditingPage(null)}
          onSave={({ html, css }) => {
            setSitemapPages(prev => prev.map(p =>
              p.id === editingPage.id
                ? { ...p, gjs_html: html, gjs_css: css || '', mockup_html: html }
                : p
            ));
            setEditingPage(null);
          }}
        />
      )}
    </div>
  );
}
