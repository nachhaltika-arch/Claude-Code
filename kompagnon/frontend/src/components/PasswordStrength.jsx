/**
 * Live-Anzeige der Passwort-Komplexitaet.
 * Muss 1:1 zu _validate_password() in auth_router.py passen.
 */
export default function PasswordStrength({ password }) {
  if (!password) return null;

  const checks = [
    { label: 'Mindestens 12 Zeichen',   ok: password.length >= 12 },
    { label: 'Grossbuchstabe (A-Z)',    ok: /[A-Z]/.test(password) },
    { label: 'Ziffer (0-9)',            ok: /[0-9]/.test(password) },
    { label: 'Sonderzeichen (!@#$%...)', ok: /[^A-Za-z0-9]/.test(password) },
  ];

  const passed = checks.filter(c => c.ok).length;
  const color  =
    passed <= 1 ? '#dc2626' :
    passed <= 2 ? '#f59e0b' :
    passed <= 3 ? '#eab308' :
                  '#16a34a';

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {checks.map((_, i) => (
          <div key={i} style={{
            flex: 1, height: 4, borderRadius: 2,
            background: i < passed ? color : 'var(--border-light, #e2e8f0)',
            transition: 'background 0.2s',
          }} />
        ))}
      </div>
      {checks.map(c => (
        <div key={c.label} style={{
          fontSize: 11,
          color: c.ok ? '#16a34a' : 'var(--text-tertiary, #94a3b8)',
          display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2,
        }}>
          <span>{c.ok ? '✓' : '○'}</span>
          {c.label}
        </div>
      ))}
    </div>
  );
}

/**
 * JS-Seite der Validierung (1:1 Mirror von _validate_password).
 * Returnt true wenn alle Regeln erfuellt sind.
 */
export function isPasswordStrong(password) {
  if (!password || password.length < 12) return false;
  if (!/[A-Z]/.test(password)) return false;
  if (!/[0-9]/.test(password)) return false;
  if (!/[^A-Za-z0-9]/.test(password)) return false;
  return true;
}
