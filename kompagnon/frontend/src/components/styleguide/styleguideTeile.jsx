/**
 * Die Bausteine der Style-Guide-Ansicht (L-25).
 *
 * Farbkacheln, Typografiekarten, die Demo-Bloecke und die Live-Vorschau. Am
 * 2026-08-30 aus `StyleGuideView.jsx` herausgeloest — 774 der damals 1.560
 * Zeilen. Alle waren dort schon eigene Funktionen.
 */
import { useRef } from 'react';
import { aufTaste } from '../../utils/tastaturBedienung';
import { KC_DARK, colorScale } from './styleguideDaten';

export function SectionShell({ title, right, children }) {
  return (
    <section style={{ marginBottom: 22 }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <h2 style={{
          margin: 0, fontSize: 18, fontWeight: 800, color: KC_DARK,
          letterSpacing: '-0.01em',
        }}>{title}</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {right}
        </div>
      </div>
      {children}
    </section>
  );
}
export function ShufflePin({ shortcut, onClick }) {
  return (
    <button type="button" onClick={onClick}
      title={`Würfeln (${shortcut})`}
      style={{
        background: '#fff', color: 'var(--text-secondary)',
        border: '1px solid var(--border-light)', borderRadius: 6,
        padding: '4px 8px', fontSize: 12, fontWeight: 700,
        cursor: 'pointer', fontFamily: 'inherit',
        display: 'inline-flex', alignItems: 'center', gap: 6,
      }}>
      <span style={{ fontSize: 13 }}>⇄</span>
      <span>Shuffle</span>
      <span style={{
        background: 'var(--surface)', color: 'var(--text-secondary)',
        padding: '1px 5px', borderRadius: 3,
        fontSize: 10, fontWeight: 800, letterSpacing: '0.04em',
      }}>{shortcut}</span>
    </button>
  );
}

export function LightDarkToggle({ lightDark, onToggle }) {
  return (
    <div style={{
      display: 'inline-flex',
      border: '1px solid var(--border-light)', borderRadius: 6, overflow: 'hidden',
      background: '#fff',
    }}>
      <button type="button" onClick={() => lightDark !== 'light' && onToggle()}
        title="Light Mode"
        style={{
          padding: '6px 10px',
          background: lightDark === 'light' ? '#fef9c3' : 'transparent',
          color: lightDark === 'light' ? '#854d0e' : 'var(--text-tertiary)',
          border: 'none', cursor: 'pointer', fontSize: 13,
        }}>☀</button>
      <button type="button" onClick={() => lightDark !== 'dark' && onToggle()}
        title="Dark Mode"
        style={{
          padding: '6px 10px',
          background: lightDark === 'dark' ? '#1e293b' : 'transparent',
          color: lightDark === 'dark' ? '#fef9c3' : 'var(--text-tertiary)',
          border: 'none', cursor: 'pointer', fontSize: 13,
        }}>☾</button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ColorsSection — Tile-Grid mit Neutrals + Brand-Farben + "+"-Card
// ─────────────────────────────────────────────────────────────────────────────

export const BRAND_TILES = [
  { key: 'accent_1', label: 'Primary',  isMain: true },
  { key: 'accent_2', label: 'Secondary', isMain: false },
  { key: 'accent_3', label: 'Akzent',    isMain: false },
];

export function ColorsSection({ palette, lightDark, onTogglelightDark, onShuffle, onSetToken, onResetAll }) {
  const neutralsScale = [
    palette.bg_primary, palette.bg_surface, palette.border, palette.text_muted, palette.text_primary,
  ];

  return (
    <SectionShell
      title="Colors"
      right={
        <>
          <LightDarkToggle lightDark={lightDark} onToggle={onTogglelightDark} />
          <ShufflePin shortcut="C" onClick={onShuffle} />
        </>
      }
    >
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 12,
      }}>
        <ColorTile
          label="Neutrals"
          hex={null}
          scale={neutralsScale}
          isMain={false}
          onChangeHex={null}
          onResetAll={onResetAll}
        />
        {BRAND_TILES.map((t) => (
          <ColorTile
            key={t.key}
            label={t.label}
            hex={palette[t.key]}
            scale={colorScale(palette[t.key])}
            isMain={t.isMain}
            onChangeHex={(v) => onSetToken(t.key, v)}
          />
        ))}
        <AddColorTile />
      </div>
    </SectionShell>
  );
}

export function ColorTile({ label, hex, scale, isMain, onChangeHex, onResetAll }) {
  const inputRef = useRef(null);
  const isReadonly = !onChangeHex;
  const handleClick = () => {
    if (!isReadonly && inputRef.current) inputRef.current.click();
  };

  // Card-Background = ggf. die Farbe selbst (für Brand-Tiles), sonst weiß (Neutrals)
  const bg = hex || '#FFFFFF';
  const fg = hex ? readableOn(hex) : '#0F172A';

  return (
    <div role="button" tabIndex={0} onKeyDown={aufTaste(handleClick)}
      onClick={handleClick}
      style={{
        background: bg,
        border: `1px solid ${hex ? 'transparent' : 'var(--border-light)'}`,
        borderRadius: 10,
        padding: '14px 14px 0',
        cursor: isReadonly ? 'default' : 'pointer',
        position: 'relative',
        minHeight: 130,
        display: 'flex', flexDirection: 'column',
        boxShadow: hex ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
        overflow: 'hidden',
      }}>
      {/* Header: Label + Main-Badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: fg }}>{label}</div>
        {isMain && (
          <span style={{
            fontSize: 9, fontWeight: 800, color: fg,
            background: 'rgba(255,255,255,0.20)',
            border: `1px solid ${fg === '#FFFFFF' ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.18)'}`,
            padding: '2px 8px', borderRadius: 999,
            textTransform: 'uppercase', letterSpacing: '0.06em',
          }}>Main</span>
        )}
      </div>

      {/* Hex */}
      {hex && (
        <div style={{
          fontSize: 18, fontWeight: 800, color: fg, marginTop: 24,
          fontFamily: 'ui-monospace, "SF Mono", monospace', letterSpacing: '-0.01em',
        }}>{hex.replace('#', '').toUpperCase()}</div>
      )}

      {/* Color-Scale Streifen unten */}
      <div style={{ display: 'flex', height: 28, marginTop: 14, marginLeft: -14, marginRight: -14 }}>
        {scale.map((s, i) => (
          <div key={i} style={{ flex: 1, background: s }} />
        ))}
      </div>

      {/* Hidden Color-Picker */}
      {!isReadonly && (
        <input aria-label="Farbe waehlen"
          ref={inputRef}
          type="color"
          value={hex || '#000000'}
          onChange={(e) => onChangeHex(e.target.value.toUpperCase())}
          style={{ display: 'none' }}
        />
      )}

      {/* Reset-All bei Neutrals — kein direkter Edit, aber Reset-Button */}
      {onResetAll && (
        <button type="button"
          onClick={(e) => { e.stopPropagation(); onResetAll(); }}
          title="Alle Color-Overrides zurücksetzen"
          style={{
            position: 'absolute', top: 8, right: 8,
            background: 'rgba(255,255,255,0.85)', color: 'var(--text-secondary)',
            border: '1px solid var(--border-light)', borderRadius: 4,
            padding: '2px 6px', fontSize: 9, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
          }}>↻ Reset</button>
      )}
    </div>
  );
}

export function AddColorTile() {
  return (
    <div
      title="Custom-Farbe (kommt bald)"
      style={{
        background: '#fafafa',
        border: '2px dashed var(--border-light)',
        borderRadius: 10,
        padding: '14px',
        minHeight: 130,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--border-medium)', fontSize: 32, fontWeight: 300,
        cursor: 'not-allowed',
      }}>+</div>
  );
}

// Liefert eine lesbare Vordergrundfarbe für einen Background-Hex
export function readableOn(hex) {
  const m = hex.replace('#', '');
  if (m.length !== 6) return '#0F172A';
  const r = parseInt(m.slice(0, 2), 16);
  const g = parseInt(m.slice(2, 4), 16);
  const b = parseInt(m.slice(4, 6), 16);
  const luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luma > 0.55 ? '#0F172A' : '#FFFFFF';
}

// ─────────────────────────────────────────────────────────────────────────────
// TypographySection — Heading + Body Cards
// ─────────────────────────────────────────────────────────────────────────────

export const FONT_SCALES = [
  { id: 'small',   label: 'Small — normal' },
  { id: 'default', label: 'Standard' },
  { id: 'large',   label: 'Large — Display' },
];

export function TypographySection({ typoPairing, fontScale, onScaleChange, onShuffle }) {
  return (
    <SectionShell
      title="Typography"
      right={
        <>
          <select aria-label="Schriftgroessen-Stufe"
            value={fontScale}
            onChange={(e) => onScaleChange(e.target.value)}
            style={{
              padding: '5px 10px',
              border: '1px solid var(--border-light)', borderRadius: 6,
              fontSize: 12, fontFamily: 'inherit', color: 'var(--text-secondary)',
              background: '#fff', cursor: 'pointer', outline: 'none', fontWeight: 600,
            }}
          >
            {FONT_SCALES.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
          <ShufflePin shortcut="T" onClick={onShuffle} />
        </>
      }
    >
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
      }}>
        <TypoCard label="Heading" font={typoPairing.heading} weight={typoPairing.heading_weight} />
        <TypoCard label="Body"    font={typoPairing.body}    weight={typoPairing.body_weight} />
      </div>
    </SectionShell>
  );
}

export function TypoCard({ label, font, weight }) {
  return (
    <div style={{
      background: '#fff',
      border: '1px solid var(--border-light)', borderRadius: 10,
      padding: '14px 16px',
      minHeight: 130,
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
    }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>
      <div style={{
        fontFamily: `'${font}', system-ui, sans-serif`, fontWeight: weight,
        fontSize: 28, color: KC_DARK, letterSpacing: '-0.01em',
        margin: '16px 0 12px',
      }}>{font}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-secondary)' }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          fontWeight: 700, color: KC_DARK,
        }}>
          <span style={{
            display: 'inline-block', width: 14, height: 14,
            background: 'conic-gradient(from -45deg, #EA4335 0deg 90deg, #FBBC05 90deg 180deg, #34A853 180deg 270deg, #4285F4 270deg 360deg)',
            borderRadius: '50%',
          }} />
          Google
        </span>
        <span style={{ color: 'var(--border-medium)' }}>|</span>
        <span style={{ color: '#16a34a', fontWeight: 700 }}>Free</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// UIStylingSection — Buttons & Forms + Cards & Images Demo-Cards
// ─────────────────────────────────────────────────────────────────────────────

export function UIStylingSection({
  palette, uiStyle, cardVariant, buttonVariants, typo, forms, card,
  onCycleUi, onCycleCard, onShuffle,
}) {
  return (
    <SectionShell
      title="UI Styling"
      right={<ShufflePin shortcut="U" onClick={onShuffle} />}
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <ButtonsFormsDemo
          palette={palette} ui={uiStyle} variants={buttonVariants}
          typo={typo} forms={forms} onClick={onCycleUi}
        />
        <CardsImagesDemo
          palette={palette} ui={uiStyle} cardVariant={cardVariant}
          typo={typo} card={card} variants={buttonVariants}
          onClick={onCycleCard}
        />
      </div>
    </SectionShell>
  );
}

export function ButtonsFormsDemo({ palette, ui, variants, typo, forms, onClick }) {
  return (
    <div role="button" tabIndex={0} onKeyDown={aufTaste(onClick)} onClick={onClick}
      title="Klicken um den UI-Stil zu wechseln"
      style={{
        background: '#fff',
        border: '1px solid var(--border-light)', borderRadius: 10,
        padding: '16px 14px', cursor: 'pointer',
        minHeight: 200,
        display: 'flex', flexDirection: 'column', gap: 14,
      }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        Buttons & Forms
      </div>

      {/* Buttons-Demo */}
      <div style={{ display: 'flex', gap: 8 }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          background: variants.primary.bg, color: variants.primary.fg,
          border: `1px solid ${variants.primary.border}`,
          borderRadius: ui.button_radius,
          padding: '7px 14px', fontSize: 12, fontWeight: 700,
          fontFamily: `'${typo.body}', system-ui`,
          boxShadow: variants.primary.shadow,
        }}>Button</span>
        <span style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          background: variants.secondary.bg, color: variants.secondary.fg,
          border: `${ui.border_width} solid ${variants.secondary.border}`,
          borderRadius: ui.button_radius,
          padding: '7px 14px', fontSize: 12, fontWeight: 700,
          fontFamily: `'${typo.body}', system-ui`,
        }}>Button</span>
      </div>

      {/* Form-Demo */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
          Label
        </div>
        <div style={{
          padding: '8px 10px', fontSize: 12,
          color: forms.placeholder,
          background: forms.style === 'filled' ? 'var(--bg-app)' : 'transparent',
          border: forms.style === 'underlined' ? 'none' : `1px solid ${forms.style === 'outlined' ? 'var(--border-medium)' : 'transparent'}`,
          borderBottom: forms.style === 'underlined' ? '1px solid var(--border-medium)' : undefined,
          borderRadius: forms.style === 'underlined' ? 0 : ui.button_radius,
        }}>Placeholder</div>
      </div>
    </div>
  );
}

export function CardsImagesDemo({ palette, ui, cardVariant, typo, card, variants, onClick }) {
  // Mini-Bild als CSS-Gradient (kein Asset noetig)
  const imgBg = 'linear-gradient(135deg, var(--text-tertiary) 0%, var(--text-secondary) 50%, var(--text-secondary) 100%)';

  return (
    <div role="button" tabIndex={0} onKeyDown={aufTaste(onClick)} onClick={onClick}
      title="Klicken um die Card-Variante zu wechseln"
      style={{
        background: '#fff',
        border: '1px solid var(--border-light)', borderRadius: 10,
        padding: '16px 14px', cursor: 'pointer',
        minHeight: 200,
        display: 'flex', flexDirection: 'column', gap: 12,
      }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        Cards & Images
      </div>

      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        {/* 2 Mini-Image-Cards */}
        <div style={{
          width: 50, height: 60, background: imgBg,
          borderRadius: ui.card_radius,
          border: card.border_width === '0px' ? 'none' : `${card.border_width} solid ${card.border_color}`,
          boxShadow: card.shadow,
        }} />
        <div style={{
          width: 50, height: 60, background: imgBg,
          borderRadius: ui.card_radius,
          border: card.border_width === '0px' ? 'none' : `${card.border_width} solid ${card.border_color}`,
          boxShadow: card.shadow,
        }} />

        {/* Mini-Card mit Text */}
        <div style={{
          flex: 1,
          background: card.background,
          border: card.border_width === '0px' ? 'none' : `${card.border_width} solid ${card.border_color}`,
          borderRadius: card.radius,
          boxShadow: card.shadow,
          padding: '8px 10px',
          fontFamily: `'${typo.body}', system-ui`,
        }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: palette.text_primary, lineHeight: 1.2, marginBottom: 4 }}>
            Medium length section heading
          </div>
          <div style={{ fontSize: 8, color: palette.text_muted, lineHeight: 1.35 }}>
            Pick a card style that matches your overall aesthetic.
          </div>
          <div style={{
            marginTop: 6, display: 'inline-block',
            background: variants.primary.bg, color: variants.primary.fg,
            border: `1px solid ${variants.primary.border}`,
            borderRadius: ui.button_radius,
            padding: '3px 8px', fontSize: 8, fontWeight: 700,
          }}>Button</div>
        </div>
      </div>

      <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
        {cardVariant.label} · {ui.label}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// DeviceToggle — unten rechts in der Live-Preview
// ─────────────────────────────────────────────────────────────────────────────

export function DeviceToggle({ device, onChange }) {
  const items = [
    { id: 'desktop', icon: '🖥', label: 'Desktop' },
    { id: 'tablet',  icon: '📱', label: 'Tablet'  },
    { id: 'mobile',  icon: '📱', label: 'Mobile'  },
  ];
  return (
    <div style={{
      position: 'absolute', bottom: 16, right: 24,
      display: 'inline-flex',
      background: '#fff', border: '1px solid var(--border-light)', borderRadius: 8,
      padding: 3, gap: 1,
      boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
    }}>
      {items.map((it) => {
        const active = device === it.id;
        return (
          <button key={it.id} type="button" onClick={() => onChange(it.id)}
            title={it.label}
            style={{
              padding: '4px 8px',
              background: active ? KC_DARK : 'transparent',
              color: active ? '#fff' : 'var(--text-secondary)',
              border: 'none', borderRadius: 5, cursor: 'pointer',
              fontSize: 13, fontFamily: 'inherit', fontWeight: 700,
              minWidth: 30,
            }}>
            {/* Geräte-Icons in SVG für saubere Darstellung */}
            <DeviceIcon kind={it.id} active={active} />
          </button>
        );
      })}
    </div>
  );
}

export function DeviceIcon({ kind, active }) {
  const stroke = active ? '#fff' : 'var(--text-secondary)';
  if (kind === 'desktop') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" /><line x1="8" y1="21" x2="16" y2="21" /><line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    );
  }
  if (kind === 'tablet') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="2" width="16" height="20" rx="2" /><line x1="12" y1="18" x2="12.01" y2="18" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="7" y="2" width="10" height="20" rx="2" /><line x1="12" y1="18" x2="12.01" y2="18" />
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LivePreview — Sample Wireframe-Section mit aktuellen Tokens
// ─────────────────────────────────────────────────────────────────────────────

export function LivePreview({ palette, typo, ui, spacing, variants, semantic, forms, card, badges, fontScale, device }) {
  const spX = spacing?.scale?.[5] ?? 32;
  const spY = spacing?.section_y ?? 64;
  const gap = spacing?.gap ?? 16;
  const isCompact = device === 'mobile';

  const heroSize = fontScale === 'large' ? 40 : fontScale === 'small' ? 26 : 32;
  const bodySize = fontScale === 'large' ? 17 : fontScale === 'small' ? 14 : 15;

  const primary   = variants?.primary   || { bg: palette.accent_1, fg: palette.bg_primary, border: palette.accent_1, shadow: ui.shadow };
  const secondary = variants?.secondary || { bg: 'transparent', fg: palette.accent_1, border: palette.accent_1, shadow: 'none' };

  return (
    <div style={{
      background: palette.bg_primary,
      borderRadius: 12, overflow: 'hidden',
      border: `1px solid ${palette.border}`,
      boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
    }}>
      {/* Mini-Nav */}
      <div style={{
        padding: `${isCompact ? 14 : 18}px ${spX * 0.75}px`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: `1px solid ${palette.border}`,
        background: palette.bg_primary,
        fontFamily: `'${typo.body}', system-ui`,
        gap: 12, flexWrap: 'wrap',
      }}>
        <div style={{
          fontFamily: `'${typo.heading}', system-ui`, fontWeight: typo.heading_weight,
          fontSize: 18, color: palette.text_primary, fontStyle: 'italic',
        }}>Logo</div>
        {!isCompact && (
          <div style={{ display: 'flex', gap: 18, fontSize: 12, color: palette.text_primary, fontWeight: 600 }}>
            <span>Leistungen</span><span>Strategie</span><span>Design</span><span>Mehr ▾</span>
          </div>
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <span style={{
            background: 'transparent', color: palette.text_primary,
            border: `${ui.border_width} solid ${palette.border}`, borderRadius: ui.button_radius,
            padding: '5px 11px', fontSize: 12, fontWeight: 700,
          }}>Kontakt</span>
          <span style={{
            background: primary.bg, color: primary.fg,
            border: `1px solid ${primary.border}`, borderRadius: ui.button_radius,
            padding: '5px 11px', fontSize: 12, fontWeight: 700, boxShadow: primary.shadow,
          }}>{isCompact ? 'Menü' : 'Menü'}</span>
        </div>
      </div>

      {/* Hero */}
      <div style={{
        padding: `${spY * 0.6}px ${spX}px`,
        background: palette.bg_primary,
        color: palette.text_primary,
        fontFamily: `'${typo.body}', system-ui`,
      }}>
        <div style={{
          fontSize: 12, color: palette.text_muted,
          fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em',
          marginBottom: 8,
        }}>Wallbox-Installation</div>
        <h1 style={{
          fontFamily: `'${typo.heading}', system-ui`, fontWeight: typo.heading_weight,
          fontSize: heroSize, lineHeight: 1.15, margin: `0 0 ${gap}px`,
          color: palette.text_primary, letterSpacing: '-0.01em',
        }}>
          Förderfähige Wallbox in 14 Tagen — fix installiert.
        </h1>
        <p style={{
          fontSize: bodySize, lineHeight: 1.5, color: palette.text_muted,
          margin: `0 0 ${gap * 1.5}px`, maxWidth: 480,
        }}>
          Wir kümmern uns um Beratung, Antrag, Installation und Anmeldung beim
          Netzbetreiber. Festpreis vorab — keine Überraschungen.
        </p>
        <div style={{ display: 'flex', gap: gap * 0.6, flexWrap: 'wrap' }}>
          <button type="button" style={{
            background: primary.bg, color: primary.fg,
            border: `1px solid ${primary.border}`, borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: 'inherit', cursor: 'pointer', boxShadow: primary.shadow,
          }}>Festpreis anfragen</button>
          <button type="button" style={{
            background: secondary.bg, color: secondary.fg,
            border: `${ui.border_width} solid ${secondary.border}`,
            borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: 'inherit', cursor: 'pointer',
          }}>Beratung vereinbaren</button>
        </div>

        {semantic && (
          <div style={{ display: 'flex', gap: gap * 0.5, flexWrap: 'wrap', marginTop: gap * 1.5 }}>
            {[
              { key: 'success', label: '✓ Förderung bewilligt' },
              { key: 'warn',    label: '⏱ Termin in Bearbeitung' },
              { key: 'info',    label: 'ℹ THG-Quote inklusive' },
            ].map((s) => {
              const c = semantic[s.key];
              return (
                <span key={s.key} style={{
                  padding: '4px 10px', background: c.bg, color: c.fg,
                  border: `1px solid ${c.border}`, borderRadius: ui.button_radius,
                  fontSize: 10, fontWeight: 700,
                }}>{s.label}</span>
              );
            })}
          </div>
        )}
      </div>

      {/* Image-Placeholder */}
      <div style={{
        margin: `0 ${spX}px ${spY * 0.5}px`,
        background: palette.bg_surface,
        borderRadius: ui.card_radius,
        border: `1px solid ${palette.border}`,
        height: isCompact ? 180 : 280,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: palette.text_muted,
      }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="9" cy="9" r="2" />
          <path d="M21 15l-5-5L5 21" />
        </svg>
      </div>

      {/* Trust-Strip */}
      <div style={{
        padding: '14px 28px',
        background: palette.bg_surface,
        borderTop: `1px solid ${palette.border}`,
        display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center',
        fontFamily: `'${typo.body}', system-ui`, color: palette.text_muted,
        fontSize: 12, fontWeight: 600,
      }}>
        <span>✓ Innungsmeisterbetrieb</span>
        <span>·</span><span>✓ THG-Quote inklusive</span>
        <span>·</span><span>✓ Festpreis-Garantie</span>
        {!isCompact && <><span>·</span><span>✓ Förderantrag inklusive</span></>}
      </div>

      {/* Feature-Cards */}
      <div style={{
        padding: `${spY * 0.5}px ${spX}px`,
        background: palette.bg_primary,
        borderTop: `1px solid ${palette.border}`,
      }}>
        <h2 style={{
          fontFamily: `'${typo.heading}', system-ui`, fontWeight: typo.heading_weight,
          fontSize: 22, color: palette.text_primary, margin: `0 0 ${gap}px`,
        }}>Drei Pakete, ein Festpreis</h2>
        <div style={{
          display: 'grid', gridTemplateColumns: isCompact ? '1fr' : 'repeat(auto-fit, minmax(180px, 1fr))',
          gap,
        }}>
          {[
            { title: 'Standard', desc: '11 kW, einphasig, ideal für Single-Garage', status: 'info',    statusLabel: 'Beliebt' },
            { title: 'Komfort',  desc: '22 kW dreiphasig, Lastmanagement',           status: 'success', statusLabel: 'Empfohlen' },
            { title: 'Premium',  desc: 'PV-Integration, App-Steuerung, Förderpaket', status: 'warn',    statusLabel: 'Limitiert' },
          ].map((f, i) => (
            <div key={i} style={{
              background: card?.background || palette.bg_surface,
              border: card?.border_width === '0px'
                ? 'none'
                : `${card?.border_width || ui.border_width} solid ${card?.border_color || palette.border}`,
              borderRadius: card?.radius || ui.card_radius,
              padding: card?.padding || '16px',
              boxShadow: card?.shadow || ui.shadow,
              fontFamily: `'${typo.body}', system-ui`, color: palette.text_primary,
              position: 'relative',
            }}>
              {badges?.[f.status] && (
                <span style={{
                  position: 'absolute', top: 10, right: 10,
                  padding: '2px 8px',
                  background: badges[f.status].bg, color: badges[f.status].fg,
                  border: `1px solid ${badges[f.status].border}`,
                  borderRadius: badges[f.status].radius,
                  fontSize: 9, fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>{f.statusLabel}</span>
              )}
              <div style={{
                fontFamily: `'${typo.heading}', system-ui`, fontWeight: typo.heading_weight,
                fontSize: 15, color: palette.text_primary, marginBottom: 6, paddingRight: 70,
              }}>{f.title}</div>
              <div style={{ fontSize: 12, color: palette.text_muted, lineHeight: 1.45 }}>
                {f.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Inline-Form */}
      {forms && (
        <div style={{
          padding: `${spY * 0.5}px ${spX}px`,
          background: palette.bg_surface,
          borderTop: `1px solid ${palette.border}`,
        }}>
          <h3 style={{
            fontFamily: `'${typo.heading}', system-ui`, fontWeight: typo.heading_weight,
            fontSize: 18, color: palette.text_primary, margin: `0 0 ${gap}px`,
          }}>Kostenlose Beratung</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: isCompact ? '1fr' : 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: gap * 0.7,
          }}>
            <input aria-label="Name" type="text" placeholder="Name" style={inputStyle(forms, palette, ui)} />
            <input aria-label="E-Mail" type="email" placeholder="E-Mail" style={inputStyle(forms, palette, ui)} />
            <button type="button" style={{
              background: primary.bg, color: primary.fg,
              border: `1px solid ${primary.border}`, borderRadius: ui.button_radius,
              padding: '10px 16px', fontSize: 12, fontWeight: 700,
              fontFamily: `'${typo.body}', system-ui`, cursor: 'pointer',
              boxShadow: primary.shadow,
            }}>Termin anfragen</button>
          </div>
        </div>
      )}
    </div>
  );
}

export function inputStyle(forms, palette, ui) {
  return {
    padding: '10px 12px', fontSize: 13,
    color: palette.text_primary,
    background: forms.style === 'filled' ? palette.bg_primary : 'transparent',
    border: forms.style === 'underlined'
      ? 'none'
      : forms.style === 'outlined'
        ? `1px solid ${palette.border}`
        : 'none',
    borderBottom: forms.style === 'underlined' ? `1px solid ${palette.border}` : undefined,
    borderRadius: forms.style === 'underlined' ? 0 : ui.button_radius,
    outline: 'none',
  };
}
