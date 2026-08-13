/**
 * Der Block-Vertrag, sichtbar gemacht.
 *
 * Das Backend (`services/block_contract.py`) prueft jeden Block und liefert
 * seinen Befund als `contract: { konform, verstoesse: [{ regel, text }] }` mit.
 * Ohne diese Anzeige faellt ein Block wortlos auf „Entwurf" zurueck und
 * verschwindet aus dem Wireframe-Editor — das sieht aus wie ein Fehler, ist
 * aber eine Entscheidung mit Begruendung. Hier steht die Begruendung.
 */
import React from 'react';

// Kurztitel je Regel. Der Backend-Text sagt, was zu tun ist; die Ueberschrift
// sagt, worum es geht.
const REGEL_TITEL = {
  R0: 'Leerer Block',
  R1: 'Fremde Ressource',
  R2: 'Wurzel und Markierung',
  R3: 'Slots',
  R4: 'Bedienbarkeit im Editor',
};

export function istEntwurf(item) {
  return (item?.status || 'approved') === 'draft';
}

/** Zaehlt die Verstoesse — auch wenn gar kein Befund mitgeliefert wurde. */
export function anzahlVerstoesse(contract) {
  return (contract?.verstoesse || []).length;
}

export function StatusBadge({ status, style }) {
  const entwurf = status === 'draft';
  return (
    <span style={{
      fontSize: 9,
      fontWeight: 700,
      padding: '2px 6px',
      borderRadius: 3,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      whiteSpace: 'nowrap',
      background: entwurf ? '#FEF3C7' : '#dcfce7',
      color: entwurf ? '#92400e' : '#166534',
      ...style,
    }}>
      {entwurf ? 'Entwurf' : 'Freigegeben'}
    </span>
  );
}

/**
 * Der Befund im Klartext — plus der Freigabe-Knopf, wenn nichts mehr offen ist.
 * `onApprove` weglassen heisst: nur anzeigen, nicht freigeben (z.B. im
 * KI-Ergebnis, das noch gar nicht in der Bibliothek liegt).
 */
export function ContractPanel({
  contract, status, onApprove, approving = false, stale = false, hinweis,
}) {
  if (!contract) return null;

  const verstoesse = contract.verstoesse || [];
  const konform = !!contract.konform && verstoesse.length === 0;
  const entwurf = status === 'draft';

  // Freigegeben und sauber: kein Kasten. Wer nichts zu klaeren hat, braucht
  // keinen Hinweis.
  if (konform && !entwurf) return null;

  return (
    <div style={{
      border: `1px solid ${konform ? '#86efac' : '#fca5a5'}`,
      background: konform ? '#f0fdf4' : '#fef2f2',
      borderRadius: 8,
      padding: 12,
      marginBottom: 12,
    }}>
      <div style={{
        fontSize: 11, fontWeight: 800, textTransform: 'uppercase',
        letterSpacing: '0.05em', marginBottom: 6,
        color: konform ? '#166534' : '#991b1b',
      }}>
        {konform
          ? '✓ Vertrag erfuellt — Freigabe moeglich'
          : `Vertrag verletzt — ${verstoesse.length} ${verstoesse.length === 1 ? 'Punkt' : 'Punkte'} offen`}
      </div>

      {!konform && (
        <ul style={{ margin: '0 0 8px', paddingLeft: 18, color: '#7f1d1d', fontSize: 12 }}>
          {verstoesse.map((v, i) => (
            <li key={`${v.regel}-${i}`} style={{ marginBottom: 4 }}>
              <strong style={{ fontWeight: 700 }}>
                {v.regel} · {REGEL_TITEL[v.regel] || 'Vertrag'}
              </strong>
              <div>{v.text}</div>
            </li>
          ))}
        </ul>
      )}

      <div style={{ fontSize: 11, color: konform ? '#15803d' : '#991b1b' }}>
        {hinweis || (entwurf
          ? 'Als Entwurf gespeichert. Entwuerfe erscheinen nicht im Wireframe-Editor '
            + 'und landen auf keiner Kundenseite.'
          : 'Der Block ist freigegeben, verletzt aber den Vertrag — die naechste '
            + 'Bearbeitung setzt ihn auf Entwurf zurueck.')}
      </div>

      {stale && (
        <div style={{ fontSize: 11, color: '#92400e', marginTop: 6 }}>
          Der Befund gilt fuer den zuletzt geprueften Stand. Nach dem Speichern wird neu geprueft.
        </div>
      )}

      {onApprove && entwurf && (
        <button
          type="button"
          onClick={onApprove}
          disabled={!konform || approving || stale}
          title={stale ? 'Erst speichern — die Freigabe prueft den gespeicherten Stand'
            : (konform ? 'Block fuer den Wireframe-Editor freigeben'
              : 'Erst die offenen Punkte beheben — die Freigabe wird sonst abgelehnt')}
          style={{
            marginTop: 10, padding: '7px 14px',
            background: konform && !approving && !stale ? '#10b981' : '#94a3b8',
            color: '#fff', border: 'none', borderRadius: 6,
            fontSize: 11, fontWeight: 700, fontFamily: 'inherit',
            textTransform: 'uppercase', letterSpacing: '0.04em',
            cursor: konform && !approving && !stale ? 'pointer' : 'not-allowed',
          }}
        >
          {approving ? 'Gibt frei…' : '✓ Freigeben'}
        </button>
      )}
    </div>
  );
}
