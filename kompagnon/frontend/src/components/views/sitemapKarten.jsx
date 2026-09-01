/**
 * Die Karten der Sitemap — Spalten, Seitenkarte, Abschnittszeilen (L-25).
 *
 * Am 2026-08-30 aus `SitemapViewV2.jsx` herausgeloest — 751 der damals 2.210
 * Zeilen, die groesste der drei Gruppen. Alle acht waren dort schon eigene
 * Funktionen und nehmen ihre Eingaben ueber Eigenschaften entgegen; der
 * Schnitt verschiebt sie nur dorthin, wo man sie sucht.
 */
import { Fragment, useEffect, useRef, useState } from 'react';
import { aufTaste } from '../../utils/tastaturBedienung';
import toast from 'react-hot-toast';
import {
  COL_GAP, KC_DARK, KC_MID, PAGE_W, ROW_GAP, SECTION_CATALOG, SECTION_LABEL, TYPE_META,
} from './sitemapDaten';

export function PageColumn({
  page, tree,
  selectedPageId, onSelect,
  onAddSibling, onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection, onToggleGroup,
  isFirstSibling = false,
  dragState, setDragState, dropTarget, setDropTarget, moveSection, endDrag,
  inheritedSections = null,  // Phase 4: nicht-null wenn Eltern-Page eine Gruppe ist
  linksByPageId = null, pages = null,
  setCardRef = null,
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
          onToggleGroup={onToggleGroup}
          inheritedSections={inheritedSections}
          dragState={dragState}
          setDragState={setDragState}
          dropTarget={dropTarget}
          setDropTarget={setDropTarget}
          moveSection={moveSection}
          endDrag={endDrag}
          links={linksByPageId?.get(page.id)}
          pages={pages}
          onSelectPage={onSelect}
          setCardRef={setCardRef}
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
            background: 'var(--border-medium)',
          }} />
          {/* Horizontale Linie ueber alle Kinder */}
          {children.length > 1 && (
            <div style={{
              position: 'absolute',
              top: -ROW_GAP / 2,
              left: 0, right: 0,
              height: 1,
              background: 'var(--border-medium)',
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
                onToggleGroup={onToggleGroup}
                isFirstSibling={idx === 0}
                dragState={dragState}
                setDragState={setDragState}
                dropTarget={dropTarget}
                setDropTarget={setDropTarget}
                moveSection={moveSection}
                endDrag={endDrag}
                inheritedSections={page.is_group ? (page.group_template_sections || []) : null}
                linksByPageId={linksByPageId}
                pages={pages}
                setCardRef={setCardRef}
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
export function ChildPageColumn(props) {
  return (
    <div style={{ position: 'relative' }}>
      {/* Vertikale Linie ueber jedem Kind, verbindet zur horizontalen Eltern-Linie */}
      <div style={{
        position: 'absolute',
        top: -ROW_GAP / 2,
        left: '50%', transform: 'translateX(-50%)',
        width: 1, height: ROW_GAP / 2,
        background: 'var(--border-medium)',
      }} />
      <PageColumn {...props} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PageCard — Header + Section-Liste + Add-Section-Button
// ─────────────────────────────────────────────────────────────────────────────

export function PageCard({
  page,
  isActive, onSelect,
  onAddChild, onDelete, onDuplicate, onAddSection, onRemoveSection, onToggleGroup,
  inheritedSections = null,
  dragState, setDragState, dropTarget, setDropTarget, moveSection, endDrag,
  links = null, pages = null, onSelectPage = null,
  setCardRef = null,
}) {
  const [linksOpen, setLinksOpen] = useState(false);
  const internalLinks = links?.internal || [];
  const externalLinks = links?.external || [];
  const hasLinks = internalLinks.length > 0 || externalLinks.length > 0;
  const meta = TYPE_META[page.page_type] || TYPE_META.info;
  // Phase 4: Section-Anzeige bestimmen.
  // - Page ist selbst Gruppe? → group_template_sections (editierbar als Template)
  // - Eltern ist Gruppe? → inheritedSections (read-only, vom Template uebernommen)
  // - Sonst: page.sections
  const isGroup = !!page.is_group;
  const isInherited = !isGroup && inheritedSections != null;
  const sections = isGroup
    ? (Array.isArray(page.group_template_sections) ? page.group_template_sections : [])
    : isInherited
    ? inheritedSections
    : (Array.isArray(page.sections) ? page.sections : []);
  const sectionsEditable = !isInherited; // Inherited = read-only
  const [menuOpen, setMenuOpen] = useState(false);
  const cardRef = useRef(null);

  // Phase C polish: Card-DOM-Node beim Parent registrieren fuer SVG-Edges
  useEffect(() => {
    if (!setCardRef) return;
    setCardRef(page.id, cardRef.current);
    return () => setCardRef(page.id, null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page.id]);

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
    <div role="button" tabIndex={0} onKeyDown={aufTaste(cardClick)}
      ref={cardRef}
      onClick={cardClick}
      style={{
        position: 'relative',
        width: PAGE_W, flexShrink: 0,
        background: '#fff',
        border: isActive
          ? `2px solid ${KC_MID}`
          : isGroup
          ? `1px solid ${KC_MID}`
          : '1px solid var(--border-light)',
        borderRadius: 10,
        boxShadow: isActive
          ? `0 4px 16px color-mix(in srgb, ${KC_MID} 20%, transparent)`
          : '0 1px 3px rgba(0,0,0,0.04)',
        cursor: 'pointer',
        overflow: 'visible',
      }}
    >
      {/* Page-Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '10px 12px',
        background: isGroup ? '#ecfeff' : 'var(--bg-app)',
        borderBottom: '1px solid var(--border-light)',
        borderTopLeftRadius: 10, borderTopRightRadius: 10,
      }}>
        <span style={{ fontSize: 14, flexShrink: 0 }}>
          {isGroup ? '📂' : meta.icon}
        </span>
        <div style={{
          flex: 1, minWidth: 0,
          fontSize: 12, fontWeight: 700, color: KC_DARK,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {page.page_name}
        </div>
        {isGroup && (
          <span style={{
            fontSize: 12, fontWeight: 800, color: '#fff', background: KC_MID,
            padding: '2px 6px', borderRadius: 4,
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}>
            Gruppe
          </span>
        )}
        {page.ist_pflichtseite && (
          <span title="Pflichtseite" style={{ fontSize: 12 }}>🔒</span>
        )}
        <button
          type="button" data-noselect
          onClick={(e) => { e.stopPropagation(); setMenuOpen((v) => !v); }}
          aria-label="Menü"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-secondary)', fontSize: 16, lineHeight: 1, padding: '0 4px',
            fontWeight: 700,
          }}
        >
          ⋯
        </button>
      </div>

      {/* Section-Liste */}
      <div style={{ padding: '8px 12px 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {isInherited && (
          <div style={{
            marginBottom: 4, padding: '4px 8px',
            fontSize: 12, color: '#0e7490',
            background: '#ecfeff', border: '1px solid #a5f3fc',
            borderRadius: 4,
          }}>
            🔗 Sections aus übergeordneter Gruppe — Änderungen oben in der Gruppe.
          </div>
        )}
        {isGroup && (
          <div style={{
            marginBottom: 4, padding: '4px 8px',
            fontSize: 12, color: '#0e7490',
            background: '#ecfeff', border: '1px solid #a5f3fc',
            borderRadius: 4,
          }}>
            📂 Section-Template — wird automatisch von allen Kind-Pages übernommen.
          </div>
        )}
        {sections.length === 0 ? (
          <div data-noselect style={{
            padding: '20px 8px', textAlign: 'center',
            color: 'var(--text-tertiary)', fontSize: 12, fontStyle: 'italic',
          }}>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, 0); }}
              style={{
                width: '100%', padding: '10px 12px',
                background: 'var(--bg-app)', border: '1px dashed var(--border-medium)',
                borderRadius: 6, fontSize: 12, fontWeight: 700,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
                marginBottom: 6,
              }}
            >
              + Section
            </button>
            <div style={{ fontSize: 12, color: 'var(--border-medium)' }}>oder</div>
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
                fontSize: 12, color: '#7c3aed', fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              ✨ Generate content
            </button>
          </div>
        ) : isInherited ? (
          // Phase 4: read-only Anzeige der geerbten Sections (vom Eltern-Group).
          sections.map((key, idx) => (
            <InheritedSectionRow key={`${key}-${idx}`} sectionKey={key} idx={idx} />
          ))
        ) : (
          <>
            {/* DropZone vor erster Section */}
            <DropZone
              pageId={page.id} position={0}
              dragState={dragState} dropTarget={dropTarget}
              setDropTarget={setDropTarget}
              onDrop={moveSection} endDrag={endDrag}
            />
            {sections.map((key, idx) => (
              <Fragment key={`${key}-${idx}`}>
                <SectionRow
                  sectionKey={key} idx={idx} pageId={page.id}
                  onRemove={() => onRemoveSection(page.id, idx)}
                  onAddBelow={() => onAddSection(page.id, idx + 1)}
                  dragState={dragState} setDragState={setDragState}
                  endDrag={endDrag}
                />
                <DropZone
                  pageId={page.id} position={idx + 1}
                  dragState={dragState} dropTarget={dropTarget}
                  setDropTarget={setDropTarget}
                  onDrop={moveSection} endDrag={endDrag}
                />
              </Fragment>
            ))}
            {/* "+" unter der letzten Section */}
            <button
              type="button" data-noselect
              onClick={(e) => { e.stopPropagation(); onAddSection(page.id, sections.length); }}
              style={{
                marginTop: 4, padding: '6px 10px',
                background: 'transparent', border: '1px dashed var(--border-medium)',
                borderRadius: 6, fontSize: 12, fontWeight: 600,
                color: KC_MID, cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              + Section hinzufügen
            </button>
          </>
        )}
      </div>

      {/* Phase C: Link-Footer — zeigt Anzahl interner/externer Links der Page */}
      {hasLinks && (
        <div role="button" tabIndex={0} onKeyDown={aufTaste((e) => { e.stopPropagation(); setLinksOpen((v) => !v); })} data-noselect style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 12px',
          borderTop: '1px solid var(--border-light)',
          background: linksOpen ? '#eff6ff' : 'var(--bg-app)',
          fontSize: 12,
          cursor: 'pointer',
        }} onClick={(e) => { e.stopPropagation(); setLinksOpen((v) => !v); }}>
          {internalLinks.length > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 3,
              padding: '2px 6px', borderRadius: 4,
              background: '#dbeafe', color: '#1e40af',
              fontWeight: 700,
            }}>
              🔗 {internalLinks.length} intern
            </span>
          )}
          {externalLinks.length > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 3,
              padding: '2px 6px', borderRadius: 4,
              background: 'var(--surface)', color: 'var(--text-secondary)',
              fontWeight: 700,
            }}>
              ↗ {externalLinks.length} extern
            </span>
          )}
          <span style={{ flex: 1 }} />
          <span style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
            {linksOpen ? '▲' : '▼'}
          </span>
        </div>
      )}

      {/* Phase C: Link-Detail-Popover — eingeklappte Liste der Ziele */}
      {hasLinks && linksOpen && (
        <div role="button" tabIndex={0} onKeyDown={aufTaste((e) => e.stopPropagation())} data-noselect onClick={(e) => e.stopPropagation()} style={{
          padding: '8px 10px',
          background: 'var(--bg-app)',
          borderTop: '1px solid var(--border-light)',
          fontSize: 12, color: 'var(--text-secondary)',
          maxHeight: 200, overflowY: 'auto',
        }}>
          {internalLinks.length > 0 && (
            <>
              <div style={{
                fontSize: 12, fontWeight: 700, color: '#1e40af',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                marginBottom: 4,
              }}>
                Intern ({internalLinks.length})
              </div>
              {internalLinks.map((l, i) => {
                const target = pages?.find((p) => p.id === l.toPageId);
                return (
                  <button
                    key={`int-${i}`} type="button"
                    onClick={() => { setLinksOpen(false); onSelectPage?.(l.toPageId); }}
                    title={`Slot „${l.slot}" → ${l.value}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, width: '100%',
                      padding: '4px 6px', marginBottom: 2,
                      background: '#fff', border: '1px solid #dbeafe', borderRadius: 4,
                      fontSize: 12, fontFamily: 'inherit', color: '#1e40af',
                      cursor: 'pointer', textAlign: 'left',
                    }}
                  >
                    <span style={{ flex: 1, minWidth: 0,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 600,
                    }}>
                      → {target?.page_name || `Page #${l.toPageId}`}
                    </span>
                    <code style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>
                      {l.slot}
                    </code>
                  </button>
                );
              })}
            </>
          )}
          {externalLinks.length > 0 && (
            <>
              <div style={{
                fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)',
                textTransform: 'uppercase', letterSpacing: '0.06em',
                marginTop: internalLinks.length > 0 ? 6 : 0, marginBottom: 4,
              }}>
                Extern ({externalLinks.length})
              </div>
              {externalLinks.map((l, i) => (
                <a key={`ext-${i}`}
                  href={l.url} target="_blank" rel="noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  title={`Slot „${l.slot}"${l.unresolved ? ' — interner Pfad ohne Ziel' : ''}`}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    padding: '4px 6px', marginBottom: 2,
                    background: '#fff',
                    border: `1px solid ${l.unresolved ? '#fca5a5' : 'var(--border-light)'}`,
                    borderRadius: 4,
                    fontSize: 12, color: l.unresolved ? '#991B1B' : 'var(--text-secondary)',
                    textDecoration: 'none',
                    overflow: 'hidden',
                  }}
                >
                  <span style={{ flex: 1, minWidth: 0,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {l.unresolved ? '⚠ ' : '↗ '}
                    {l.url}
                  </span>
                  <code style={{ fontSize: 12, color: 'var(--text-tertiary)', fontFamily: 'ui-monospace, monospace' }}>
                    {l.slot}
                  </code>
                </a>
              ))}
            </>
          )}
        </div>
      )}

      {/* Context-Menu (Dropdown) */}
      {menuOpen && (
        <div
          data-noselect
          style={{
            position: 'absolute', top: 38, right: 8, zIndex: 50,
            background: '#fff', border: '1px solid var(--border-light)', borderRadius: 8,
            boxShadow: '0 6px 20px rgba(0,0,0,0.10)',
            minWidth: 180, padding: 4,
            display: 'flex', flexDirection: 'column',
          }}
        >
          <MenuItem onClick={() => { setMenuOpen(false); onAddChild(page.id); }}>+ Sub-Seite</MenuItem>
          <MenuItem
            onClick={() => { setMenuOpen(false); onAddSection(page.id, sections.length); }}
            disabled={isInherited}
          >
            + Section
          </MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onDuplicate(page.id); }}>📋 Duplizieren</MenuItem>
          <MenuItem onClick={() => { setMenuOpen(false); onSelect(page.id); }}>✏️ Bearbeiten…</MenuItem>
          <div style={{ height: 1, background: 'var(--border-light)', margin: '4px 2px' }} />
          <MenuItem
            onClick={() => { setMenuOpen(false); onToggleGroup(page.id); }}
            disabled={page.ist_pflichtseite}
          >
            {isGroup ? '↩ Zurück zur Page' : '📂 Als Gruppe markieren'}
          </MenuItem>
          <div style={{ height: 1, background: 'var(--border-light)', margin: '4px 2px' }} />
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

export function MenuItem({ children, onClick, danger, disabled }) {
  return (
    <button
      type="button" onClick={onClick} disabled={disabled}
      style={{
        background: 'transparent', border: 'none',
        padding: '6px 10px', textAlign: 'left',
        fontSize: 12, fontWeight: 600,
        color: disabled ? 'var(--border-medium)' : danger ? '#dc2626' : 'var(--text-secondary)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        borderRadius: 4, fontFamily: 'inherit',
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = danger ? '#FEF2F2' : 'var(--surface)';
      }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      {children}
    </button>
  );
}

// Eine Section-Reihe in der Page-Karte. Phase 3: native HTML5 drag — die
// Section selbst ist die Drag-Quelle. Drop-Targets sind die DropZones zwischen
// den Sections.
export function SectionRow({
  sectionKey, idx, pageId, onRemove, onAddBelow,
  dragState, setDragState, endDrag,
}) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';
  const [hover, setHover] = useState(false);

  const isBeingDragged =
    dragState && dragState.fromPageId === pageId && dragState.fromIdx === idx;

  return (
    <div
      data-noselect
      draggable
      onDragStart={(e) => {
        e.stopPropagation();
        setDragState({ fromPageId: pageId, fromIdx: idx, sectionKey });
        // Damit Firefox den Drag akzeptiert — Payload wird per State gefuehrt
        try { e.dataTransfer.setData('text/plain', sectionKey); } catch (_) {}
        e.dataTransfer.effectAllowed = 'move';
      }}
      onDragEnd={(e) => { e.stopPropagation(); endDrag(); }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        padding: '8px 10px',
        background: hover ? 'var(--bg-app)' : '#fff',
        border: '1px solid var(--border-light)', borderRadius: 6,
        fontSize: 12,
        cursor: 'grab',
        opacity: isBeingDragged ? 0.4 : 1,
        transition: 'opacity 0.1s',
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2,
      }}>
        <span aria-hidden style={{ color: 'var(--border-medium)', fontSize: 12, lineHeight: 1, userSelect: 'none' }}>⠿</span>
        <span style={{ color: 'var(--border-medium)', fontVariantNumeric: 'tabular-nums', minWidth: 14, fontSize: 12 }}>
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
        fontSize: 12, color: 'var(--text-secondary)',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {desc}
      </div>
      {hover && !dragState && (
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

// Phase 4: Read-only-Variante einer Section-Zeile, fuer Kinder einer Gruppe.
// Keine Drag-Handles, keine Remove/Add-Buttons — Aenderungen muessen am
// Eltern-Group gemacht werden.
export function InheritedSectionRow({ sectionKey, idx }) {
  const label = SECTION_LABEL[sectionKey] || sectionKey;
  const desc = SECTION_CATALOG[sectionKey] || '';
  return (
    <div data-noselect style={{
      padding: '8px 10px',
      background: 'var(--bg-app)',
      border: '1px dashed var(--border-medium)', borderRadius: 6,
      fontSize: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
        <span style={{ color: 'var(--border-medium)', fontVariantNumeric: 'tabular-nums', minWidth: 14, fontSize: 12 }}>
          {idx + 1}
        </span>
        <span style={{ fontWeight: 700, color: 'var(--text-secondary)', flex: 1, minWidth: 0,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {label}
        </span>
      </div>
      <div style={{
        fontSize: 12, color: 'var(--text-secondary)',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {desc}
      </div>
    </div>
  );
}

// Phase 3: DropZone — duenner Spacer zwischen / nach Sections, der bei aktivem
// Drag als Drop-Target fungiert. Highlightet sich wenn der gezogene Eintrag
// drueber schwebt.
export function DropZone({ pageId, position, dragState, dropTarget, setDropTarget, onDrop, endDrag }) {
  const isActive = !!dragState; // nur sichtbar wenn etwas gezogen wird
  const isHighlighted =
    dropTarget && dropTarget.pageId === pageId && dropTarget.position === position;

  // Self-drop nicht erlauben — ein Section kann nicht direkt vor oder hinter
  // sich selbst gedroppt werden (no-op Move).
  const isSelfPosition =
    dragState
    && dragState.fromPageId === pageId
    && (dragState.fromIdx === position || dragState.fromIdx + 1 === position);

  return (
    <div
      data-noselect
      onDragOver={(e) => {
        if (!isActive || isSelfPosition) return;
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'move';
        if (!isHighlighted) setDropTarget({ pageId, position });
      }}
      onDragLeave={(e) => {
        // Leave-Events feuern auch fuer Kinder; nur reagieren wenn wir wirklich
        // den DropZone verlassen.
        if (e.currentTarget.contains(e.relatedTarget)) return;
        if (isHighlighted) setDropTarget(null);
      }}
      onDrop={(e) => {
        if (!isActive || isSelfPosition) return;
        e.preventDefault();
        e.stopPropagation();
        onDrop({
          fromPageId: dragState.fromPageId,
          fromIdx:    dragState.fromIdx,
          toPageId:   pageId,
          toIdx:      position,
          sectionKey: dragState.sectionKey,
        });
        endDrag();
      }}
      style={{
        height: isActive ? (isHighlighted ? 14 : 8) : 2,
        margin: isActive ? '2px 0' : 0,
        borderRadius: 3,
        background: isHighlighted ? KC_MID : 'transparent',
        transition: 'height 0.1s, background 0.1s',
      }}
    />
  );
}

// "+"-Button zwischen / nach Pages
export function AddPagePlus({ onClick, large = false }) {
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
// Phase D: Bottom-Toolbar — schwebt unten im Canvas, Zoom + Page-Count
// ─────────────────────────────────────────────────────────────────────────────

