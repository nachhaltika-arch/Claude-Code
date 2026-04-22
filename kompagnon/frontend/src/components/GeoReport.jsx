/**
 * GeoReport — vereinfachte Ansicht fuer das Kundenportal.
 * Kunde sieht Score, Bedeutung und was gemacht wird — KEINE technischen Details.
 */

import { useState, useEffect } from 'react';
import API_BASE_URL from '../config';

const LEVEL_INFO = (score) => {
  if (score >= 75) return {
    emoji: '🏆', label: 'Sehr gut aufgestellt', color: '#27ae60', bg: '#ECFDF5',
    text: 'Ihre Website wird von KI-Systemen gut gefunden und kann zitiert werden.',
  };
  if (score >= 50) return {
    emoji: '⚡', label: 'Gut – Potenzial vorhanden', color: '#f39c12', bg: '#FFFBEB',
    text: 'Grundlagen sind da. Mit gezielten Verbesserungen werden Sie oefter von KI-Systemen genannt.',
  };
  return {
    emoji: '🔧', label: 'Verbesserungsbedarf', color: '#e74c3c', bg: '#FEF2F2',
    text: 'KI-Systeme koennen Ihren Betrieb noch nicht optimal finden. Wir optimieren das fuer Sie.',
  };
};

export default function GeoReport({ projectId, customerToken }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    const headers = customerToken
      ? { Authorization: `Bearer ${customerToken}` }
      : {};
    fetch(`${API_BASE_URL}/api/geo/${projectId}/result`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [projectId, customerToken]);

  if (loading) return <p style={{ textAlign: 'center', color: '#6B7280', padding: 24 }}>Wird geladen...</p>;
  if (!data || data.status !== 'done') return null;

  const score = data.geo_score_total || 0;
  const info = LEVEL_INFO(score);

  return (
    <div style={{ padding: 20, maxWidth: 600, margin: '0 auto' }}>
      <h3 style={{ color: '#004F59', marginBottom: 16 }}>🤖 KI-Sichtbarkeit Ihrer Website</h3>

      <div style={{ background: info.bg, border: `1px solid ${info.color}40`, borderRadius: 12, padding: 20, marginBottom: 16, textAlign: 'center' }}>
        <div style={{ fontSize: 40 }}>{info.emoji}</div>
        <div style={{ fontSize: 52, fontWeight: 900, color: info.color, lineHeight: 1.1 }}>{score}</div>
        <div style={{ fontSize: 14, color: info.color, fontWeight: 700, marginBottom: 8 }}>{info.label}</div>
        <p style={{ fontSize: 13, color: '#374151', margin: 0 }}>{info.text}</p>
      </div>

      <div style={{ fontSize: 13, color: '#6B7280', lineHeight: 1.7 }}>
        <strong style={{ color: '#374151' }}>Was wir fuer Sie analysieren:</strong>
        <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
          <li>Ob ChatGPT, Perplexity und Google AI Ihren Betrieb korrekt einordnen koennen</li>
          <li>Ob technische KI-Signale (llms.txt, strukturierte Daten) vorhanden sind</li>
          <li>Ob Ihre Inhalte fuer KI-Antworten geeignet sind</li>
        </ul>
      </div>

      {data.upsell_active && (
        <div style={{ marginTop: 16, background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 8, padding: '12px 16px' }}>
          <strong style={{ fontSize: 13, color: '#1E40AF' }}>✅ GEO-Monitoring aktiv</strong>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#1E40AF' }}>
            Wir pruefen monatlich automatisch Ihre KI-Sichtbarkeit und informieren Sie ueber Veraenderungen.
          </p>
        </div>
      )}
    </div>
  );
}
