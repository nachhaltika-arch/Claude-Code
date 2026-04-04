const TEAL      = '#008EAA';
const DARK_TEAL = '#004F59';
const WHITE     = '#FFFFFF';

export default function KompagnonLogo({ variant = 'color', height = 40, showTagline = false }) {
  const isWhite = variant === 'white';
  const isIcon  = variant === 'icon';

  const markFill    = isWhite ? WHITE     : DARK_TEAL;  // ellipse
  const kFill       = isWhite ? DARK_TEAL : WHITE;      // "k" letter
  const bowFill     = isWhite ? WHITE     : TEAL;       // teal bow
  const textFill    = isWhite ? WHITE     : TEAL;       // wordmark

  const viewBox = isIcon ? '0 0 70 70' : '0 0 280 70';

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      style={{ height, width: 'auto' }}
      aria-label="KOMPAGNON Logo"
      role="img"
    >
      {/* ── Bildmarke ── */}
      {/* 1. Ellipse */}
      <ellipse cx="32" cy="35" rx="32" ry="35" fill={markFill} />

      {/* 2. "k" */}
      <text
        x="7"
        y="52"
        fontFamily="'Noto Sans', sans-serif"
        fontWeight="900"
        fontSize="44"
        fill={kFill}
      >
        k
      </text>

      {/* 3. Teal bow */}
      <path
        d="M 46,8 C 62,8 70,20 70,35 C 70,50 62,62 46,62
           C 56,62 63,50 63,35 C 63,20 56,8 46,8 Z"
        fill={bowFill}
      />

      {/* ── Wortmarke (not shown in 'icon' variant) ── */}
      {!isIcon && (
        <>
          {/* Zeile 1: KOMPAGNON® */}
          <text
            x="84"
            y={showTagline ? '30' : '36'}
            fontFamily="'Noto Sans', sans-serif"
            fontWeight="900"
            fontSize="22"
            fill={textFill}
            letterSpacing="1"
          >
            KOMPAGNON®
          </text>

          {/* Zeile 2: communications */}
          <text
            x="84"
            y={showTagline ? '47' : '52'}
            fontFamily="'Noto Sans', sans-serif"
            fontWeight="400"
            fontSize="11"
            fill={textFill}
            letterSpacing="2.5"
          >
            communications
          </text>

          {/* Zeile 3: tagline (optional) */}
          {showTagline && (
            <text
              x="84"
              y="62"
              fontFamily="'Noto Sans', sans-serif"
              fontWeight="400"
              fontSize="9"
              fill={textFill}
              letterSpacing="3"
            >
              KOMPAGNON.GROUP
            </text>
          )}
        </>
      )}
    </svg>
  );
}
