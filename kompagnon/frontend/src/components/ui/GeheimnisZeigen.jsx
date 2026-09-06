import { useEffect, useRef, useState } from 'react';

/**
 * Ein einmal sichtbares Geheimnis — zum Kopieren, nicht zum Abschreiben.
 *
 * **Der Anlass (Wunsch David, 06.09.2026).** Das temporäre Passwort stand in
 * einem `alert()`. Daraus kopiert man es mit Mühe: Der Dialog lässt sich je
 * nach Browser nicht markieren, manche blocken ihn ganz, und wer versehentlich
 * „OK" drückt, hat es verloren — zurückholen kann man es nicht, denn gespeichert
 * wird nur der Hash.
 *
 * **Deshalb bleibt es stehen, bis jemand es wegklickt.** Kein Zeitablauf: Ein
 * Feld, das nach zehn Sekunden verschwindet, zwingt zur Eile bei genau der
 * Handlung, bei der Eile schadet.
 *
 * **Zwei Wege zum Kopieren, weil einer ausfallen kann.** `navigator.clipboard`
 * gibt es nur über HTTPS und nicht in jedem Browser; das Feld daneben ist
 * markierbar und wird beim Klick von selbst ausgewählt. Ein Knopf, der still
 * nichts tut, wäre schlimmer als keiner.
 */
export default function GeheimnisZeigen({ titel, wert, hinweis, onSchliessen }) {
  const [kopiert, setKopiert] = useState(false);
  const feld = useRef(null);

  useEffect(() => { setKopiert(false); }, [wert]);

  if (!wert) return null;

  const kopieren = async () => {
    try {
      await navigator.clipboard.writeText(wert);
      setKopiert(true);
    } catch {
      /* Kein Zugriff auf die Zwischenablage — dann wenigstens markieren,
         damit Strg+C greift. */
      feld.current?.select();
      setKopiert(false);
    }
  };

  return (
    <div style={S.rahmen} role="status">
      <div style={S.kopf}>
        <span style={S.titel}>{titel}</span>
        <button style={S.zu} onClick={onSchliessen} aria-label="Schließen">×</button>
      </div>

      <div style={S.zeile}>
        <input ref={feld} style={S.feld} value={wert} readOnly
               onFocus={(e) => e.target.select()}
               onClick={(e) => e.target.select()}
               aria-label={titel} />
        <button style={S.knopf} onClick={kopieren}>
          {kopiert ? 'Kopiert' : 'Kopieren'}
        </button>
      </div>

      {/* **Der Satz gehört dazu.** Wer nicht weiß, dass es nur einmal zu
          sehen ist, klickt weg und muss neu zurücksetzen — beim Kunden
          bedeutet das einen zweiten Anruf. */}
      <p style={S.hinweis}>
        {hinweis || 'Wird nur dieses eine Mal angezeigt. Gespeichert ist nur '
          + 'der Hash — nach dem Schließen lässt es sich nicht wiederholen, '
          + 'nur neu setzen.'}
      </p>
    </div>
  );
}

const S = {
  rahmen: { background: 'var(--bg-app)', border: '1px solid var(--brand-primary)', borderRadius: 8, padding: '16px 18px', marginBottom: 16 },
  kopf: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 },
  titel: { fontSize: 13, fontWeight: 900, textTransform: 'uppercase', letterSpacing: '.05em', color: 'var(--text-secondary)' },
  zu: { background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: 'var(--text-tertiary)', cursor: 'pointer', padding: '0 4px' },
  zeile: { display: 'flex', gap: 10, flexWrap: 'wrap' },
  feld: { flex: '1 1 240px', padding: '11px 13px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 15, fontFamily: 'var(--font-mono, monospace)' },
  knopf: { flex: 'none', fontWeight: 700, fontSize: 14, padding: '11px 20px', borderRadius: 6, border: 'none', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', cursor: 'pointer' },
  hinweis: { fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.55, margin: '10px 0 0', maxWidth: '64ch' },
};
