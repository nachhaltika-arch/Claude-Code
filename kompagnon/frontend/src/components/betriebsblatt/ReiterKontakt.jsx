/**
 * Der Reiter „Kontakt" des Betriebsblatts (L-25).
 *
 * Am 2026-08-30 aus `LeadProfile.jsx` herausgeloest. Die Bedingung bleibt am
 * Aufrufort, damit dort sichtbar bleibt, wann der Reiter erscheint.
 */
import { oeffnungszeitenAlsJson, oeffnungszeitenAlsText } from '../../utils/oeffnungszeiten';
import Card from '../ui/Card';
import Button from '../ui/Button';
import WZSearch from '../WZSearch';

export default function ReiterKontakt({
  lead,
  isMobile,
  editData,
  editMode,
  extractFromImpressum,
  extractResult,
  extracting,
  fieldRow,
  inputStyle,
  isTablet,
  saveEdit,
  saving,
  sectionLabel,
  setEditData,
  setEditMode,
}) {
  return (
        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)', margin: 0 }}>Kontakt & Betrieb</h2>
            {!editMode && (
              <Button variant="secondary" size="sm" onClick={() => setEditMode(true)}>✏️ Bearbeiten</Button>
            )}
          </div>

          {!editMode && lead.website_url && (
            <div style={{ marginBottom: 16, padding: '12px 14px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                Automatisch aus Impressum befüllen
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 10 }}>
                Liest Firmenname, Adresse, Handelsregister u.v.m. direkt aus dem Impressum von <strong>{lead.website_url.replace(/^https?:\/\//, '')}</strong>
              </div>

              {extractResult && (
                <div style={{
                  padding: '8px 10px', borderRadius: 'var(--radius-sm)',
                  background: extractResult.success ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
                  color: extractResult.success ? 'var(--status-success-text)' : 'var(--status-danger-text)',
                  fontSize: 12, marginBottom: 8,
                }}>
                  {extractResult.success ? '✓' : '✕'} {extractResult.message}
                </div>
              )}

              <button onClick={extractFromImpressum} disabled={extracting} style={{
                padding: '7px 14px',
                background: extracting ? 'var(--bg-surface)' : 'var(--brand-primary)',
                color: extracting ? 'var(--text-tertiary)' : 'white',
                border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                fontSize: 12, fontWeight: 500, cursor: extracting ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6,
              }}>
                {extracting ? (
                  <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Impressum wird gelesen...</>
                ) : '🔍 Impressum auslesen'}
              </button>
            </div>
          )}

          {editMode ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Betrieb</div>
                </div>

                {[
                  ['Firmenname', 'company_name', 'Mustermann GmbH'],
                  ['Gesellschaftsform', 'legal_form', 'GmbH, UG, GmbH & Co. KG'],
                  ['Vorname Geschäftsführer', 'ceo_first_name', 'Max'],
                  ['Nachname Geschäftsführer', 'ceo_last_name', 'Mustermann'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}
                <div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Gewerk / Branche</div>
                  <WZSearch
                    value={editData.wz_code ? { code: editData.wz_code, title: editData.wz_title } : null}
                    onChange={(entry) => setEditData(p => ({
                      ...p,
                      wz_code: entry?.code || '',
                      wz_title: entry?.title || '',
                      trade: entry?.title || '',
                    }))}
                    placeholder="Branche suchen..."
                  />
                </div>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Adresse</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Straße</div>
                    <input aria-label="Musterstraße" value={editData.street || ''} onChange={e => setEditData(p => ({...p, street: e.target.value}))} placeholder="Musterstraße" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Nr.</div>
                    <input aria-label="12a" value={editData.house_number || ''} onChange={e => setEditData(p => ({...p, house_number: e.target.value}))} placeholder="12a" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>PLZ</div>
                    <input aria-label="Postleitzahl" value={editData.postal_code || ''} onChange={e => setEditData(p => ({...p, postal_code: e.target.value}))} placeholder="56070" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Ort</div>
                    <input aria-label="Koblenz" value={editData.city || ''} onChange={e => setEditData(p => ({...p, city: e.target.value}))} placeholder="Koblenz" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                {/* Oeffnungszeiten (L-15, L-99). `schema.org/LocalBusiness`
                    verlangt sie, und ohne sie antwortet der SEO-Agent mit 400.
                    Gespeichert wird JSON, eingegeben werden Zeilen — sieben
                    Spalten waeren sieben Migrationen beim ersten Sonderfall
                    wie „Sa nach Vereinbarung". */}
                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Öffnungszeiten</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: -4, marginBottom: 8 }}>
                    Je Zeile ein Eintrag: <code>Mo-Fr 08:00-17:00</code>. Wird für
                    die schema.org-Auszeichnung und den SEO-Agenten gebraucht.
                  </div>
                  <textarea
                    aria-label="Öffnungszeiten, je Zeile ein Eintrag"
                    value={oeffnungszeitenAlsText(editData.opening_hours)}
                    onChange={e => setEditData(p => ({ ...p, opening_hours: oeffnungszeitenAlsJson(e.target.value) }))}
                    placeholder={'Mo-Do 08:00-17:00\nFr 08:00-13:00'}
                    rows={4}
                    style={{ ...inputStyle, resize: 'vertical', fontFamily: 'var(--font-mono, monospace)', lineHeight: 1.6 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                </div>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Kontakt</div>
                </div>

                {[
                  ['Ansprechpartner', 'contact_name', 'Max Mustermann'],
                  ['Telefon', 'phone', '+49 261 123456'],
                  ['Mobilfunknummer', 'mobile', '+49 170 1234567'],
                  ['E-Mail', 'email', 'info@firma.de'],
                  ['Website', 'website_url', 'www.firma.de'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Rechtliches</div>
                </div>

                {[
                  ['USt-IdNr.', 'vat_id', 'DE123456789'],
                  ['Handelsreg.-Nr.', 'register_number', 'HRB 12345'],
                  ['Handelsregister', 'register_court', 'Amtsgericht Koblenz'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5, marginTop: 8 }}>Notizen</div>
                  <textarea aria-label="Interne Notizen..." value={editData.notes || ''} onChange={e => setEditData(p => ({...p, notes: e.target.value}))} placeholder="Interne Notizen..." rows={3}
                    style={{ ...inputStyle, resize: 'vertical', minHeight: 70 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
                <Button variant="primary" onClick={saveEdit} disabled={saving}>
                  {saving ? 'Wird gespeichert...' : '✓ Speichern'}
                </Button>
                <Button variant="secondary" onClick={() => setEditMode(false)}>Abbrechen</Button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : isTablet ? '1fr 1fr' : '1fr 1fr 1fr', gap: 24 }}>
              <div>
                <div style={sectionLabel}>Betrieb</div>
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🔧', lead.trade, 'Gewerk')}
              </div>
              <div>
                <div style={sectionLabel}>Kontakt</div>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('📱', lead.mobile, 'Mobilfunknummer')}
                {fieldRow('✉️', lead.email, 'E-Mail')}
                {fieldRow('🌐', lead.website_url?.replace(/^https?:\/\//, ''), 'Website')}
              </div>
              <div>
                <div style={sectionLabel}>Adresse</div>
                {fieldRow('📍', [lead.street && `${lead.street} ${lead.house_number || ''}`.trim(), [lead.postal_code, lead.city].filter(Boolean).join(' ')].filter(Boolean).join(', '), 'Anschrift')}
                {(lead.vat_id || lead.register_number) && (
                  <>
                    <div style={{ ...sectionLabel, marginTop: 16 }}>Rechtliches</div>
                    {fieldRow('🏛️', lead.vat_id, 'USt-IdNr.')}
                    {fieldRow('📋', lead.register_number, 'Handelsreg.-Nr.')}
                    {fieldRow('⚖️', lead.register_court, 'Handelsregister')}
                  </>
                )}
              </div>
            </div>
          )}
        </Card>
        );
}
