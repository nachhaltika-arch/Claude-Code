// Rueckfrage vor dem Loeschen von Projekten.
//
// Sie zeigt zuerst, was verschwindet — und was NICHT verschwindet. An
// `projects` haengen fuenfzehn Tabellen; in `customers` stecken wiederkehrender
// Umsatz und CMS-Zugangsdaten. Ein „Wirklich loeschen?" ohne Zahlen laesst
// genau das aus, was man wissen muesste.
//
// Die Zahlen kommen vom Server (`GET /api/projects/loeschvorschau`), nicht aus
// einer Annahme im Frontend: Was wirklich am Projekt haengt, weiss nur die
// Datenbank.
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import API_BASE_URL from "../config";
import { loeschFrage, vorschauZeilen } from "../utils/projektAuswahl";

const ROT = "#dc2626";

export default function ProjekteLoeschenModal({ ids, namen, token, onClose, onGeloescht }) {
  const kopf = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  const [vorschau, setVorschau] = useState(null);
  const [laedt, setLaedt] = useState(true);
  const [loescht, setLoescht] = useState(false);
  const [fehler, setFehler] = useState("");

  useEffect(() => {
    let abgebrochen = false;
    (async () => {
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/projects/loeschvorschau?ids=${ids.join(",")}`,
          { headers: kopf },
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const daten = await res.json();
        if (!abgebrochen) setVorschau(daten);
      } catch (e) {
        // Ohne Vorschau wird nicht geloescht: Der Knopf bleibt gesperrt.
        if (!abgebrochen) setFehler("Die Vorschau konnte nicht geladen werden.");
      } finally {
        if (!abgebrochen) setLaedt(false);
      }
    })();
    return () => { abgebrochen = true; };
  }, [ids.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  const loeschen = async () => {
    setLoescht(true);
    setFehler("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/loeschen`, {
        method: "POST", headers: kopf, body: JSON.stringify({ ids }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const bericht = await res.json();
      onGeloescht(ids, bericht);
    } catch (e) {
      setFehler("Das Löschen ist fehlgeschlagen. Es wurde nichts entfernt.");
      setLoescht(false);
    }
  };

  const { geloescht, bleibt } = vorschauZeilen(vorschau);

  return createPortal(
    <div
      onClick={loescht ? undefined : onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000, padding: 16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#fff", borderRadius: 12, padding: 32, width: "100%", maxWidth: 520,
          boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
          maxHeight: "calc(100vh - 32px)", overflowY: "auto",
        }}
      >
        <h2 style={{ margin: "0 0 4px", fontSize: 20, color: ROT }}>{loeschFrage(namen)}</h2>
        <p style={{ margin: "0 0 20px", color: "#666", fontSize: 14 }}>
          Das lässt sich nicht rückgängig machen.
        </p>

        {laedt && <p style={{ color: "#888", fontSize: 13 }}>Wird geprüft…</p>}

        {!laedt && vorschau && (
          <>
            <Abschnitt
              titel="Wird mit gelöscht"
              farbe={ROT}
              zeilen={geloescht}
              leerText="Außer den Projekten selbst hängt nichts daran."
            />
            {bleibt.length > 0 && (
              <Abschnitt
                titel="Bleibt erhalten"
                farbe="#059669"
                zeilen={bleibt}
                hinweis="Der Nachweis, was wann an wen ging, verschwindet nicht mit dem Projekt."
              />
            )}
          </>
        )}

        {fehler && (
          <div style={{ marginTop: 16, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: ROT, fontSize: 13 }}>
            {fehler}
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 24 }}>
          <button
            onClick={onClose}
            disabled={loescht}
            style={{ padding: "9px 20px", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: loescht ? "default" : "pointer", fontSize: 14 }}
          >Abbrechen</button>
          <button
            onClick={loeschen}
            disabled={loescht || laedt || !vorschau}
            style={{
              padding: "9px 20px", borderRadius: 8, border: "none",
              cursor: (loescht || laedt || !vorschau) ? "default" : "pointer",
              background: ROT, opacity: (loescht || laedt || !vorschau) ? 0.5 : 1,
              color: "#fff", fontWeight: 700, fontSize: 14,
            }}
          >{loescht ? "Wird gelöscht…" : `Endgültig löschen`}</button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

function Abschnitt({ titel, farbe, zeilen, leerText, hinweis }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase", color: farbe, marginBottom: 6 }}>
        {titel}
      </div>
      {zeilen.length === 0 && leerText && (
        <div style={{ fontSize: 13, color: "#888" }}>{leerText}</div>
      )}
      {zeilen.map(({ tabelle, beschriftung, anzahl }) => (
        <div key={tabelle} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "3px 0", borderBottom: "1px solid #f3f3f3" }}>
          <span style={{ color: "#444" }}>{beschriftung}</span>
          <span style={{ color: "#666", fontVariantNumeric: "tabular-nums" }}>{anzahl}</span>
        </div>
      ))}
      {hinweis && zeilen.length > 0 && (
        <div style={{ fontSize: 12, color: "#888", marginTop: 6 }}>{hinweis}</div>
      )}
    </div>
  );
}
