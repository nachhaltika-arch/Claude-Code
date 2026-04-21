import { useState } from "react";

const API_BASE_URL = process.env.REACT_APP_API_URL || "";

export default function NewProjectModal({ onClose, onProjectCreated }) {
  const token = localStorage.getItem("kompagnon_token");
  const h = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };

  const [stufe, setStufe] = useState("search");
  const [suche, setSuche] = useState("");
  const [sucheErgebnisse, setSucheErgebnisse] = useState([]);
  const [sucheLoading, setSucheLoading] = useState(false);

  const [form, setForm] = useState({
    company_name: "",
    website_url: "",
    contact_name: "",
    email: "",
    trade: "",
  });
  const [saving, setSaving] = useState(false);
  const [fehler, setFehler] = useState("");

  const handleSuche = async (val) => {
    setSuche(val);
    if (val.length < 2) { setSucheErgebnisse([]); return; }
    setSucheLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/?search=${encodeURIComponent(val)}&limit=8`, { headers: h });
      const data = await res.json();
      const leads = Array.isArray(data) ? data : (data.items || []);
      setSucheErgebnisse(leads);
    } catch { setSucheErgebnisse([]); }
    finally { setSucheLoading(false); }
  };

  const handleLeadWaehlen = async (lead) => {
    if (!lead.website_url) {
      setFehler(`"${lead.company_name}" hat keine Domain hinterlegt. Bitte erst die Domain ergänzen oder ein neues Unternehmen anlegen.`);
      setStufe("create");
      setForm(f => ({ ...f, company_name: lead.company_name }));
      return;
    }
    setSaving(true);
    setFehler("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/from-lead/${lead.id}`, { method: "POST", headers: h });
      const data = await res.json();
      if (res.ok) {
        onProjectCreated(data);
        onClose();
      } else {
        setFehler(data?.detail?.message || data?.detail || "Fehler beim Anlegen des Projekts.");
      }
    } catch { setFehler("Verbindungsfehler. Bitte erneut versuchen."); }
    finally { setSaving(false); }
  };

  const handleNeuAnlegen = async () => {
    setFehler("");
    if (!form.company_name.trim()) { setFehler("Bitte Firmenname eingeben."); return; }
    if (!form.website_url.trim()) { setFehler("Bitte Website-Domain eingeben."); return; }
    setSaving(true);
    try {
      const leadRes = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: "POST", headers: h, body: JSON.stringify({ ...form, status: "new", legacy_type: "lead" }),
      });
      const lead = await leadRes.json();
      if (!leadRes.ok) { setFehler(lead?.detail || "Fehler beim Anlegen des Unternehmens."); return; }

      const projRes = await fetch(`${API_BASE_URL}/api/projects/from-lead/${lead.id}`, { method: "POST", headers: h });
      const proj = await projRes.json();
      if (projRes.ok) {
        onProjectCreated(proj);
        onClose();
      } else {
        setFehler(proj?.detail?.message || proj?.detail || "Projekt konnte nicht gestartet werden.");
      }
    } catch { setFehler("Verbindungsfehler. Bitte erneut versuchen."); }
    finally { setSaving(false); }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
    }}>
      <div style={{
        background: "#fff", borderRadius: 12, padding: 32, width: "100%", maxWidth: 520,
        boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
      }}>
        <h2 style={{ margin: "0 0 4px", fontSize: 20, color: "#004F59" }}>Neues Projekt starten</h2>
        <p style={{ margin: "0 0 24px", color: "#666", fontSize: 14 }}>
          Bitte wähle ein bestehendes Unternehmen oder lege ein neues an.
        </p>

        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          <button
            onClick={() => setStufe("search")}
            style={{
              flex: 1, padding: "8px 0", borderRadius: 8, border: "none", cursor: "pointer",
              background: stufe === "search" ? "#008EAA" : "#f0f0f0",
              color: stufe === "search" ? "#fff" : "#333", fontWeight: 600, fontSize: 14,
            }}
          >Bestehendes Unternehmen</button>
          <button
            onClick={() => setStufe("create")}
            style={{
              flex: 1, padding: "8px 0", borderRadius: 8, border: "none", cursor: "pointer",
              background: stufe === "create" ? "#008EAA" : "#f0f0f0",
              color: stufe === "create" ? "#fff" : "#333", fontWeight: 600, fontSize: 14,
            }}
          >Neues Unternehmen</button>
        </div>

        {stufe === "search" && (
          <div>
            <input
              type="text"
              placeholder="Firmenname suchen..."
              value={suche}
              onChange={e => handleSuche(e.target.value)}
              style={{ width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box" }}
            />
            {sucheLoading && <p style={{ color: "#888", fontSize: 13, margin: "8px 0 0" }}>Suche...</p>}
            {sucheErgebnisse.length > 0 && (
              <div style={{ marginTop: 8, border: "1px solid #eee", borderRadius: 8, overflow: "hidden" }}>
                {sucheErgebnisse.map(lead => (
                  <div
                    key={lead.id}
                    onClick={() => handleLeadWaehlen(lead)}
                    style={{
                      padding: "10px 14px", cursor: "pointer", borderBottom: "1px solid #f0f0f0",
                      display: "flex", justifyContent: "space-between", alignItems: "center",
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "#f5f5f5"}
                    onMouseLeave={e => e.currentTarget.style.background = "#fff"}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{lead.company_name}</div>
                      <div style={{ fontSize: 12, color: lead.website_url ? "#008EAA" : "#f59e0b" }}>
                        {lead.website_url || "Keine Domain hinterlegt"}
                      </div>
                    </div>
                    <span style={{ fontSize: 12, color: "#999" }}>&rarr;</span>
                  </div>
                ))}
              </div>
            )}
            {suche.length >= 2 && !sucheLoading && sucheErgebnisse.length === 0 && (
              <p style={{ color: "#888", fontSize: 13, margin: "8px 0 0" }}>
                Kein Unternehmen gefunden.{" "}
                <button onClick={() => setStufe("create")} style={{ color: "#008EAA", background: "none", border: "none", cursor: "pointer", padding: 0, textDecoration: "underline" }}>
                  Neu anlegen &rarr;
                </button>
              </p>
            )}
          </div>
        )}

        {stufe === "create" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { key: "company_name", label: "Firmenname *", placeholder: "z.B. Müller Haustechnik GmbH", type: "text" },
              { key: "website_url", label: "Website / Domain *", placeholder: "z.B. https://muellerhaustechnik.de", type: "text" },
              { key: "contact_name", label: "Ansprechpartner", placeholder: "z.B. Hans Müller", type: "text" },
              { key: "email", label: "E-Mail", placeholder: "z.B. info@muellerhaustechnik.de", type: "email" },
              { key: "trade", label: "Gewerk / Branche", placeholder: "z.B. Sanitär, Heizung, Klima", type: "text" },
            ].map(({ key, label, placeholder, type }) => (
              <div key={key}>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#444", marginBottom: 4 }}>{label}</label>
                <input
                  type={type}
                  placeholder={placeholder}
                  value={form[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  style={{ width: "100%", padding: "9px 14px", borderRadius: 8, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box" }}
                />
              </div>
            ))}
          </div>
        )}

        {fehler && (
          <div style={{ marginTop: 16, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 13 }}>
            {fehler}
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 24 }}>
          <button
            onClick={onClose}
            disabled={saving}
            style={{ padding: "9px 20px", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: "pointer", fontSize: 14 }}
          >Abbrechen</button>
          {stufe === "create" && (
            <button
              onClick={handleNeuAnlegen}
              disabled={saving}
              style={{
                padding: "9px 20px", borderRadius: 8, border: "none", cursor: "pointer",
                background: "#FAE600", color: "#000", fontWeight: 700, fontSize: 14,
              }}
            >{saving ? "Wird angelegt..." : "Unternehmen anlegen & Projekt starten"}</button>
          )}
        </div>
      </div>
    </div>
  );
}
