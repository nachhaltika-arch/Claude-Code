import grapesjs from 'grapesjs';
import 'grapesjs/dist/css/grapes.min.css';
import gjsNewsletter from 'grapesjs-preset-newsletter';
import { useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../config';

const DEFAULT_TEMPLATE = `
<table style="width:100%;max-width:650px;margin:0 auto;font-family:Arial,sans-serif">
  <tr><td style="background:#008eaa;padding:30px;text-align:center">
    <h1 style="color:white;margin:0;font-size:28px">KOMPAGNON</h1>
  </td></tr>
  <tr><td style="padding:32px;background:#ffffff">
    <h2 style="color:#1a2332;margin:0 0 16px">Betreff hier eintragen</h2>
    <p style="color:#64748b;line-height:1.7;margin:0 0 24px">
      Inhalt der E-Mail hier schreiben...
    </p>
    <table style="width:100%"><tr><td style="text-align:center">
      <a href="#" style="display:inline-block;background:#008eaa;color:white;
         padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:bold">
        Jetzt handeln
      </a>
    </td></tr></table>
  </td></tr>
  <tr><td style="padding:20px;background:#f8f9fa;text-align:center">
    <p style="color:#94a3b8;font-size:12px;margin:0">
      KOMPAGNON Communications BP GmbH &bull; kompagnon.eu
    </p>
  </td></tr>
</table>`;

export default function NewsletterDesigner({ leadId, projectId, onSend, onSave, initialHtml }) {
  const editorRef = useRef(null);
  const [showSendModal, setShowSendModal] = useState(false);
  const [sendTo, setSendTo] = useState('');
  const [subject, setSubject] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  const handleSend = async () => {
    if (!sendTo || !subject) return;
    setSending(true); setSendResult(null);
    try {
      const html = editorRef.current.runCommand('gjs-get-inlined-html');
      const res = await fetch(`${API_BASE_URL}/api/messages/send-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
                   Authorization: `Bearer ${localStorage.getItem('token')}` },
        body: JSON.stringify({ to: sendTo, subject, html,
                               lead_id: leadId || null,
                               project_id: projectId || null }),
      });
      const data = await res.json();
      setSendResult(data.success ? 'success' : 'error');
      if (data.success && onSend) onSend(html);
    } catch { setSendResult('error'); }
    finally { setSending(false); }
  };

  useEffect(() => {
    const editor = grapesjs.init({
      container: '#gjs-newsletter',
      height: 'calc(100vh - 160px)',
      storageManager: false,
      fromElement: false,
      components: initialHtml || DEFAULT_TEMPLATE,
      plugins: [gjsNewsletter],
      pluginsOpts: {
        [gjsNewsletter]: {
          modalLabelImport: 'HTML importieren',
          modalLabelExport: 'HTML exportieren',
          updateStyleManager: true,
          showStylesOnChange: true,
        },
      },
      deviceManager: {
        devices: [
          { name: 'Desktop', width: '650px' },
          { name: 'Mobil', width: '375px', widthMedia: '480px' },
        ],
      },
    });

    editorRef.current = editor;

    editor.Panels.addButton('options', {
      id: 'nl-save', className: 'fa fa-save',
      command: 'nl-save-cmd', attributes: { title: 'Als Entwurf speichern' },
    });
    editor.Panels.addButton('options', {
      id: 'nl-send', className: 'fa fa-paper-plane',
      command: 'nl-send-cmd', attributes: { title: 'Newsletter senden' },
    });
    editor.Commands.add('nl-save-cmd', {
      run: () => {
        const html = editor.runCommand('gjs-get-inlined-html');
        if (onSave) onSave(html);
      },
    });
    editor.Commands.add('nl-send-cmd', {
      run: () => setShowSendModal(true),
    });

    return () => { if (editorRef.current) editorRef.current.destroy(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position:'relative',display:'flex',flexDirection:'column',height:'100vh' }}>
      <div style={{ padding:'8px 16px',background:'#1a2332',
                    display:'flex',alignItems:'center',gap:12 }}>
        <span style={{ color:'white',fontWeight:600 }}>Newsletter Designer</span>
        {(leadId || projectId) && (
          <span style={{ color:'#64748b',fontSize:12 }}>
            {projectId ? `Projekt #${projectId}` : `Lead #${leadId}`}
          </span>
        )}
      </div>
      <div id="gjs-newsletter" style={{ flex:1 }} />

      {showSendModal && (
        <div style={{ position:'fixed',top:0,right:0,bottom:0,left:0,background:'rgba(0,0,0,0.5)',
                      display:'flex',alignItems:'center',justifyContent:'center',zIndex:9999 }}>
          <div style={{ background:'var(--bg-surface)',borderRadius:12,
                        padding:32,width:440,maxWidth:'90vw' }}>
            <h3 style={{ margin:'0 0 20px',color:'var(--text-primary)' }}>
              Newsletter senden
            </h3>
            <label style={{ display:'block',marginBottom:6,fontSize:13,
                            color:'var(--text-secondary)' }}>Empfaenger (E-Mail)</label>
            <input type="email" value={sendTo}
              onChange={(e) => setSendTo(e.target.value)}
              placeholder="kunde@beispiel.de"
              style={{ width:'100%',padding:'10px 12px',borderRadius:6,
                       border:'1px solid var(--color-border-primary)',
                       marginBottom:16,fontSize:14,boxSizing:'border-box',
                       background:'var(--bg-app)',color:'var(--text-primary)' }} />
            <label style={{ display:'block',marginBottom:6,fontSize:13,
                            color:'var(--text-secondary)' }}>Betreff</label>
            <input type="text" value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Ihr Newsletter von KOMPAGNON"
              style={{ width:'100%',padding:'10px 12px',borderRadius:6,
                       border:'1px solid var(--color-border-primary)',
                       marginBottom:20,fontSize:14,boxSizing:'border-box',
                       background:'var(--bg-app)',color:'var(--text-primary)' }} />
            {sendResult === 'success' && (
              <p style={{ color:'var(--color-text-success)',
                          background:'var(--color-background-success)',
                          padding:'8px 12px',borderRadius:6,
                          fontSize:13,marginBottom:16 }}>
                E-Mail erfolgreich gesendet!
              </p>
            )}
            {sendResult === 'error' && (
              <p style={{ color:'var(--color-text-danger)',
                          background:'var(--color-background-danger)',
                          padding:'8px 12px',borderRadius:6,
                          fontSize:13,marginBottom:16 }}>
                Fehler — SMTP pruefen.
              </p>
            )}
            <div style={{ display:'flex',gap:10,justifyContent:'flex-end' }}>
              <button onClick={() => { setShowSendModal(false); setSendResult(null); }}
                style={{ padding:'8px 20px',
                         border:'1px solid var(--color-border-primary)',
                         borderRadius:6,background:'transparent',
                         color:'var(--text-secondary)',cursor:'pointer' }}>
                Abbrechen
              </button>
              <button onClick={handleSend}
                disabled={sending || !sendTo || !subject}
                style={{ padding:'8px 20px',border:'none',borderRadius:6,
                         background:'#008eaa',color:'white',
                         cursor:'pointer',fontWeight:600,opacity:sending?0.7:1 }}>
                {sending ? 'Wird gesendet...' : 'Jetzt senden'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
