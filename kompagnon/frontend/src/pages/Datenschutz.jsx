import React from 'react';
import { Link } from 'react-router-dom';

export default function Datenschutz() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-kompagnon-900 text-white py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div onClick={() => window.history.back()} className="text-kompagnon-300 text-sm cursor-pointer hover:text-white mb-4 flex items-center gap-2">
            ← Zurueck
          </div>
          <h1 className="text-3xl font-extrabold">Datenschutzerklaerung</h1>
          <p className="text-kompagnon-300 mt-2 text-sm">Gemaess DSGVO / BDSG</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="card card-body space-y-8">

          <S title="1. Verantwortliche Stelle">
            <p>Verantwortlich fuer die Datenverarbeitung auf dieser Website:</p>
            <p className="font-semibold text-slate-900 mt-2">KOMPAGNON</p>
            <p>[Strasse und Hausnummer]</p>
            <p>[PLZ] [Stadt]</p>
            <p>E-Mail: info@kompagnon.de</p>
            <p>Telefon: [Telefonnummer]</p>
          </S>

          <S title="2. Erhebung und Speicherung personenbezogener Daten">
            <p>
              Beim Besuch unserer Website werden automatisch Informationen durch den Browser uebermittelt und in Server-Log-Dateien gespeichert.
              Diese Daten koennen keiner bestimmten Person zugeordnet werden und werden nicht mit anderen Datenquellen zusammengefuehrt.
            </p>
            <p className="mt-2">Folgende Daten werden erhoben:</p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li>IP-Adresse des anfragenden Rechners</li>
              <li>Datum und Uhrzeit des Zugriffs</li>
              <li>Name und URL der abgerufenen Datei</li>
              <li>Website, von der aus der Zugriff erfolgt (Referrer-URL)</li>
              <li>Verwendeter Browser und ggf. Betriebssystem</li>
              <li>Name des Access-Providers</li>
            </ul>
            <p className="mt-2">
              Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der technisch fehlerfreien Darstellung und Optimierung der Website).
            </p>
          </S>

          <S title="3. Cookies">
            <p>
              Unsere Website verwendet Cookies. Cookies sind kleine Textdateien, die auf Ihrem Endgeraet gespeichert werden.
              Einige Cookies sind technisch notwendig (Session-Cookies), andere dienen der Analyse Ihres Nutzerverhaltens (Analyse-Cookies).
            </p>
            <p className="mt-2 font-medium text-slate-700">Technisch notwendige Cookies:</p>
            <ul className="list-disc pl-5 mt-1 space-y-1">
              <li>Session-Cookie fuer die Anmeldung (JWT-Token)</li>
              <li>Cookie-Consent-Einstellungen</li>
            </ul>
            <p className="mt-2">
              Sie koennen Ihren Browser so einstellen, dass Sie ueber das Setzen von Cookies informiert werden und diese einzeln erlauben oder ablehnen.
            </p>
            <p className="mt-2">Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (technisch notwendig) bzw. Art. 6 Abs. 1 lit. a DSGVO (Einwilligung fuer Analyse-Cookies).</p>
          </S>

          <S title="4. Kontaktformular und Audit-Tool">
            <p>
              Wenn Sie unser Kontaktformular, Checkout-Formular oder das Website-Audit-Tool nutzen, werden die von Ihnen eingegebenen Daten
              (z.B. Name, E-Mail, Telefon, Website-URL, Firmenname) zum Zweck der Bearbeitung Ihrer Anfrage bei uns gespeichert.
            </p>
            <p className="mt-2">
              Die Daten werden nicht ohne Ihre Einwilligung an Dritte weitergegeben.
              Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (Vertragsdurchfuehrung bzw. vorvertragliche Massnahmen).
            </p>
          </S>

          <S title="5. Registrierung und Nutzerkonto">
            <p>
              Bei der Registrierung eines Nutzerkontos erheben wir: E-Mail-Adresse, Vor- und Nachname, optional Telefonnummer und Position.
              Passwoerter werden ausschliesslich als kryptographischer Hash (bcrypt) gespeichert — wir haben keinen Zugriff auf Ihr Klartext-Passwort.
            </p>
            <p className="mt-2">
              Bei Nutzung der Zwei-Faktor-Authentifizierung (2FA) wird ein TOTP-Geheimnis serverseitig verschluesselt gespeichert.
            </p>
            <p className="mt-2">Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO.</p>
          </S>

          <S title="6. Website-Audit und Analyse">
            <p>
              Beim Ausfuehren eines Website-Audits wird die eingegebene Website-URL analysiert. Dabei werden oeffentlich zugaengliche Informationen
              der Ziel-Website abgerufen (HTML, Meta-Tags, Performance-Daten via Google PageSpeed API).
            </p>
            <p className="mt-2">
              Die Analyseergebnisse werden in unserer Datenbank gespeichert und koennen als PDF-Bericht heruntergeladen werden.
              Eine KI-gestuetzte Auswertung erfolgt ueber die Claude API (Anthropic) — dabei werden keine personenbezogenen Daten an Anthropic uebermittelt,
              sondern nur technische Pruefergebnisse der Website.
            </p>
          </S>

          <S title="7. Einsatz von Drittanbietern">
            <p className="font-medium text-slate-700">Google PageSpeed Insights API</p>
            <p>Zur technischen Analyse von Websites nutzen wir die Google PageSpeed Insights API. Datenschutzerklaerung von Google: https://policies.google.com/privacy</p>
            <p className="font-medium text-slate-700 mt-3">Anthropic Claude API</p>
            <p>Fuer die KI-gestuetzte Bewertung nutzen wir die Claude API von Anthropic. Es werden keine personenbezogenen Daten uebermittelt.</p>
            <p className="font-medium text-slate-700 mt-3">Hosting</p>
            <p>Diese Website wird bei [Hosting-Anbieter, z.B. Render.com / Hetzner] gehostet. Der Hosting-Anbieter erhebt Server-Log-Dateien (siehe Punkt 2).</p>
          </S>

          <S title="8. SSL-Verschluesselung">
            <p>
              Diese Website nutzt aus Sicherheitsgruenden eine SSL- bzw. TLS-Verschluesselung. Eine verschluesselte Verbindung erkennen Sie an dem
              Schloss-Symbol in der Adresszeile Ihres Browsers und daran, dass die Adresszeile mit "https://" beginnt.
            </p>
          </S>

          <S title="9. Ihre Rechte als betroffene Person">
            <p>Sie haben gegenueber uns folgende Rechte:</p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li><span className="font-medium text-slate-700">Auskunftsrecht</span> (Art. 15 DSGVO) — Welche Daten wir ueber Sie gespeichert haben</li>
              <li><span className="font-medium text-slate-700">Berichtigungsrecht</span> (Art. 16 DSGVO) — Korrektur unrichtiger Daten</li>
              <li><span className="font-medium text-slate-700">Loeschungsrecht</span> (Art. 17 DSGVO) — Loeschung Ihrer Daten</li>
              <li><span className="font-medium text-slate-700">Einschraenkung der Verarbeitung</span> (Art. 18 DSGVO)</li>
              <li><span className="font-medium text-slate-700">Datenportabilitaet</span> (Art. 20 DSGVO) — Herausgabe Ihrer Daten in maschinenlesbarem Format</li>
              <li><span className="font-medium text-slate-700">Widerspruchsrecht</span> (Art. 21 DSGVO) — Widerspruch gegen die Verarbeitung</li>
            </ul>
            <p className="mt-2">Zur Ausuebung Ihrer Rechte wenden Sie sich bitte an: info@kompagnon.de</p>
          </S>

          <S title="10. Widerruf Ihrer Einwilligung">
            <p>
              Soweit die Verarbeitung auf Ihrer Einwilligung beruht (Art. 6 Abs. 1 lit. a DSGVO), koennen Sie diese jederzeit
              mit Wirkung fuer die Zukunft widerrufen. Die Rechtmaessigkeit der bis zum Widerruf erfolgten Datenverarbeitung bleibt davon unberuehrt.
            </p>
          </S>

          <S title="11. Beschwerderecht bei der Aufsichtsbehoerde">
            <p>
              Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehoerde ueber die Verarbeitung Ihrer personenbezogenen Daten zu beschweren.
              Die fuer uns zustaendige Aufsichtsbehoerde ist:
            </p>
            <p className="mt-2">[Name der Landesbehoerde]</p>
            <p>[Adresse der Behoerde]</p>
            <p>[Website der Behoerde]</p>
          </S>

          <S title="12. Aenderungen dieser Datenschutzerklaerung">
            <p>
              Wir behalten uns vor, diese Datenschutzerklaerung anzupassen, damit sie stets den aktuellen rechtlichen Anforderungen entspricht
              oder um Aenderungen unserer Leistungen umzusetzen. Fuer Ihren erneuten Besuch gilt dann die neue Datenschutzerklaerung.
            </p>
          </S>

          <div className="pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-400">Stand: Maerz 2026</p>
          </div>
        </div>

        <div className="alert-warning mt-6 rounded-xl">
          <span>Hinweis: </span>
          <p className="text-xs">
            Bitte ersetzen Sie alle Platzhalter in eckigen Klammern [ ] mit Ihren echten Angaben und passen Sie die Erklaerung
            an Ihre tatsaechlich eingesetzten Dienste und Verarbeitungsvorgaenge an. Diese Vorlage ersetzt keine Rechtsberatung.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 py-6 mt-8">
        <div className="max-w-3xl mx-auto px-6 flex justify-between items-center text-xs text-slate-400">
          <span>2026 KOMPAGNON</span>
          <div className="flex gap-4">
            <Link to="/impressum" className="hover:text-slate-600">Impressum</Link>
            <Link to="/datenschutz" className="hover:text-slate-600">Datenschutz</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function S({ title, children }) {
  return (
    <section>
      <h2 className="text-lg font-bold text-slate-900 mb-3 pb-2 border-b border-slate-100">{title}</h2>
      <div className="text-slate-600 space-y-1 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
