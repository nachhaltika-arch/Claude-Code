// Helper functions
export function getTemplatesByCategory(cat) {
  return cat === 'Alle' ? templates : templates.filter(t => t.category === cat);
}
export function getTemplatesByStyle(style) {
  return templates.filter(t => t.style === style);
}
export function getTemplateById(id) {
  return templates.find(t => t.id === id);
}
export const categories = ['Alle', 'Elektriker', 'Klempner & Sanitär', 'Maler & Lackierer', 'Dachdecker', 'Schreiner & Tischler', 'Fliesenleger', 'Heizungsbauer', 'Garten & Landschaftsbau', 'Kfz-Werkstatt', 'Zimmermann & Holzbau', 'Reinigungsservice', 'Umzugsunternehmen', 'Allgemein'];

export const templates = [
  {
    id: 'tpl-001',
    name: 'Modern Elektriker',
    category: 'Elektriker',
    style: 'modern',
    emoji: '⚡',
    colors: { primary: '#0d6efd', secondary: '#1a2332', accent: '#ffc107' },
    fonts: { heading: 'Inter, sans-serif', body: 'system-ui, sans-serif' },
    thumbnail: null,
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Handwerker</title></head>
<body style="margin:0;font-family:sans-serif;">
  <header style="background:#1a2332;color:#fff;padding:2rem;text-align:center;">
    <h1>Ihr zuverlässiger Handwerker</h1>
    <p>Qualität und Erfahrung seit Jahren</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <section style="margin-bottom:2rem;">
      <h2>Unsere Leistungen</h2>
      <ul><li>Renovierung</li><li>Reparatur</li><li>Neubau</li></ul>
    </section>
    <section><h2>Kontakt</h2><p>Tel: 0800 123 456</p></section>
  </main>
</body>
</html>`,
  },
  {
    id: 'elektriker-modern',
    name: 'Elektriker Modern',
    category: 'Elektro',
    emoji: '⚡',
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Elektriker</title></head>
<body style="margin:0;font-family:sans-serif;">
  <header style="background:#0d6efd;color:#fff;padding:2rem;text-align:center;">
    <h1>Ihr Elektriker</h1>
    <p>Schnell, sicher, zuverlässig</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <h2>Leistungen</h2>
    <p>Elektroinstallation, Reparaturen, Smart Home</p>
    <h2>Kontakt</h2><p>info@elektriker.de</p>
  </main>
</body>
</html>`,
  },
  {
    id: 'gastronomie-klassisch',
    name: 'Restaurant Klassisch',
    category: 'Gastronomie',
    emoji: '🍽️',
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Restaurant</title></head>
<body style="margin:0;font-family:Georgia,serif;">
  <header style="background:#2c1810;color:#f5deb3;padding:3rem;text-align:center;">
    <h1>Willkommen in unserem Restaurant</h1>
    <p>Genuss und Gastfreundschaft</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <h2>Speisekarte</h2>
    <p>Traditionelle Küche mit saisonalen Zutaten.</p>
    <h2>Reservierung</h2><p>Tel: 0800 789 012</p>
  </main>
</body>
</html>`,
  },
  {
    id: 'friseursalon-modern',
    name: 'Friseursalon Modern',
    category: 'Beauty',
    emoji: '✂️',
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Friseursalon</title></head>
<body style="margin:0;font-family:sans-serif;">
  <header style="background:#c8a96e;color:#fff;padding:2rem;text-align:center;">
    <h1>Ihr Friseursalon</h1>
    <p>Haarpflege auf höchstem Niveau</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <h2>Unsere Dienstleistungen</h2>
    <p>Schneiden, Färben, Stylen – für Damen und Herren.</p>
    <h2>Termin buchen</h2><p>Online oder telefonisch: 0800 345 678</p>
  </main>
</body>
</html>`,
  },
  {
    id: 'arztpraxis-serioes',
    name: 'Arztpraxis Seriös',
    category: 'Gesundheit',
    emoji: '🏥',
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Arztpraxis</title></head>
<body style="margin:0;font-family:sans-serif;">
  <header style="background:#006494;color:#fff;padding:2rem;text-align:center;">
    <h1>Ihre Arztpraxis</h1>
    <p>Ihre Gesundheit ist unser Auftrag</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <h2>Leistungen</h2>
    <p>Allgemeinmedizin, Vorsorge, Beratung</p>
    <h2>Sprechzeiten</h2><p>Mo–Fr 8–18 Uhr</p>
  </main>
</body>
</html>`,
  },
  {
    id: 'fitness-studio',
    name: 'Fitnessstudio',
    category: 'Sport',
    emoji: '💪',
    html: `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>Fitnessstudio</title></head>
<body style="margin:0;font-family:sans-serif;">
  <header style="background:#e63946;color:#fff;padding:2rem;text-align:center;">
    <h1>Ihr Fitnessstudio</h1>
    <p>Stärker werden – jeden Tag</p>
  </header>
  <main style="max-width:900px;margin:2rem auto;padding:0 1rem;">
    <h2>Kurse & Training</h2>
    <p>Krafttraining, Cardio, Yoga und mehr.</p>
    <h2>Mitgliedschaft</h2><p>Ab 29 € / Monat</p>
  </main>
</body>
</html>`,
  },
];
