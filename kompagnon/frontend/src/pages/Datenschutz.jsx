import React from 'react';
import { Link } from 'react-router-dom';

export default function Datenschutz() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-kompagnon-900 text-white py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div onClick={() => window.history.back()} className="text-kompagnon-300 text-sm cursor-pointer hover:text-white mb-4 flex items-center gap-2">
            ← Zurück
          </div>
          <h1 className="text-3xl font-extrabold">Datenschutzerklärung</h1>
          <p className="text-kompagnon-300 mt-2 text-sm">Gemäß DSGVO / BDSG</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="card card-body space-y-8">

          <S title="1. Datenschutz auf einen Blick">
            <p className="font-medium text-slate-700">Allgemeine Hinweise</p>
            <p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.</p>
            <p className="font-medium text-slate-700 mt-3">Datenerfassung auf dieser Website</p>
            <p><span className="font-medium">Wer ist verantwortlich?</span> Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten können Sie dem Abschnitt „Hinweis zur Verantwortlichen Stelle" entnehmen.</p>
            <p className="mt-2"><span className="font-medium">Wie erfassen wir Ihre Daten?</span> Ihre Daten werden zum einen dadurch erhoben, dass Sie uns diese mitteilen (z. B. Kontaktformular). Andere Daten werden automatisch beim Besuch der Website durch unsere IT-Systeme erfasst (z. B. Internetbrowser, Betriebssystem, Uhrzeit des Seitenaufrufs).</p>
            <p className="mt-2"><span className="font-medium">Welche Rechte haben Sie?</span> Sie haben jederzeit das Recht, unentgeltlich Auskunft über Herkunft, Empfänger und Zweck Ihrer gespeicherten personenbezogenen Daten zu erhalten. Sie haben außerdem ein Recht auf Berichtigung oder Löschung dieser Daten sowie das Recht auf Einschränkung der Verarbeitung und ein Beschwerderecht bei der zuständigen Aufsichtsbehörde.</p>
          </S>

          <S title="2. Hosting und Content Delivery Networks (CDN)">
            <p className="font-medium text-slate-700">Externes Hosting</p>
            <p>Diese Website wird bei einem externen Dienstleister gehostet. Die personenbezogenen Daten, die auf dieser Website erfasst werden, werden auf den Servern des Hosters gespeichert (u. a. IP-Adressen, Kontaktanfragen, Meta- und Kommunikationsdaten).</p>
            <p className="mt-2">Der Einsatz des Hosters erfolgt zum Zwecke der Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO) und im Interesse einer sicheren, schnellen und effizienten Bereitstellung unseres Online-Angebots (Art. 6 Abs. 1 lit. f DSGVO).</p>
            <p className="mt-3 font-medium text-slate-700">Wir setzen folgenden Hoster ein:</p>
            <p>Mittwald CM Service GmbH &amp; Co. KG</p>
            <p>Königsberger Straße 4–6, 32339 Espelkamp</p>
            <p>Telefon: +49-5772-293-100</p>
            <p>Web: <a href="https://www.mittwald.de/datenschutz" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">www.mittwald.de/datenschutz</a></p>
            <p className="mt-2">Wir haben einen Vertrag über Auftragsverarbeitung mit unserem Hoster geschlossen.</p>
          </S>

          <S title="3. Allgemeine Hinweise und Pflichtinformationen">
            <p className="font-medium text-slate-700">Datenschutz</p>
            <p>Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre personenbezogenen Daten vertraulich und entsprechend der gesetzlichen Datenschutzvorschriften sowie dieser Datenschutzerklärung.</p>
            <p className="mt-3 font-medium text-slate-700">Hinweis zur verantwortlichen Stelle</p>
            <p>KOMPAGNON communications BP GmbH</p>
            <p>Marienfelder Straße 52, 56070 Koblenz</p>
            <p>Telefon: +49-261-88447-0</p>
            <p>E-Mail: <a href="mailto:info@kompagnon.eu" className="text-kompagnon-600 hover:underline">info@kompagnon.eu</a></p>
            <p className="mt-3 font-medium text-slate-700">Speicherdauer</p>
            <p>Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer genannt wurde, verbleiben Ihre personenbezogenen Daten bei uns, bis der Zweck für die Datenverarbeitung entfällt.</p>
            <p className="mt-3 font-medium text-slate-700">Gesetzlich vorgeschriebener Datenschutzbeauftragter</p>
            <p>defensIT UG (haftungsbeschränkt) · Hr. Björn Viohl</p>
            <p>Frankenstrasse 2, 56068 Koblenz</p>
            <p>Telefon: +49(0)261 9888 964-14</p>
            <p>E-Mail: <a href="mailto:Bjoern.Viohl@defensIT.de" className="text-kompagnon-600 hover:underline">Bjoern.Viohl@defensIT.de</a></p>
            <p>Web: <a href="https://www.defensIT.de" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">www.defensIT.de</a></p>
            <p className="mt-3 font-medium text-slate-700">Hinweis zur Datenweitergabe in die USA</p>
            <p>Auf unserer Website sind unter anderem Tools von Unternehmen mit Sitz in den USA eingebunden. Wenn diese Tools aktiv sind, können Ihre personenbezogenen Daten an die US-Server der jeweiligen Unternehmen weitergegeben werden. Wir weisen darauf hin, dass die USA kein sicherer Drittstaat im Sinne des EU-Datenschutzrechts sind.</p>
            <p className="mt-3 font-medium text-slate-700">SSL- bzw. TLS-Verschlüsselung</p>
            <p>Diese Seite nutzt aus Sicherheitsgründen eine SSL- bzw. TLS-Verschlüsselung. Eine verschlüsselte Verbindung erkennen Sie daran, dass die Adresszeile des Browsers von „http://" auf „https://" wechselt.</p>
            <p className="mt-3 font-medium text-slate-700">Recht auf Datenübertragbarkeit</p>
            <p>Sie haben das Recht, Daten, die wir auf Grundlage Ihrer Einwilligung oder in Erfüllung eines Vertrags automatisiert verarbeiten, an sich oder an einen Dritten in einem gängigen, maschinenlesbaren Format aushändigen zu lassen.</p>
            <p className="mt-3 font-medium text-slate-700 uppercase text-xs tracking-wider">Widerspruchsrecht (Art. 21 DSGVO)</p>
            <p className="uppercase text-xs">WENN DIE DATENVERARBEITUNG AUF GRUNDLAGE VON ART. 6 ABS. 1 LIT. E ODER F DSGVO ERFOLGT, HABEN SIE JEDERZEIT DAS RECHT, AUS GRÜNDEN, DIE SICH AUS IHRER BESONDEREN SITUATION ERGEBEN, GEGEN DIE VERARBEITUNG IHRER PERSONENBEZOGENEN DATEN WIDERSPRUCH EINZULEGEN.</p>
            <p className="mt-3 font-medium text-slate-700">Widerspruch gegen Werbe-E-Mails</p>
            <p>Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten zur Übersendung von nicht ausdrücklich angeforderter Werbung wird hiermit widersprochen.</p>
          </S>

          <S title="4. Datenerfassung auf dieser Website">
            <p className="font-medium text-slate-700">Cookies</p>
            <p>Unsere Internetseiten verwenden so genannte „Cookies". Cookies sind kleine Textdateien und richten auf Ihrem Endgerät keinen Schaden an. Sie werden entweder vorübergehend für die Dauer einer Sitzung (Session-Cookies) oder dauerhaft (permanente Cookies) gespeichert.</p>
            <p className="mt-2">Sie können Ihren Browser so einstellen, dass Sie über das Setzen von Cookies informiert werden und Cookies nur im Einzelfall erlauben oder generell ausschließen. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO bzw. Art. 6 Abs. 1 lit. a DSGVO bei Einwilligung.</p>
            <p className="mt-3 font-medium text-slate-700">Server-Log-Dateien</p>
            <p>Der Provider der Seiten erhebt und speichert automatisch Informationen in Server-Log-Dateien:</p>
            <ul className="list-disc pl-5 mt-1 space-y-1">
              <li>Browsertyp und Browserversion</li>
              <li>verwendetes Betriebssystem</li>
              <li>Referrer URL</li>
              <li>Hostname des zugreifenden Rechners</li>
              <li>Uhrzeit der Serveranfrage</li>
              <li>IP-Adresse</li>
            </ul>
            <p className="mt-2">Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.</p>
            <p className="mt-3 font-medium text-slate-700">Kontaktformular</p>
            <p>Wenn Sie uns per Kontaktformular Anfragen zukommen lassen, werden Ihre Angaben inklusive der von Ihnen dort angegebenen Kontaktdaten zwecks Bearbeitung der Anfrage bei uns gespeichert. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO bzw. Art. 6 Abs. 1 lit. f DSGVO.</p>
            <p className="mt-3 font-medium text-slate-700">Anfrage per E-Mail, Telefon oder Telefax</p>
            <p>Wenn Sie uns per E-Mail, Telefon oder Telefax kontaktieren, wird Ihre Anfrage inklusive aller daraus hervorgehenden personenbezogenen Daten zum Zwecke der Bearbeitung bei uns gespeichert. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO bzw. Art. 6 Abs. 1 lit. f DSGVO.</p>
          </S>

          <S title="5. Analyse-Tools und Werbung">
            <p className="font-medium text-slate-700">Google Analytics</p>
            <p>Diese Website nutzt Funktionen des Webanalysedienstes Google Analytics. Anbieter: Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland.</p>
            <p className="mt-2">Google Analytics ermöglicht es dem Websitebetreiber, das Verhalten der Websitebesucher zu analysieren (Seitenaufrufe, Verweildauer, verwendete Betriebssysteme, Herkunft). Die von Google erfassten Informationen werden in der Regel an einen Server in den USA übertragen und dort gespeichert.</p>
            <p className="mt-2">Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Analyse des Nutzerverhaltens) bzw. Art. 6 Abs. 1 lit. a DSGVO bei Einwilligung.</p>
            <p className="mt-2">Die Datenübertragung in die USA wird auf die Standardvertragsklauseln der EU-Kommission gestützt. Details: <a href="https://privacy.google.com/businesses/controllerterms/mccs/" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">privacy.google.com/businesses/controllerterms/mccs/</a></p>
            <p className="mt-2 font-medium text-slate-700">IP-Anonymisierung</p>
            <p>Wir haben auf dieser Website die Funktion IP-Anonymisierung aktiviert. Dadurch wird Ihre IP-Adresse von Google innerhalb von Mitgliedstaaten der EU vor der Übermittlung in die USA gekürzt.</p>
            <p className="mt-2 font-medium text-slate-700">Browser Plugin</p>
            <p>Sie können die Erfassung Ihrer Daten durch Google verhindern durch Download des Browser-Plugins unter: <a href="https://tools.google.com/dlpage/gaoptout?hl=de" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">tools.google.com/dlpage/gaoptout</a></p>
            <p className="mt-2">Mehr Informationen: <a href="https://support.google.com/analytics/answer/6004245?hl=de" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">support.google.com/analytics/answer/6004245</a></p>
            <p className="mt-2 font-medium text-slate-700">Speicherdauer</p>
            <p>Bei Google gespeicherte Daten auf Nutzer- und Ereignisebene werden nach 14 Monaten anonymisiert bzw. gelöscht. Details: <a href="https://support.google.com/analytics/answer/7667196?hl=de" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">support.google.com/analytics/answer/7667196</a></p>
          </S>

          <S title="6. Plugins und Tools">
            <p className="font-medium text-slate-700">Google Web Fonts</p>
            <p>Diese Seite nutzt zur einheitlichen Darstellung von Schriftarten Web Fonts von Google. Beim Aufruf einer Seite lädt Ihr Browser die benötigten Web Fonts in den Browsercache. Zu diesem Zweck muss Ihr Browser Verbindung zu den Servern von Google aufnehmen. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.</p>
            <p className="mt-2">Weitere Informationen: <a href="https://developers.google.com/fonts/faq" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">developers.google.com/fonts/faq</a></p>
            <p className="mt-3 font-medium text-slate-700">Google Maps</p>
            <p>Diese Seite nutzt den Kartendienst Google Maps. Anbieter: Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland. Zur Nutzung der Funktionen von Google Maps ist es notwendig, Ihre IP-Adresse zu speichern. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO.</p>
            <p className="mt-2">Mehr Informationen: <a href="https://policies.google.com/privacy?hl=de" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">policies.google.com/privacy</a></p>
          </S>

          <S title="7. Eigene Dienste">
            <p className="font-medium text-slate-700">Umgang mit Bewerberdaten</p>
            <p>Wir bieten Ihnen die Möglichkeit, sich bei uns zu bewerben (z. B. per E-Mail, postalisch oder via Online-Bewerberformular). Wir verarbeiten Ihre personenbezogenen Daten (Kontakt- und Kommunikationsdaten, Bewerbungsunterlagen, Notizen im Rahmen von Bewerbungsgesprächen), soweit dies zur Entscheidung über die Begründung eines Beschäftigungsverhältnisses erforderlich ist. Rechtsgrundlage: § 26 BDSG-neu, Art. 6 Abs. 1 lit. b DSGVO.</p>
            <p className="mt-2">Sofern wir Ihnen kein Stellenangebot machen können, behalten wir uns das Recht vor, die von Ihnen übermittelten Daten bis zu 6 Monate nach Beendigung des Bewerbungsverfahrens aufzubewahren. Anschließend werden die Daten gelöscht.</p>
            <p className="mt-3 font-medium text-slate-700">Leadinfo</p>
            <p>Wir nutzen den Lead-Generation-Service von Leadinfo B.V., Rotterdam, Niederlande. Dieser erkennt Besuche von Unternehmen auf unserer Website anhand von IP-Adressen und zeigt uns hierzu öffentlich verfügbare Informationen (z. B. Firmennamen oder Adressen). Darüber hinaus setzt Leadinfo zwei First-Party-Cookies zur Auswertung des Nutzerverhaltens ein.</p>
            <p className="mt-2">Weitere Informationen und Opt-out: <a href="https://www.leadinfo.com/en/opt-out" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">www.leadinfo.com/en/opt-out</a></p>
          </S>

          <div className="pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-400">Stand: 2026</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 py-6 mt-8">
        <div className="max-w-3xl mx-auto px-6 flex justify-between items-center text-xs text-slate-400">
          <span>© 2026 KOMPAGNON communications BP GmbH</span>
          <div className="flex gap-4">
            <Link to="/impressum" className="hover:text-slate-600">Impressum</Link>
            <Link to="/datenschutz" className="hover:text-slate-600">Datenschutz</Link>
            <Link to="/barrierefreiheit" className="hover:text-slate-600">Barrierefreiheit</Link>
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
      <div className="text-slate-600 space-y-2 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
