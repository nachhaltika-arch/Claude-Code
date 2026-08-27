/**
 * GeoOptimizerStep — ProzessFlow-Schritt fuer GEO/GAIO Analyse & Optimierung
 *
 * Sitzt im ProzessFlow zwischen Website-Audit (2) und Vollanalyse (3).
 * Zeigt: Score-Uebersicht, Einzelwerte, Empfehlungen, generierte Dateien, Upsell-Badge.
 */

import { useState, useEffect, useCallback } from 'react';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import { datumKurz, monatUndJahr } from '../utils/datum';

const SCORE_COLOR = (score) => {
  if (score >= 75) return '#27ae60';
  if (score >= 50) return '#f39c12';
  return '#e74c3c';
};

const SCORE_LABEL = (score) => {
  if (score >= 75) return 'Gut';
  if (score >= 50) return 'Ausbaufaehig';
  return 'Handlungsbedarf';
};

const ScoreBar = ({ label, score }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
      <span>{label}</span>
      <span style={{ fontWeight: 600, color: SCORE_COLOR(score) }}>{score}/100</span>
    </div>
    <div style={{ height: 8, background: '#E5E7EB', borderRadius: 4, overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          width: `${Math.min(score, 100)}%`,
          background: SCORE_COLOR(score),
          borderRadius: 4,
          transition: 'width 0.6s ease',
        }}
      />
    </div>
  </div>
);

export default function GeoOptimizerStep({ projectId, isAdmin: isAdminProp, onComplete }) {
  const { token, hasRole } = useAuth();
  const isAdmin = isAdminProp ?? (typeof hasRole === 'function' ? hasRole('admin') : false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('analyse');
  const [files, setFiles] = useState(null);
  const [monitoring, setMonitoring] = useState(null);
  const [upsellLoading, setUpsellLoading] = useState(false);
  // ── Nennung in KI-Antworten (L-58 b) ──────────────────────────────
  // Der Endpunkt gibt es seit dem 17.08.2026 und hatte bis zum 25.08. keinen
  // einzigen Aufrufer. Der Kasten oben verspricht dem Nutzer, es werde
  // geprueft, ob die Seite "gefunden und zitiert" wird — geprueft wurde bis
  // dahin nur das Erste.
  const [nennung, setNennung] = useState(null);
  const [nennungLaeuft, setNennungLaeuft] = useState(false);
  const [nennungFehler, setNennungFehler] = useState('');
  const [verlauf, setVerlauf] = useState(null);
  const [wirkung, setWirkung] = useState(null);

  // ── Das laufende Abo (26.08.2026, L-105) ──────────────────────────
  // `POST /api/geo-payments/{id}/cancel` gibt es seit dem Bau des Add-ons
  // und wurde **von nirgendwo** aufgerufen. Der Kasten darunter schaltet nur,
  // ob das Add-on *angeboten* wird (`upsell_active`); das tatsaechliche
  // Stripe-Abo, das der Kunde im Portal mit einem Klick abschliesst, sah im
  // Innendienst niemand — und kuendigen konnte es niemand ausser per curl.
  const [abo, setAbo] = useState(null);
  const [aboLaeuft, setAboLaeuft] = useState(false);
  const [aboFrage, setAboFrage] = useState(false);
  const [aboFehler, setAboFehler] = useState('');

  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const loadResult = useCallback(async () => {
    if (!projectId) return;
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo/${projectId}/result`, { headers });
      if (resp.ok) {
        const data = await resp.json();
        setResult(data);
        if (data.status === 'done' && onComplete) onComplete(data.geo_score_total);
      }
    } catch (err) {
      console.error('GEO result load error:', err);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, token]);

  useEffect(() => {
    loadResult();
  }, [loadResult]);

  useEffect(() => {
    if (!result || !['pending', 'running'].includes(result.status)) return;
    const interval = setInterval(loadResult, 3000);
    return () => clearInterval(interval);
  }, [result?.status, loadResult]);

  const startAnalysis = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo/${projectId}/analyze`, {
        method: 'POST',
        headers,
      });
      if (resp.ok) {
        await loadResult();
      } else {
        const err = await resp.json();
        alert(err.detail || 'Fehler beim Starten der Analyse');
      }
    } catch (err) {
      alert('Verbindungsfehler');
    } finally {
      setLoading(false);
    }
  };

  const generateFiles = async () => {
    setGenerating(true);
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo/${projectId}/generate`, {
        method: 'POST',
        headers,
      });
      if (resp.ok) {
        const filesResp = await fetch(`${API_BASE_URL}/api/geo/${projectId}/files`, { headers });
        if (filesResp.ok) {
          const data = await filesResp.json();
          setFiles(data.files);
          setActiveTab('dateien');
        }
      } else {
        const err = await resp.json();
        alert(err.detail || 'Fehler beim Generieren');
      }
    } catch (err) {
      alert('Verbindungsfehler');
    } finally {
      setGenerating(false);
    }
  };

  // **Lesen kostet nichts, Messen kostet Geld.** Deshalb zwei Aufrufe: Der
  // Verlauf wird beim Oeffnen des Reiters geladen, der Lauf nur auf Klick.
  const ladeVerlauf = useCallback(async () => {
    if (!projectId) return;
    try {
      const resp = await fetch(
        `${API_BASE_URL}/api/geo/${projectId}/ki-sichtbarkeit/verlauf`, { headers });
      if (resp.ok) setVerlauf(await resp.json());
    } catch (err) {
      console.error('Verlauf der Nennungen nicht ladbar:', err);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, token]);

  // **Der Wirkungsbericht nach 60 Tagen (GEO-01, Position 7).** Er war seit
  // dem 25.08.2026 gebaut und hatte bis zum 27.08. **keinen Aufrufer** — der
  // vierte Fund derselben Art in dieser Datei-Familie. Er rechnet nur auf
  // vorhandenen Daten, kostet also nichts und darf beim Oeffnen des Reiters
  // geladen werden; die Nennungsmessung darunter kostet Geld und bleibt am
  // Knopf.
  const ladeWirkung = useCallback(async () => {
    if (!projectId) return;
    try {
      const resp = await fetch(
        `${API_BASE_URL}/api/geo/${projectId}/wirkungsbericht`, { headers });
      // 404 heisst „fuer dieses Projekt gibt es keine GEO-Analyse" — kein
      // Fehler, sondern eine Auskunft. Der Abschnitt bleibt dann einfach weg.
      if (resp.ok) setWirkung(await resp.json());
    } catch (err) {
      console.error('Wirkungsbericht nicht ladbar:', err);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, token]);

  const pruefeNennung = async () => {
    setNennungLaeuft(true);
    setNennungFehler('');
    try {
      const resp = await fetch(
        `${API_BASE_URL}/api/geo/${projectId}/ki-sichtbarkeit?max_fragen=3`,
        { method: 'POST', headers });
      const daten = await resp.json();
      if (resp.ok) {
        setNennung(daten);
        await ladeVerlauf();
      } else {
        // 503 heisst: kein Schluessel hinterlegt. Das ist keine Aussage ueber
        // den Betrieb, und der Text sagt das auch.
        setNennungFehler(daten.detail || 'Die Pruefung ist fehlgeschlagen.');
      }
    } catch (err) {
      setNennungFehler('Verbindungsfehler — die Pruefung wurde nicht durchgefuehrt.');
    } finally {
      setNennungLaeuft(false);
    }
  };

  const ladeAbo = useCallback(async () => {
    if (!projectId || !isAdmin) return;
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo-payments/${projectId}/status`, { headers });
      setAbo(resp.ok ? await resp.json() : null);
    } catch {
      // Kein Rueckfall auf „kein Abo": Das waere eine Aussage, und geladen
      // werden konnte nichts.
      setAbo(null);
    }
  }, [projectId, isAdmin]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { ladeAbo(); }, [ladeAbo]);

  const aboKuendigen = async () => {
    setAboLaeuft(true); setAboFehler('');
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo-payments/${projectId}/cancel`,
        { method: 'POST', headers });
      const daten = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(daten.detail || `Status ${resp.status}`);
      setAboFrage(false);
      await ladeAbo();
    } catch (e) {
      setAboFehler(`Die Kuendigung wurde nicht eingereicht (${e.message}).`);
    } finally {
      setAboLaeuft(false);
    }
  };

  const loadMonitoring = async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/api/geo/${projectId}/monitoring`, { headers });
      if (resp.ok) setMonitoring(await resp.json());
    } catch (err) {
      console.error('Monitoring load error:', err);
    }
  };

  const toggleUpsell = async (active, price) => {
    if (!isAdmin) return;
    setUpsellLoading(true);
    try {
      await fetch(`${API_BASE_URL}/api/geo/${projectId}/upsell`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ upsell_active: active, upsell_price: price }),
      });
      await loadResult();
    } catch (err) {
      alert('Fehler beim Speichern');
    } finally {
      setUpsellLoading(false);
    }
  };

  if (!result || result.status === 'not_started') {
    return (
      <div style={{ padding: 24, maxWidth: 680, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
          <h2 style={{ color: 'var(--brand-primary)', marginBottom: 8 }}>GEO/KI-Sichtbarkeit analysieren</h2>
          <p style={{ color: '#6B7280', maxWidth: 480, margin: '0 auto 24px' }}>
            Pruefe ob die Website von KI-Systemen wie ChatGPT, Perplexity oder Google AI
            korrekt gefunden und zitiert wird. Score, Empfehlungen und automatische
            Optimierungsdateien inklusive.
          </p>
          <button
            onClick={startAnalysis}
            disabled={loading}
            style={{
              background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none',
              padding: '12px 28px', borderRadius: 8, fontSize: 15, fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Wird gestartet...' : 'GEO-Analyse starten'}
          </button>
        </div>
      </div>
    );
  }

  if (['pending', 'running'].includes(result.status)) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>⏳</div>
        <h3 style={{ color: 'var(--brand-primary)' }}>GEO-Analyse laeuft...</h3>
        <p style={{ color: '#6B7280' }}>
          Wir pruefen llms.txt, robots.txt, strukturierte Daten und Inhalte (~30 Sekunden)
        </p>
        <div style={{ marginTop: 16, background: '#E5E7EB', borderRadius: 4, height: 8, overflow: 'hidden' }}>
          <div style={{ height: '100%', background: 'var(--kc-mid)', width: '60%', animation: 'pulse 1.5s infinite' }} />
        </div>
      </div>
    );
  }

  if (result.status === 'failed') {
    return (
      <div style={{ padding: 24 }}>
        <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: 16 }}>
          <strong>Analyse fehlgeschlagen</strong>
          <p style={{ margin: '8px 0 16px', color: '#991B1B', fontSize: 13 }}>
            {result.error_message || 'Unbekannter Fehler'}
          </p>
          <button onClick={startAnalysis} style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', padding: '8px 16px', borderRadius: 6, cursor: 'pointer' }}>
            Erneut versuchen
          </button>
        </div>
      </div>
    );
  }

  const score = result.geo_score_total || 0;
  const recs = result.recommendations || [];

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: '0 auto' }}>

      <div style={{
        background: 'linear-gradient(135deg, var(--brand-primary) 0%, var(--kc-mid) 100%)',
        borderRadius: 12, padding: '24px 28px', color: '#fff', marginBottom: 20,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 16,
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>🤖 GEO/KI-Sichtbarkeit</h2>
          <p style={{ margin: '4px 0 0', opacity: 0.8, fontSize: 13 }}>
            Wie gut findet ChatGPT &amp; Co. diesen Betrieb?
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, fontWeight: 900, lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: 13, opacity: 0.9 }}>{SCORE_LABEL(score)} · /100</div>
        </div>
      </div>

      {/* Das laufende Abo — Stand und Kuendigung (26.08.2026, L-105).
        * Getrennt vom Kasten darunter: Der schaltet, ob das Add-on
        * **angeboten** wird; hier steht, ob der Kunde es **gebucht** hat. */}
      {isAdmin && abo?.subscription_status && (
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 8, padding: '12px 16px', marginBottom: 12,
          display: 'flex', flexDirection: 'column', gap: 10,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <strong style={{ fontSize: 14 }}>Abo des Kunden</strong>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-tertiary)' }}>
                Status: {abo.subscription_status}
                {abo.subscription_status === 'cancel_at_period_end'
                  && ' — laeuft zum Periodenende aus'}
              </p>
            </div>
            {abo.subscription_status === 'active' && !aboFrage && (
              <button type="button" onClick={() => setAboFrage(true)}
                style={{ background: 'transparent', color: 'var(--status-danger-text, var(--status-error-text))', border: '1px solid currentColor', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontFamily: 'var(--font-sans)' }}>
                Abo kuendigen
              </button>
            )}
          </div>

          {aboFrage && (
            <div role="alertdialog" style={{ fontSize: 13, lineHeight: 1.55, padding: '10px 12px', borderRadius: 6, background: 'var(--status-warning-bg)', color: 'var(--status-warning-text)' }}>
              <div style={{ marginBottom: 8 }}>
                Das GEO-Abo dieses Kunden zum <strong>Periodenende</strong>
                {' '}kuendigen? Bis dahin laeuft es weiter; abgebucht wird nichts mehr danach.
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" disabled={aboLaeuft} onClick={aboKuendigen}
                  style={{ padding: '6px 14px', border: 'none', borderRadius: 6, background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontSize: 12, fontWeight: 700, cursor: aboLaeuft ? 'default' : 'pointer', opacity: aboLaeuft ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}>
                  {aboLaeuft ? 'Wird eingereicht …' : 'Ja, kuendigen'}
                </button>
                <button type="button" onClick={() => setAboFrage(false)}
                  style={{ padding: '6px 14px', border: '1px solid currentColor', borderRadius: 6, background: 'transparent', color: 'inherit', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Abbrechen
                </button>
              </div>
            </div>
          )}

          {aboFehler && (
            <div role="alert" style={{ fontSize: 12, padding: '8px 12px', borderRadius: 6, background: 'var(--status-error-bg)', color: 'var(--status-error-text)' }}>
              {aboFehler}
            </div>
          )}
        </div>
      )}

      {isAdmin && (
        <div style={{
          background: result.upsell_active ? '#ECFDF5' : '#F9FAFB',
          border: `1px solid ${result.upsell_active ? '#6EE7B7' : '#E5E7EB'}`,
          borderRadius: 8, padding: '12px 16px', marginBottom: 16,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          gap: 12, flexWrap: 'wrap',
        }}>
          <div>
            <strong style={{ fontSize: 14 }}>
              {result.upsell_active ? '✅ GEO Add-on aktiv' : '💼 GEO Add-on (Upsell)'}
            </strong>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#6B7280' }}>
              {result.upsell_active
                ? `Als Zusatzprodukt fuer EUR ${result.upsell_price || '–'}/Monat gebucht`
                : 'Monatliches GEO-Monitoring als separates Produkt anbieten'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {!result.upsell_active && (
              <button
                onClick={() => {
                  const price = prompt('Monatspreis in EUR (z.B. 49):', '49');
                  if (price) toggleUpsell(true, parseFloat(price));
                }}
                disabled={upsellLoading}
                style={{ background: 'var(--kc-yellow)', color: '#000', border: 'none', padding: '6px 14px', borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: 13 }}
              >
                Als Upsell aktivieren
              </button>
            )}
            {result.upsell_active && (
              <button
                onClick={() => toggleUpsell(false, null)}
                disabled={upsellLoading}
                style={{ background: '#F3F4F6', color: '#374151', border: '1px solid #D1D5DB', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}
              >
                Deaktivieren
              </button>
            )}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 4, marginBottom: 16, borderBottom: '2px solid #E5E7EB' }}>
        {[
          { id: 'analyse', label: '📊 Analyse' },
          { id: 'empfehlungen', label: `🔧 Empfehlungen (${recs.length})` },
          { id: 'dateien', label: '📁 Dateien' },
          { id: 'nennung', label: '💬 Nennung' },
          { id: 'monitoring', label: '📈 Verlauf' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              if (tab.id === 'monitoring' && !monitoring) loadMonitoring();
              if (tab.id === 'monitoring' && !wirkung) ladeWirkung();
              if (tab.id === 'nennung' && !verlauf) ladeVerlauf();
            }}
            style={{
              background: 'none', border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--kc-mid)' : '2px solid transparent',
              padding: '8px 14px', cursor: 'pointer', fontSize: 13,
              fontWeight: activeTab === tab.id ? 700 : 400,
              color: activeTab === tab.id ? 'var(--kc-mid)' : '#6B7280',
              marginBottom: -2,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'analyse' && (
        <div>
          <ScoreBar label="llms.txt (KI-Visitenkarte)" score={result.llms_txt_score || 0} />
          <ScoreBar label="robots.txt (KI-Bots erlaubt)" score={result.robots_ai_score || 0} />
          <ScoreBar label="Strukturierte Daten (schema.org)" score={result.structured_data_score || 0} />
          <ScoreBar label="Inhaltstiefe & Fachbegriffe" score={result.content_depth_score || 0} />
          <ScoreBar label="Lokale Signale" score={result.local_signal_score || 0} />

          <button
            onClick={startAnalysis}
            disabled={loading}
            style={{ marginTop: 16, background: '#F3F4F6', border: '1px solid #D1D5DB', padding: '8px 16px', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}
          >
            🔄 Erneut analysieren
          </button>
        </div>
      )}

      {activeTab === 'empfehlungen' && (
        <div>
          {recs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 32, color: '#6B7280' }}>
              ✅ Keine kritischen Empfehlungen — gute GEO-Basis!
            </div>
          ) : (
            recs.map((rec, i) => (
              <div key={i} style={{
                background: rec.prioritaet === 'hoch' || rec.priorität === 'hoch' ? '#FFF7ED' : '#F9FAFB',
                border: `1px solid ${rec.prioritaet === 'hoch' || rec.priorität === 'hoch' ? '#FED7AA' : '#E5E7EB'}`,
                borderRadius: 8, padding: '14px 16px', marginBottom: 10,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <strong style={{ fontSize: 14 }}>{rec.titel}</strong>
                  <span style={{
                    fontSize: 11, fontWeight: 700,
                    background: rec.prioritaet === 'hoch' || rec.priorität === 'hoch' ? '#FED7AA' : '#D1D5DB',
                    color: rec.prioritaet === 'hoch' || rec.priorität === 'hoch' ? '#92400E' : '#374151',
                    padding: '2px 8px', borderRadius: 20,
                  }}>
                    {(rec.prioritaet || rec.priorität || '').toUpperCase()}
                  </span>
                </div>
                <p style={{ margin: '4px 0 8px', fontSize: 13, color: '#374151' }}>{rec.beschreibung}</p>
                {rec.aufwand && (
                  <span style={{ fontSize: 12, color: '#6B7280' }}>⏱️ Aufwand: {rec.aufwand}</span>
                )}
              </div>
            ))
          )}

          {result.status === 'done' && (
            <div style={{ marginTop: 20, padding: 16, background: '#EFF6FF', borderRadius: 8, border: '1px solid #BFDBFE' }}>
              <strong style={{ fontSize: 14 }}>🚀 Automatisch optimieren</strong>
              <p style={{ margin: '6px 0 12px', fontSize: 13, color: '#1E40AF' }}>
                KOMPAGNON erstellt alle noetigen Dateien automatisch:
                llms.txt, schema.org Code, Ground Page und robots.txt-Empfehlung.
              </p>
              <button
                onClick={generateFiles}
                disabled={generating}
                style={{
                  background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none',
                  padding: '10px 20px', borderRadius: 6, fontWeight: 700,
                  cursor: generating ? 'not-allowed' : 'pointer', opacity: generating ? 0.7 : 1, fontSize: 14,
                }}
              >
                {generating ? 'Wird generiert...' : '✨ Dateien automatisch generieren'}
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'dateien' && (
        <div>
          {!files ? (
            <div style={{ textAlign: 'center', padding: 32 }}>
              <p style={{ color: '#6B7280', marginBottom: 16 }}>
                Noch keine Dateien generiert. Starte die automatische Optimierung.
              </p>
              <button
                onClick={generateFiles}
                disabled={generating || result.status !== 'done'}
                style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', padding: '10px 20px', borderRadius: 6, fontWeight: 700, cursor: 'pointer', fontSize: 14 }}
              >
                {generating ? 'Generiert...' : '✨ Jetzt generieren'}
              </button>
            </div>
          ) : (
            Object.entries(files).map(([key, content]) => {
              const labels = {
                llms_txt: '📄 llms.txt — KI-Visitenkarte',
                schema_org_script: '🔖 schema.org — Strukturierte Daten (HTML)',
                ground_page_html: '🌐 Ground Page — KI-Infoseite (HTML)',
                robots_patch: '🤖 robots.txt — Empfehlungen',
              };
              return (
                <div key={key} style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <strong style={{ fontSize: 14 }}>{labels[key] || key}</strong>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(content);
                        alert(`${key} in Zwischenablage kopiert!`);
                      }}
                      style={{ background: '#F3F4F6', border: '1px solid #D1D5DB', padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontSize: 12 }}
                    >
                      📋 Kopieren
                    </button>
                  </div>
                  <pre style={{
                    background: '#1F2937', color: '#F9FAFB', padding: 14,
                    borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: 200,
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>
                    {content?.substring(0, 1000)}{content?.length > 1000 ? '\n\n... [gekuerzt]' : ''}
                  </pre>
                </div>
              );
            })
          )}
        </div>
      )}

      {activeTab === 'nennung' && (
        <div>
          <div style={{
            background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 8,
            padding: '14px 16px', marginBottom: 16, fontSize: 13, color: '#374151',
          }}>
            <strong>Zwei verschiedene Fragen.</strong> Die Analyse nebenan misst, ob eine
            Maschine den Betrieb <em>lesen</em> kann. Hier wird gefragt, ob sie ihn auch
            <em> nennt</em> — mit denselben Fragen, die ein Kunde stellt.
            {' '}Jeder Lauf kostet Geld und fliesst deshalb in keinen Score ein.
          </div>

          <button
            onClick={pruefeNennung}
            disabled={nennungLaeuft}
            style={{
              background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
              border: 'none', padding: '10px 20px', borderRadius: 8, fontSize: 14,
              fontWeight: 600, cursor: nennungLaeuft ? 'not-allowed' : 'pointer',
              opacity: nennungLaeuft ? 0.7 : 1, marginBottom: 16,
            }}
          >
            {nennungLaeuft ? 'Wird gefragt … (bis zu einer Minute)' : 'Nennung jetzt pruefen'}
          </button>

          {nennungFehler && (
            <div style={{
              background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 8,
              padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#78350F',
            }}>
              <strong>Nicht gemessen.</strong> {nennungFehler}
              <div style={{ marginTop: 6 }}>
                Das ist <strong>keine</strong> Aussage ueber den Betrieb — es wurde nicht gefragt.
              </div>
            </div>
          )}

          {nennung && (
            <div style={{ display: 'grid', gap: 10, marginBottom: 20 }}>
              {Object.entries(nennung.anbieter || {}).map(([schluessel, block]) => (
                <div key={schluessel} style={{
                  border: '1px solid #E5E7EB', borderRadius: 8, padding: '12px 16px',
                  background: block.collected ? '#fff' : '#F9FAFB',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between',
                                alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
                    <strong style={{ fontSize: 14 }}>{block.anzeige || schluessel}</strong>
                    {block.collected ? (
                      <span style={{ fontSize: 14, fontWeight: 700,
                                     color: SCORE_COLOR((block.quote || 0) * 100) }}>
                        {block.genannt_bei} von {block.beantwortet} Fragen
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: '#6B7280' }}>nicht erhoben</span>
                    )}
                  </div>
                  {block.collected ? (
                    <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
                      Modell {block.modell}
                      {block.fehler > 0 && ` · ${block.fehler} Frage(n) ohne Antwort`}
                    </div>
                  ) : (
                    <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
                      {block.grund}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {verlauf?.verlauf?.length > 0 && (
            <div>
              <h4 style={{ fontSize: 14, margin: '0 0 8px' }}>Verlauf</h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13,
                                fontVariantNumeric: 'tabular-nums' }}>
                  <thead>
                    <tr style={{ textAlign: 'left', color: '#6B7280' }}>
                      <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Lauf</th>
                      <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Genannt bei</th>
                      <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Nicht erhoben</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...verlauf.verlauf].reverse().map((eintrag, i) => (
                      <tr key={eintrag.am || i}>
                        <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6' }}>
                          {datumKurz(eintrag.am)}
                        </td>
                        <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6' }}>
                          {Object.entries(eintrag.anbieter || {})
                            .map(([k, w]) => `${k}: ${w.genannt_bei}/${w.von}`)
                            .join(' · ') || '—'}
                        </td>
                        <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6',
                                     color: '#6B7280' }}>
                          {(eintrag.nicht_erhoben || []).join(', ') || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div>
          {/* **Der Wirkungsbericht nach 60 Tagen.** Er steht ueber dem
              Monatsverlauf, weil er die Frage beantwortet, die der Kunde
              stellt — „hat es etwas gebracht" —, waehrend der Verlauf
              darunter die Rohdaten zeigt.

              Ist er noch nicht faellig, steht **der Grund** da und nicht
              nichts: Eine leere Stelle liest sich wie ein Fehler, und wer
              den Bericht sucht, sucht dann im Werkzeug statt im Kalender. */}
          {wirkung && (
            <div style={{ border: '1px solid #E5E7EB', borderRadius: 8,
                          padding: 14, marginBottom: 16,
                          background: wirkung.faellig ? 'var(--bg-surface)' : 'transparent' }}>
              <h4 style={{ fontSize: 14, margin: '0 0 8px' }}>
                Wirkungsbericht (60 Tage)
              </h4>

              {!wirkung.faellig ? (
                <p style={{ color: '#6B7280', fontSize: 13, margin: 0, lineHeight: 1.6 }}>
                  {wirkung.grund}.
                </p>
              ) : (
                <>
                  {wirkung.klartext && (
                    <p style={{ fontSize: 13, margin: '0 0 10px', lineHeight: 1.7 }}>
                      {wirkung.klartext}
                    </p>
                  )}
                  <div style={{ display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                                gap: 10 }}>
                    {/* Zwei Groessen, zwei Kaesten — bewusst nicht zu einer Zahl
                        verrechnet. Den GEO-Wert stellen wir her; ob ein
                        Assistent den Betrieb nennt, entscheidet dessen
                        Anbieter. Eine gemeinsame Zahl verkaufte eine Wirkung,
                        die niemand zusichern kann. */}
                    {[
                      { titel: 'GEO-Wert', daten: wirkung.geo_wert,
                        grund: wirkung.geo_wert_grund,
                        fuss: 'unser Werk' },
                      { titel: 'Nennungen', daten: wirkung.nennungen,
                        grund: wirkung.nennungen_grund,
                        fuss: 'entscheiden die Anbieter' },
                    ].map(({ titel, daten, grund, fuss }) => (
                      <div key={titel} style={{ border: '1px solid #F3F4F6',
                                                borderRadius: 6, padding: '10px 12px' }}>
                        <div style={{ fontSize: 11, textTransform: 'uppercase',
                                      letterSpacing: '.07em', color: '#6B7280',
                                      fontWeight: 700 }}>{titel}</div>
                        {daten ? (
                          <div style={{ marginTop: 6, fontVariantNumeric: 'tabular-nums' }}>
                            <span style={{ fontSize: 20, fontWeight: 800 }}>
                              {daten.vorher} → {daten.heute}
                            </span>
                            <span style={{ fontSize: 13, marginLeft: 8,
                                           color: daten.veraenderung > 0 ? 'var(--status-success-text)'
                                                : daten.veraenderung < 0 ? 'var(--status-danger-text)'
                                                : '#6B7280' }}>
                              {daten.veraenderung > 0 ? '+' : ''}{daten.veraenderung}
                            </span>
                          </div>
                        ) : (
                          <p style={{ fontSize: 12, color: '#6B7280', margin: '6px 0 0',
                                      lineHeight: 1.6 }}>
                            {grund || 'Noch keine Vergleichsdaten.'}
                          </p>
                        )}
                        <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 6 }}>{fuss}</div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {!monitoring ? (
            <p style={{ color: '#6B7280', textAlign: 'center', padding: 24 }}>Wird geladen...</p>
          ) : monitoring.history.length === 0 ? (
            <p style={{ color: '#6B7280', textAlign: 'center', padding: 24 }}>
              Noch keine Monitoring-Daten — der erste Report erscheint am 1. des naechsten Monats.
            </p>
          ) : (
            <div>
              <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 12 }}>
                Monatliche GEO-Score Entwicklung (letzter Check: {datumKurz(monitoring.last_monitored_at, 'Nie')})
              </p>
              {monitoring.history.slice().reverse().map((entry, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #F3F4F6' }}>
                  <span style={{ fontSize: 13, color: '#374151' }}>
                    {monatUndJahr(entry.date)}
                  </span>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <span style={{ fontSize: 15, fontWeight: 700, color: SCORE_COLOR(entry.score) }}>{entry.score}/100</span>
                    {entry.change !== 0 && (
                      <span style={{ fontSize: 12, color: entry.change > 0 ? '#27ae60' : '#e74c3c' }}>
                        {entry.change > 0 ? `+${entry.change}` : entry.change}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
