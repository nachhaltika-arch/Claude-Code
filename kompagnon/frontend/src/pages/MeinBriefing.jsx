/**
 * Der Kunde füllt sein Briefing selbst aus — und lädt hoch, was dazugehört.
 *
 * **Der Auftrag (26.08.2026, David).**
 *
 * **Kein zweiter Assistent.** `BriefingWizard` ist gebaut, sechs Schritte,
 * mit Entwurfsspeicherung und Feldprüfung. Er ruft genau vier Adressen auf,
 * und die tragen seit heute einen Kundenweg. Der Wizard merkt nicht, wer ihn
 * bedient — nur die KI-Vorschlagsknöpfe sind aus (`ohneVorschlaege`), weil
 * jeder Klick ein Modellaufruf ist und das eine Preisfrage bleibt.
 *
 * **Warum die Dateien auf derselben Seite stehen:** Der Assistent fragt nach
 * Logo, Fotos und Vorbildern. Wer dabei die Seite wechseln muss, verliert den
 * Faden — und der Entwurf steht ohnehin lokal, es geht nichts verloren.
 */
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import SeitenTitel from '../components/ui/SeitenTitel';
import BriefingWizard from '../components/BriefingWizard';
import MeineDateien from '../components/kunde/MeineDateien';

export default function MeinBriefing() {
  const { token, user } = useAuth();
  const leadId = user?.lead_id;

  const [betrieb, setBetrieb] = useState(null);
  const [fehler, setFehler] = useState('');
  const [fertig, setFertig] = useState(false);
  const [pdfLaeuft, setPdfLaeuft] = useState(false);

  /**
   * Das Briefing als Dokument holen.
   *
   * Der Weg dahin (`GET /api/briefings/mein/{lead_id}/pdf`) entstand am
   * selben Tag wie diese Seite \u2014 und blieb ohne Knopf. Genau die Klasse,
   * aus der an diesem Tag vier Produktionsfehler kamen; diesmal war es meine
   * eigene Zeile. Der Abruf braucht die Kopfzeile mit dem Zugangstoken,
   * deshalb kein schlichter Link: Der Browser sendet sie nicht mit.
   */
  const pdfLaden = async () => {
    setPdfLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/briefings/mein/${leadId}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      const daten = await antwort.blob();
      const adresse = URL.createObjectURL(daten);
      const verweis = document.createElement('a');
      verweis.href = adresse;
      verweis.download = `Briefing-${leadId}.pdf`;
      document.body.appendChild(verweis);
      verweis.click();
      document.body.removeChild(verweis);
      URL.revokeObjectURL(adresse);
    } catch (e) {
      setFehler(`Das PDF konnte nicht erstellt werden (${e.message}). `
        + 'Bitte tragen Sie zuerst etwas ein und speichern Sie den Entwurf.');
    } finally {
      setPdfLaeuft(false);
    }
  };

  useEffect(() => {
    if (!leadId) return;
    const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
    fetch(`${API_BASE_URL}/api/leads/${leadId}`, { headers: kopf })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Status ${r.status}`))))
      .then(setBetrieb)
      .catch((e) => setFehler(`Ihr Betrieb konnte nicht geladen werden (${e.message}).`));
  }, [leadId, token]);

  if (!leadId) {
    return (
      <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
        <SeitenTitel>Mein Briefing</SeitenTitel>
        Ihr Konto ist noch keinem Betrieb zugeordnet. Bitte wenden Sie sich an
        Ihren Betreuer.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <SeitenTitel>Mein Briefing</SeitenTitel>

      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--text-tertiary)', maxWidth: '68ch' }}>
        Hier tragen Sie ein, was nur Sie wissen: Ihre Leistungen, Ihre Kunden,
        was Sie von anderen unterscheidet. Sie können jederzeit unterbrechen —
        Ihre Eingaben bleiben stehen.
      </p>

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, padding: '10px 14px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>{fehler}</div>
      )}

      {fertig && (
        <div style={{
          fontSize: 13, padding: '12px 16px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-success-bg)', color: 'var(--status-success-text)',
          lineHeight: 1.55,
        }}>
          Danke — Ihr Briefing ist bei uns. Ihr Betreuer meldet sich; über
          „Meine Daten" können Sie ihm jederzeit schreiben.
        </div>
      )}

      {/* `embedded` haelt den Assistenten in der Seite statt in einem
        * Ueberlagerungsfenster — ein Kunde hat keinen zweiten Bildschirm
        * daneben, von dem aus er ihn geoeffnet haette. */}
      <BriefingWizard
        leadId={Number(leadId)}
        leadData={betrieb}
        embedded
        ohneVorschlaege
        kundenweg
        onClose={() => {}}
        onComplete={() => setFertig(true)}
      />

      <MeineDateien leadId={Number(leadId)} token={token} />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
        <button type="button" onClick={pdfLaden} disabled={pdfLaeuft} style={{
          padding: '9px 16px', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)',
          color: 'var(--text-primary)', fontSize: 12, fontWeight: 600,
          fontFamily: 'var(--font-sans)', cursor: pdfLaeuft ? 'default' : 'pointer',
          opacity: pdfLaeuft ? 0.6 : 1,
        }}>
          {pdfLaeuft ? 'Wird erstellt \u2026' : 'Briefing als PDF laden'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          Was Sie eingetragen haben, als Dokument \u2014 zum Ablegen oder Weitergeben.
        </span>
      </div>
    </div>
  );
}
