/**
 * Das rechte Feld zum Tauschen und Hinzufuegen von Bloecken (L-25).
 *
 * Am 2026-08-30 aus `WireframeView.jsx` herausgeloest — 114 Zeilen. Es stand
 * dort als JSX-Ausdruck mitten in der Rueckgabe; die Bedingung `swapPanel.open`
 * bleibt beim Aufrufer, damit am Aufrufort sichtbar bleibt, **wann** es
 * erscheint.
 *
 * **Warum ueberhaupt:** Ohne dieses Stueck blieb die Ansicht bei 818 Zeilen —
 * achtzehn ueber der Grenze. Ein Schnitt, der knapp darueber endet, ist kein
 * Schnitt, sondern eine Verschiebung auf morgen.
 */
import { CATEGORIES, KC_DARK, KC_MID } from './wireframeDaten';
import { LibraryCard } from './wireframeTeile';

export default function BlockTauschPanel({
  swapPanel,
  setSwapPanel,
  libraryLoading,
  filteredLibrary,
  recommendations,
  searchQuery,
  setSearchQuery,
  activeCategory,
  setActiveCategory,
  addBlock,
  swapBlock,
}) {
  return (
    <aside
      style={{
        width: 340,
        flexShrink: 0,
        background: '#fff',
        borderLeft: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-4px 0 12px rgba(0,0,0,0.04)',
      }}
    >
      <div style={{ padding: '16px 16px 12px', borderBottom: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: KC_DARK, textTransform: 'uppercase' }}>
            {swapPanel.mode === 'swap' ? 'Block tauschen' : 'Block hinzufügen'}
          </div>
          <button
            type="button"
            onClick={() => setSwapPanel({ open: false, targetIdx: null, mode: 'swap' })}
            aria-label="Schließen"
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: 'var(--text-secondary)' }}
          >
            ✕
          </button>
        </div>
        <input aria-label="Suchen…"
          type="text"
          placeholder="Suchen…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '7px 10px',
            border: '1px solid var(--border-medium)',
            borderRadius: 6,
            fontSize: 12,
            outline: 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', gap: 4, padding: '8px 12px', borderBottom: '1px solid var(--border-light)', overflowX: 'auto' }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            style={{
              padding: '4px 10px',
              border: 'none',
              borderRadius: 4,
              background: activeCategory === cat ? KC_DARK : 'transparent',
              color: activeCategory === cat ? '#fff' : 'var(--text-secondary)',
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              flexShrink: 0,
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        {libraryLoading && <div style={{ padding: 16, color: 'var(--text-secondary)', fontSize: 12 }}>Lädt…</div>}
        {!libraryLoading && filteredLibrary.length === 0 && (
          <div style={{ padding: 16, color: 'var(--text-tertiary)', fontSize: 12 }}>
            Keine Treffer.
          </div>
        )}
        {/* W2: „Empfohlen für diesen Slot" — Top-3 Vorschläge.
            Sichtbar nur wenn keine User-Filter aktiv (Default-Zustand),
            damit gefilterte Suche nicht durch eine Empfehlungs-Liste
            verwirrt wird. */}
        {recommendations.length > 0 && !searchQuery && activeCategory === 'Alle' && (
          <div style={{
            marginBottom: 12, padding: 8,
            background: '#FEF3C7', border: '1px solid #FCD34D',
            borderRadius: 8,
          }}>
            <div style={{
              fontSize: 12, fontWeight: 800, color: '#92400E',
              textTransform: 'uppercase', letterSpacing: '0.06em',
              marginBottom: 6, padding: '0 2px',
            }}>
              💡 Empfohlen für diesen Slot
            </div>
            {recommendations.map((c) => (
              <LibraryCard
                key={`rec-${c.slug}`}
                item={c}
                onPick={() => (swapPanel.mode === 'swap' ? swapBlock(swapPanel.targetIdx, c.slug) : addBlock(c.slug))}
                compact
              />
            ))}
          </div>
        )}

        {filteredLibrary.map((c) => (
          <LibraryCard
            key={c.slug}
            item={c}
            onPick={() => (swapPanel.mode === 'swap' ? swapBlock(swapPanel.targetIdx, c.slug) : addBlock(c.slug))}
          />
        ))}
      </div>
    </aside>
  );
}
