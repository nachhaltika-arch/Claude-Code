/**
 * Die Karten der Wireframe-Ansicht (L-25).
 *
 * Seitenminiatur, Blockkarte, Bibliothekskarte. Am 2026-08-30 aus
 * `WireframeView.jsx` herausgeloest — und beim ersten Anlauf zusammen mit dem
 * Detailfeld, was **894 Zeilen** ergab: eine neue Datei ueber der Grenze ist
 * kein Fortschritt, sondern eine verschobene Schuld. Das Detailfeld steht
 * deshalb fuer sich in `SectionDetailPanel.jsx`.
 */
import { aufTaste } from '../../utils/tastaturBedienung';
import { KC_DARK, KC_MID, renderSlots } from './wireframeDaten';

export function PageThumb({ page, library, isActive, onClick }) {
  const blocks = (page.blocks || []).slice().sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  const blockCount = blocks.length;

  // Echte Mini-Preview: Sections in 1200px-Container, dann 0.13x scaled.
  // Container width 156px (1200 * 0.13), height auto.
  const SCALE = 0.13;
  const PAGE_W = 156;
  const VIRTUAL_W = Math.round(PAGE_W / SCALE);
  const PREVIEW_H = 220;

  return (
    <button
      type="button" onClick={onClick}
      title={page.page_name || `Seite ${page.page_id}`}
      style={{
        width: PAGE_W, flexShrink: 0,
        background: '#fff',
        border: isActive ? '2px solid #008EAA' : '1px solid var(--border-light)',
        borderRadius: 6, overflow: 'hidden',
        cursor: 'pointer', padding: 0,
        boxShadow: isActive ? '0 4px 12px var(--kc-mid-a-20)' : 'none',
        transition: 'border-color 120ms, box-shadow 120ms',
        fontFamily: 'inherit',
      }}
    >
      {/* Header */}
      <div style={{
        height: 22, padding: '0 6px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: isActive ? '#004F59' : 'var(--bg-app)',
        color: isActive ? '#fff' : '#334155',
        fontSize: 10, fontWeight: 700,
        whiteSpace: 'nowrap', overflow: 'hidden',
      }}>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {page.page_name || `#${page.page_id}`}
        </span>
        <span style={{ fontSize: 9, opacity: 0.7, marginLeft: 4, flexShrink: 0 }}>
          {blockCount}
        </span>
      </div>
      {/* Mini-Preview */}
      <div style={{
        height: PREVIEW_H, overflow: 'hidden',
        background: '#fff', position: 'relative',
        pointerEvents: 'none',
      }}>
        {blockCount === 0 ? (
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--border-medium)', fontSize: 9, fontStyle: 'italic',
          }}>leer</div>
        ) : (
          <div style={{
            width: VIRTUAL_W,
            transform: `scale(${SCALE})`,
            transformOrigin: 'top left',
          }}>
            {blocks.map((b, i) => {
              const lib = library.find((c) => c.slug === b.slug);
              const html = renderSlots(lib?.html_template || '', b?.slots);
              return html ? (
                <div key={i} dangerouslySetInnerHTML={{ __html: html }} />
              ) : (
                <div key={i} style={{
                  height: 80, background: 'var(--surface)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--text-tertiary)', fontSize: 16,
                }}>{b.slug}</div>
              );
            })}
          </div>
        )}
      </div>
    </button>
  );
}

export function BlockCard({
  idx, block, libraryEntry, libraryGeladen = false,
  isDragOver, isDragging,
  onDragStart, onDragOver, onDrop, onDragEnd,
  onSwap, onVariation, onEdit, onRemove,
}) {
  // W3: Slot-Werte aus dem Block in die Live-Preview einrendern. Stufe B: Hat
  // der Block eine eigene Fassung für diesen Kunden, wird die gezeigt — sonst
  // sähe man hier etwas anderes als auf der Seite.
  const eigeneFassung = (block?.html_override || '').trim();
  const html = renderSlots(eigeneFassung || libraryEntry?.html_template || '', block?.slots);
  const name = libraryEntry?.name || block.slug;
  const category = libraryEntry?.category || '—';
  // Der Editor laedt nur freigegebene Bloecke. Fehlt der Eintrag, ist der Block
  // entweder auf Entwurf zurueckgefallen oder geloescht — beides muss dastehen,
  // sonst wirkt die leere Karte wie ein Anzeigefehler.
  const fehltInBibliothek = libraryGeladen && !libraryEntry && !eigeneFassung;

  // Phase B: Klick auf die ganze Card oeffnet das Detail-Panel (Relume-UX).
  // Buttons im Header bekommen stopPropagation, damit sie nicht zusaetzlich
  // den Card-Click ausloesen.
  const stop = (e) => e.stopPropagation();

  return (
    <div role="button" tabIndex={0} onKeyDown={aufTaste(onEdit)}
      draggable
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
      onClick={onEdit}
      style={{
        position: 'relative',
        background: '#fff',
        border: isDragOver ? `2px dashed ${KC_MID}` : '1px solid var(--border-light)',
        borderRadius: 8,
        overflow: 'hidden',
        opacity: isDragging ? 0.4 : 1,
        transition: 'opacity 0.1s',
        cursor: 'pointer',
      }}
    >
      {/* Compact-Header — Drag-Handle + Name + Category-Badge + Hover-Actions */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 10px',
          background: 'var(--bg-app)', borderBottom: '1px solid var(--border-light)',
          fontSize: 11,
        }}
      >
        <span
          aria-hidden title="Ziehen zum Sortieren"
          style={{ cursor: 'grab', color: 'var(--text-tertiary)', fontSize: 14, lineHeight: 1, userSelect: 'none' }}
        >⠿</span>
        <span style={{
          background: 'var(--border-light)', color: 'var(--text-secondary)',
          fontSize: 9, fontWeight: 700,
          padding: '2px 6px', borderRadius: 3,
          textTransform: 'uppercase', letterSpacing: '0.05em',
        }}>{category}</span>
        <span style={{
          flex: 1, minWidth: 0,
          fontSize: 11, fontWeight: 700, color: KC_DARK,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>{name}</span>
        {eigeneFassung && (
          <span
            title="Für diesen Kunden umgeschrieben — die Bibliotheksvorlage wird hier nicht verwendet"
            style={{
              background: '#ede9fe', color: '#5b21b6',
              fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 3,
              textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap',
            }}
          >Eigene Fassung</span>
        )}
        {fehltInBibliothek && (
          <span
            title="Nicht in der freigegebenen Bibliothek — wird auf der Kundenseite nicht ausgegeben"
            style={{
              background: '#fee2e2', color: '#991b1b',
              fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 3,
              textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap',
            }}
          >Fehlt</span>
        )}
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'ui-monospace, monospace', fontSize: 10 }}>
          #{idx + 1}
        </span>
        <button
          type="button" onClick={(e) => { stop(e); onEdit(); }}
          title="Slots editieren / als Custom speichern"
          style={{
            background: 'transparent', color: KC_DARK,
            border: `1px solid ${KC_DARK}`, borderRadius: 4,
            padding: '2px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >✏️ Edit</button>
        <button
          type="button" onClick={(e) => { stop(e); onVariation(); }}
          title="Variante aus gleicher Kategorie vorschlagen"
          style={{
            background: KC_MID, color: '#fff',
            border: 'none', borderRadius: 4,
            padding: '3px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >🔄 Variante</button>
        <button
          type="button" onClick={(e) => { stop(e); onSwap(); }}
          style={{
            background: 'transparent', color: KC_MID,
            border: `1px solid ${KC_MID}`, borderRadius: 4,
            padding: '2px 8px', fontSize: 10, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >Tauschen</button>
        <button
          type="button" onClick={(e) => { stop(e); onRemove(); }} aria-label="Block entfernen"
          style={{
            background: 'transparent', color: '#dc2626',
            border: '1px solid #fca5a5', borderRadius: 4,
            padding: '2px 8px', fontSize: 11, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}
        >✕</button>
      </div>

      {/* Live HTML-Preview — pointerEvents:none damit Klicks im Section-Inhalt
          (Links, Buttons) nicht aktiv sind. Section rendert sich responsiv,
          weil die outer-width vom Preview-Size-Toggle bestimmt wird. */}
      <div
        style={{
          background: '#fff',
          minHeight: 80,
          pointerEvents: 'none',
        }}
      >
        {html && <div dangerouslySetInnerHTML={{ __html: html }} />}
        {!html && fehltInBibliothek && (
          <div style={{ padding: 20, background: '#fef2f2', color: '#991b1b', fontSize: 12 }}>
            <strong style={{ display: 'block', marginBottom: 4 }}>
              Dieser Block steht nicht in der freigegebenen Bibliothek.
            </strong>
            Er ist entweder auf Entwurf zurückgefallen (Vertrag verletzt) oder gelöscht
            worden. So wie er hier steht, wird er auf der Kundenseite nicht ausgegeben —
            im Komponenten-Manager unter <code>{block.slug}</code> nachsehen, dort steht
            der Grund. Bis dahin: Block tauschen oder entfernen.
          </div>
        )}
        {!html && !fehltInBibliothek && (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 12, fontStyle: 'italic' }}>
            {libraryGeladen ? 'Kein HTML-Template hinterlegt' : 'Vorschau lädt…'}
          </div>
        )}
      </div>
    </div>
  );
}

// ── W2: Library-Card (wiederverwendbar — auch in der "Empfohlen"-Sektion) ─────

export function LibraryCard({ item, onPick, compact = false }) {
  const thumbHeight = compact ? 70 : 90;
  return (
    <button
      type="button"
      onClick={onPick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: 0,
        border: '1px solid var(--border-light)',
        borderRadius: 8,
        background: '#fff',
        marginBottom: compact ? 6 : 8,
        cursor: 'pointer',
        overflow: 'hidden',
        transition: 'border-color 0.15s, transform 0.1s',
        fontFamily: 'inherit',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = KC_MID;
        e.currentTarget.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-light)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {item.html_template ? (
        <div style={{
          height: thumbHeight, overflow: 'hidden',
          background: 'var(--bg-app)',
          borderBottom: '1px solid var(--border-light)',
          position: 'relative',
        }}>
          <div style={{
            width: 1200, transform: 'scale(0.25)', transformOrigin: 'top left',
            pointerEvents: 'none',
          }}
            dangerouslySetInnerHTML={{ __html: item.html_template }}
          />
        </div>
      ) : (
        <div style={{
          height: 60, background: 'var(--surface)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-tertiary)', fontSize: 10, fontStyle: 'italic',
        }}>
          Keine Vorschau
        </div>
      )}
      <div style={{ padding: compact ? '6px 8px' : 8 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: KC_DARK, marginBottom: 2 }}>{item.name}</div>
        <div style={{ fontSize: 9, color: 'var(--text-secondary)', fontFamily: 'ui-monospace, monospace' }}>{item.slug}</div>
      </div>
    </button>
  );
}

// ── Phase B: Section-Detail-Panel (Inline-Side-Panel rechts) ─────────────────
//
// Ersetzt das alte SlotEditorModal — kein Overlay mehr, sondern ein Panel das
// neben dem Block-Canvas sitzt. Erweitert um:
//   - Free-Form-KI-Prompt + Asset/Element-Toggles + "Generate copy"-Button,
//     der via /api/components/generate-copy die Slot-Werte in einem Rutsch
//     vom KI-Modell (Sonnet) befuellen laesst.
//   - Erweiterter Modus (HTML editieren / Custom speichern) ist eingeklappt.

