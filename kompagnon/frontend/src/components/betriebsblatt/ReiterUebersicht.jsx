/**
 * Der Reiter „Uebersicht" des Betriebsblatts (L-25).
 *
 * Am 2026-08-30 aus `LeadProfile.jsx` herausgeloest — 467 der damals 2.747
 * Zeilen, der groesste der vierzehn Reiter. Er stand dort als JSX-Ausdruck
 * mitten in der Rueckgabe; die Bedingung `activeTab === "overview"` bleibt am
 * Aufrufort, damit dort sichtbar bleibt, wann er erscheint.
 */
import { DomainBadge, scoreColor } from './blattBausteine';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import {
  herkunftLabel, herkunftVariant, leadSourceLabel, rechtsgrundlageLabel,
} from '../../utils/leadStatus';
import { datumKurz } from '../../utils/datum';
import { befundZeilen, geprueftAmText } from '../../utils/anreicherung';
import { aufTaste } from '../../utils/tastaturBedienung';
import Zeiterfassung from '../betrieb/Zeiterfassung';

export default function ReiterUebersicht({
  isMobile,
  leadId,
  token,
  addDomain,
  checkDomain,
  createScreenshot,
  deleteDomain,
  domainAdding,
  domainForm,
  domainFormOffen,
  domainLoading,
  domains,
  fieldRow,
  isDesktop,
  isTablet,
  latestAudit,
  levelColor,
  loadQrCode,
  loading,
  navigate,
  profile,
  projectData,
  projectId,
  qrData,
  qrLoading,
  screenshotLoading,
  setActiveTab,
  setDomainForm,
  setDomainFormOffen,
  setEditMode,
  setOpenAudit,
}) {
  // **Dieselbe Zerlegung wie in `LeadProfile`.** `lead`, Punktzahl, Stufe und
  // Verlauf kommen aus `profile`; sie einzeln durchzureichen hiesse, dieselbe
  // Zerlegung an zwei Stellen zu pflegen.
  const { lead, current_score, current_level, score_history = [] } = profile;

  return (
        <>
        {/* Herkunft und Rechtsgrundlage (nur intern) — L-59.
            Hier stand eine eigene, vierte Quellenliste (SOURCE_MAP mit
            facebook/linkedin/google_ads/briefkarte/…), und der Block zeigte
            sich nur, wenn `utm_source` oder `kampagne_quelle` gesetzt war —
            also bei den wenigsten Betrieben. Die Quelle, die tatsächlich
            geführt wird (`lead_source`), stand gar nicht da, und die
            Rechtsgrundlage nirgends im ganzen System.

            Jetzt eine Liste (`utils/leadStatus.js`, gespiegelt von
            `services/lead_quellen.py`) und immer sichtbar: Eine ungeführte
            Quelle oder eine offene Rechtsgrundlage soll auffallen, nicht
            verschwinden. */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
          padding: '8px 14px', background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
          fontSize: 12, marginBottom: 12, width: 'fit-content', maxWidth: '100%',
        }}>
          <span style={{ color: 'var(--text-tertiary)' }}>Quelle:</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            {leadSourceLabel(lead.lead_source)}
          </span>
          <Badge variant={herkunftVariant(lead.datenherkunft)}>
            {herkunftLabel(lead.datenherkunft)}
          </Badge>
          <Badge variant={lead.rechtsgrundlage ? 'info' : 'warning'}>
            {rechtsgrundlageLabel(lead.rechtsgrundlage)}
          </Badge>
          {(lead.utm_campaign || lead.kampagne_quelle) && (
            <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>
              · {lead.utm_campaign || lead.kampagne_quelle}
            </span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: isDesktop ? '340px 1fr' : isTablet ? '280px 1fr' : '1fr', gap: 16, alignItems: 'flex-start', minWidth: 0, width: '100%', overflowX: 'hidden' }}>

          {/* Linke Spalte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>

            {/* Screenshot */}
            <Card padding="sm" style={{ overflow: 'hidden', maxHeight: isMobile ? 200 : 'none', width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ background: 'var(--bg-app)', padding: '7px 10px', display: 'flex', alignItems: 'center', gap: 5, borderBottom: '1px solid var(--border-light)', margin: '-12px -12px 0' }}>
                {['#ef4444','#f59e0b','#22c55e'].map(c => (
                  <div key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                ))}
                <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', border: '1px solid var(--border-light)' }}>
                  {lead.website_url || 'Keine Website'}
                </div>
                {lead.website_url && (
                  <a href={lead.website_url.startsWith('http') ? lead.website_url : 'https://' + lead.website_url} target="_blank" rel="noopener noreferrer" aria-label="Website des Betriebs in neuem Tab oeffnen" style={{ fontSize: 12, color: 'var(--text-tertiary)', flexShrink: 0 }}>↗</a>
                )}
                <button onClick={createScreenshot} disabled={screenshotLoading} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: screenshotLoading ? 'wait' : 'pointer', fontSize: 12, padding: '1px 4px', flexShrink: 0 }} title="Screenshot aktualisieren">
                  {screenshotLoading ? '⏳' : '🔄'}
                </button>
              </div>

              <div style={{ padding: '4px 10px 6px' }}>
                <DomainBadge reachable={lead.domain_reachable ?? null} checkedAt={lead.domain_checked_at} loading={domainLoading} onCheck={checkDomain} />
              </div>

              <div style={{ margin: '0 -12px', position: 'relative', minHeight: 160, overflow: 'hidden' }}>
                {screenshotLoading ? (
                  <div style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', gap: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Screenshot wird erstellt...</span>
                  </div>
                ) : lead.website_screenshot ? (
                  <>
                    <img src={lead.website_screenshot} alt="Website" style={{ width: '100%', maxHeight: isMobile ? '150px' : '300px', objectFit: 'cover', objectPosition: 'top', display: 'block', borderRadius: 0 }} />
                    {current_score !== null && (
                      <div style={{ position: 'absolute', bottom: 8, right: 8, background: 'rgba(15,28,32,0.85)', backdropFilter: 'blur(6px)', borderRadius: 'var(--radius-md)', padding: '4px 10px' }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: levelColor }}>{current_score}/100</span>
                      </div>
                    )}
                  </>
                ) : (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(createScreenshot)} onClick={createScreenshot} style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', cursor: lead.website_url ? 'pointer' : 'default', gap: 8 }}
                    onMouseEnter={e => { if (lead.website_url) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-app)'; }}
                  >
                    <span style={{ fontSize: 28 }}>📸</span>
                    <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{lead.website_url ? 'Klicken für Screenshot' : 'Keine Website hinterlegt'}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Score Verlauf */}
            {score_history.length >= 2 && (
              <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Score-Verlauf</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {score_history.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {i > 0 && <span style={{ color: 'var(--border-medium)', fontSize: 12 }}>→</span>}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 15, fontWeight: 600, color: scoreColor(s.score) }}>{s.score}</div>
                        <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{s.date}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Kategorie Scores */}
            {latestAudit && (
              <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Kategorien</div>
                {[
                  ['Compliance', latestAudit.rc_score, 25],
                  ['Performance', latestAudit.tp_score, 15],
                  ['Barrierefreiheit', latestAudit.bf_score, 15],
                  ['Sicherheit', latestAudit.si_score, 10],
                  ['SEO', latestAudit.se_score, 10],
                  ['UX', latestAudit.ux_score, 10],
                ].map(([label, score, max]) => {
                  const pct = Math.min(100, ((score || 0) / max) * 100);
                  const col = pct >= 70 ? 'var(--status-success-text)' : pct >= 50 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';
                  return (
                    <div key={label} style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                        <span style={{ fontWeight: 500, color: col }}>{score || 0}/{max}</span>
                      </div>
                      <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: col, borderRadius: 2, transition: 'width 0.6s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </Card>
            )}
          </div>

          {/* Rechte Spalte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>

            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kontaktdaten</span>
                <button onClick={() => { setActiveTab('contact'); setEditMode(true); }} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Bearbeiten →</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile || isTablet ? '1fr' : '1fr 1fr', gap: '0 16px' }}>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('✉️', lead.email, 'E-Mail')}
                {fieldRow('🌐', lead.website_url?.replace(/^https?:\/\//, ''), 'Website')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
                  <span style={{ fontSize: 14, color: 'var(--brand-primary-mid)', flexShrink: 0, marginTop: 1, width: 18, textAlign: 'center' }}>👤</span>
                  <div>
                    <div style={{ fontSize: 13, color: lead.geschaeftsfuehrer ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{lead.geschaeftsfuehrer || '–'}</div>
                    {/* „(auto)" sagte, woher der Wert kommt — das interessiert die
                      * Maschine, nicht den Menschen davor (UX-25). */}
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 1 }}>Geschäftsführer</div>
                  </div>
                </div>
                {fieldRow('📍', [lead.street && `${lead.street} ${lead.house_number || ''}`.trim(), [lead.postal_code, lead.city].filter(Boolean).join(' ')].filter(Boolean).join(', '), 'Adresse')}
              </div>
              {/* Die technische Prüfung stand bis zum 17.08.2026 als Zeile
                * „[Auto-Enrichment] SSL: OK | …" in den Notizen — im Feld für
                * das, was ein Mensch schreibt, und bei jedem Lauf erneut
                * davorgesetzt. Sie hat jetzt einen eigenen Platz (UX-06).
                * „nicht geprüft" steht ausdrücklich da: Es ist nicht dasselbe
                * wie „fehlt". */}
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 6 }}>
                  Technische Prüfung
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {befundZeilen(profile.anreicherung).map(({ schluessel, beschriftung, wert, art }) => (
                    <span key={schluessel} style={{
                      fontSize: 11, padding: '3px 8px', borderRadius: 'var(--radius-sm)',
                      background: art === 'gut' ? 'var(--status-success-bg)'
                        : art === 'fehlt' ? 'var(--status-danger-bg)' : 'var(--bg-app)',
                      color: art === 'gut' ? 'var(--status-success-text)'
                        : art === 'fehlt' ? 'var(--status-danger-text)' : 'var(--text-tertiary)',
                    }}>
                      {beschriftung}: {wert}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 5 }}>
                  {geprueftAmText(profile.anreicherung)}
                </div>
              </div>

              {lead.notes && (
                <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, fontStyle: 'italic' }}>
                  {lead.notes}
                </div>
              )}
            </Card>

            {/* ── Weitere Domains ── */}
            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>
                Weitere Domains
              </div>

              {/* Domain list */}
              {domains.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: '8px 0', textAlign: 'center' }}>
                  Keine weiteren Domains
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
                  {domains.map(d => (
                    <div key={d.id} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '7px 10px', borderRadius: 'var(--radius-md)',
                      background: d.is_primary ? 'var(--bg-active)' : 'var(--bg-app)',
                      border: `1px solid ${d.is_primary ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                    }}>
                      {d.is_primary && (
                        <span title="Primär" style={{ fontSize: 13, flexShrink: 0 }}>⭐</span>
                      )}
                      <a
                        href={d.url.startsWith('http') ? d.url : 'https://' + d.url}
                        target="_blank" rel="noopener noreferrer"
                        style={{
                          fontSize: 12, flex: 1, minWidth: 0,
                          color: d.is_primary ? 'var(--brand-primary)' : 'var(--text-secondary)',
                          fontWeight: d.is_primary ? 500 : 400,
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          textDecoration: 'none',
                        }}
                        onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
                        onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}
                      >
                        {d.url.replace(/^https?:\/\//, '')}
                      </a>
                      {d.label && (
                        <span style={{
                          fontSize: 10, padding: '1px 7px', borderRadius: 'var(--radius-full)',
                          background: 'var(--bg-surface)', color: 'var(--text-tertiary)',
                          border: '1px solid var(--border-light)', flexShrink: 0,
                        }}>
                          {d.label}
                        </span>
                      )}
                      <button
                        onClick={() => deleteDomain(d.id)}
                        title="Löschen"
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px',
                          color: 'var(--text-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: 13, flexShrink: 0,
                          lineHeight: 1, transition: 'color 0.1s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.color = 'var(--status-danger-text)'}
                        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
                      >
                        🗑
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Das Formular stand immer offen und nahm auf der Übersicht
                * Platz weg — bei den meisten Betrieben gibt es gar keine
                * zweite Domain. Jetzt erst auf Verlangen (UX-26). */}
              {!domainFormOffen && (
                <button
                  onClick={() => setDomainFormOffen(true)}
                  style={{ marginTop: domains.length ? 10 : 0, padding: '6px 10px', fontSize: 12,
                    background: 'none', border: '1px dashed var(--border-medium)',
                    borderRadius: 'var(--radius-md)', color: 'var(--text-secondary)',
                    cursor: 'pointer', width: '100%', fontFamily: 'var(--font-sans)' }}
                >
                  + Domain hinzufügen
                </button>
              )}

              {domainFormOffen && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: domains.length ? 10 : 0, borderTop: domains.length ? '1px solid var(--border-light)' : 'none' }}>
                <input aria-label="Adresse der Domain"
                  value={domainForm.url}
                  onChange={e => setDomainForm(f => ({ ...f, url: e.target.value }))}
                  onKeyDown={e => e.key === 'Enter' && addDomain()}
                  placeholder="https://shop.firma.de"
                  style={{
                    padding: '7px 10px', fontSize: 12,
                    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-app)', color: 'var(--text-primary)',
                    fontFamily: 'var(--font-sans)', outline: 'none',
                  }}
                />
                <input aria-label="Label (z.B. Shop, Karriere)"
                  value={domainForm.label}
                  onChange={e => setDomainForm(f => ({ ...f, label: e.target.value }))}
                  placeholder="Label (z.B. Shop, Karriere)"
                  style={{
                    padding: '7px 10px', fontSize: 12,
                    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-app)', color: 'var(--text-primary)',
                    fontFamily: 'var(--font-sans)', outline: 'none',
                  }}
                />
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={domainForm.is_primary}
                      onChange={e => setDomainForm(f => ({ ...f, is_primary: e.target.checked }))}
                      style={{ cursor: 'pointer' }}
                    />
                    Als primär markieren
                  </label>
                  <button
                    onClick={addDomain}
                    disabled={!domainForm.url.trim() || domainAdding}
                    style={{
                      padding: '6px 14px', fontSize: 12, fontWeight: 600,
                      background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                      border: 'none', borderRadius: 'var(--radius-md)',
                      cursor: domainForm.url.trim() && !domainAdding ? 'pointer' : 'not-allowed',
                      opacity: domainForm.url.trim() && !domainAdding ? 1 : 0.5,
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    {domainAdding ? '…' : 'Hinzufügen'}
                  </button>
                </div>
              </div>
              )}
            </Card>

            {latestAudit && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Letzter Audit</span>
                  <button onClick={() => setActiveTab('audits')} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Alle anzeigen →</button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: `${levelColor}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: levelColor }}>{latestAudit.total_score}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{current_level}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{datumKurz(latestAudit.created_at, 'Datum unbekannt')}</div>
                  </div>
                </div>
                {latestAudit.ai_summary && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                    {latestAudit.ai_summary.substring(0, 200)}{latestAudit.ai_summary.length > 200 ? '...' : ''}
                  </div>
                )}
                {/* Sah aus wie deaktiviert. Gemessen: `--brand-primary-mid`
                  * auf `--bg-active` ergibt im Hellmodus **3.39** — unter der
                  * Schwelle für Text. (Im Dunkelmodus waren es 5.62; die
                  * Arbeitsliste vermutete es umgekehrt.) Mit
                  * `--brand-primary` sind es 8.16, und mit Halbfett und
                  * sichtbarem Rand sieht der Knopf aus wie einer (UX-18). */}
                <button onClick={() => setOpenAudit(latestAudit)} style={{ marginTop: 10, width: '100%', padding: '9px', background: 'var(--bg-active)', border: '1px solid var(--brand-primary-mid)', borderRadius: 'var(--radius-md)', color: 'var(--brand-primary)', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Vollständigen Bericht anzeigen
                </button>
              </Card>
            )}

            {/* ── Projekt ── */}
            {projectData && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Projekt</span>
                  <button onClick={() => navigate(`/app/projects/${projectId}`)} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Öffnen →
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {fieldRow('🔄', projectData.status?.replace('phase_', 'Phase ') || '–', 'Phase')}
                  {fieldRow('📦', projectData.package_type || '–', 'Paket')}
                  {fieldRow('💳', projectData.payment_status || '–', 'Zahlung')}
                  {fieldRow('📅', projectData.go_live_date || '–', 'Go-Live')}
                </div>
                <button
                  onClick={() => navigate(`/app/projects/${projectId}`)}
                  style={{ marginTop: 10, width: '100%', padding: '7px', background: 'var(--bg-active)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', color: 'var(--brand-primary-mid)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                >
                  📁 Zum Projekt
                </button>
              </Card>
            )}

            {/* Zeiterfassung (26.08.2026, Entscheidung David). Ohne sie
              * bleibt die Marge dauerhaft „unbekannt" — `actual_hours` war an
              * jedem Projekt 0, `time_tracking` leer, und `POST
              * /api/projects/{id}/time` hatte keinen Aufrufer (L-105).
              * Sie steht neben dem Projektkasten, weil sie zum Projekt
              * gehoert und nicht zum Betrieb. */}
            {projectId && (
              <Zeiterfassung projectId={projectId}
                phase={projectData?.status ? Number(String(projectData.status).replace('phase_', '')) || null : null}
                token={token} />
            )}

            {(lead.vat_id || lead.register_number || lead.register_court) && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>Rechtliches</div>
                {fieldRow('🏛️', lead.vat_id, 'USt-IdNr.')}
                {fieldRow('📋', lead.register_number, 'Handelsreg.-Nr.')}
                {fieldRow('⚖️', lead.register_court, 'Handelsregister')}
              </Card>
            )}

            {/* QR-Code */}
            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kunden-Zugang</span>
                <button onClick={() => setActiveTab('qrcode')} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Details →</button>
              </div>
              {qrLoading ? (
                <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                </div>
              ) : qrData ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); })} style={{ background: 'white', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: 8, flexShrink: 0, cursor: 'pointer' }}
                    onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                    title="Klicken zum Herunterladen">
                    <img src={`data:image/png;base64,${qrData.qr_code_base64}`} alt="QR-Code" style={{ width: 90, height: 90, display: 'block' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {lead.email && (
                      <div style={{ background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 'var(--radius-sm)', padding: '3px 8px', fontSize: 11, fontWeight: 500, marginBottom: 8, display: 'inline-block' }}>
                        🔐 @{lead.email.split('@')[1]}
                      </div>
                    )}
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 10 }}>
                      {qrData.portal_url.replace('https://', '')}
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <button onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                        style={{ padding: '5px 10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        ⬇ PNG
                      </button>
                      <button onClick={() => navigator.clipboard.writeText(qrData.portal_url)}
                        style={{ padding: '5px 10px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        📋 Link
                      </button>
                      {lead.email && (
                        <a href={`mailto:${lead.email}?subject=Ihr persönlicher Zugang&body=Ihr Zugangslink:%0D%0A${qrData.portal_url}`}
                          aria-label="Zugangslink per E-Mail senden" style={{ padding: '5px 10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)', fontSize: 11, textDecoration: 'none', fontFamily: 'var(--font-sans)' }}>
                          ✉️
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <button onClick={loadQrCode} style={{ padding: '8px 16px', background: 'var(--bg-active)', color: 'var(--brand-primary-mid)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    QR-Code generieren
                  </button>
                </div>
              )}
            </Card>
          </div>
        </div>
        </>
        );
}
