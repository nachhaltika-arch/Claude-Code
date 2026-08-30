import React, { useState, useEffect } from 'react';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import toast from 'react-hot-toast';
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
      {activeTab === 'sitemap' && (() => {
        if (!sitemapLoaded && !sitemapLoading) loadSitemapPages();
        const ST = {
          geplant:        { bg: '#EFF6FF', text: '#1D4ED8', label: 'Geplant' },
          in_bearbeitung: { bg: '#FEF9C3', text: '#92400E', label: 'In Bearb.' },
          freigegeben:    { bg: '#FEF3C7', text: '#B45309', label: 'Freigegeben' },
          live:           { bg: '#DCFCE7', text: '#166534', label: 'Live' },
        };
        const TI = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', sonstige: '📄' };
        const PAGE_TYPES = [
          { v: 'startseite', l: 'Startseite' }, { v: 'leistung', l: 'Leistung' },
          { v: 'info', l: 'Info' }, { v: 'vertrauen', l: 'Vertrauen' },
          { v: 'conversion', l: 'Conversion' }, { v: 'sonstige', l: 'Sonstige' },
        ];
        const inp = { width: '100%', padding: '7px 10px', fontSize: 13, border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' };
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={() => setAddPageOpen(o => !o)}
                style={{ padding: '8px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                ➕ Seite hinzufügen
              </button>
              <button onClick={() => setKiConfirm(true)} disabled={kiGenerating || !leadId}
                style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: kiGenerating ? 0.6 : 1 }}>
                {kiGenerating ? '⏳ Generiere…' : '🤖 KI-Vorlage laden'}
              </button>
              <button onClick={downloadSitemapPdf} disabled={!leadId}
                style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                📄 PDF herunterladen
              </button>
            </div>

            {/* KI Confirm */}
            {kiConfirm && (
              <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: '#92660A', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ flex: 1 }}>⚠️ KI-Vorlage überschreibt alle vorhandenen (Nicht-Pflicht-)Seiten.</span>
                <button onClick={generateKI} style={{ padding: '6px 14px', background: 'var(--warn)', color: 'var(--kc-black)', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Ja, generieren</button>
                <button onClick={() => setKiConfirm(false)} style={{ padding: '6px 14px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
              </div>
            )}

            {/* Add page form */}
            {addPageOpen && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>Neue Seite anlegen</div>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Seitenname *</label>
                    <input aria-label="Seitenname" value={addPageForm.page_name} onChange={e => setAddPageForm(f => ({ ...f, page_name: e.target.value }))} placeholder="z.B. Leistungen" style={inp} />
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
                    <select aria-label="Typ" value={addPageForm.page_type} onChange={e => setAddPageForm(f => ({ ...f, page_type: e.target.value }))} style={inp}>
                      {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Übergeordnete Seite</label>
                    <select aria-label="Übergeordnete Seite" value={addPageForm.parent_id} onChange={e => setAddPageForm(f => ({ ...f, parent_id: e.target.value }))} style={inp}>
                      <option value="">– Keine –</option>
                      {sitemapPages.filter(p => !p.ist_pflichtseite).map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={createPage} disabled={addPageSaving || !addPageForm.page_name.trim()}
                    style={{ padding: '7px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: addPageSaving ? 0.6 : 1 }}>
                    {addPageSaving ? 'Speichert…' : '💾 Anlegen'}
                  </button>
                  <button onClick={() => setAddPageOpen(false)}
                    style={{ padding: '7px 14px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Abbrechen
                  </button>
                </div>
              </div>
            )}

            {/* Page list */}
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {sitemapLoading ? (
                <div style={{ padding: 32, textAlign: 'center' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
                </div>
              ) : sitemapPages.filter(p => !p.ist_pflichtseite).length === 0 ? (
                <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>🗺️</div>
                  <div style={{ fontSize: 13 }}>Noch keine Seiten geplant.</div>
                </div>
              ) : (
                <>
                  {sitemapPages.filter(p => !p.ist_pflichtseite).map(page => {
                    const st = ST[page.status] || ST.geplant;
                    return (
                      <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderBottom: '1px solid var(--border-light)', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 17, flexShrink: 0 }}>{TI[page.page_type] || '📄'}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.page_name}</div>
                          {page.ziel_keyword && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{page.ziel_keyword}</div>}
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text, whiteSpace: 'nowrap', flexShrink: 0 }}>{st.label}</span>
                        {/* Action buttons */}
                        {(() => {
                          const aBtn = (bg, color) => ({
                            padding: '5px 11px', fontSize: 12, fontWeight: 500,
                            background: bg, color, border: 'none',
                            borderRadius: 'var(--radius-md)', cursor: 'pointer',
                            fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap',
                          });
                          return (
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              <button
                                onClick={() => { setEditPageModal(page); setEditPageForm({ page_name: page.page_name, page_type: page.page_type, ziel_keyword: page.ziel_keyword || '', zweck: page.zweck || '', cta_text: page.cta_text || '', status: page.status || 'geplant' }); }}
                                style={aBtn('#1a2332', '#fff')}>
                                ✏️ Bearbeiten
                              </button>
                              <button
                                onClick={() => { setActiveDesignPage(page); setActiveTab('design'); }}
                                style={aBtn('var(--brand-primary)', '#fff')}>
                                🎨 Design
                              </button>
                              <button
                                onClick={() => { setActiveDesignPage(page); setActiveTab('design'); }}
                                style={aBtn('#059669', '#fff')}>
                                📝 Content
                              </button>
                              <button
                                onClick={() => {
                                  if (page.mockup_html) {
                                    const w = window.open('', '_blank');
                                    w.document.write(page.mockup_html);
                                    w.document.close();
                                  } else {
                                    toast.error('Noch kein Design für diese Seite');
                                  }
                                }}
                                style={aBtn('var(--bg-elevated)', 'var(--text-primary)')}>
                                👁 Vorschau
                              </button>
                              <button
                                onClick={() => setEditingPage(page)}
                                style={aBtn('#7c3aed', '#fff')}>
                                🖊️ Editor
                              </button>
                            </div>
                          );
                        })()}
                      </div>
                    );
                  })}
                  {sitemapPages.filter(p => p.ist_pflichtseite).map((page, idx, arr) => {
                    const st = ST[page.status] || ST.geplant;
                    return (
                      <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderBottom: idx < arr.length - 1 ? '1px solid var(--border-light)' : 'none', background: 'var(--bg-app)' }}>
                        <span style={{ fontSize: 15, flexShrink: 0, color: 'var(--text-tertiary)' }}>🔒</span>
                        <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text-tertiary)' }}>{page.page_name}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: '#F3F4F6', color: '#6B7280' }}>⚖️ Pflicht</span>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text }}>{st.label}</span>
                      </div>
                    );
                  })}
                  <div style={{ padding: '8px 14px', fontSize: 11, color: 'var(--text-tertiary)', borderTop: '1px solid var(--border-light)' }}>
                    4 Pflichtseiten werden von KOMPAGNON rechtskonform befüllt.
                  </div>
                </>
              )}
            </div>

            {/* Edit page modal */}
            {editPageModal && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center', padding: isMobile ? 0 : 20 }}
                onClick={e => e.target === e.currentTarget && setEditPageModal(null)}>
                <div style={{ background: 'var(--bg-surface)', borderRadius: isMobile ? '16px 16px 0 0' : 'var(--radius-xl)', padding: 24, width: '100%', maxWidth: 480, maxHeight: isMobile ? '92vh' : '85vh', overflowY: 'auto' }}
                  onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Seite bearbeiten</span>
                    <button onClick={() => setEditPageModal(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)' }}>×</button>
                  </div>
                  {[
                    { k: 'page_name', label: 'Seitenname', type: 'text' },
                    { k: 'ziel_keyword', label: 'Ziel-Keyword', type: 'text' },
                    { k: 'zweck', label: 'Zweck / Beschreibung', type: 'textarea' },
                    { k: 'cta_text', label: 'CTA-Text', type: 'text' },
                  ].map(f => (
                    <div key={f.k} style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>{f.label}</label>
                      {f.type === 'textarea'
                        ? <textarea aria-label={f.label} value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} rows={3} style={{ ...inp, resize: 'vertical' }} />
                        : <input aria-label={f.label} type="text" value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} style={inp} />
                      }
                    </div>
                  ))}
                  <div style={{ marginBottom: 16 }}>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
                    <select aria-label="Typ" value={editPageForm.page_type || 'info'} onChange={e => setEditPageForm(p => ({ ...p, page_type: e.target.value }))} style={inp}>
                      {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
                    </select>
                  </div>
                  <div style={{ marginBottom: 20 }}>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Status</label>
                    <select aria-label="Status" value={editPageForm.status || 'geplant'} onChange={e => setEditPageForm(p => ({ ...p, status: e.target.value }))} style={inp}>
                      <option value="geplant">Geplant</option>
                      <option value="in_bearbeitung">In Bearbeitung</option>
                      <option value="freigegeben">Freigegeben</option>
                      <option value="live">Live</option>
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={saveEditPage} disabled={editPageSaving}
                      style={{ flex: 1, padding: '10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: editPageSaving ? 0.6 : 1 }}>
                      {editPageSaving ? 'Speichert…' : '💾 Speichern'}
                    </button>
                    <button onClick={() => setEditPageModal(null)}
                      style={{ flex: 1, padding: '10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      Abbrechen
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* ── DESIGN TAB ── */}
      {activeTab === 'design' && (() => {
        if (!sitemapLoaded && !sitemapLoading) loadSitemapPages();
        const PAGE_ICONS = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', kontakt: '✉️' };
        const contentPages = sitemapPages.filter(p => !p.ist_pflichtseite);

        // Auto-set first page if not set yet
        if (contentPages.length > 0 && !activeDesignPage) {
          const first = contentPages.find(p => p.page_type === 'startseite') || contentPages[0];
          setActiveDesignPage(first);
          if (!pageVersions[first.id]) loadVersionsForPage(first.id);
        }

        if (sitemapLoaded && contentPages.length === 0) {
          return (
            <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 24, textAlign: 'center' }}>
              <div style={{ fontSize: 24, marginBottom: 12 }}>🗺️</div>
              <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>Noch keine Sitemap-Seiten angelegt</div>
              <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 16 }}>Bitte zuerst im Sitemap-Tab die Website-Struktur planen.</div>
              <button onClick={() => setActiveTab('sitemap')} style={{ padding: '8px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                Zur Sitemap →
              </button>
            </div>
          );
        }

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── Page tab strip ── */}
            {contentPages.length > 0 && (
              <div style={{ display: 'flex', gap: 0, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none', borderBottom: '1px solid var(--border-light)', marginBottom: 4 }}>
                {contentPages.map(page => (
                  <button key={page.id}
                    onClick={() => {
                      setActiveDesignPage(page);
                      setDesignResult(null);
                      if (!pageVersions[page.id]) loadVersionsForPage(page.id);
                    }}
                    style={{
                      flexShrink: 0, padding: '8px 16px', border: 'none',
                      borderBottom: activeDesignPage?.id === page.id ? '2px solid var(--brand-primary)' : '2px solid transparent',
                      background: 'none', cursor: 'pointer', fontSize: 13,
                      fontWeight: activeDesignPage?.id === page.id ? 600 : 400,
                      color: activeDesignPage?.id === page.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                      whiteSpace: 'nowrap', marginBottom: -1, display: 'flex', alignItems: 'center', gap: 5,
                    }}>
                    {PAGE_ICONS[page.page_type] || '📄'} {page.page_name}
                    {(pageVersions[page.id]?.length || 0) > 0 && (
                      <span style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', borderRadius: 99, padding: '1px 6px', fontSize: 10 }}>
                        {pageVersions[page.id].length}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* ── Active page info + generator ── */}
            {activeDesignPage && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>🎨 KI-Entwurf generieren</div>

                {/* Active page info box */}
                <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '10px 14px', marginBottom: 14, fontSize: 13 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                    {PAGE_ICONS[activeDesignPage.page_type] || '📄'} {activeDesignPage.page_name}
                  </div>
                  {activeDesignPage.ziel_keyword && <div style={{ color: 'var(--text-secondary)' }}>🔑 Keyword: <strong>{activeDesignPage.ziel_keyword}</strong></div>}
                  {activeDesignPage.zweck && <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>🎯 Zweck: {activeDesignPage.zweck}</div>}
                </div>

                {!projectId && (
                  <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#92660A', marginBottom: 12 }}>
                    Noch kein verknüpftes Projekt gefunden — bitte zuerst ein Projekt anlegen.
                  </div>
                )}
                <button onClick={generateDesign} disabled={designRunning || !projectId}
                  style={{ padding: '10px 22px', borderRadius: 8, border: 'none', background: designRunning || !projectId ? 'var(--bg-muted)' : 'var(--brand-primary)', color: designRunning || !projectId ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 600, cursor: designRunning || !projectId ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  {designRunning && <span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />}
                  {designRunning ? 'Generiere Entwurf…' : '🎨 KI-Entwurf generieren'}
                </button>
                {designSlow && <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8 }}>⏳ Claude denkt gründlich nach — das kann bis zu 55 Sekunden dauern…</div>}
                {designError && <div style={{ background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-text)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--status-danger-text)', marginTop: 12 }}>{designError}</div>}
              </div>
            )}

            {/* ── Result preview ── */}
            {designResult && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Generierter Entwurf</div>
                  {typeof designResult === 'string' && designResult.startsWith('<') && (
                    <button onClick={() => window.open('data:text/html;charset=utf-8,' + encodeURIComponent(designResult), '_blank')}
                      style={{ padding: '5px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      👁 Im Browser öffnen
                    </button>
                  )}
                </div>
                {typeof designResult === 'string' && designResult.trim().startsWith('<') ? (
                  <iframe srcDoc={designResult} style={{ width: '100%', height: 600, border: '1px solid var(--border-light)', borderRadius: 8 }} title="Vorschau" />
                ) : (
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'inherit', lineHeight: 1.7, margin: 0 }}>{typeof designResult === 'string' ? designResult : JSON.stringify(designResult, null, 2)}</pre>
                )}
              </div>
            )}

            {/* ── Version history for active page ── */}
            {activeDesignPage && (pageVersions[activeDesignPage.id]?.length || 0) > 0 && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>🕓 Versionen — {activeDesignPage.page_name}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(pageVersions[activeDesignPage.id] || []).map(v => (
                    <div key={v.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13 }}>
                      <div>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{v.version_name}</span>
                        <span style={{ color: 'var(--text-tertiary)', marginLeft: 10, fontSize: 11 }}>{v.created_at}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={async () => {
                          const res = await fetch(`${API_BASE_URL}/api/designs/version/${v.id}`, { headers: h });
                          if (res.ok) { const d = await res.json(); setDesignResult(d.html_content); }
                        }} style={{ padding: '4px 10px', fontSize: 11, borderRadius: 5, border: '1px solid var(--border-medium)', background: 'var(--bg-surface)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                          👁 Laden
                        </button>
                        <button onClick={async () => {
                          if (!window.confirm('Version löschen?')) return;
                          await fetch(`${API_BASE_URL}/api/designs/version/${v.id}`, { method: 'DELETE', headers: h });
                          setPageVersions(prev => ({ ...prev, [activeDesignPage.id]: prev[activeDesignPage.id].filter(x => x.id !== v.id) }));
                        }} style={{ padding: '4px 10px', fontSize: 11, borderRadius: 5, border: '1px solid var(--status-danger-text)', background: 'transparent', color: 'var(--status-danger-text)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                          🗑
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        );
      })()}
      {activeTab === 'pagespeed' && (
        leadId
          ? <PageSpeedSection leadId={leadId} headers={h} />
          : <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Lade Projektdaten…</div>
      )}

      {/* ── BRAND DESIGN TAB ── */}
      {activeTab === 'branddesign' && (() => {
        const lid = leadId || customerId;
        const loadBrandData = () => {
          loadJson(`${API_BASE_URL}/api/branddesign/${lid}`, { headers: h }, { context: 'Markendesign' })
            .then(d => { if (d) setBrandData(d); });
        };

        if (!brandLoaded && lid) {
          setBrandLoaded(true);
          loadBrandData();
        }

        const scrapeWebsite = async () => {
          setScraping(true);
          try {
            await fetch(`${API_BASE_URL}/api/branddesign/${lid}/scrape`, { method: 'POST', headers: h });
            loadBrandData();
          } catch { toast.error('Scraping fehlgeschlagen'); }
          finally { setScraping(false); }
        };

        const analyzeScreenshot = async () => {
          setAnalyzing(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/analyze-screenshot`, { method: 'POST', headers: h });
            if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Fehler'); }
            const d = await res.json(); setBrandData(prev => ({ ...prev, ...d }));
            toast.success('Screenshot analysiert!');
          } catch (e) { toast.error(e.message || 'Analyse fehlgeschlagen'); }
          finally { setAnalyzing(false); }
        };

        const uploadPdf = async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          const formData = new FormData();
          formData.append('file', file);
          try {
            const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/upload-pdf`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              body: formData,
            });
            if (!res.ok) throw new Error('Upload fehlgeschlagen');
            toast.success('PDF hochgeladen!');
            loadBrandData();
          } catch (e) { toast.error(e.message); }
        };

        const downloadPdf = async () => {
          const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/pdf`, { headers: h });
          if (!res.ok) { toast.error('PDF nicht verfügbar'); return; }
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = brandData?.pdf_filename || 'brand.pdf'; a.click();
          URL.revokeObjectURL(url);
        };

        const primaryBtn = { padding: '9px 16px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
        const secondaryBtn = { padding: '9px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6 };
        const sectionLabel = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 };

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Status banner */}
            <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 13,
              background: brandData?.scraped_at ? '#dcfce7' : brandData?.scrape_failed ? '#fff7ed' : 'var(--bg-elevated)',
              color:      brandData?.scraped_at ? '#166534'  : brandData?.scrape_failed ? '#92400e'  : 'var(--text-tertiary)',
              border: `1px solid ${brandData?.scraped_at ? '#86efac' : brandData?.scrape_failed ? '#fcd34d' : 'var(--border-light)'}`,
            }}>
              {brandData?.scraped_at
                ? `✅ Branddesign erfasst · ${brandData.scraped_at}`
                : brandData?.scrape_failed
                  ? '⚠️ Website konnte nicht gescrapt werden — Screenshot-Analyse verfügbar'
                  : 'Noch kein Branddesign erfasst'}
            </div>

            {/* Action buttons */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={scrapeWebsite} disabled={scraping} style={primaryBtn}>
                {scraping ? '⏳ Wird gescrapt…' : '🌐 Website scrapen'}
              </button>
              <button onClick={analyzeScreenshot} disabled={analyzing} style={secondaryBtn}>
                {analyzing ? '⏳ KI analysiert…' : '🤖 Screenshot analysieren'}
              </button>
              <label style={{ ...secondaryBtn, cursor: 'pointer' }}>
                📄 PDF hochladen
                <input type="file" accept=".pdf" onChange={uploadPdf} style={{ display: 'none' }} />
              </label>
            </div>

            {/* Alles scannen — sequential carousel */}
            {(() => {
              const SCAN_STEPS = [
                { key: 'scrape',    label: 'Brand Scrape',    icon: '🌐', endpoint: () => fetch(`${API_BASE_URL}/api/branddesign/${lid}/scrape`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
                { key: 'fonts',     label: 'Font-Recherche',  icon: '🔤', endpoint: () => fetch(`${API_BASE_URL}/api/branddesign/${lid}/suggest-fonts`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
                { key: 'crawler',   label: 'Website-Crawler', icon: '🕷️', endpoint: async () => {
                  await fetch(`${API_BASE_URL}/api/crawler/start/${lid}`, { method: 'POST', headers: h });
                  for (let i = 0; i < 30; i++) {
                    await new Promise(r => setTimeout(r, 2000));
                    const s = await fetch(`${API_BASE_URL}/api/crawler/status/${lid}`, { headers: h }).then(r => r.json());
                    if (s.status === 'completed' || s.status === 'done') return s;
                    if (s.status === 'failed' || s.status === 'error') throw new Error('Crawler failed');
                  }
                  return { status: 'timeout' };
                }},
                { key: 'pagespeed', label: 'PageSpeed',       icon: '⚡', endpoint: () => fetch(`${API_BASE_URL}/api/leads/${lid}/pagespeed`, { method: 'POST', headers: h }).then(r => { if (r.ok) return r.json(); throw new Error(); }) },
              ];

              const runAllScans = async () => {
                setScanRunning(true);
                setScanResults([]);
                for (let i = 0; i < SCAN_STEPS.length; i++) {
                  setScanStep(i);
                  try {
                    const result = await SCAN_STEPS[i].endpoint();
                    setScanResults(prev => [...prev, { key: SCAN_STEPS[i].key, ok: true, data: result }]);
                    if (SCAN_STEPS[i].key === 'scrape' && result) setBrandData(result);
                  } catch {
                    setScanResults(prev => [...prev, { key: SCAN_STEPS[i].key, ok: false }]);
                  }
                }
                setScanStep(-1);
                setScanRunning(false);
                toast.success('Alle Scans abgeschlossen');
                loadBrandData();
              };

              return (
                <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: '14px 16px', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: scanRunning || scanResults.length > 0 ? 14 : 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Komplett-Scan</div>
                    <button onClick={runAllScans} disabled={scanRunning} style={{
                      padding: '7px 16px', fontSize: 12, fontWeight: 700,
                      background: scanRunning ? 'var(--border-medium)' : 'linear-gradient(135deg, #008EAA 0%, #006B80 100%)',
                      color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                      cursor: scanRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
                      display: 'flex', alignItems: 'center', gap: 6,
                    }}>
                      {scanRunning ? '⏳ Läuft…' : '🚀 Alles scannen'}
                    </button>
                  </div>

                  {(scanRunning || scanResults.length > 0) && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {SCAN_STEPS.map((step, i) => {
                        const result = scanResults.find(r => r.key === step.key);
                        const isActive = scanRunning && scanStep === i;
                        const isDone = !!result;
                        const isFailed = result && !result.ok;
                        const isPending = !isDone && !isActive;
                        return (
                          <div key={step.key} style={{
                            flex: '1 1 0', minWidth: isMobile ? '45%' : 120,
                            padding: '10px 12px', borderRadius: 'var(--radius-md)',
                            border: `2px solid ${isActive ? 'var(--kc-mid)' : isDone ? (isFailed ? '#e74c3c' : '#3B6D11') : 'var(--border-light)'}`,
                            background: isActive ? '#E6F6FA' : isDone ? (isFailed ? '#FEF2F2' : '#EAF4E0') : 'var(--bg-surface)',
                            transition: 'all 0.3s ease',
                            opacity: isPending && scanRunning ? 0.5 : 1,
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                              <span style={{ fontSize: 16 }}>{isDone ? (isFailed ? '❌' : '✅') : isActive ? '⏳' : step.icon}</span>
                              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{step.label}</span>
                            </div>
                            {isActive && (
                              <div style={{ height: 3, borderRadius: 2, background: 'var(--border-light)', overflow: 'hidden' }}>
                                <div style={{
                                  height: '100%', width: '60%', borderRadius: 2,
                                  background: 'var(--kc-mid)',
                                  animation: 'scanPulse 1.2s ease-in-out infinite alternate',
                                }} />
                              </div>
                            )}
                            {isDone && !isFailed && <div style={{ fontSize: 10, color: '#3B6D11', marginTop: 2 }}>Fertig</div>}
                            {isFailed && <div style={{ fontSize: 10, color: '#e74c3c', marginTop: 2 }}>Fehlgeschlagen</div>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Color palette */}
            {brandData?.primary_color && (
              <div>
                <div style={sectionLabel}>Farben</div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
                  {[
                    { label: 'Primär',       color: brandData.primary_color },
                    { label: 'Sekundär',     color: brandData.secondary_color },
                    { label: 'Akzent',       color: brandData.accent_color },
                    { label: 'Hintergrund',  color: brandData.background_color },
                    { label: 'Text',         color: brandData.text_color },
                  ].filter(c => c.color).map(({ label, color }) => (
                    <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <div role="button" tabIndex={0} onKeyDown={aufTaste(() => { navigator.clipboard.writeText(color); toast.success(color + ' kopiert!'); })}
                        style={{ width: 52, height: 52, borderRadius: 8, background: color, border: '1px solid var(--border-light)', cursor: 'pointer' }}
                        onClick={() => { navigator.clipboard.writeText(color); toast.success(color + ' kopiert!'); }}
                      />
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{label}</div>
                      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-primary)' }}>{color}</div>
                    </div>
                  ))}
                </div>
                {brandData.all_colors?.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {brandData.all_colors.map((c, i) => {
                      const hex = c.startsWith('#') ? c : '#' + c;
                      return (
                        <div role="button" tabIndex={0} onKeyDown={aufTaste(() => navigator.clipboard.writeText(hex))} key={i} style={{ width: 24, height: 24, borderRadius: 4, background: hex, border: '1px solid var(--border-light)', cursor: 'pointer' }}
                          onClick={() => navigator.clipboard.writeText(hex)} title={hex} />
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Fonts */}
            {(brandData?.font_primary || brandData?.font_secondary) && (
              <div>
                <div style={sectionLabel}>Schriften</div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {brandData.font_primary && (
                    <div style={{ background: 'var(--bg-elevated)', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 4 }}>Primär</div>
                      <div style={{ fontSize: 15, fontFamily: brandData.font_primary }}>{brandData.font_primary}</div>
                    </div>
                  )}
                  {brandData.font_secondary && (
                    <div style={{ background: 'var(--bg-elevated)', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-light)' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 4 }}>Sekundär</div>
                      <div style={{ fontSize: 15, fontFamily: brandData.font_secondary }}>{brandData.font_secondary}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Design style + notes */}
            {brandData?.design_style && (
              <div>
                <div style={sectionLabel}>Designstil</div>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  <span style={{ background: 'var(--bg-elevated)', padding: '4px 10px', borderRadius: 20, fontSize: 12, border: '1px solid var(--border-light)' }}>
                    {brandData.design_style}
                  </span>
                  {brandData.font_style && (
                    <span style={{ background: 'var(--bg-elevated)', padding: '4px 10px', borderRadius: 20, fontSize: 12, border: '1px solid var(--border-light)' }}>
                      {brandData.font_style}
                    </span>
                  )}
                </div>
                {brandData.brand_notes && (
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, background: 'var(--bg-elevated)', padding: 12, borderRadius: 8, border: '1px solid var(--border-light)' }}>
                    {brandData.brand_notes}
                  </div>
                )}
              </div>
            )}

            {/* PDF section */}
            {brandData?.pdf_filename && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 8 }}>
                <span style={{ fontSize: 20 }}>📄</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{brandData.pdf_filename}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Branddesign-Dokument</div>
                </div>
                <button onClick={downloadPdf} style={{ fontSize: 12, padding: '5px 10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                  ⬇ Download
                </button>
              </div>
            )}

          </div>
        );
      })()}

      {activeTab === 'cms'       && <CmsConnectionSection customerId={customerId} headers={h} />}
      {activeTab === 'akademy'   && <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>

        {/* Section header — stacked on mobile */}
        <div style={{
          padding: isMobile ? '12px 16px' : '16px 20px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: isMobile ? 'stretch' : 'center',
          justifyContent: 'space-between',
          gap: isMobile ? 10 : 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>🎓</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Akademie</span>
            {!loadingAcademy && assigned.length > 0 && (
              <span style={{ background: 'var(--brand-primary-light)', color: 'var(--brand-primary-mid)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600, padding: '2px 8px' }}>
                {assigned.length}
              </span>
            )}
          </div>
          {/* Full-width button on mobile */}
          <button
            onClick={() => setShowModal(true)}
            style={{
              padding: '8px 14px',
              background: 'var(--brand-primary)',
              color: 'var(--text-inverse)',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              ...(isMobile ? { width: '100%' } : {}),
            }}
          >+ Kurs zuweisen</button>
        </div>

        {/* SCHRITT 4 — Course table with horizontal scroll */}
        <div style={{ padding: '4px 0' }}>
          {loadingAcademy ? (
            <div style={{ padding: '32px 20px', display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
            </div>
          ) : assigned.length === 0 ? (
            <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>📚</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>Noch keine Kurse zugewiesen</div>
              <div style={{ fontSize: 12 }}>Klicke auf „+ Kurs zuweisen" um diesem Kunden Zugriff zu geben.</div>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              {/* Table header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                minWidth: 520, gap: 12, padding: '8px 20px',
                fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                borderBottom: '1px solid var(--border-light)',
              }}>
                <span>Kurs</span><span>Fortschritt</span><span>Zertifikat</span><span />
              </div>

              {assigned.map(row => (
                <div
                  key={row.course_id}
                  style={{
                    display: 'grid', gridTemplateColumns: '1fr 180px 120px 40px',
                    minWidth: 520, gap: 12, padding: '12px 20px',
                    alignItems: 'center', borderBottom: '1px solid var(--border-light)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-app)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Course name */}
                  <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                    {row.course_title}
                    {row.assigned_at && (
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Zugewiesen: {row.assigned_at}</div>
                    )}
                  </div>

                  {/* Progress bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                        {row.total_lessons > 0 ? `${row.completed}/${row.total_lessons}` : '—'}
                      </span>
                      <span style={{ fontSize: 10, fontWeight: 600, color: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--text-tertiary)' }}>
                        {row.progress_pct}%
                      </span>
                    </div>
                    <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${row.progress_pct}%`, height: '100%', background: row.progress_pct === 100 ? 'var(--status-success-text)' : 'var(--brand-primary)', borderRadius: 3, transition: 'width 0.4s' }} />
                    </div>
                  </div>

                  {/* Certificate */}
                  <div>
                    {row.certificate_code ? (
                      <a
                        href={`/academy/certificate/${row.certificate_code}`}
                        target="_blank" rel="noreferrer"
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: 4,
                          padding: '3px 10px',
                          background: 'var(--status-success-bg)',
                          color: 'var(--status-success-text)',
                          borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 700,
                          textDecoration: 'none',
                        }}
                      >🏆 Zertifikat</a>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                    )}
                  </div>

                  {/* Remove button */}
                  <button
                    onClick={() => handleRemove(row.course_id)}
                    disabled={removing === row.course_id}
                    title="Kurs entfernen"
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--status-danger-text)', padding: 4,
                      borderRadius: 'var(--radius-sm)',
                      opacity: removing === row.course_id ? 0.4 : 0.6,
                      display: 'flex', alignItems: 'center', transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={e => e.currentTarget.style.opacity = removing === row.course_id ? '0.4' : '0.6'}
                  >
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M2.5 4h11M6 4V2.5h4V4M4 4l.8 9.5h6.4L12 4"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>}

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
