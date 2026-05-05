/**
 * SitemapView — Visueller Sitemap-Tree (Relume-Style) auf Reactflow-Basis.
 *
 * Phase 2 der Crawl-Import-Feature: Read-only Tree-Visualisierung der Pages.
 * Drag&Drop / Reorder kommt in Phase 4.
 *
 * Props:
 *   projectId             — Project.id
 *   leadId                — für /api/sitemap/{leadId}
 *   wireframeData         — aktueller Wireframe ({pages:[...]})
 *   onGenerateWireframe   — Callback: KI-Wireframe-Job
 *   onNavigateToWireframe — Callback: View-Switcher zu Wireframe
 *   onRegenerateSitemap   — Callback: KI-Sitemap-Vorschlag (existing)
 *
 * Datenquellen:
 *   GET  /api/sitemap/{leadId}                  — alle Pages
 *   POST /api/sitemap/{leadId}/import-existing  — Bestand crawlen (Phase 1)
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  Panel,
} from '@xyflow/react';
import dagre from 'dagre';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

// Spiegelt SitemapPlaner-Konventionen — gleiche Farben/Icons
const TYPE_META = {
  startseite: { label: 'Startseite',      color: '#008EAA', icon: '🏠' },
  leistung:   { label: 'Leistungsseite',  color: '#2563EB', icon: '🔧' },
  info:       { label: 'Info-Seite',      color: '#059669', icon: 'ℹ️' },
  vertrauen:  { label: 'Vertrauensseite', color: '#D97706', icon: '⭐' },
  conversion: { label: 'Kontakt',         color: '#DC2626', icon: '📞' },
  rechtlich:  { label: 'Rechtlich',       color: '#6B7280', icon: '⚖️' },
  sonstige:   { label: 'Sonstige',        color: '#8B5CF6', icon: '📄' },
  ground:     { label: 'Übersicht',       color: '#0EA5E9', icon: '📋' },
};

// source → optionales Badge auf der Karte
const SOURCE_BADGE = {
  crawled:      { label: 'Bestand', bg: '#FEF3C7', color: '#92400E' },
  ki_generated: { label: 'KI',      bg: '#DCFCE7', color: '#166534' },
  manual:       { label: null,      bg: null,      color: null },
};

const NODE_W = 240;
const NODE_H = 110;

// ── Custom Node ──────────────────────────────────────────────────────────────

function PageNode({ data }) {
  const { page, blockCount } = data;
  const meta = TYPE_META[page.page_type] || TYPE_META.info;
  const sourceBadge = SOURCE_BADGE[page.source] || SOURCE_BADGE.manual;

  return (
    <div style={{
      width: NODE_W,
      background: '#fff',
      border: `2px solid ${meta.color}`,
      borderRadius: 12,
      padding: '10px 12px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      <Handle type="target" position={Position.Top}
        style={{ background: meta.color, width: 8, height: 8, border: 'none' }}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 18, flexShrink: 0 }}>{meta.icon}</span>
        <div style={{
          fontWeight: 700, fontSize: 13, color: KC_DARK,
          flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {page.page_name}
        </div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
        <span style={{
          fontSize: 9, fontWeight: 700,
          padding: '2px 6px', borderRadius: 4,
          background: meta.color + '15', color: meta.color,
          textTransform: 'uppercase', letterSpacing: '0.04em',
        }}>
          {meta.label}
        </span>
        {sourceBadge.label && (
          <span style={{
            fontSize: 9, fontWeight: 700,
            padding: '2px 6px', borderRadius: 4,
            background: sourceBadge.bg, color: sourceBadge.color,
            textTransform: 'uppercase', letterSpacing: '0.04em',
          }}>
            {sourceBadge.label}
          </span>
        )}
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontSize: 11, color: '#64748b',
      }}>
        <span>{blockCount} Block{blockCount === 1 ? '' : 's'}</span>
        {page.original_url ? (
          <a
            href={page.original_url} target="_blank" rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            style={{ color: KC_MID, textDecoration: 'none', fontSize: 11, fontWeight: 600 }}
          >
            ↗ Original
          </a>
        ) : null}
      </div>
      <Handle type="source" position={Position.Bottom}
        style={{ background: meta.color, width: 8, height: 8, border: 'none' }}
      />
    </div>
  );
}

const NODE_TYPES = { page: PageNode };

// ── Layout (dagre) ───────────────────────────────────────────────────────────

function layoutTree(pages, blocksByPageId) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 40, ranksep: 70 });

  pages.forEach((p) => {
    g.setNode(String(p.id), { width: NODE_W, height: NODE_H });
  });
  pages.forEach((p) => {
    if (p.parent_id) g.setEdge(String(p.parent_id), String(p.id));
  });
  dagre.layout(g);

  const nodes = pages.map((p) => {
    const pos = g.node(String(p.id));
    return {
      id: String(p.id),
      type: 'page',
      position: { x: pos.x - NODE_W / 2, y: pos.y - NODE_H / 2 },
      data: { page: p, blockCount: (blocksByPageId.get(p.id) || []).length },
    };
  });

  const parentEdges = pages
    .filter((p) => p.parent_id)
    .map((p) => ({
      id: `e-${p.parent_id}-${p.id}`,
      source: String(p.parent_id),
      target: String(p.id),
      type: 'smoothstep',
      style: { stroke: '#94a3b8', strokeWidth: 1.5 },
    }));

  // Phase 3: "Ersetzt"-Mappings — KI-Vorschlag → konsolidierte Bestandsseiten.
  // Visuell als gestrichelte rote Edge, die auf den ersten Blick zeigt, welche
  // Bestandspages durch den KI-Vorschlag entfallen / ersetzt werden.
  const pageIdSet = new Set(pages.map((p) => p.id));
  const replaceEdges = [];
  pages.forEach((p) => {
    const ids = Array.isArray(p.replaces_page_ids) ? p.replaces_page_ids : [];
    ids.forEach((bestandId) => {
      if (!pageIdSet.has(bestandId) || bestandId === p.id) return;
      replaceEdges.push({
        id: `r-${p.id}-${bestandId}`,
        source: String(p.id),
        target: String(bestandId),
        type: 'straight',
        animated: false,
        label: 'ersetzt',
        labelStyle: { fill: '#DC2626', fontSize: 10, fontWeight: 700 },
        labelBgStyle: { fill: '#FEF2F2' },
        labelBgPadding: [4, 2],
        style: { stroke: '#DC2626', strokeWidth: 1.5, strokeDasharray: '6 4' },
      });
    });
  });

  return { nodes, edges: [...parentEdges, ...replaceEdges] };
}

// ── Main ─────────────────────────────────────────────────────────────────────

export default function SitemapView({
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
  const [importing, setImporting] = useState(false);

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

  // ── Phase 4: re-parent via edge connect, entparent via edge click ──────────

  const isAncestor = useCallback((potentialAncestorId, descendantId) => {
    // Walk up the parent chain from descendantId; return true if we hit
    // potentialAncestorId. Used to reject edges that would create a cycle.
    const byId = new Map(pages.map((p) => [p.id, p]));
    let current = byId.get(descendantId);
    let safety = pages.length + 1;
    while (current && current.parent_id && safety-- > 0) {
      if (current.parent_id === potentialAncestorId) return true;
      current = byId.get(current.parent_id);
    }
    return false;
  }, [pages]);

  const persistParentChange = useCallback(async (childId, newParentId) => {
    // Only the changed page needs to be sent — backend's /reorder is a partial
    // update keyed by id. We keep the page's existing position untouched.
    const child = pages.find((p) => p.id === childId);
    if (!child) return;
    const body = [{ id: childId, position: child.position ?? 0, parent_id: newParentId }];
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/reorder`, {
        method: 'PUT', headers, body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        const msg = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      // Optimistic local update so the tree re-layouts without a round-trip
      setPages((prev) => prev.map((p) =>
        p.id === childId ? { ...p, parent_id: newParentId } : p,
      ));
    } catch (e) {
      toast.error(`Speichern fehlgeschlagen: ${e.message}`);
      loadPages(); // resync to server state on failure
    }
  }, [pages, leadId, headers, loadPages]);

  const handleConnect = useCallback((conn) => {
    const sourceId = parseInt(conn.source, 10);
    const targetId = parseInt(conn.target, 10);
    if (!sourceId || !targetId || sourceId === targetId) return;

    const target = pages.find((p) => p.id === targetId);
    const source = pages.find((p) => p.id === sourceId);
    if (!target || !source) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht umgehängt werden.');
      return;
    }
    if (target.parent_id === sourceId) return; // no-op
    if (isAncestor(targetId, sourceId)) {
      toast.error('Verbindung erzeugt eine Schleife — abgebrochen.');
      return;
    }
    persistParentChange(targetId, sourceId);
    toast.success(`„${target.page_name}" ist jetzt Kind von „${source.page_name}"`);
  }, [pages, isAncestor, persistParentChange]);

  const handleEdgeClick = useCallback((_evt, edge) => {
    // Only parent edges (id prefix 'e-') are removable. Replace-mapping edges
    // (prefix 'r-') are derived from replaces_page_ids and read-only.
    if (!edge.id.startsWith('e-')) return;
    const targetId = parseInt(edge.target, 10);
    const target = pages.find((p) => p.id === targetId);
    if (!target) return;
    if (target.ist_pflichtseite) {
      toast.error('Pflichtseiten können nicht umgehängt werden.');
      return;
    }
    if (!window.confirm(`Verbindung lösen — „${target.page_name}" wird zur Top-Level-Seite. Fortfahren?`)) return;
    persistParentChange(targetId, null);
  }, [pages, persistParentChange]);

  const handleImportExisting = async () => {
    if (!leadId) return;
    if (!window.confirm(
      'Die Bestands-Website wird automatisch gecrawlt.\n\n' +
      'Bestehende „Bestand"-Seiten werden ersetzt — manuelle und KI-Vorschläge bleiben.\n\n' +
      'Fortfahren?'
    )) return;
    setImporting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${leadId}/import-existing`, {
        method: 'POST', headers,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body.detail;
        const msg = typeof detail === 'string'
          ? detail
          : detail?.message || detail?.code || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      toast.success(`${body.imported} Seite${body.imported === 1 ? '' : 'n'} aus Bestand importiert`);
      loadPages();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setImporting(false);
    }
  };

  const blocksByPageId = useMemo(() => {
    const map = new Map();
    (wireframeData?.pages || []).forEach((p) => {
      map.set(p.page_id, (p.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0)));
    });
    return map;
  }, [wireframeData]);

  const totalBlocks = (wireframeData?.pages || []).reduce(
    (sum, p) => sum + (p.blocks?.length || 0),
    0,
  );

  const { nodes, edges } = useMemo(() => {
    if (pages.length === 0) return { nodes: [], edges: [] };
    const out = layoutTree(pages, blocksByPageId);
    // Lock Pflichtseiten — they cannot be reparented; UX makes that explicit.
    const locked = out.nodes.map((n) => {
      const isPflicht = !!n.data?.page?.ist_pflichtseite;
      return isPflicht
        ? { ...n, draggable: false, connectable: false }
        : n;
    });
    return { nodes: locked, edges: out.edges };
  }, [pages, blocksByPageId]);

  return (
    <div style={{
      padding: 24, fontFamily: 'var(--font-sans, system-ui)',
      height: '100%', display: 'flex', flexDirection: 'column',
    }}>
      {/* Topbar */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: 12,
        alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 20, flexShrink: 0,
      }}>
        <div>
          <h1 style={{
            fontSize: 22, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>
            Sitemap
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            {pages.length} Seite{pages.length === 1 ? '' : 'n'} · {totalBlocks} Block-Zuweisung{totalBlocks === 1 ? '' : 'en'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            type="button" onClick={handleImportExisting} disabled={importing}
            style={{
              background: 'transparent', color: KC_MID,
              border: `1.5px solid ${KC_MID}`, borderRadius: 8,
              padding: '9px 16px', fontSize: 13, fontWeight: 700,
              cursor: importing ? 'wait' : 'pointer',
              opacity: importing ? 0.6 : 1,
            }}
          >
            {importing ? 'Crawlt…' : '📥 Bestand importieren'}
          </button>
          <button
            type="button" onClick={onRegenerateSitemap}
            style={{
              background: 'transparent', color: KC_DARK,
              border: `1.5px solid ${KC_DARK}`, borderRadius: 8,
              padding: '9px 16px', fontSize: 13, fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Sitemap neu generieren
          </button>
          <button
            type="button" onClick={onGenerateWireframe} disabled={pages.length === 0}
            style={{
              background: KC_YELLOW, color: '#000',
              border: 'none', borderRadius: 8,
              padding: '10px 18px', fontSize: 13, fontWeight: 800,
              cursor: pages.length === 0 ? 'not-allowed' : 'pointer',
              opacity: pages.length === 0 ? 0.5 : 1,
              textTransform: 'uppercase', letterSpacing: '0.04em',
            }}
          >
            KI-Wireframe erzeugen
          </button>
          <button
            type="button" onClick={onNavigateToWireframe} disabled={totalBlocks === 0}
            style={{
              background: KC_MID, color: '#fff',
              border: 'none', borderRadius: 8,
              padding: '10px 18px', fontSize: 13, fontWeight: 700,
              cursor: totalBlocks === 0 ? 'not-allowed' : 'pointer',
              opacity: totalBlocks === 0 ? 0.5 : 1,
            }}
          >
            Zu Wireframe →
          </button>
        </div>
      </div>

      {loading && <div style={{ color: '#64748b', fontSize: 14 }}>Sitemap wird geladen…</div>}
      {error && (
        <div style={{ background: '#FEF2F2', color: '#991B1B', padding: 12, borderRadius: 8, fontSize: 13 }}>
          {error}
        </div>
      )}

      {!loading && !error && pages.length === 0 && (
        <div style={{
          border: '2px dashed #cbd5e1', borderRadius: 16, padding: 40,
          textAlign: 'center', color: '#64748b',
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🗺</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: KC_DARK, marginBottom: 6 }}>
            Noch keine Sitemap-Seiten
          </div>
          <div style={{ fontSize: 13, marginBottom: 16 }}>
            Importiere die Bestands-Website oder lass die KI eine neue Struktur vorschlagen.
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button" onClick={handleImportExisting} disabled={importing}
              style={{
                background: KC_MID, color: '#fff',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 700,
                cursor: importing ? 'wait' : 'pointer',
              }}
            >
              {importing ? 'Crawlt…' : '📥 Bestand importieren'}
            </button>
            <button
              type="button" onClick={onRegenerateSitemap}
              style={{
                background: KC_YELLOW, color: '#000',
                border: 'none', borderRadius: 8,
                padding: '10px 18px', fontSize: 13, fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              KI-Vorschlag generieren
            </button>
          </div>
        </div>
      )}

      {!loading && !error && pages.length > 0 && (
        <div style={{
          flex: 1, minHeight: 500,
          background: '#f8fafc', borderRadius: 12,
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
        }}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={NODE_TYPES}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              minZoom={0.2}
              maxZoom={1.5}
              nodesDraggable
              nodesConnectable
              elementsSelectable
              onConnect={handleConnect}
              onEdgeClick={handleEdgeClick}
              defaultEdgeOptions={{ type: 'smoothstep' }}
            >
              <Background gap={16} color="#e2e8f0" />
              <Controls showInteractive={false} />
              <Panel position="top-left" style={{
                background: 'rgba(255,255,255,0.92)', border: '1px solid #e2e8f0',
                borderRadius: 8, padding: '6px 10px', fontSize: 11, color: '#475569',
                boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
              }}>
                💡 Kartenrand → Kartenrand ziehen = neue Hierarchie · Linie klicken = entkoppeln
              </Panel>
              <MiniMap
                pannable zoomable
                nodeColor={(n) => {
                  const meta = TYPE_META[n.data?.page?.page_type] || TYPE_META.info;
                  return meta.color;
                }}
              />
            </ReactFlow>
          </ReactFlowProvider>
        </div>
      )}
    </div>
  );
}
