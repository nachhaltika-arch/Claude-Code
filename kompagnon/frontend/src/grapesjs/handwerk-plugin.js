import { renderBlock } from './handwerk-blocks';

const BLOCK_CONFIGS = [
  { id: 'hero',           label: 'Hero-Bereich',     category: 'Sektionen',
    defaultData: { headline: 'Ihre Ueberschrift', subline: 'Unterzeile', cta_text: 'Jetzt anfragen', cta_link: '/kontakt' } },
  { id: 'leistungen-grid', label: 'Leistungen-Grid', category: 'Sektionen',
    defaultData: { headline: 'Unsere Leistungen', items: [
      { icon: '🔧', titel: 'Leistung 1', beschreibung: 'Beschreibung hier' },
      { icon: '⚡', titel: 'Leistung 2', beschreibung: 'Beschreibung hier' },
      { icon: '🏠', titel: 'Leistung 3', beschreibung: 'Beschreibung hier' },
    ]} },
  { id: 'usp-balken',    label: 'USP-Balken',        category: 'Sektionen',
    defaultData: { items: [
      { icon: '\u2713', titel: '25 Jahre Erfahrung' },
      { icon: '\u23F0', titel: '24h Notdienst', sub: 'Immer erreichbar' },
      { icon: '\uD83D\uDCCD', titel: 'Regional vor Ort' },
    ]} },
  { id: 'ueber-uns',     label: 'Ueber uns',          category: 'Sektionen',
    defaultData: { label: 'Ueber uns', headline: 'Ihr Partner vor Ort', text: 'Text hier...', cta_text: 'Mehr erfahren', cta_link: '/ueber-uns' } },
  { id: 'cta-banner',    label: 'CTA-Banner',        category: 'Sektionen',
    defaultData: { headline: 'Bereit loszulegen?', subline: 'Kontaktieren Sie uns', cta_text: 'Jetzt anfragen', cta_link: '/kontakt' } },
  { id: 'kontakt-form',  label: 'Kontaktformular',   category: 'Sektionen',
    defaultData: { headline: 'Kontakt aufnehmen', cta_text: 'Nachricht senden' } },
  { id: 'footer',        label: 'Footer',             category: 'Sektionen',
    defaultData: { firma: 'Ihr Betrieb' } },
];

export default function handwerkPlugin(editor, opts = {}) {
  const { brand = {} } = opts;

  BLOCK_CONFIGS.forEach(({ id, label, category, defaultData }) => {

    // Block im Panel registrieren
    editor.BlockManager.add(`handwerk-${id}`, {
      label,
      category,
      content: {
        type:       `handwerk-${id}`,
        attributes: { 'data-block': id },
      },
    });

    // Traits fuer den rechten Editor-Panel
    const traits = [
      { type: 'text', name: 'headline', label: 'Ueberschrift', changeProp: 1 },
      { type: 'text', name: 'subline',  label: 'Unterzeile',  changeProp: 1 },
      ...(id === 'hero' ? [
        { type: 'text', name: 'cta_text',  label: 'Button-Text',  changeProp: 1 },
        { type: 'text', name: 'cta_link',  label: 'Button-Link',  changeProp: 1 },
        { type: 'text', name: 'cta2_text', label: '2. Button',    changeProp: 1 },
        { type: 'text', name: 'badge',     label: 'Badge-Text',   changeProp: 1 },
      ] : []),
      ...(id === 'cta-banner' ? [
        { type: 'text', name: 'cta_text', label: 'Button-Text', changeProp: 1 },
        { type: 'text', name: 'cta_link', label: 'Button-Link', changeProp: 1 },
        { type: 'text', name: 'phone',    label: 'Telefon',     changeProp: 1 },
      ] : []),
      ...(id === 'ueber-uns' ? [
        { type: 'text', name: 'text',     label: 'Text',        changeProp: 1 },
        { type: 'text', name: 'bild',     label: 'Bild-URL',    changeProp: 1 },
        { type: 'text', name: 'cta_text', label: 'Button-Text', changeProp: 1 },
        { type: 'text', name: 'cta_link', label: 'Button-Link', changeProp: 1 },
      ] : []),
    ].map(t => ({ ...t, default: defaultData[t.name] || '' }));

    // Komponenten-Typ registrieren
    editor.DomComponents.addType(`handwerk-${id}`, {
      isComponent: el =>
        el.tagName === 'SECTION' && el.dataset?.block === id,

      model: {
        defaults: {
          tagName:   'section',
          draggable: true,
          droppable: false,
          copyable:  true,
          attributes: { 'data-block': id },
          traits,
          components: renderBlock(id, defaultData, brand),
        },
        init() {
          this.listenTo(this, 'change:traits', this.onTraitChange);
        },
        onTraitChange() {
          const data = { ...defaultData };
          this.getTraits().forEach(t => { data[t.get('name')] = t.get('value') || ''; });
          this.components(renderBlock(id, data, brand));
        },
      },
    });
  });

  // Ctrl+S zum Speichern
  editor.Keymaps.add('ns:save', 'ctrl+s', () => {
    editor.trigger('kompagnon:save');
  });
}
