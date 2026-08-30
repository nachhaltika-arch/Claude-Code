/**
 * WireframeView — Block-Canvas pro Sitemap-Seite mit Tausch- und Hinzufügen-
 * Panel. Liest Component-Library aus /api/components, persistiert Änderungen
 * via POST /api/projects/{id}/wireframe.
 *
 * Props:
 *   projectId
 *   leadId
 *   wireframeData            — { pages: [{page_id, page_name, blocks: [...]}] }
 *   onWireframeChange(next)  — wird nach jedem Save aufgerufen
 *   onNavigateToStyleGuide   — View-Switcher
 */
import { useEffect, useMemo, useState, useCallback } from 'react';
import API_BASE_URL from '../../config';
import { useAuth } from '../../context/AuthContext';
// Am 30.08.2026 herausgeloest (L-25): Die Datei trug 1.719 Zeilen und darin
// vier Unterkomponenten samt ihrem Wortschatz.
import {
KC_DARK, PREVIEW_WIDTHS,
} from '../wireframe/wireframeDaten';
import {
  BlockCard, PageThumb,
} from '../wireframe/wireframeTeile';
import SectionDetailPanel from '../wireframe/SectionDetailPanel';
import BlockTauschPanel from '../wireframe/BlockTauschPanel';

export default function WireframeView({
  projectId,
  leadId,
  wireframeData,
  onWireframeChange,
  onNavigateToStyleGuide,
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
    [token],
  );

  const pages = wireframeData?.pages || [];
  const [activePageId, setActivePageId] = useState(pages[0]?.page_id || null);
  const [library, setLibrary] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [swapPanel, setSwapPanel] = useState({ open: false, targetIdx: null, mode: 'swap' }); // mode: swap|add
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('Alle');
  const [saving, setSaving] = useState(false);
  // W1 Relume-Parität: Preview-Width-Toggle ('mobile' | 'tablet' | 'desktop')
  const [previewSize, setPreviewSize] = useState('desktop');
  // W1 Drag-Reorder-State (native HTML5 DnD)
  const [draggedIdx, setDraggedIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);
  // W3 Slot-Editor: { idx } oder null
  const [editPanel, setEditPanel] = useState(null);
  // Stufe C: vorgeschlagene Abfolge für die aktive Seite
  const [komposition, setKomposition] = useState({ status: 'idle', ergebnis: null, fehler: '' });

  // Default-Page auf erste setzen sobald Daten reinkommen
  useEffect(() => {
    if (!activePageId && pages.length > 0) {
      setActivePageId(pages[0].page_id);
    }
  }, [pages, activePageId]);

  // Eine Abfolge gilt für genau eine Seite.
  useEffect(() => {
    setKomposition({ status: 'idle', ergebnis: null, fehler: '' });
  }, [activePageId]);

  // Component-Library beim ersten Mount eagerly laden — die BlockCards
  // brauchen html_template für Live-Preview, sonst zeigen sie leere Karten
  // bevor der User das Swap-Panel öffnet.
  useEffect(() => {
    if (library.length > 0) return;
    setLibraryLoading(true);
    fetch(`${API_BASE_URL}/api/components`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setLibrary(Array.isArray(data) ? data : []))
      .finally(() => setLibraryLoading(false));
  }, [library.length, headers]);

  const activePage = pages.find((p) => p.page_id === activePageId) || null;
  const activeBlocks = (activePage?.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const filteredLibrary = useMemo(() => {
    let list = library;
    if (activeCategory !== 'Alle') {
      list = list.filter((c) => c.category === activeCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      list = list.filter(
        (c) =>
          c.slug.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q) ||
          (c.tags || []).some((t) => t.toLowerCase().includes(q)),
      );
    }
    return list;
  }, [library, activeCategory, searchQuery]);

  // W2: Empfohlen-Top-3 für den aktuellen Slot. Basis:
  //  - swap-Mode → gleiche Kategorie wie der zu tauschende Block, exkl. selbst & existierende
  //  - add-Mode  → noch-nicht-verwendete Library-Items
  // Nicht durch Filter / Suche beeinflusst — bleibt bewusst above-fold sichtbar.
  const recommendations = useMemo(() => {
    if (!swapPanel.open || library.length === 0) return [];
    const usedSlugs = new Set(activeBlocks.map((b) => b.slug));
    if (swapPanel.mode === 'swap') {
      const target = activeBlocks[swapPanel.targetIdx];
      if (!target) return [];
      const targetEntry = library.find((c) => c.slug === target.slug);
      if (!targetEntry) return [];
      return library
        .filter((c) => c.category === targetEntry.category && c.slug !== target.slug && !usedSlugs.has(c.slug))
        .slice(0, 3);
    }
    return library.filter((c) => !usedSlugs.has(c.slug)).slice(0, 3);
  }, [swapPanel.open, swapPanel.mode, swapPanel.targetIdx, library, activeBlocks]);

  // ── Mutationen am Wireframe ─────────────────────────────────────────────────

  const [saveFehler, setSaveFehler] = useState('');

  const persist = useCallback(
    async (nextData) => {
      setSaving(true);
      setSaveFehler('');
      try {
        const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe`, {
          method: 'POST',
          headers,
          body: JSON.stringify(nextData),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          // Seit Stufe B kann der Save inhaltlich abgelehnt werden: Eine
          // Variante, die den Vertrag verletzt, wird nicht gespeichert. Das in
          // die Konsole zu schreiben hiesse, den Nutzer mit einem Wireframe
          // zurueckzulassen, das er fuer gespeichert haelt.
          const detail = body?.detail;
          const gruende = (detail?.verstoesse || [])
            .map((v) => `${v.regel}: ${v.text}`).join(' · ');
          throw new Error(gruende
            ? `${detail.message || 'Nicht gespeichert.'} ${gruende}`
            : (typeof detail === 'string' ? detail : `Speichern fehlgeschlagen (${res.status})`));
        }
        onWireframeChange?.(nextData);
        return true;
      } catch (e) {
        setSaveFehler(e.message || 'Speichern fehlgeschlagen');
        return false;
      } finally {
        setSaving(false);
      }
    },
    [projectId, headers, onWireframeChange],
  );

  // ── Stufe C: die Seite komponieren ──────────────────────────────────────
  //
  // Vorgeschlagen wird nur die Abfolge — welche Sections in welcher Reihenfolge.
  // Das Markup je Section schreibt danach Stufe B, ein Block nach dem anderen.
  // Ein Aufruf für die ganze Seite wäre lang, teuer und beim kleinsten
  // Formfehler ganz verloren.
  const komponiere = async () => {
    if (!activePageId) return;
    setKomposition({ status: 'laeuft', ergebnis: null, fehler: '' });
    try {
      const start = await fetch(`${API_BASE_URL}/api/projects/${projectId}/wireframe/compose`, {
        method: 'POST', headers, body: JSON.stringify({ page_id: activePageId }),
      });
      const gestartet = await start.json().catch(() => ({}));
      if (!start.ok) {
        const detail = gestartet?.detail;
        throw new Error(typeof detail === 'string' ? detail : `Fehler ${start.status}`);
      }
      const frist = Date.now() + 180_000;
      while (Date.now() < frist) {
        // eslint-disable-next-line no-await-in-loop
        await new Promise((r) => setTimeout(r, 2000));
        // eslint-disable-next-line no-await-in-loop
        const res = await fetch(
          `${API_BASE_URL}/api/projects/wireframe-compose-jobs/${gestartet.job_id}`,
          { headers },
        );
        if (res.status === 404) throw new Error('Auftrag nicht gefunden');
        // eslint-disable-next-line no-await-in-loop
        const job = await res.json();
        if (job.status === 'done') {
          setKomposition({ status: 'fertig', ergebnis: job.result, fehler: '' });
          return;
        }
        if (job.status === 'error') throw new Error(job.error || 'Unbekannter Fehler');
      }
      throw new Error('Zeitüberschreitung — bitte erneut versuchen');
    } catch (e) {
      setKomposition({ status: 'fehler', ergebnis: null, fehler: e.message || 'Fehlgeschlagen' });
    }
  };

  const kompositionUebernehmen = async () => {
    const sections = komposition.ergebnis?.sections || [];
    if (!activePage || sections.length === 0) return;
    // Slot-Vorgaben aus der Bibliothek — dieselbe Regel wie beim Hinzufügen.
    const nextBlocks = sections.map((s, i) => {
      const lib = library.find((c) => c.slug === s.slug);
      const slots = (lib?.slots || []).reduce((acc, slot) => {
        if (slot.key) acc[slot.key] = slot.default ?? '';
        return acc;
      }, {});
      return { slug: s.slug, order: i, slots };
    });
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    const ok = await persist(nextData);
    if (ok !== false) setKomposition({ status: 'idle', ergebnis: null, fehler: '' });
  };

  const swapBlock = (targetIdx, newSlug) => {
    if (!activePage) return;
    const lib = library.find((c) => c.slug === newSlug);
    const defaultSlots = (lib?.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    const nextBlocks = activeBlocks.map((b, i) =>
      i === targetIdx ? { slug: newSlug, order: b.order ?? i, slots: defaultSlots } : b,
    );
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
    setSwapPanel({ open: false, targetIdx: null, mode: 'swap' });
  };

  const addBlock = (newSlug) => {
    if (!activePage) return;
    const lib = library.find((c) => c.slug === newSlug);
    const defaultSlots = (lib?.slots || []).reduce((acc, s) => {
      if (s.key) acc[s.key] = s.default ?? '';
      return acc;
    }, {});
    const order = activeBlocks.length;
    const nextBlocks = [...activeBlocks, { slug: newSlug, order, slots: defaultSlots }];
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
    setSwapPanel({ open: false, targetIdx: null, mode: 'swap' });
  };

  // ── Stufe B: eigene Fassung für diesen Kunden ───────────────────────────
  //
  // Gespeichert wird über denselben Weg wie jede andere Änderung — und damit
  // durch dasselbe Tor: Der Server lehnt eine Variante ab, die den Vertrag
  // verletzt, und `persist` sagt es.
  const setzeVariante = async (targetIdx, html) => {
    if (!activePage) return false;
    const nextBlocks = activeBlocks.map((b, i) => {
      if (i !== targetIdx) return b;
      const { html_override: _weg, ...ohne } = b;
      return html ? { ...ohne, html_override: html } : ohne;
    });
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    return persist(nextData);
  };

  const removeBlock = (targetIdx) => {
    if (!activePage) return;
    const nextBlocks = activeBlocks
      .filter((_, i) => i !== targetIdx)
      .map((b, i) => ({ ...b, order: i }));
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // W2: KI-Variation — fragt Backend nach Alternativ-Block gleicher Kategorie
  // und tauscht den aktuellen Block dadurch aus. Other Blocks der Page werden
  // als exclude_slugs mitgegeben, damit kein Duplikat vorgeschlagen wird.
  const requestVariation = async (targetIdx) => {
    if (!activePage) return;
    const current = activeBlocks[targetIdx];
    if (!current) return;
    try {
      const otherSlugs = activeBlocks
        .filter((_, i) => i !== targetIdx)
        .map((b) => b.slug);
      const res = await fetch(`${API_BASE_URL}/api/components/variation`, {
        method: 'POST', headers,
        body: JSON.stringify({
          current_slug:  current.slug,
          exclude_slugs: otherSlugs,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : `Fehler ${res.status}`;
        // eslint-disable-next-line no-console
        console.warn('variation failed:', msg);
        return;
      }
      // Library-Cache mit dem neuen Eintrag aktualisieren falls der noch nicht drin
      // (sollte er aber sein — eager-Load am Mount).
      if (body?.slug && !library.find((c) => c.slug === body.slug)) {
        setLibrary((prev) => [...prev, body]);
      }
      swapBlock(targetIdx, body.slug);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.warn('variation request failed:', e);
    }
  };

  // W3: Slot-Werte eines Blocks updaten + persistieren.
  const updateBlockSlots = (targetIdx, nextSlots) => {
    if (!activePage) return;
    const nextBlocks = activeBlocks.map((b, i) =>
      i === targetIdx ? { ...b, slots: nextSlots } : b,
    );
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // W3: Block-HTML als neuer Custom-Library-Eintrag speichern. Antwort enthält
  // den neuen ComponentLibrary-Eintrag — wir cachen ihn lokal und tauschen den
  // Block der aktuellen Page auf den neuen Slug aus.
  const saveAsCustom = async (targetIdx, payload) => {
    const res = await fetch(`${API_BASE_URL}/api/components/save-custom`, {
      method: 'POST', headers,
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = body?.detail;
      throw new Error(typeof detail === 'string' ? detail : `Fehler ${res.status}`);
    }
    // Gespeichert, aber nicht freigegeben: der Block verletzt den Vertrag. Ihn
    // trotzdem in die Seite zu tauschen waere die stille Variante — die Seite
    // haette dann einen Block, den sie nicht ausgeben kann. Also stehen lassen
    // und sagen, woran es liegt.
    if (body.status === 'draft') {
      const gruende = (body.contract?.verstoesse || [])
        .map((v) => `${v.regel}: ${v.text}`).join(' · ');
      throw new Error(
        `Als Entwurf gespeichert — der Block bleibt aus der Seite draussen. ${gruende}`,
      );
    }
    // Library-Cache erweitern + Block auf neuen Slug umstellen
    setLibrary((prev) => [...prev, body]);
    swapBlock(targetIdx, body.slug);
    return body;
  };

  // W1: Drag-Reorder — verschiebt Block von fromIdx an toIdx, persistiert.
  const moveBlock = (fromIdx, toIdx) => {
    if (!activePage || fromIdx === toIdx || fromIdx == null || toIdx == null) return;
    const next = [...activeBlocks];
    const [moved] = next.splice(fromIdx, 1);
    next.splice(toIdx, 0, moved);
    const nextBlocks = next.map((b, i) => ({ ...b, order: i }));
    const nextData = {
      ...wireframeData,
      pages: pages.map((p) => (p.page_id === activePageId ? { ...p, blocks: nextBlocks } : p)),
    };
    persist(nextData);
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (pages.length === 0) {
    return (
      <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>📐</div>
        <div style={{ fontSize: 15, fontWeight: 600, color: KC_DARK, marginBottom: 6 }}>
          Noch kein Wireframe vorhanden
        </div>
        <div style={{ fontSize: 13 }}>
          Wechsle zur Sitemap-Ansicht und starte den KI-Wireframe-Generator.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Storyboard oben — alle Pages horizontal scrollbar (Relume-Style) */}
      <aside style={{
        flexShrink: 0,
        background: 'var(--bg-app)',
        borderBottom: '1px solid var(--border-light)',
        padding: '12px 16px',
        overflowX: 'auto', overflowY: 'hidden',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Pages · {pages.length}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
            Klick auf eine Page um sie unten zu bearbeiten
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, paddingBottom: 4 }}>
          {pages.map((p) => (
            <PageThumb
              key={p.page_id}
              page={p}
              library={library}
              isActive={p.page_id === activePageId}
              onClick={() => setActivePageId(p.page_id)}
            />
          ))}
        </div>
      </aside>

      {/* Hauptbereich: Block-Canvas der aktiven Seite + optional Slide-In rechts */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
      <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
        {/* Topbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 20,
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 900, color: KC_DARK, margin: 0, textTransform: 'uppercase' }}>
              {activePage?.page_name || 'Seite'}
            </h1>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              {activeBlocks.length} Block{activeBlocks.length === 1 ? '' : 's'}
              {saving && ' · speichert…'}
            </p>
            {saveFehler && (
              <p style={{
                fontSize: 11, color: '#991b1b', background: '#fef2f2',
                border: '1px solid #fca5a5', borderRadius: 6,
                padding: '6px 8px', marginTop: 6, maxWidth: 620, lineHeight: 1.4,
              }}>{saveFehler}</p>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {/* W1 Relume-Parität: Responsive-Preview-Toggle */}
            <div style={{
              display: 'inline-flex', gap: 0,
              border: '1px solid var(--border-light)', borderRadius: 8, overflow: 'hidden',
            }}>
              {[
                { id: 'mobile',  label: '📱', title: 'Mobile (375px)' },
                { id: 'tablet',  label: '📲', title: 'Tablet (768px)' },
                { id: 'desktop', label: '🖥', title: 'Desktop (volle Breite)' },
              ].map((s) => {
                const active = previewSize === s.id;
                return (
                  <button
                    key={s.id} type="button" title={s.title}
                    onClick={() => setPreviewSize(s.id)}
                    style={{
                      background: active ? KC_DARK : 'transparent',
                      color: active ? '#fff' : 'var(--text-secondary)',
                      border: 'none', cursor: 'pointer',
                      padding: '8px 12px', fontSize: 14, lineHeight: 1,
                      fontFamily: 'inherit',
                    }}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={() => {
                setEditPanel(null);
                setSwapPanel({ open: true, targetIdx: null, mode: 'add' });
              }}
              style={{
                background: 'transparent',
                color: KC_DARK,
                border: `1.5px solid ${KC_DARK}`,
                borderRadius: 8,
                padding: '8px 16px',
                fontSize: 12,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              + Block hinzufügen
            </button>
            <button
              type="button"
              onClick={komponiere}
              disabled={komposition.status === 'laeuft' || library.length === 0}
              title="Claude schlägt eine Abfolge für diese Seite vor — Reihenfolge, Rhythmus, Pflicht-Sections"
              style={{
                background: '#7c3aed', opacity: komposition.status === 'laeuft' ? 0.5 : 1,
                color: '#fff', border: 'none', borderRadius: 8,
                padding: '8px 16px', fontSize: 12, fontWeight: 700,
                cursor: komposition.status === 'laeuft' ? 'wait' : 'pointer',
              }}
            >
              {komposition.status === 'laeuft' ? 'Komponiert…' : '✨ Seite komponieren'}
            </button>
            <button
              type="button"
              onClick={onNavigateToStyleGuide}
              disabled={activeBlocks.length === 0}
              style={{
                background: KC_DARK,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                fontSize: 12,
                fontWeight: 700,
                cursor: activeBlocks.length === 0 ? 'not-allowed' : 'pointer',
                opacity: activeBlocks.length === 0 ? 0.4 : 1,
              }}
            >
              Zu Style Guide →
            </button>
          </div>
        </div>

        {/* Stufe C: der Vorschlag für diese Seite */}
        {komposition.status === 'fehler' && (
          <div style={{
            margin: '0 auto 12px', maxWidth: 720, padding: '8px 12px',
            background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8,
            color: '#991b1b', fontSize: 12,
          }}>{komposition.fehler}</div>
        )}
        {komposition.status === 'fertig' && komposition.ergebnis && (
          <div style={{
            margin: '0 auto 16px', maxWidth: 720, padding: 14,
            background: '#faf5ff', border: '1px solid #d8b4fe', borderRadius: 10,
          }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: '#6b21a8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Vorgeschlagene Abfolge
            </div>
            {komposition.ergebnis.aufbau && (
              <p style={{ fontSize: 12, color: '#4c1d95', fontStyle: 'italic', margin: '6px 0 10px' }}>
                „{komposition.ergebnis.aufbau}"
              </p>
            )}
            <ol style={{ margin: '0 0 10px', paddingLeft: 20, fontSize: 12, color: '#4c1d95' }}>
              {(komposition.ergebnis.sections || []).map((s, i) => (
                <li key={`${s.slug}-${i}`} style={{ marginBottom: 4 }}>
                  <strong>{s.rolle || s.category}</strong> · {s.name || s.slug}
                  {s.auftrag && <div style={{ color: '#6b21a8' }}>{s.auftrag}</div>}
                </li>
              ))}
            </ol>
            {!komposition.ergebnis.contract?.konform && (
              <div style={{
                padding: 8, marginBottom: 10, background: '#fef2f2',
                border: '1px solid #fca5a5', borderRadius: 6, color: '#991b1b', fontSize: 11,
              }}>
                <strong>Die Abfolge hat offene Punkte — Übernehmen ist gesperrt:</strong>
                <ul style={{ margin: '4px 0 0', paddingLeft: 16 }}>
                  {(komposition.ergebnis.contract?.verstoesse || []).map((v, i) => (
                    <li key={`${v.regel}-${i}`}>{v.regel}: {v.text}</li>
                  ))}
                </ul>
              </div>
            )}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                type="button" onClick={kompositionUebernehmen}
                disabled={!komposition.ergebnis.contract?.konform}
                style={{
                  padding: '7px 14px',
                  background: komposition.ergebnis.contract?.konform ? 'var(--success)' : 'var(--text-tertiary)',
                  color: 'var(--text-on-brand)', border: 'none', borderRadius: 6,
                  fontSize: 11, fontWeight: 700, fontFamily: 'inherit',
                  cursor: komposition.ergebnis.contract?.konform ? 'pointer' : 'not-allowed',
                }}
              >✓ Abfolge übernehmen</button>
              <button
                type="button"
                onClick={() => setKomposition({ status: 'idle', ergebnis: null, fehler: '' })}
                style={{
                  padding: '7px 14px', background: '#fff', border: '1px solid var(--border-medium)',
                  borderRadius: 6, fontSize: 11, fontWeight: 700, fontFamily: 'inherit',
                  cursor: 'pointer',
                }}
              >Verwerfen</button>
              <span style={{ fontSize: 11, color: '#6b21a8' }}>
                Ersetzt die {activeBlocks.length} Block{activeBlocks.length === 1 ? '' : 's'} dieser
                Seite. Slot-Texte gehen dabei verloren; das Markup je Section
                schreibst du danach je Block über „Für diesen Kunden umschreiben".
              </span>
            </div>
          </div>
        )}

        {/* W1: Block-Liste mit Live-Preview + native Drag-Reorder.
            Container-Width entspricht dem Preview-Size-Toggle (mobile/tablet/desktop). */}
        <div style={{
          margin: '0 auto',
          maxWidth: PREVIEW_WIDTHS[previewSize],
          width: '100%',
          transition: 'max-width 0.2s ease',
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {activeBlocks.map((b, idx) => (
              <BlockCard
                key={`${b.slug}-${idx}`}
                idx={idx}
                block={b}
                libraryEntry={library.find((c) => c.slug === b.slug)}
                // Solange die Bibliothek laedt, fehlt jeder Eintrag — die
                // Warnung darf erst danach erscheinen, sonst blinkt sie bei
                // jedem Seitenaufruf an allen Bloecken auf.
                libraryGeladen={!libraryLoading && library.length > 0}
                isDragOver={dragOverIdx === idx && draggedIdx !== idx}
                isDragging={draggedIdx === idx}
                onDragStart={() => setDraggedIdx(idx)}
                onDragOver={(e) => { e.preventDefault(); setDragOverIdx(idx); }}
                onDrop={() => { moveBlock(draggedIdx, idx); setDraggedIdx(null); setDragOverIdx(null); }}
                onDragEnd={() => { setDraggedIdx(null); setDragOverIdx(null); }}
                onSwap={() => {
                  setEditPanel(null);
                  setSwapPanel({ open: true, targetIdx: idx, mode: 'swap' });
                }}
                onVariation={() => requestVariation(idx)}
                onEdit={() => {
                  setSwapPanel({ open: false, targetIdx: null, mode: 'swap' });
                  setEditPanel({ idx });
                }}
                onRemove={() => removeBlock(idx)}
              />
            ))}
            {activeBlocks.length === 0 && (
              <div
                style={{
                  textAlign: 'center',
                  padding: 32,
                  border: '2px dashed var(--border-medium)',
                  borderRadius: 12,
                  color: 'var(--text-tertiary)',
                  fontSize: 13,
                }}
              >
                Diese Seite hat noch keine Blöcke. Klick auf „+ Block hinzufügen".
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Phase B: Section-Detail-Panel als Inline-Side-Panel rechts.
          Mutually exclusive mit swapPanel — kann nicht gleichzeitig offen sein
          (siehe state-coordination in onEdit / setSwapPanel). */}
      {editPanel && !swapPanel.open && (() => {
        const target = activeBlocks[editPanel.idx];
        const lib = target ? library.find((c) => c.slug === target.slug) : null;
        if (!target) return null;
        return (
          <SectionDetailPanel
            block={target}
            libraryEntry={lib}
            headers={headers}
            projectId={projectId}
            pageId={activePageId}
            onVarianteUebernehmen={(html) => setzeVariante(editPanel.idx, html)}
            onClose={() => setEditPanel(null)}
            onSaveSlots={(values) => {
              updateBlockSlots(editPanel.idx, values);
              setEditPanel(null);
            }}
            onSaveAsCustom={async (payload) => {
              // Wirft, wenn der Block den Vertrag verletzt — die Meldung
              // gehoert ins Panel, nicht in die Konsole.
              await saveAsCustom(editPanel.idx, payload);
              setEditPanel(null);
            }}
          />
        );
      })()}

      {/* Rechtes Slide-In-Panel: Block-Tausch / Hinzufuegen. Seit dem
          30.08.2026 eine eigene Datei (L-25) — die Bedingung bleibt hier,
          damit am Aufrufort steht, wann es erscheint. */}
      {swapPanel.open && (
        <BlockTauschPanel
          swapPanel={swapPanel}
          setSwapPanel={setSwapPanel}
          libraryLoading={libraryLoading}
          filteredLibrary={filteredLibrary}
          recommendations={recommendations}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          activeCategory={activeCategory}
          setActiveCategory={setActiveCategory}
          addBlock={addBlock}
          swapBlock={swapBlock}
        />
      )}
      </div>
    </div>
  );
}

// ── Page-Thumbnail (Storyboard-Item) ─────────────────────────────────────────

