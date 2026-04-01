const academyCourses = [
  // Mitarbeiter-Kurse
  { id: 'akquise-prozess', title: 'Der KOMPAGNON Akquise-Prozess', description: 'Vom Erstkontakt bis zum Auftrag — der komplette Vertriebsprozess für neue Kunden Schritt für Schritt erklärt.', category: 'Akquise', categoryColor: 'primary', audience: 'employee', formats: ['text', 'video', 'checklist'] },
  { id: 'audit-durchfuehren', title: 'Website-Audit durchführen', description: 'Wie Sie einen Homepage Standard Audit starten, interpretieren und dem Kunden präsentieren.', category: 'Audit', categoryColor: 'warning', audience: 'employee', formats: ['text', 'video'] },
  { id: '7-projektphasen', title: 'Die 7 Projektphasen', description: 'Von der Akquisition über Briefing, Content, Technik, QA bis Go-Live und Post-Launch — jede Phase im Detail.', category: 'Projekt', categoryColor: 'success', audience: 'employee', formats: ['text', 'checklist'] },
  { id: 'system-bedienen', title: 'KOMPAGNON-System bedienen', description: 'Dashboard, Pipeline, Domain-Import, Audit-Tool und Kundenkartei effektiv nutzen.', category: 'Tools', categoryColor: 'info', audience: 'employee', formats: ['text', 'video'] },
  { id: 'kaltakquise', title: 'Kaltakquise & Anschreiben', description: 'Vorlagen, Skripte und Best Practices für die telefonische und schriftliche Kaltakquise.', category: 'Vertrieb', categoryColor: 'danger', audience: 'employee', formats: ['text', 'checklist'] },
  { id: 'qualitaetsstandards', title: 'Qualitätsstandards & Übergabe', description: 'Checklisten für die finale QA, Kundenübergabe und den reibungslosen Go-Live.', category: 'Qualität', categoryColor: 'secondary', audience: 'employee', formats: ['text', 'checklist'] },

  // Kunden-Kurse
  { id: 'projekt-ablauf', title: 'So läuft Ihr Website-Projekt ab', description: 'Ein Überblick über alle Schritte von der Beauftragung bis zur fertigen Website — was wann passiert.', category: 'Start', categoryColor: 'primary', audience: 'customer', formats: ['text', 'video'] },
  { id: 'vorbereitung', title: 'Was wir von Ihnen brauchen', description: 'Logo, Texte, Fotos, Zugangsdaten — welche Materialien wir benötigen und wie Sie diese am besten liefern.', category: 'Vorbereitung', categoryColor: 'info', audience: 'customer', formats: ['text', 'checklist'] },
  { id: 'audit-verstehen', title: 'Ihren Audit-Bericht verstehen', description: 'Was die Scores bedeuten, welche Kategorien es gibt und wo der größte Handlungsbedarf besteht.', category: 'Audit', categoryColor: 'warning', audience: 'customer', formats: ['text'] },
  { id: 'website-pflegen', title: 'Ihre neue Website pflegen', description: 'Einführung in WordPress: Texte ändern, Bilder tauschen, Seiten erstellen — ohne Programmierkenntnisse.', category: 'Website', categoryColor: 'success', audience: 'customer', formats: ['text', 'video'] },
  { id: 'seo-google', title: 'Gefunden werden — SEO & Google Business', description: 'Wie Ihre Website bei Google sichtbar wird und wie Sie Ihr Google Business Profil optimal nutzen.', category: 'SEO', categoryColor: 'secondary', audience: 'customer', formats: ['text'] },
];

export default academyCourses;
