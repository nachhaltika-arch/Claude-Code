export const zusatzTemplates = [
  {
    id: 'elektriker-profi',
    name: 'Elektriker Profi',
    category: 'Elektriker',
    style: 'modern',
    thumbnail: '⚡',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Elektriker Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0d6efd;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0d6efd,#1a3a6b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0d6efd;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0d6efd;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0d6efd;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0d6efd;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0d6efd22,#0d6efd44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0d6efd;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">⚡ Elektriker Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Elektriker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Elektriker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">⚡</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@elektrikerprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Elektriker Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'elektriker-notfall',
    name: 'Elektriker Notdienst',
    category: 'Elektriker',
    style: 'modern',
    thumbnail: '🔌',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Elektriker Notdienst</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#dc2626;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#dc2626,#7f1d1d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#dc2626;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#dc2626;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#dc2626;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#dc2626;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#dc262622,#dc262644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#dc2626;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔌 Elektriker Notdienst</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Elektriker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Elektriker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔌</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@elektrikernotfall.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Elektriker Notdienst – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'elektriker-smart',
    name: 'Smart Home Elektriker',
    category: 'Elektriker',
    style: 'minimalistisch',
    thumbnail: '💡',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Smart Home Elektriker</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#6d28d9;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#6d28d9,#4c1d95);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#6d28d9;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#6d28d9;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#6d28d9;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#6d28d9;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#6d28d922,#6d28d944);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#6d28d9;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">💡 Smart Home Elektriker</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Elektriker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Elektriker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">💡</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@elektrikersmart.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Smart Home Elektriker – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'sanitaer-profi',
    name: 'Sanitär Profi',
    category: 'Klempner & Sanitär',
    style: 'modern',
    thumbnail: '🚿',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Sanitär Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0891b2;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0891b2,#0e4f6b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0891b2;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0891b2;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0891b2;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0891b2;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0891b222,#0891b244);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0891b2;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🚿 Sanitär Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Klempner & Sanitär-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Klempner & Sanitär. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🚿</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@sanitaerprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Sanitär Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'sanitaer-notfall',
    name: 'Klempner Notdienst',
    category: 'Klempner & Sanitär',
    style: 'modern',
    thumbnail: '🔧',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Klempner Notdienst</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#ea580c;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#ea580c,#7c2d12);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#ea580c;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#ea580c;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#ea580c;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#ea580c;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#ea580c22,#ea580c44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#ea580c;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔧 Klempner Notdienst</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Klempner & Sanitär-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Klempner & Sanitär. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔧</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@sanitaernotfall.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Klempner Notdienst – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'sanitaer-premium',
    name: 'Bad & Sanitär Premium',
    category: 'Klempner & Sanitär',
    style: 'klassisch',
    thumbnail: '🛁',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Bad & Sanitär Premium</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0e7490;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0e7490,#164e63);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0e7490;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0e7490;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0e7490;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0e7490;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0e749022,#0e749044);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0e7490;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🛁 Bad & Sanitär Premium</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Klempner & Sanitär-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Klempner & Sanitär. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🛁</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@sanitaerpremium.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Bad & Sanitär Premium – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'maler-modern',
    name: 'Maler Modern',
    category: 'Maler & Lackierer',
    style: 'modern',
    thumbnail: '🎨',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Maler Modern</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#ea580c;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#ea580c,#9a3412);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#ea580c;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#ea580c;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#ea580c;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#ea580c;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#ea580c22,#ea580c44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#ea580c;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🎨 Maler Modern</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Maler & Lackierer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Maler & Lackierer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🎨</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@malermodern.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Maler Modern – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'maler-premium',
    name: 'Malermeister Premium',
    category: 'Maler & Lackierer',
    style: 'klassisch',
    thumbnail: '🖌️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Malermeister Premium</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#c2410c;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#c2410c,#7c2d12);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#c2410c;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#c2410c;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#c2410c;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#c2410c;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#c2410c22,#c2410c44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#c2410c;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🖌️ Malermeister Premium</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Maler & Lackierer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Maler & Lackierer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🖌️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@malerpremium.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Malermeister Premium – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'maler-fassade',
    name: 'Fassaden & Lackierung',
    category: 'Maler & Lackierer',
    style: 'minimalistisch',
    thumbnail: '🏗️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Fassaden & Lackierung</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#78716c;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#78716c,#44403c);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#78716c;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#78716c;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#78716c;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#78716c;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#78716c22,#78716c44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#78716c;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏗️ Fassaden & Lackierung</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Maler & Lackierer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Maler & Lackierer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏗️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@malerfassade.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Fassaden & Lackierung – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'dachdecker-profi',
    name: 'Dachdecker Profi',
    category: 'Dachdecker',
    style: 'modern',
    thumbnail: '🏠',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dachdecker Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#92400e;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#92400e,#451a03);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#92400e;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#92400e;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#92400e;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#92400e;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#92400e22,#92400e44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#92400e;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏠 Dachdecker Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Dachdecker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Dachdecker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏠</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@dachdeckerprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Dachdecker Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'dachdecker-notfall',
    name: 'Dachdecker Notdienst',
    category: 'Dachdecker',
    style: 'modern',
    thumbnail: '⛺',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dachdecker Notdienst</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#dc2626;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#dc2626,#7f1d1d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#dc2626;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#dc2626;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#dc2626;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#dc2626;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#dc262622,#dc262644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#dc2626;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">⛺ Dachdecker Notdienst</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Dachdecker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Dachdecker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">⛺</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@dachdeckernotfall.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Dachdecker Notdienst – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'dachdecker-modern',
    name: 'Dach & Fassade Modern',
    category: 'Dachdecker',
    style: 'minimalistisch',
    thumbnail: '🏗️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dach & Fassade Modern</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#57534e;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#57534e,#292524);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#57534e;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#57534e;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#57534e;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#57534e;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#57534e22,#57534e44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#57534e;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏗️ Dach & Fassade Modern</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Dachdecker-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Dachdecker. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏗️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@dachdeckermodern.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Dach & Fassade Modern – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'schreiner-profi',
    name: 'Schreiner Profi',
    category: 'Schreiner & Tischler',
    style: 'klassisch',
    thumbnail: '🪵',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Schreiner Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#78350f;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#78350f,#3b1809);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#78350f;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#78350f;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#78350f;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#78350f;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#78350f22,#78350f44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#78350f;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🪵 Schreiner Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Schreiner & Tischler-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Schreiner & Tischler. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🪵</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@schreinerprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Schreiner Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'schreiner-massivholz',
    name: 'Massivholz Tischler',
    category: 'Schreiner & Tischler',
    style: 'klassisch',
    thumbnail: '🪚',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Massivholz Tischler</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#854d0e;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#854d0e,#422006);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#854d0e;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#854d0e;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#854d0e;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#854d0e;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#854d0e22,#854d0e44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#854d0e;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🪚 Massivholz Tischler</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Schreiner & Tischler-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Schreiner & Tischler. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🪚</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@schreinermassivholz.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Massivholz Tischler – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'schreiner-modern',
    name: 'Schreiner Modern',
    category: 'Schreiner & Tischler',
    style: 'modern',
    thumbnail: '🪑',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Schreiner Modern</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#a16207;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#a16207,#713f12);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#a16207;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#a16207;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#a16207;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#a16207;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#a1620722,#a1620744);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#a16207;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🪑 Schreiner Modern</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Schreiner & Tischler-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Schreiner & Tischler. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🪑</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@schreinermodern.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Schreiner Modern – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'fliesen-profi',
    name: 'Fliesenleger Profi',
    category: 'Fliesenleger',
    style: 'modern',
    thumbnail: '🔲',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Fliesenleger Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#475569;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#475569,#1e293b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#475569;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#475569;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#475569;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#475569;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#47556922,#47556944);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#475569;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔲 Fliesenleger Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Fliesenleger-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Fliesenleger. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔲</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@fliesenprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Fliesenleger Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'fliesen-bad',
    name: 'Bad & Fliesen Spezialist',
    category: 'Fliesenleger',
    style: 'minimalistisch',
    thumbnail: '🛁',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Bad & Fliesen Spezialist</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0891b2;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0891b2,#0e4f6b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0891b2;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0891b2;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0891b2;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0891b2;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0891b222,#0891b244);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0891b2;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🛁 Bad & Fliesen Spezialist</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Fliesenleger-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Fliesenleger. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🛁</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@fliesenbad.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Bad & Fliesen Spezialist – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'fliesen-modern',
    name: 'Fliesen & Design',
    category: 'Fliesenleger',
    style: 'minimalistisch',
    thumbnail: '✨',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Fliesen & Design</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#64748b;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#64748b,#334155);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#64748b;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#64748b;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#64748b;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#64748b;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#64748b22,#64748b44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#64748b;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">✨ Fliesen & Design</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Fliesenleger-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Fliesenleger. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">✨</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@fliesenmodern.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Fliesen & Design – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'heizung-profi',
    name: 'Heizungsbauer Profi',
    category: 'Heizungsbauer',
    style: 'modern',
    thumbnail: '🔥',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Heizungsbauer Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#dc2626;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#dc2626,#7f1d1d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#dc2626;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#dc2626;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#dc2626;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#dc2626;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#dc262622,#dc262644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#dc2626;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔥 Heizungsbauer Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Heizungsbauer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Heizungsbauer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔥</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@heizungprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Heizungsbauer Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'heizung-waermepumpe',
    name: 'Wärmepumpen Spezialist',
    category: 'Heizungsbauer',
    style: 'modern',
    thumbnail: '♨️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Wärmepumpen Spezialist</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0891b2;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0891b2,#0e4f6b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0891b2;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0891b2;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0891b2;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0891b2;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0891b222,#0891b244);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0891b2;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">♨️ Wärmepumpen Spezialist</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Heizungsbauer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Heizungsbauer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">♨️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@heizungwaermepumpe.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Wärmepumpen Spezialist – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'heizung-solar',
    name: 'Solar & Heizung',
    category: 'Heizungsbauer',
    style: 'minimalistisch',
    thumbnail: '☀️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Solar & Heizung</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#d97706;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#d97706,#78350f);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#d97706;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#d97706;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#d97706;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#d97706;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#d9770622,#d9770644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#d97706;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">☀️ Solar & Heizung</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Heizungsbauer-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Heizungsbauer. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">☀️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@heizungsolar.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Solar & Heizung – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'garten-design',
    name: 'Garten Design',
    category: 'Garten & Landschaftsbau',
    style: 'modern',
    thumbnail: '🌿',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Garten Design</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#16a34a;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#16a34a,#14532d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#16a34a;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#16a34a;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#16a34a;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#16a34a;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#16a34a22,#16a34a44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#16a34a;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🌿 Garten Design</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Garten & Landschaftsbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Garten & Landschaftsbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🌿</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@gartendesign.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Garten Design – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'garten-pflege',
    name: 'Gartenpflege Profi',
    category: 'Garten & Landschaftsbau',
    style: 'klassisch',
    thumbnail: '🌳',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Gartenpflege Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#15803d;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#15803d,#052e16);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#15803d;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#15803d;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#15803d;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#15803d;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#15803d22,#15803d44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#15803d;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🌳 Gartenpflege Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Garten & Landschaftsbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Garten & Landschaftsbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🌳</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@gartenpflege.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Gartenpflege Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'garten-landschaft',
    name: 'Landschaftsbau & Außenanlagen',
    category: 'Garten & Landschaftsbau',
    style: 'minimalistisch',
    thumbnail: '🏡',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Landschaftsbau & Außenanlagen</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#4d7c0f;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#4d7c0f,#1a2e05);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#4d7c0f;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#4d7c0f;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#4d7c0f;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#4d7c0f;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#4d7c0f22,#4d7c0f44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#4d7c0f;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏡 Landschaftsbau & Außenanlagen</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Garten & Landschaftsbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Garten & Landschaftsbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏡</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@gartenlandschaft.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Landschaftsbau & Außenanlagen – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'kfz-profi',
    name: 'Kfz-Werkstatt Profi',
    category: 'Kfz-Werkstatt',
    style: 'modern',
    thumbnail: '🚗',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Kfz-Werkstatt Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#1f2937;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#1f2937,#030712);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#1f2937;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#1f2937;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#1f2937;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#1f2937;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#1f293722,#1f293744);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#1f2937;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🚗 Kfz-Werkstatt Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Kfz-Werkstatt-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Kfz-Werkstatt. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🚗</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@kfzprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Kfz-Werkstatt Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'kfz-express',
    name: 'Kfz Express Service',
    category: 'Kfz-Werkstatt',
    style: 'modern',
    thumbnail: '🔩',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Kfz Express Service</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#dc2626;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#dc2626,#7f1d1d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#dc2626;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#dc2626;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#dc2626;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#dc2626;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#dc262622,#dc262644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#dc2626;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔩 Kfz Express Service</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Kfz-Werkstatt-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Kfz-Werkstatt. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔩</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@kfzexpress.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Kfz Express Service – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'kfz-premium',
    name: 'Auto & Karosserie Premium',
    category: 'Kfz-Werkstatt',
    style: 'klassisch',
    thumbnail: '🏎️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Auto & Karosserie Premium</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#374151;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#374151,#111827);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#374151;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#374151;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#374151;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#374151;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#37415122,#37415144);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#374151;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏎️ Auto & Karosserie Premium</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Kfz-Werkstatt-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Kfz-Werkstatt. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏎️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@kfzpremium.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Auto & Karosserie Premium – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'zimmermann-profi',
    name: 'Zimmermann Profi',
    category: 'Zimmermann & Holzbau',
    style: 'klassisch',
    thumbnail: '🪚',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Zimmermann Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#92400e;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#92400e,#451a03);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#92400e;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#92400e;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#92400e;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#92400e;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#92400e22,#92400e44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#92400e;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🪚 Zimmermann Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Zimmermann & Holzbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Zimmermann & Holzbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🪚</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@zimmermannprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Zimmermann Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'zimmermann-dach',
    name: 'Dachstuhl & Zimmerei',
    category: 'Zimmermann & Holzbau',
    style: 'klassisch',
    thumbnail: '🏠',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dachstuhl & Zimmerei</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#78350f;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#78350f,#3b1809);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#78350f;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#78350f;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#78350f;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#78350f;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#78350f22,#78350f44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#78350f;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏠 Dachstuhl & Zimmerei</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Zimmermann & Holzbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Zimmermann & Holzbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏠</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@zimmermanndach.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Dachstuhl & Zimmerei – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'zimmermann-holzbau',
    name: 'Holzbau Meister',
    category: 'Zimmermann & Holzbau',
    style: 'modern',
    thumbnail: '🪵',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Holzbau Meister</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#a16207;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#a16207,#3b1809);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#a16207;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#a16207;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#a16207;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#a16207;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#a1620722,#a1620744);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#a16207;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🪵 Holzbau Meister</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Zimmermann & Holzbau-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Zimmermann & Holzbau. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🪵</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@zimmermannholzbau.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Holzbau Meister – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'reinigung-profi',
    name: 'Reinigungsservice Profi',
    category: 'Reinigungsservice',
    style: 'modern',
    thumbnail: '✨',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Reinigungsservice Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0284c7;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0284c7,#0c4a6e);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0284c7;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0284c7;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0284c7;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0284c7;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0284c722,#0284c744);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0284c7;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">✨ Reinigungsservice Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Reinigungsservice-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Reinigungsservice. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">✨</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@reinigungprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Reinigungsservice Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'reinigung-gewerbe',
    name: 'Gewerbereinigung',
    category: 'Reinigungsservice',
    style: 'minimalistisch',
    thumbnail: '🧹',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Gewerbereinigung</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0891b2;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0891b2,#0e4f6b);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0891b2;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0891b2;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0891b2;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0891b2;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0891b222,#0891b244);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0891b2;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🧹 Gewerbereinigung</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Reinigungsservice-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Reinigungsservice. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🧹</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@reinigunggewerbe.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Gewerbereinigung – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'reinigung-premium',
    name: 'Premium Gebäudereinigung',
    category: 'Reinigungsservice',
    style: 'klassisch',
    thumbnail: '🫧',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Premium Gebäudereinigung</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#6d28d9;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#6d28d9,#3b0764);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#6d28d9;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#6d28d9;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#6d28d9;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#6d28d9;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#6d28d922,#6d28d944);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#6d28d9;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🫧 Premium Gebäudereinigung</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Reinigungsservice-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Reinigungsservice. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🫧</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@reinigungpremium.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Premium Gebäudereinigung – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'umzug-profi',
    name: 'Umzug Profi',
    category: 'Umzugsunternehmen',
    style: 'modern',
    thumbnail: '📦',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Umzug Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#7c3aed;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#7c3aed,#3b0764);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#7c3aed;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#7c3aed;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#7c3aed;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#7c3aed;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#7c3aed22,#7c3aed44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#7c3aed;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">📦 Umzug Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Umzugsunternehmen-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Umzugsunternehmen. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">📦</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@umzugprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Umzug Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'umzug-express',
    name: 'Umzug Express',
    category: 'Umzugsunternehmen',
    style: 'modern',
    thumbnail: '🚚',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Umzug Express</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#dc2626;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#dc2626,#7f1d1d);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#dc2626;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#dc2626;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#dc2626;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#dc2626;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#dc262622,#dc262644);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#dc2626;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🚚 Umzug Express</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Umzugsunternehmen-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Umzugsunternehmen. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🚚</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@umzugexpress.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Umzug Express – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'umzug-premium',
    name: 'Umzug & Lagerung Premium',
    category: 'Umzugsunternehmen',
    style: 'klassisch',
    thumbnail: '🏠',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Umzug & Lagerung Premium</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#1d4ed8;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#1d4ed8,#1e3a8a);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#1d4ed8;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#1d4ed8;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#1d4ed8;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#1d4ed8;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#1d4ed822,#1d4ed844);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#1d4ed8;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🏠 Umzug & Lagerung Premium</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Umzugsunternehmen-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Umzugsunternehmen. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🏠</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@umzugpremium.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Umzug & Lagerung Premium – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'handwerk-profi',
    name: 'Handwerk Profi',
    category: 'Allgemein',
    style: 'modern',
    thumbnail: '🔨',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Handwerk Profi</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#0d6efd;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#0d6efd,#1e3a8a);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#0d6efd;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#0d6efd;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#0d6efd;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#0d6efd;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#0d6efd22,#0d6efd44);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#0d6efd;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🔨 Handwerk Profi</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Allgemein-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Allgemein. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🔨</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@handwerkprofi.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Handwerk Profi – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'handwerk-regional',
    name: 'Handwerk Regional',
    category: 'Allgemein',
    style: 'klassisch',
    thumbnail: '🛠️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Handwerk Regional</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#1a2332;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#1a2332,#0f172a);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#1a2332;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#1a2332;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#1a2332;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#1a2332;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#1a233222,#1a233244);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#1a2332;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">🛠️ Handwerk Regional</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Allgemein-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Allgemein. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">🛠️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@handwerkregional.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Handwerk Regional – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  },
  {
    id: 'handwerk-qualitaet',
    name: 'Handwerk Qualität',
    category: 'Allgemein',
    style: 'minimalistisch',
    thumbnail: '⚒️',
    html: `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Handwerk Qualität</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;color:#333;}
nav{background:#374151;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;}
nav .logo{color:#fff;font-size:1.3rem;font-weight:700;}
nav a{color:rgba(255,255,255,0.85);text-decoration:none;margin-left:1.5rem;font-size:.9rem;}
.hero{background:linear-gradient(135deg,#374151,#111827);color:#fff;padding:5rem 2rem;text-align:center;}
.hero h1{font-size:2.5rem;margin-bottom:1rem;}
.hero p{font-size:1.15rem;opacity:.9;max-width:600px;margin:0 auto 2rem;}
.btn{background:#fff;color:#374151;padding:.75rem 2rem;border-radius:6px;font-weight:700;text-decoration:none;display:inline-block;}
.services{padding:4rem 2rem;background:#f8f9fa;}
.services h2{text-align:center;font-size:2rem;margin-bottom:2.5rem;color:#374151;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto;}
.card{background:#fff;border-radius:10px;padding:2rem;box-shadow:0 2px 10px rgba(0,0,0,.08);text-align:center;}
.card .icon{font-size:2.5rem;margin-bottom:1rem;}
.card h3{color:#374151;margin-bottom:.5rem;}
.about{padding:4rem 2rem;max-width:900px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;}
.about h2{font-size:1.8rem;color:#374151;margin-bottom:1rem;}
.about-img{background:linear-gradient(135deg,#37415122,#37415144);border-radius:12px;height:250px;display:flex;align-items:center;justify-content:center;font-size:5rem;}
.contact{background:#374151;color:#fff;padding:4rem 2rem;text-align:center;}
.contact h2{font-size:1.8rem;margin-bottom:1rem;}
.contact p{opacity:.9;margin-bottom:.5rem;}
footer{background:#1a2332;color:#aaa;text-align:center;padding:1.5rem;font-size:.85rem;}
@media(max-width:600px){.about{grid-template-columns:1fr;}.hero h1{font-size:1.8rem;}}
</style>
</head>
<body>
<nav>
  <div class="logo">⚒️ Handwerk Qualität</div>
  <div><a href="#leistungen">Leistungen</a><a href="#ueber-uns">Über uns</a><a href="#kontakt">Kontakt</a></div>
</nav>
<section class="hero">
  <h1>Ihr zuverlässiger Allgemein-Betrieb</h1>
  <p>Qualität, Pünktlichkeit und faire Preise – direkt aus Ihrer Region.</p>
  <a class="btn" href="#kontakt">Jetzt anfragen</a>
</section>
<section class="services" id="leistungen">
  <h2>Unsere Leistungen</h2>
  <div class="grid">
    <div class="card"><div class="icon">🔧</div><h3>Montage & Installation</h3><p>Fachgerechte Installation durch erfahrene Meister.</p></div>
    <div class="card"><div class="icon">🛡️</div><h3>Wartung & Inspektion</h3><p>Regelmäßige Wartung für lange Lebensdauer.</p></div>
    <div class="card"><div class="icon">⚡</div><h3>Notdienst 24/7</h3><p>Schnelle Hilfe rund um die Uhr – auch am Wochenende.</p></div>
    <div class="card"><div class="icon">📋</div><h3>Beratung & Planung</h3><p>Individuelle Lösungen für Ihre Anforderungen.</p></div>
    <div class="card"><div class="icon">🏆</div><h3>Qualitätsgarantie</h3><p>Alle Arbeiten mit Gewährleistung und Materialgarantie.</p></div>
    <div class="card"><div class="icon">💰</div><h3>Faire Preise</h3><p>Transparente Kostenvoranschläge ohne versteckte Kosten.</p></div>
  </div>
</section>
<section id="ueber-uns">
  <div class="about">
    <div>
      <h2>Über uns</h2>
      <p>Seit über 20 Jahren sind wir Ihr verlässlicher Partner für alle Aufgaben rund um Allgemein. Als inhabergeführter Fachbetrieb legen wir größten Wert auf handwerkliche Qualität und persönlichen Service.</p>
      <br><p>Unser Team aus zertifizierten Fachkräften steht Ihnen für Beratung, Planung und Ausführung zur Verfügung – von der kleinen Reparatur bis zum Großprojekt.</p>
    </div>
    <div class="about-img">⚒️</div>
  </div>
</section>
<section class="contact" id="kontakt">
  <h2>Kontakt aufnehmen</h2>
  <p>📞 Tel: 0800 123 45 67</p>
  <p>📧 info@handwerkqualitaet.de</p>
  <p>📍 Musterstraße 1, 12345 Musterstadt</p>
  <br><p><strong>Mo–Fr: 7:00–18:00 Uhr | Notdienst: 24/7</strong></p>
</section>
<footer>© 2024 Handwerk Qualität – Alle Rechte vorbehalten</footer>
</body>
</html>`,
  }
];