import React from 'react';
import { Link } from 'react-router-dom';

export default function Impressum() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-kompagnon-900 text-white py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div onClick={() => window.history.back()} className="text-kompagnon-300 text-sm cursor-pointer hover:text-white mb-4 flex items-center gap-2">
            ← Zurueck
          </div>
          <h1 className="text-3xl font-extrabold">Impressum</h1>
          <p className="text-kompagnon-300 mt-2 text-sm">Angaben gemaess Paragraph 5 TMG</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="card card-body space-y-8">

          <Section title="Unternehmen">
            <p className="font-semibold text-slate-900">KOMPAGNON</p>
            <p>[Strasse und Hausnummer]</p>
            <p>[PLZ] [Stadt]</p>
            <p>Deutschland</p>
          </Section>

          <Section title="Kontakt">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-kompagnon-500">Tel:</span>
                <span>[Telefonnummer]</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-kompagnon-500">E-Mail:</span>
                <a href="mailto:info@kompagnon.de" className="text-kompagnon-600 hover:underline">info@kompagnon.de</a>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-kompagnon-500">Web:</span>
                <a href="https://kompagnon.de" className="text-kompagnon-600 hover:underline">www.kompagnon.de</a>
              </div>
            </div>
          </Section>

          <Section title="Vertreten durch">
            <p>[Vor- und Nachname des Geschaeftsfuehrers]</p>
          </Section>

          <Section title="Handelsregister">
            <p><span className="font-medium text-slate-700">Registergericht:</span> [Amtsgericht Stadt]</p>
            <p><span className="font-medium text-slate-700">Registernummer:</span> [HRB XXXXX]</p>
          </Section>

          <Section title="Umsatzsteuer-ID">
            <p>
              Umsatzsteuer-Identifikationsnummer gemaess Paragraph 27a Umsatzsteuergesetz:
              <span className="font-medium text-slate-800 ml-1">DE [XXXXXXXXX]</span>
            </p>
          </Section>

          <Section title="Verantwortlich fuer den Inhalt nach Paragraph 55 Abs. 2 RStV">
            <p>[Vor- und Nachname]</p>
            <p>[Strasse und Hausnummer]</p>
            <p>[PLZ] [Stadt]</p>
          </Section>

          <Section title="Streitschlichtung">
            <p>
              Die Europaeische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{' '}
              <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer" className="text-kompagnon-600 hover:underline">
                https://ec.europa.eu/consumers/odr/
              </a>
            </p>
            <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
          </Section>

          <Section title="Haftung fuer Inhalte">
            <p>
              Als Diensteanbieter sind wir gemaess Paragraph 7 Abs. 1 TMG fuer eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich.
              Nach Paragraphen 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, uebermittelte oder gespeicherte fremde Informationen zu ueberwachen
              oder nach Umstaenden zu forschen, die auf eine rechtswidrige Taetigkeit hinweisen.
            </p>
          </Section>

          <Section title="Urheberrecht">
            <p>
              Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht.
              Die Vervielfaeltigung, Bearbeitung, Verbreitung und jede Art der Verwertung ausserhalb der Grenzen des Urheberrechtes
              beduerfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
            </p>
          </Section>

          <div className="pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-400">Stand: Maerz 2026</p>
          </div>
        </div>

        <div className="alert-warning mt-6 rounded-xl">
          <span>Hinweis: </span>
          <p className="text-xs">
            Bitte ersetzen Sie alle Platzhalter in eckigen Klammern [ ] mit Ihren echten Angaben.
            Ein unvollstaendiges Impressum kann zu Abmahnungen fuehren.
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

function Section({ title, children }) {
  return (
    <section>
      <h2 className="text-lg font-bold text-slate-900 mb-3 pb-2 border-b border-slate-100">{title}</h2>
      <div className="text-slate-600 space-y-1 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
