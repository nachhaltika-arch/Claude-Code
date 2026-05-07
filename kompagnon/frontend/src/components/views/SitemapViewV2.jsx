/**
 * SitemapViewV2 — Phase 1 des Relume-Style-Sitemap-Rebuilds.
 *
 * Layout:
 *   - Horizontale Anordnung der Pages, Tree-Connectors fuer Hierarchie
 *   - Page-Karten zeigen die ganze Section-Liste inline (mit Description)
 *   - "+" zwischen Pages (sibling) und zwischen Sections (add)
 *   - "..." Context-Menu pro Page mit Aktionen (Duplicate / Delete / etc.)
 *
 * Phase 2 ergaenzt eine linke Add-Sidebar.
 * Phase 3 ergaenzt Drag-and-Drop fuer Sections.
 * Phase 4 ergaenzt Page-Groups (eltern → wiederholte Kinder mit shared sections).
 *
 * Backend-Endpoints (alle existierend in routers/sitemap.py):
 *   GET    /api/sitemap/{leadId}              — pages laden
 *   POST   /api/sitemap/{leadId}/pages        — Page anlegen
 *   PUT    /api/sitemap/pages/{id}            — Page-Details aktualisieren (incl sections)
 *   DELETE /api/sitemap/pages/{id}            — Page loeschen (Pflichtseiten geblockt)
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

// Spiegelung des Backend-SECTION_CATALOG (routers/sitemap.py).
const SECTION_CATALOG = {
  header_nav:          'Sticky-Header: Logo + Hauptnavigation + ggf. CTA-Button',
  hero_value_equation: 'Hero mit Hormozi-Outcome+Time+Effort-Versprechen (Startseite)',
  hero_service:        'Hero für Service-Detail-Page mit klarem Outcome',
  hero_minimal:        'Kompakter Hero — für Über uns / Kontakt / Rechtliches',
  problem:             'Pain-Point-Section — typische Schmerzen der Zielgruppe',
  offer_stack:         'Hormozi-Wertbox: EUR-Positionen + Gesamtwert + Anker',
  process_steps:       '4-6 nummerierte Schritte mit Zeitangabe',
  guarantee_block:     '5 AGB-konforme Garantien (Risk Reversal)',
  urgency_block:       'Echte Stichtage (BAFA/GEG/Slot-Cap)',
  trust_strip:         'Logo-Streifen (Innung, Hersteller, Zertifikate)',
  fallstudien_3:       '3 Fallstudien-Cards mit Zahlen',
  service_grid:        'Übersicht aller Services',
  team:                'Team-/Meister-Vorstellung mit Fotos',
  faq:                 'Allgemeine FAQ — 8-12 Fragen',
  faq_service:         'Service-spezifische FAQ',
  content_richtext:    'Reiner Fließtext-Block — für Info-/Rechtsseiten',
  cta_inline:          'Inline-CTA zwischen Sections',
  cta_final:           'Finale CTA + Sticky-Mobile-Bottom-Bar',
  contact_form:        'Kontakt-Formular mit Tel/Mail/WhatsApp',
  footer_legal:        'Footer mit Pflicht-Links',
};

// Lesbare Labels fuer die Section-Keys in der Page-Card.
const SECTION_LABEL = {
  header_nav:          'Header / Navigation',
  hero_value_equation: 'Hero (Value-Equation)',
  hero_service:        'Hero (Service)',
  hero_minimal:        'Hero (Minimal)',
  problem:             'Problem-Section',
  offer_stack:         'Offer-Stack',
  process_steps:       'Prozess-Schritte',
  guarantee_block:     'Garantien',
  urgency_block:       'Urgency / Stichtage',
  trust_strip:         'Trust-Strip',
  fallstudien_3:       'Fallstudien (3)',
  service_grid:        'Service-Grid',
  team:                'Team',
  faq:                 'FAQ',
  faq_service:         'FAQ (Service)',
  content_richtext:    'Fließtext-Block',
  cta_inline:          'CTA (inline)',
  cta_final:           'CTA (final)',
  contact_form:        'Kontakt-Formular',
  footer_legal:        'Footer',
};

const PAGE_TYPE_OPTIONS = [
  { value: 'startseite', label: 'Startseite' },
  { value: 'leistung',   label: 'Leistungsseite' },
  { value: 'info',       label: 'Info-Seite' },
  { value: 'vertrauen',  label: 'Vertrauensseite' },
  { value: 'conversion', label: 'Kontakt' },
  { value: 'rechtlich',  label: 'Rechtlich' },
  { value: 'sonstige',   label: 'Sonstige' },
  { value: 'ground',     label: 'Übersicht' },
];

const TYPE_META = {
  startseite: { label: 'Startseite',      icon: '🏠' },
  leistung:   { label: 'Leistungsseite',  icon: '🔧' },
  info:       { label: 'Info-Seite',      icon: 'ℹ️' },
  vertrauen:  { label: 'Vertrauensseite', icon: '⭐' },
  conversion: { label: 'Kontakt',         icon: '📞' },
  rechtlich:  { label: 'Rechtlich',       icon: '⚖️' },
  sonstige:   { label: 'Sonstige',        icon: '📄' },
  ground:     { label: 'Übersicht',       icon: '📋' },
};

const PAGE_W = 280;       // Pixel-Breite einer Page-Karte
const COL_GAP = 40;       // Abstand zwischen Geschwister-Spalten
const ROW_GAP = 56;       // Abstand zwischen Eltern und Kinder-Reihe (inkl. Connector)

// ─────────────────────────────────────────────────────────────────────────────

export default function SitemapViewV2({
  projectId,
  leadId,
  wireframeData,
  onGenerateWireframe,
  onNavigateToWireframe,
  onRegenerateSitemap,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [addPageState, setAddPageState] = useState(null);   // null | { parent_id, position }
  const [addSectionState, setAddSectionState] = useState(null); // null | { page_id, position }

  // Pages laden
  const loadPages = useCallback(() => {
    if (!leadId) return;
    setLoading(true);
    setError('');
    fetch(`${API_BASE_URL}/api/sitemap/${leadId}`, { headers })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => setPages(Array.isArray(data) ? data : data.pages || []))
      .catch((e) => setError(e.message || 'Sitemap konnte nicht geladen werden'))
      .finally(() => setLoading(false));
  }, [leadId, headers]);

  useEffect(() => { loadPages(); }, [loadPages]);

  // ── Mutationen ────────────────────────────────────────────────────────────

  const savePageDetails = useCallback(async (pageId, updates) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${pageId}`, {
        method: 'PUT', headers,
        body: JSON.stringify(updates),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        throw new Error(typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`);
      }
      const fresh = await res.json();
      setPages((prev) => prev.map((p) => (p.id === pageId ? fresh : p)));
      toast.success('Gespeichert');
      return fresh;
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
      return null;
    }
  }, [headers]);

  const createPage = useCallback(async (parentId, name, pageType, position) => {
    if (!leadId || !name?.trim()) return null;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/pages`, {
        method: 'POST', headers,
        body: JSON.stringify({
          page_name: name.trim(),
          page_type: pageType || 'info',
          parent_id: parentId || null,
          position: position ?? pages.length,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const created = await res.json();
      toast.success(`„${created.page_name}" angelegt`);
      loadPages();
      return created;
    } catch (e) {
      toast.error(`Anlegen fehlgeschlagen: ${e.message}`);
      return null;
    }
  }, [leadId, headers, pages.length, loadPages]);

  const deletePage = useCallback(async (pageId) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht gelöscht werden.');
      return;
    }
    if (!window.confirm(`„${target.page_name}" wirklich löschen?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${pageId}`, {
        method: 'DELETE', headers,
      });
      if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      toast.success(`„${target.page_name}" gelöscht`);
      if (selectedPageId === pageId) setSelectedPageId(null);
      loadPages();
    } catch (e) {
      toast.error(`Löschen fehlgeschlagen: ${e.message}`);
    }
  }, [headers, pages, selectedPageId, loadPages]);

  // Duplicate = Page anlegen mit identischen Sections + selber Eltern
  const duplicatePage = useCallback(async (pageId) => {
    const src = pages.find((p) => p.id === pageId);
    if (!src) return;
    const dup = await createPage(src.parent_id, `${src.page_name} (Kopie)`, src.page_type, pages.length);
    if (dup && Array.isArray(src.sections) && src.sections.length > 0) {
      // Sections kopieren — Backend akzeptiert sections im PUT
      await savePageDetails(dup.id, { sections: src.sections });
    }
  }, [pages, createPage, savePageDetails]);

  const addSectionToPage = useCallback((pageId, sectionKey, position) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    if (!sectionKey || !SECTION_CATALOG[sectionKey]) return;
    const next = Array.isArray(target.sections) ? [...target.sections] : [];
    const insertAt = typeof position === 'number' ? position : next.length;
    next.splice(insertAt, 0, sectionKey);
    savePageDetails(pageId, { sections: next });
  }, [pages, savePageDetails]);

  const removeSectionFromPage = useCallback((pageId, idx) => {
    const target = pages.find((p) => p.id === pageId);
    if (!target) return;
    const next = (target.sections || []).filter((_, i) => i !== idx);
    savePageDetails(pageId, { sections: next });
  }, [pages, savePageDetails]);

  // ── Tree-Struktur: Pages nach parent_id gruppieren ────────────────────────

  const tree = useMemo(() => {
    const byParent = new Map();
    pages.forEach((p) => {
      const key = p.parent_id ?? 'root';
      if (!byParent.has(key)) byParent.set(key, []);
      byParent.get(key).push(p);
    });
    // Innerhalb einer Ebene nach position sortieren
    byParent.forEach((arr) => arr.sort((a, b) => (a.position ?? 0) - (b.position ?? 0)));
    return byParent;
  }, [pages]);

  const topLevelPages = tree.get('root') || [];

  const blocksByPageId = useMemo(() => {
    const map = new Map();
    (wireframeData?.pages || []).forEach((p) => {
      map.set(p.page_id, p.blocks || []);
    });
    return map;
  }, [wireframeData]);

  const totalBlocks = (wireframeData?.pages || []).reduce(
    (sum, p) => sum + (p.blocks?.length || 0), 0,
  );

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', fontFamily: 'var(--font-sans, system-ui)',
      background: '#f8fafc',
    }}>
      {/* Topbar */}
      <div style={{
        flexShrink: 0,
        padding: '14px 24px',
        background: '#fff',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 16, flexWrap: 'wrap',
      }}>
        <div>
          <h1 style={{
            fontSize: 20, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>
            Sitemap
          </h1>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
            {pages.length} Seite{pages.length === 1 ? '' : 'n'} ·
            {' '}{totalBlocks} Block{totalBlocks === 1 ? '' : 's'} im Wireframe
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => setAddPageState({ parent_id: null, position: pages.length })}
            style={btnSecondary}
          >
            + Neue Seite
          </button>
          <button
            type="button"
            onClick={() => onRegenerateSitemap?.(0)}
            style={btnSecondary}
          >
            🔄 Sitemap regenerieren
          </button>
          <button
            type="button"
            onClick={onGenerateWireframe} disabled={pages.length === 0}
            style={{
              ...btnPrimary,
              cursor: pages.length === 0 ? 'not-allowed' : 'pointer',
              opacity: pages.length === 0 ? 0.5 : 1,
            }}
          >
            ⚡ KI-Wireframe erzeugen
          </button>
          <button
            type="button" onClick={onNavigateToWireframe} disabled={totalBlocks === 0}
            style={{
              ...btnTeal,
              cursor: totalBlocks === 0 ? 'not-allowed' : 'pointer',
              opacity: totalBlocks === 0 ? 0.5 : 1,
            }}
          >
            Zu Wireframe →
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        <div style={{
          flex: 1, overflow: 'auto',
          padding: '40px 24px',
        }}>
          {loading && <div style={{ color: '#64748b' }}>Sitemap wird geladen…</div>}
          {error && (
            <div style={{ background: '#FEF2F2', color: '#991B1B', padding: 12, borderRadius: 8, fontSize: 13 }}>
              {error}
            </div>
          )}

          {!loading && !error && pages.length === 0 && (
            <EmptyState
              onAddPage={() => setAddPageState({ parent_id: null, position: 0 })}
              onRegenerateSitemap={onRegenerateSitemap}
            />
          )}

          {!loading && !error && pages.length > 0 && (
            <div style={{
              display: 'flex', alignItems: 'flex-start',
              gap: COL_GAP / 2, minWidth: 'max-content',
            }}>
              {topLevelPages.map((p, idx) => (
                <PageColumn
                  key={p.id}
                  page={p} tree={tree}
                  selectedPageId={selectedPageId}
                  onSelect={setSelectedPageId}
                  onAddSibling={(afterPosition) => setAddPageState({ parent_id: null, position: afterPosition })}
                  onAddChild={(parentId) => setAddPageState({ parent_id: parentId, position: 0 })}
                  onDelete={deletePage}
                  onDuplicate={duplicatePage}
                  onAddSection={(pageId, position) => setAddSectionState({ page_id: pageId, position })}
                  onRemoveSection={removeSectionFromPage}
                  isFirstSibling={idx === 0}
                />
              ))}
              {/* "+" am rechten Ende: neue Top-Level-Seite */}
              <AddPagePlus
                onClick={() => setAddPageState({ parent_id: null, position: pages.length })}
                large
              />
            </div>
          )}
        </div>

        {/* Side-Panel: Page-Details */}
        {selectedPageId && (
          <PageDetailPanel
            page={pages.find((p) => p.id === selectedPageId) || null}
            onClose={() => setSelectedPageId(null)}
            onSave={(updates) => savePageDetails(selectedPageId, updates)}
            onDelete={() => deletePage(selectedPageId)}
          />
        )}
      </div>

      {/* Add-Page-Dialog */}
      {addPageState && (
        <AddPageDialog
          parentId={addPageState.parent_id}
          parentName={addPageState.parent_id
            ? (pages.find((p) => p.id === addPageState.parent_id)?.page_name || '')
            : null}
          onClose={() => setAddPageState(null)}
          onSubmit={async (name, type) => {
            const created = await createPage(addPageState.parent_id, name, type, addPageState.position);
            if (created) setAddPageState(null);
          }}
        />
      )}

      {/* Add-Section-Dialog */}
      {addSectionState && (
        <AddSectionDialog
          existingSections={(pages.find((p) => p.id === addSectionState.page_id)?.sections) || []}
          onClose={() => setAddSectionState(null)}
          onPick={(sectionKey) => {
            addSectionToPage(addSectionState.page_id, sectionKey, addSectionState.position);
            setAddSectionState(null);
          }}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PageColumn — eine Page-Karte + ihre Kinder als Reihe darunter (mit Connectors)
// ─────────────────────────────────────────────────────────────────────────────

function PageColumn({
  page, tree,
  selectedPageId, onSelect,
  onAddSibling, onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection,
  isFirstSibling = false,
}) {
  const children = tree.get(page.id) || [];
  const isActive = selectedPageId === page.id;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: COL_GAP / 2 }}>
        <PageCard
          page={page}
          isActive={isActive}
          onSelect={onSelect}
          onAddChild={onAddChild}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
          onAddSection={onAddSection}
          onRemoveSection={onRemoveSection}
        />
        {/* "+" zwischen Geschwistern (rechts von dieser Karte) */}
        <AddPagePlus
          onClick={() => onAddSibling((page.position ?? 0) + 1)}
        />
      </div>

      {/* Kinder-Row: gleiche Logik rekursiv */}
      {children.length > 0 && (
        <div style={{ marginTop: ROW_GAP, position: 'relative' }}>
          {/* Vertikaler Connector von Eltern-Bottom zu Kinder-Reihe */}
          <div style={{
            position: 'absolute',
            top: -ROW_GAP,
            left: '50%', transform: 'translateX(-50%)',
            width: 1, height: ROW_GAP / 2,
            background: '#cbd5e1',
          }} />
          {/* Horizontale Linie ueber alle Kinder */}
          {children.length > 1 && (
            <div style={{
              position: 'absolute',
              top: -ROW_GAP / 2,
              left: 0, right: 0,
              height: 1,
              background: '#cbd5e1',
            }} />
          )}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: COL_GAP / 2 }}>
            {children.map((c, idx) => (
              <ChildPageColumn
                key={c.id}
                page={c} tree={tree}
                selectedPageId={selectedPageId}
                onSelect={onSelect}
                onAddSibling={(afterPos) => onAddChild(page.id, afterPos)}
                onAddChild={onAddChild}
                onDelete={onDelete}
                onDuplicate={onDuplicate}
                onAddSection={onAddSection}
                onRemoveSection={onRemoveSection}
                isFirstSibling={idx === 0}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Wrapper fuer rekursives Rendering — children verhalten sich gleich.
// Eigene Komponente damit die Connector-Linie pro Kind individuell ist.
function ChildPageColumn(props) {
  return (
    <div style={{ position: 'relative' }}>
      {/* Vertikale Linie ueber jedem Kind, verbindet zur horizontalen Eltern-Linie */}
      <div style={{
        position: 'absolute',
        top: -ROW_GAP / 2,
        left: '50%', transform: 'translateX(-50%)',
        width: 1, height: ROW_GAP / 2,
        background: '#cbd5e1',
      }} />
      <PageColumn {...props} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PageCard — Header + Section-Liste + Add-Section-Button
// ─────────────────────────────────────────────────────────────────────────────

function PageCard({
  page,
  isActive, onSelect,
  onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection,
}) {
  const meta = TYPE_META[page.page_type] || TYPE_META.info;
  const sections = Array.isArray(page.sections) ? page.sections : [];
  const [menuOpen, setMenuOpen] = useState(false);
  const cardRef = useRef(null);

  // Outside click schliesst Menu
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e) => {
      if (!cardRef.current?.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const cardClick = (e) => {
    if (e.target.closest('[data-noselect]')) return;
    onSelect?.(page.id);
  };

  return (
    <div
      ref={cardRef}
      onClick={cardClick}
      style={{
        position: 'relative',
        width: PAGE_W, flexShrink: 0,
        background: '#fff',
        border: isActive ? `2px solid ${KC_MID}` : '1px solid #e2e8f0',
        borderRadius: 10,
        boxShadow: isActive
          ? `0 4px 16px ${KC_MID}33`
          : '0 1px 3px rgba(0,0,0,0.04)',
        cursor: 'pointer',
        overflow: 'visible',
      }}
    >
      {/* Page-Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 12px',
        background: '#f8fafc',
        borderBottom: '1px solid #e2e8f0',
        borderTopLeftRadius: 10, borderTopRightRadius: 10,
      }}>
        <span style={{ fontSize: 14, flexShrink: 0 }}>{meta.icon}</span>
        <div style={{
          flex: 1, minWidth: 0,
          fontSize: 12, fontWeight: 700, color: KC_DARK,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {page.page_name}
        </div>
        {page.ist_pflichtseite && (
          <span title="Pflichtseite" style={{ fontSize: 11 }}>🔒</span>
        )}
        <button
          type="button" data-noselect
          onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v); }}
          aria-label="Menü"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#64748b', fontSize: 16, lineHeight: 1, padding: '0 4px',
            fontWeight: 700,
          }}
        >
          ⋯
        </button>
      </div>

      {/* Section-Liste */}
      <div style={{ padding: '8px 12px 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {sections.length === 0 ? (
          <div data-noselect style={{
            padding: '20px 8px', textAlign: 'center',
            color: '#94a3b8', fontSize: 11, fontStyle: 'italic',
          }}>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, 0); }}
              style={{
                width: '100%', padding: '10px 12px',
                background: '#f8fafc', border: '1px dashed #cbd5e1',
                borderRadius: 6, fontSize: 12, fontWeight: 700,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
                marginBottom: 6,
              }}
            >
              + Section
            </button>
            <div style={{ fontSize: 10, color: '#cbd5e1' }}>oder</div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                // Phase B: KI-Generate ist im Wireframe-View — hier nur Hint
                toast('Tipp: Wechsel in den Wireframe-View für KI-Content-Generierung.');
              }}
              style={{
                marginTop: 6, padding: '8px 12px',
                background: 'transparent', border: 'none',
                fontSize: 11, color: '#7c3aed', fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              ✨ Generate content
            </button>
          </div>
        ) : (
          <>
            {sections.map((key, idx) => (
              <SectionRow
                key={`${key}-${idx}`}
                sectionKey={key} idx={idx}
                onRemove={() => onRemoveSection(page.id, idx)}
                onAddBelow={() => onAddSection(page.id, idx + 1)}
              />
            ))}
            {/* "+" unter der letzten Section */}
            <button
              type="button" data-noselect
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, sections.length); }}
              style={{
                marginTop: 4, padding: '6px 10px',
                background: 'transparent', border: '1px dashed #cbd5e1',
                borderRadius: 6, fontSize: 11, fontWeight: 600,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              + Section hinzufügen
            </button>
          </>
        )}
      </div>

      {/* Context-Menu (Dropdown) */}
      {menuOpen && (
        <div
          data-noselect
          style={{
            position: 'absolute', top: 38, right: 8, zIndex: 50,
            background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
            boxShadow: '0 6px 20px rgba(0,0,0,0.10)',
            minWidth: 180, padding: 4,
            display: 'flex', flexDirection: 'column',
          }}
        >
          <MenuItem onClick={() => { setMenuOpen(false); onAddChild(page.id); }}>+ Sub-Seite</MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onAddSection(page.id, (page.sections || []).length); }}>+ Section</MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onDuplicate(page.id); }}>📋 Duplizieren</MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onSelect(page.id); }}>✏️ Bearbeiten…</MenuItem>
          <div style={{ height: 1, background: '#e2e8f0', margin: '4px 2px' }} />
          <MenuItem
            danger
            disabled={page.ist_pflichtseite}
            onClick={() => { setMenuOpen(false); onDelete(page.id); }}
          >
            🗑 Löschen
          </MenuItem>
        </div>
      )}
    </div>
  );
}

function MenuItem({ children, onClick, danger, disabled }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      style={{
        background: 'transparent', border: 'none',
        padding: '6px 10px', textAlign: 'left',
        fontSize: 12, fontWeight: 600,
        color: disabled ? '#cbd5e1' : danger ? '#dc2626' : '#475569',
        cursor: disabled ? 'not-allowed' : 'pointer',
        borderRadius: 4, fontFamily: 'inherit',
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = danger ? '#FEF2F2' : '#f1f5f9';
      }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      {children}
    </button>
  );
}

// Eine Section-Reihe in der Page-Karte
function SectionRow({ sectionKey, idx, onRemove, onAddBelow }) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';
  const [hover, setHover] = useState(false);

  return (
    <div
      data-noselect
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        padding: '8px 10px',
        background: hover ? '#f8fafc' : '#fff',
        border: '1px solid #e2e8f0', borderRadius: 6,
        fontSize: 11,
        cursor: 'default',
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2,
      }}>
        <span style={{ color: '#cbd5e1', fontVariantNumeric: 'tabular-nums', minWidth: 14, fontSize: 10 }}>
          {idx + 1}
        </span>
        <span style={{ fontWeight: 700, color: KC_DARK, flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
        </span>
        {hover && (
          <button
            type="button" onClick={(e) => { e.stopPropagation(); onRemove(); }}
            aria-label="Section entfernen"
            style={{
              background: 'none', border: 'none',
              fontSize: 12, color: '#dc2626', cursor: 'pointer', padding: 0,
            }}
          >
            ×
          </button>
        )}
      </div>
      <div style={{
        fontSize: 10, color: '#64748b',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {desc}
      </div>
      {hover && (
        <button
          type="button" onClick={(e) => { e.stopPropagation(); onAddBelow(); }}
          aria-label="Section darunter einfügen"
          style={{
            position: 'absolute',
            bottom: -10, left: '50%', transform: 'translateX(-50%)',
            width: 18, height: 18, borderRadius: '50%',
            background: '#fff', border: `1px solid ${KC_MID}`,
            color: KC_MID, fontSize: 12, lineHeight: 1,
            cursor: 'pointer', zIndex: 5,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: 0, fontFamily: 'inherit', fontWeight: 700,
          }}
        >
          +
        </button>
      )}
    </div>
  );
}

// "+"-Button zwischen / nach Pages
function AddPagePlus({ onClick, large = false }) {
  const size = large ? 36 : 28;
  return (
    <button
      type="button" onClick={onClick}
      aria-label="Seite hinzufügen"
      style={{
        flexShrink: 0,
        marginTop: 18,
        width: size, height: size, borderRadius: '50%',
        background: '#fff', border: `1.5px dashed ${KC_MID}`,
        color: KC_MID, fontSize: large ? 18 : 16, lineHeight: 1, fontWeight: 700,
        cursor: 'pointer', fontFamily: 'inherit',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = KC_MID;
        e.currentTarget.style.color = '#fff';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = '#fff';
        e.currentTarget.style.color = KC_MID;
      }}
    >
      +
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// EmptyState
// ─────────────────────────────────────────────────────────────────────────────

function EmptyState({ onAddPage, onRegenerateSitemap }) {
  return (
    <div style={{
      maxWidth: 480, margin: '60px auto',
      border: '2px dashed #cbd5e1', borderRadius: 16, padding: 40,
      textAlign: 'center', color: '#64748b', background: '#fff',
    }}>
      <div style={{ fontSize: 36, marginBottom: 8 }}>🗺</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: KC_DARK, marginBottom: 8 }}>
        Noch keine Sitemap-Seiten
      </div>
      <div style={{ fontSize: 13, marginBottom: 20 }}>
        Lege manuell Seiten an oder lass die KI eine Struktur vorschlagen.
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        <button type="button" onClick={onAddPage} style={btnTeal}>
          + Erste Seite
        </button>
        <button type="button" onClick={() => onRegenerateSitemap?.(0)} style={btnYellow}>
          ⚡ KI-Vorschlag
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Side-Panel: Page-Details (Name / Type / Status / KI-Prompt)
// ─────────────────────────────────────────────────────────────────────────────

function PageDetailPanel({ page, onClose, onSave, onDelete }) {
  const [form, setForm] = useState(() => ({
    page_name: page?.page_name || '',
    page_type: page?.page_type || 'info',
    status:    page?.status    || 'geplant',
    ai_prompt: page?.ai_prompt || '',
  }));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      page_name: page?.page_name || '',
      page_type: page?.page_type || 'info',
      status:    page?.status    || 'geplant',
      ai_prompt: page?.ai_prompt || '',
    });
  }, [page?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!page) return null;
  const isPflicht = !!page.ist_pflichtseite;

  const handleSave = async () => {
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  return (
    <aside style={{
      width: 340, flexShrink: 0,
      background: '#fff',
      borderLeft: '1px solid #e2e8f0',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid #e2e8f0',
        background: '#f8fafc',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK }}>
          Seiten-Details
        </div>
        <button type="button" onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, color: '#64748b', padding: 0 }}>×</button>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {isPflicht && (
          <div style={{ fontSize: 11, color: '#92400E', background: '#FEF3C7', padding: '6px 8px', borderRadius: 6 }}>
            🔒 Pflichtseite — Name / Type sind gesperrt.
          </div>
        )}
        <div>
          <label style={lblStyle}>Page-Name</label>
          <input type="text" value={form.page_name} disabled={isPflicht}
            onChange={(e) => setForm((f) => ({ ...f, page_name: e.target.value }))}
            style={inpStyle(isPflicht)} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={lblStyle}>Type</label>
            <select value={form.page_type} disabled={isPflicht}
              onChange={(e) => setForm((f) => ({ ...f, page_type: e.target.value }))}
              style={{ ...inpStyle(isPflicht), cursor: isPflicht ? 'not-allowed' : 'pointer' }}>
              {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={lblStyle}>Status</label>
            <select value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              style={{ ...inpStyle(false), cursor: 'pointer' }}>
              <option value="geplant">Geplant</option>
              <option value="in_bearbeitung">In Bearbeitung</option>
              <option value="freigegeben">Freigegeben</option>
              <option value="live">Live</option>
            </select>
          </div>
        </div>
        <div>
          <label style={lblStyle}>KI-Anweisung (optional)</label>
          <textarea value={form.ai_prompt}
            onChange={(e) => setForm((f) => ({ ...f, ai_prompt: e.target.value }))}
            placeholder="Goal / Per-Page-Kontext für KI-Generator"
            rows={4}
            style={{ ...inpStyle(false), resize: 'vertical', fontFamily: 'inherit', minHeight: 70 }} />
        </div>
      </div>
      <div style={{
        padding: '10px 14px', borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        display: 'flex', justifyContent: 'space-between', gap: 8,
      }}>
        <button type="button" onClick={onDelete}
          disabled={isPflicht}
          style={{
            padding: '8px 12px',
            background: '#fff', border: `1px solid ${isPflicht ? '#cbd5e1' : '#fca5a5'}`,
            color: isPflicht ? '#cbd5e1' : '#dc2626',
            borderRadius: 6, fontSize: 12,
            cursor: isPflicht ? 'not-allowed' : 'pointer',
          }}>
          🗑 Löschen
        </button>
        <div style={{ display: 'flex', gap: 6 }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 12px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 12, color: '#64748b', cursor: 'pointer' }}>
            Abbrechen
          </button>
          <button type="button" onClick={handleSave} disabled={saving}
            style={{ padding: '8px 14px', background: saving ? '#94a3b8' : KC_DARK, color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: saving ? 'wait' : 'pointer' }}>
            {saving ? 'Speichert…' : '✓ Speichern'}
          </button>
        </div>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Page-Dialog (Modal)
// ─────────────────────────────────────────────────────────────────────────────

function AddPageDialog({ parentId, parentName, onClose, onSubmit }) {
  const [name, setName] = useState('');
  const [pageType, setPageType] = useState('info');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    await onSubmit(name, pageType);
    setBusy(false);
  };

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <form onSubmit={handleSubmit} style={{
        background: '#fff', borderRadius: 12, padding: 20,
        width: '100%', maxWidth: 420, boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <h3 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 700, color: KC_DARK }}>
          Neue Seite anlegen
        </h3>
        <p style={{ margin: '0 0 14px', fontSize: 11, color: '#64748b' }}>
          {parentId
            ? `Wird als Sub-Seite von „${parentName}" angelegt.`
            : 'Wird als Top-Level-Seite angelegt.'}
        </p>
        <div style={{ marginBottom: 10 }}>
          <label style={lblStyle}>Seitenname *</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="z.B. Wallbox-Installation"
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={lblStyle}>Page-Type</label>
          <select value={pageType} onChange={(e) => setPageType(e.target.value)}
            style={{ ...inpStyle(false), cursor: 'pointer' }}>
            {PAGE_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose}
            style={{ padding: '8px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12, cursor: 'pointer', color: '#64748b' }}>
            Abbrechen
          </button>
          <button type="submit" disabled={!name.trim() || busy}
            style={{ padding: '8px 18px', background: !name.trim() || busy ? '#94a3b8' : KC_MID, color: '#fff', border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: !name.trim() || busy ? 'not-allowed' : 'pointer' }}>
            {busy ? 'Anlegen…' : '+ Anlegen'}
          </button>
        </div>
      </form>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Add-Section-Dialog (Modal mit Section-Catalog)
// ─────────────────────────────────────────────────────────────────────────────

function AddSectionDialog({ existingSections, onClose, onPick }) {
  const [search, setSearch] = useState('');
  const all = Object.keys(SECTION_CATALOG);
  const used = new Set(existingSections);
  const filtered = all.filter((key) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return key.toLowerCase().includes(q) || SECTION_CATALOG[key].toLowerCase().includes(q);
  });

  return (
    <div onClick={(e) => e.target === e.currentTarget && onClose()} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: '#fff', borderRadius: 12,
        width: '100%', maxWidth: 520, maxHeight: 'calc(100vh - 32px)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: KC_DARK }}>
            Section auswählen
          </h3>
          <button type="button" onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: '#64748b' }}>×</button>
        </div>
        <div style={{ padding: '12px 18px', borderBottom: '1px solid #e2e8f0' }}>
          <input type="search" placeholder="Suchen…"
            value={search} onChange={(e) => setSearch(e.target.value)}
            style={inpStyle(false)} autoFocus />
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
          {filtered.length === 0 ? (
            <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 12, fontStyle: 'italic' }}>
              Kein Treffer für „{search}".
            </div>
          ) : (
            filtered.map((key) => {
              const isUsed = used.has(key);
              return (
                <button
                  key={key} type="button"
                  onClick={() => onPick(key)}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2,
                    width: '100%', padding: '8px 10px', marginBottom: 4,
                    background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6,
                    cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#eff6ff'; e.currentTarget.style.borderColor = KC_MID; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = '#e2e8f0'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
                    <code style={{ color: KC_MID, fontWeight: 700, fontSize: 11 }}>{key}</code>
                    <span style={{ flex: 1 }} />
                    {isUsed && (
                      <span style={{ fontSize: 9, color: '#64748b', background: '#f1f5f9', padding: '1px 6px', borderRadius: 4 }}>
                        bereits verwendet
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.4 }}>
                    {SECTION_CATALOG[key]}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared styles
// ─────────────────────────────────────────────────────────────────────────────

const lblStyle = {
  display: 'block', fontSize: 10, fontWeight: 700,
  color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em',
  marginBottom: 4,
};
const inpStyle = (disabled) => ({
  width: '100%', boxSizing: 'border-box', padding: '7px 10px',
  border: '1px solid #e2e8f0', borderRadius: 6,
  background: disabled ? '#f8fafc' : '#fff',
  color: disabled ? '#94a3b8' : '#1A2C32',
  fontSize: 12, fontFamily: 'inherit', outline: 'none',
});

const btnPrimary = {
  background: KC_YELLOW, color: '#000',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 800,
  cursor: 'pointer',
  textTransform: 'uppercase', letterSpacing: '0.04em',
  fontFamily: 'inherit',
};
const btnTeal = {
  background: KC_MID, color: '#fff',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
const btnYellow = {
  background: KC_YELLOW, color: '#000',
  border: 'none', borderRadius: 8,
  padding: '9px 16px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
const btnSecondary = {
  background: 'transparent', color: KC_DARK,
  border: `1.5px solid ${KC_DARK}`, borderRadius: 8,
  padding: '8px 14px', fontSize: 12, fontWeight: 700,
  cursor: 'pointer', fontFamily: 'inherit',
};
