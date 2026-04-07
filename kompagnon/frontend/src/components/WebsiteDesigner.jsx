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

export default function WebsiteDesigner({ projectId, leadId, initialHtml, initialCss, onSave }) {
  const editorRef = useRef(null);

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

    editor.Keymaps.add('ns:save', 'ctrl:83', 'save-db');

    return () => { if (editorRef.current) editorRef.current.destroy(); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position: 'relative', display: 'flex',
                  flexDirection: 'column', height: '100vh' }}>
      <div style={{ padding: '8px 16px', background: '#1a2332',
                    display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ color: 'white', fontWeight: 600 }}>Website Designer</span>
        <span style={{ color: '#64748b', fontSize: 12 }}>
          {projectId ? `Projekt #${projectId}` : 'Neues Design'}
        </span>
      </div>
      <div id="gjs-designer" style={{ flex: 1 }} />
    </div>
  );
}
