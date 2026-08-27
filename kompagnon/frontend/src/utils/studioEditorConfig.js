// Shared configuration for the @grapesjs/studio-sdk editor.
// Every editor in the app imports from here so the plugin set,
// license key and default options stay consistent.

import {
  tableComponent,
  listPagesComponent,
  fsLightboxComponent,
  lightGalleryComponent,
  swiperComponent,
  iconifyComponent,
  accordionComponent,
  flexComponent,
  rteProseMirror,
  canvasEmptyState,
  canvasFullSize,
  canvasGridMode,
  layoutSidebarButtons,
  youtubeAssetProvider,
} from '@grapesjs/studio-sdk-plugins';

// **Kein Rückfall mehr im Quelltext (L-75, 23.08.2026).** Hier stand ein
// Lizenzschlüssel fest verdrahtet, und er war bis heute der einzige, der
// wirkte: `REACT_APP_GJS_LICENSE_KEY` war in keinem der beiden Render-
// Frontends gesetzt — nachgemessen am ausgelieferten Paket, nicht im
// Dashboard nachgesehen.
//
// **Warum ein fester Rückfall hier die falsche Freundlichkeit war.** Er
// verhindert nicht den Ausfall, er verschiebt ihn: Fehlt die Variable, läuft
// alles weiter, und niemand merkt, dass ein Schlüssel aus dem Quelltext
// benutzt wird — bis er widerrufen wird. Ohne Rückfall bricht der Editor
// sofort und sichtbar, und das ist die ehrlichere Antwort.
//
// **Der Schutz liegt ohnehin woanders.** Ein Frontend-Schlüssel wird beim
// Bauen ins Paket gebacken und ist für jeden lesbar, der die Seite aufruft —
// so ist es bei GrapesJS Studio vorgesehen. Was ihn für Fremde wertlos macht,
// ist die **erlaubte Domain**, nicht seine Geheimhaltung. Seit dem 23.08. ist
// je eine je Umgebung eingetragen: `kas.kompagnon.group` und
// `kompagnon-frontend-staging.onrender.com`.
//
// **Lokal braucht es gar keinen Schlüssel** — Studio läuft auf localhost ohne
// Lizenz (Herstellerdoku). Der leere Wert unten ist dort also richtig.
export const STUDIO_LICENSE_KEY = process.env.REACT_APP_GJS_LICENSE_KEY || '';

// Build a fresh plugin list. We wrap in a function so each editor
// instance gets its own plugin descriptors (avoids shared state).
export const buildStudioPlugins = () => [
  tableComponent.init({}),
  listPagesComponent.init({}),
  fsLightboxComponent.init({}),
  lightGalleryComponent.init({}),
  swiperComponent.init({}),
  iconifyComponent.init({}),
  accordionComponent.init({}),
  flexComponent.init({}),
  rteProseMirror.init({}),
  canvasEmptyState.init({}),
  canvasFullSize.init({}),
  canvasGridMode.init({}),
  layoutSidebarButtons.init({}),
  youtubeAssetProvider.init({}),
];
