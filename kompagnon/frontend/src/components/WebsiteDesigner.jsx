import grapesjs from 'grapesjs';
import 'grapesjs/dist/css/grapes.min.css';
import gjsPresetWebpage from 'grapesjs-preset-webpage';
import gjsBlocksBasic from 'grapesjs-blocks-basic';
import gjsForms from 'grapesjs-plugin-forms';
import gjsFlexbox from 'grapesjs-blocks-flexbox';
import gjsCountdown from 'grapesjs-component-countdown';
import gjsTabs from 'grapesjs-tabs';
import gjsCustomCode from 'grapesjs-custom-code';
import gjsTouch from 'grapesjs-touch';
import gjsStyleGradient from 'grapesjs-style-gradient';
import gjsStyleFilter from 'grapesjs-style-filter';
import gjsTooltip from 'grapesjs-tooltip';
import { useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../config';
import JSZip from 'jszip';

const loadProjectFromZip = async (file, editor) => {
  const ext = file.name.split('.').pop().toLowerCase();

  if (ext === 'grapesjs') {
    const text = await file.text();
    try {
      const project = JSON.parse(text);
      editor.loadProjectData(project);
      return { success: true, source: 'grapesjs' };
    } catch (e) {
      return { success: false, error: 'Ungültige .grapesjs-Datei' };
    }
  }

  if (ext === 'zip') {
    try {
      const zip   = await JSZip.loadAsync(file);
      const files = Object.keys(zip.files);

      const gjsFile = files.find(
        f => f.endsWith('.grapesjs') || f.endsWith('grapesjs.json')
      );
      if (gjsFile) {
        const text    = await zip.files[gjsFile].async('string');
        const project = JSON.parse(text);
        editor.loadProjectData(project);
        return { success: true, source: 'zip-grapesjs' };
      }

      const htmlFile = files.find(f => f.endsWith('index.html'));
      const cssFile  = files.find(f => f.endsWith('style.css'));
      if (htmlFile) {
        const html = await zip.files[htmlFile].async('string');
        const css  = cssFile ? await zip.files[cssFile].async('string') : '';
        const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        const bodyHtml  = bodyMatch ? bodyMatch[1].trim() : html;
        editor.setComponents(bodyHtml);
        if (css) editor.setStyle(css);
        return { success: true, source: 'zip-html' };
      }

      return { success: false, error: 'Keine erkennbare Datei im ZIP' };
    } catch (e) {
      return { success: false, error: `ZIP-Fehler: ${e.message}` };
    }
  }

  return {
    success: false,
    error: `Format .${ext} nicht unterstützt. Bitte .zip oder .grapesjs hochladen.`,
  };
};

export default function WebsiteDesigner({ projectId, leadId, initialHtml, initialCss, onSave }) {
  const editorRef = useRef(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importing, setImporting]   = useState(false);
  const [importMsg, setImportMsg]   = useState('');
  const [importError, setImportError] = useState('');
  const [kiLoading, setKiLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !editorRef.current) return;
    setImporting(true);
    setImportMsg('');
    setImportError('');
    const result = await loadProjectFromZip(file, editorRef.current);
    setImporting(false);
    if (result.success) {
      setImportMsg(
        `✓ Template geladen (${
          result.source === 'zip-grapesjs' ? 'GrapesJS-Projekt aus ZIP' :
          result.source === 'zip-html'     ? 'HTML/CSS aus ZIP'         :
                                             '.grapesjs-Datei'
        })`
      );
      setShowImportModal(false);
    } else {
      setImportError(result.error || 'Import fehlgeschlagen');
    }
    e.target.value = '';
  };

  useEffect(() => {
    const editor = grapesjs.init({
      container: '#gjs-designer',
      height: 'calc(100vh - 120px)',
      storageManager: false,
      fromElement: false,
      components: initialHtml || '',
      style: initialCss || '',
      plugins: [
        gjsPresetWebpage, gjsBlocksBasic, gjsForms, gjsFlexbox,
        gjsCountdown, gjsTabs, gjsCustomCode, gjsTouch,
        gjsStyleGradient, gjsStyleFilter, gjsTooltip,
      ],
      pluginsOpts: {
        [gjsPresetWebpage]: {
          blocks: ['link-block', 'quote', 'text-basic'],
          modalImportTitle: 'HTML importieren',
          modalImportLabel: 'Fuege HTML/CSS Code ein:',
          filestackOpts: null, aviaryOpts: false,
          blocksBasicOpts: { flexGrid: true },
        },
        [gjsBlocksBasic]: {
          flexGrid: true,
          blocks: ['column1','column2','column3','column3-7',
                   'text','link','image','video','map'],
        },
        [gjsForms]: {}, [gjsFlexbox]: {}, [gjsCountdown]: {},
        [gjsTabs]: {}, [gjsCustomCode]: {}, [gjsTouch]: {},
        [gjsStyleGradient]: {}, [gjsStyleFilter]: {}, [gjsTooltip]: {},
      },
      canvas: {
        styles: [
          'https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.2.3/css/bootstrap.min.css',
          'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        ],
      },
      deviceManager: {
        devices: [
          { name: 'Desktop', width: '' },
          { name: 'Tablet', width: '768px', widthMedia: '992px' },
          { name: 'Mobil', width: '375px', widthMedia: '480px' },
        ],
      },
      styleManager: {
        sectors: [
          { name: 'Allgemein', open: false,
            buildProps: ['float','display','position','top','right','left','bottom'] },
          { name: 'Abstaende', open: false, buildProps: ['margin','padding'] },
          { name: 'Dimensionen', open: false,
            buildProps: ['width','height','max-width','min-height','border-radius'] },
          { name: 'Typografie', open: false,
            buildProps: ['font-family','font-size','font-weight','letter-spacing',
                         'color','line-height','text-align','text-decoration','text-shadow'] },
          { name: 'Dekorierung', open: false,
            buildProps: ['background','background-color','border','border-radius',
                         'box-shadow','opacity'] },
          { name: 'Extra', open: false,
            buildProps: ['transition','transform','perspective','cursor'] },
          { name: 'Flexbox', open: false,
            buildProps: ['flex-direction','flex-wrap','justify-content','align-items',
                         'align-content','order','flex-basis','flex-grow',
                         'flex-shrink','align-self'] },
        ],
      },
      i18n: {
        locale: 'de', detectLocale: false,
        messages: { de: {
          blockManager: { labels: {
            'column1':'1 Spalte','column2':'2 Spalten','column3':'3 Spalten',
            'text':'Text','link':'Link','image':'Bild','video':'Video','map':'Karte',
          }},
          traitManager: { empty: 'Waehle ein Element aus' },
        }},
      },
    });

    editorRef.current = editor;

    // ── KOMPAGNON Blocks ────────────────────────────────────────────────────
    editor.BlockManager.add('kompagnon-hero', {
      label: 'Hero-Sektion', category: 'KOMPAGNON',
      content: `<section style="background:#008eaa;color:white;padding:80px 40px;text-align:center">
    <h1 style="font-size:2.5rem;margin-bottom:16px">Ihr Handwerks-Spezialist</h1>
    <p style="font-size:1.2rem;margin-bottom:32px">Qualitaet aus der Region.</p>
    <a href="#kontakt" style="background:white;color:#008eaa;padding:14px 32px;
       border-radius:6px;font-weight:bold;text-decoration:none">Jetzt anfragen</a>
  </section>`,
      attributes: { class: 'fa fa-star' },
    });

    editor.BlockManager.add('kompagnon-kontakt', {
      label: 'Kontaktformular', category: 'KOMPAGNON',
      content: `<section style="padding:60px 40px;background:#f8f9fa">
    <h2 style="text-align:center;margin-bottom:32px">Kontakt aufnehmen</h2>
    <form style="max-width:600px;margin:0 auto">
      <div style="margin-bottom:16px">
        <label style="display:block;margin-bottom:6px">Name</label>
        <input type="text" placeholder="Ihr Name"
          style="width:100%;padding:12px;border:1px solid #ddd;border-radius:4px"/>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;margin-bottom:6px">E-Mail</label>
        <input type="email" placeholder="ihre@email.de"
          style="width:100%;padding:12px;border:1px solid #ddd;border-radius:4px"/>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;margin-bottom:6px">Nachricht</label>
        <textarea rows="4" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:4px"></textarea>
      </div>
      <button type="submit" style="background:#008eaa;color:white;padding:14px 32px;
        border:none;border-radius:4px;cursor:pointer">Absenden</button>
    </form>
  </section>`,
      attributes: { class: 'fa fa-envelope' },
    });

    editor.BlockManager.add('kompagnon-firmendaten', {
      label: 'Firmendaten', category: 'Data Source',
      content: `<div style="padding:20px"><h2>{{firma_name}}</h2>
    <p>{{firma_adresse}}</p><p>Tel: {{firma_telefon}}</p>
    <p>E-Mail: {{firma_email}}</p></div>`,
      attributes: { class: 'fa fa-building' },
    });

  const handleLoadKiEntwurf = async () => {
    const editor = editorRef.current;
    if (!editor || kiLoading) return;
    setKiLoading(true);
    try {
      const token = localStorage.getItem('kompagnon_token');
      const res = await fetch(
        `${API_BASE_URL}/api/customers/${projectId}/generate-design`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Fehler ${res.status}`);
      }
      const data = await res.json();
      editor.setComponents(data.html);
    } catch (e) {
      console.error('KI-Entwurf laden fehlgeschlagen:', e);
      alert(`KI-Entwurf fehlgeschlagen: ${e.message}`);
    } finally {
      setKiLoading(false);
    }
  };

    editor.BlockManager.add('kompagnon-leistungen', {
      label: 'Leistungs-Liste', category: 'Data Source',
      content: `<ul style="padding:20px 40px">
    <li style="margin-bottom:8px">Leistung 1</li>
    <li style="margin-bottom:8px">Leistung 2</li>
    <li style="margin-bottom:8px">Leistung 3</li></ul>`,
      attributes: { class: 'fa fa-list' },
    });

    editor.BlockManager.add('kompagnon-oeffnungszeiten', {
      label: 'Oeffnungszeiten', category: 'Data Source',
      content: `<table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:8px;border-bottom:1px solid #eee">Mo-Fr</td>
        <td style="padding:8px;border-bottom:1px solid #eee">07:00-17:00 Uhr</td></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee">Sa</td>
        <td style="padding:8px;border-bottom:1px solid #eee">08:00-13:00 Uhr</td></tr>
    <tr><td style="padding:8px">So</td>
        <td style="padding:8px">Geschlossen</td></tr></table>`,
      attributes: { class: 'fa fa-clock' },
    });

    // ── Toolbar Buttons ─────────────────────────────────────────────────────
    editor.Panels.addButton('options', {
      id: 'save-btn', className: 'fa fa-save',
      command: 'save-db', attributes: { title: 'Speichern (Strg+S)' },
    });
    editor.Panels.addButton('options', {
      id: 'netlify-btn', className: 'fa fa-rocket',
      command: 'deploy-netlify', attributes: { title: 'Zu Netlify deployen' },
    });

    // ── Commands ────────────────────────────────────────────────────────────
    editor.Commands.add('save-db', {
      run: (editor) => { if (onSave) onSave(editor.getHtml(), editor.getCss()); },
    });

    editor.Commands.add('deploy-netlify', {
      run: async (editor) => {
        try {
          const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/netlify/deploy`,
            { method: 'POST',
              headers: { 'Content-Type': 'application/json',
                         Authorization: `Bearer ${localStorage.getItem('token')}` },
              body: JSON.stringify({ html: editor.getHtml(), css: editor.getCss() }) });
          const data = await res.json();
          alert(data.deploy_url ? `Deployed: ${data.deploy_url}` : 'Deploy gestartet.');
        } catch { alert('Deploy fehlgeschlagen.'); }
      },
    });

    editor.Panels.addButton('options', {
      id: 'zip-import-btn', className: 'fa fa-file-archive-o',
      command: 'open-zip-import',
      attributes: { title: 'ZIP-Template importieren' },
    });
    editor.Commands.add('open-zip-import', {
      run: () => setShowImportModal(true),
    });

    editor.Keymaps.add('ns:save', 'ctrl:83', 'save-db');

    return () => { if (editorRef.current) editorRef.current.destroy(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position: 'relative', display: 'flex',
                  flexDirection: 'column', height: '100vh' }}>
      <div style={{ padding: '8px 16px', background: '#1a2332',
                    display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ color: 'white', fontWeight: 600 }}>Website Designer</span>
        <span style={{ color: '#64748b', fontSize: 12 }}>
          {projectId ? `Projekt #${projectId}` : 'Neues Design'}
        </span>

        {/* Versteckter File-Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.grapesjs"
          style={{ display: 'none' }}
          onChange={handleImportFile}
        />

        {/* Upload-Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={importing}
          title="GrapesJS ZIP oder .grapesjs-Datei importieren"
          style={{
            padding: '7px 14px',
            background: importing ? '#94a3b8' : '#7c3aed',
            color: 'white',
            border: 'none',
            borderRadius: 7,
            fontSize: 12,
            fontWeight: 600,
            cursor: importing ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            whiteSpace: 'nowrap',
          }}
        >
          {importing ? '⏳ Lädt...' : '📂 Template laden'}
        </button>

        {importMsg && (
          <span style={{ fontSize: 11, color: '#1D9E75', fontWeight: 500 }}>
            {importMsg}
          </span>
        )}
        {importError && !showImportModal && (
          <span style={{ fontSize: 11, color: '#E24B4A', fontWeight: 500 }}>
            ✗ {importError}
          </span>
        )}
      </div>
      <div id="gjs-designer" style={{ flex: 1 }} />

      {showImportModal && (
        <div style={{ position:'absolute',inset:0,background:'rgba(0,0,0,0.5)',
                      display:'flex',alignItems:'center',justifyContent:'center',zIndex:9999 }}>
          <div style={{ background:'var(--bg-surface)',borderRadius:12,
                        padding:32,width:480,maxWidth:'90vw' }}>
            <h3 style={{ margin:'0 0 16px',color:'var(--text-primary)' }}>
              ZIP-Template importieren
            </h3>
            <p style={{ fontSize:13,color:'var(--text-secondary)',marginBottom:20 }}>
              ZIP mit <code>index.html</code> hochladen. Optional: <code>style.css</code>.
            </p>
            <div onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const f = e.dataTransfer.files[0];
                if (f) { const synth = { target: { files: [f], value: '' }, preventDefault: () => {} }; handleImportFile(synth); }
              }}
              style={{ border:'2px dashed var(--color-border-secondary)',borderRadius:8,
                       padding:'32px 20px',textAlign:'center',cursor:'pointer',
                       background:'var(--bg-app)',marginBottom:16 }}>
              {importing
                ? <p style={{ margin:0,color:'var(--text-secondary)' }}>Verarbeitung...</p>
                : <><div style={{ fontSize:32,marginBottom:8 }}>📦</div>
                   <p style={{ margin:0,color:'var(--text-secondary)',fontSize:14 }}>
                     ZIP oder .grapesjs hier ablegen oder klicken
                   </p></>}
            </div>
            {importError && (
              <p style={{ color:'var(--color-text-danger)',
                          background:'var(--color-background-danger)',
                          padding:'8px 12px',borderRadius:6,fontSize:13,marginBottom:12 }}>
                {importError}
              </p>
            )}
            <div style={{ display:'flex',gap:10,justifyContent:'flex-end' }}>
              <button onClick={() => { setShowImportModal(false); setImportError(''); }}
                style={{ padding:'8px 20px',border:'1px solid var(--color-border-primary)',
                         borderRadius:6,background:'transparent',
                         color:'var(--text-secondary)',cursor:'pointer' }}>
                Abbrechen
              </button>
              <button onClick={() => fileInputRef.current?.click()} disabled={importing}
                style={{ padding:'8px 20px',border:'none',borderRadius:6,
                         background:'#0d6efd',color:'white',cursor:'pointer',fontWeight:600 }}>
                Datei auswaehlen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
