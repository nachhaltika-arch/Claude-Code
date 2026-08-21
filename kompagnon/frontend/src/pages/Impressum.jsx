import React from 'react';
import { Link } from 'react-router-dom';
import { aufTaste } from '../utils/tastaturBedienung';

export default function Impressum() {
  return (
    <div className="min-h-screen kc-legal">
      {/* Header */}
      <div className="kc-legal__band py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div role="button" tabIndex={0} onKeyDown={aufTaste(() => window.history.back())} onClick={() => window.history.back()} className="kc-legal__band-leise text-sm cursor-pointer hover:opacity-100 mb-4 flex items-center gap-2">
            ← Zurück
          </div>
          <h1 className="text-3xl font-extrabold">Impressum</h1>
          <p className="kc-legal__band-leise mt-2 text-sm">Angaben gemäß DDG</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="kc-legal__karte p-6 space-y-8">

          <Section title="Unternehmen">
            <p className="font-semibold kc-legal__stark">KOMPAGNON communications BP GmbH</p>
            <p>Marienfelder Straße 52</p>
            <p>56070 Koblenz</p>
            <p>Deutschland</p>
          </Section>

          <Section title="Kontakt">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="kc-legal__link">Tel:</span>
                <a href="tel:+4926188447-0" className="kc-legal__link hover:underline">+49-261-88447-0</a>
              </div>
              <div className="flex items-center gap-3">
                <span className="kc-legal__link">Fax:</span>
                <span>+49-261-88447-70</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="kc-legal__link">E-Mail:</span>
                <a href="mailto:info@kompagnon.eu" className="kc-legal__link hover:underline">info@kompagnon.eu</a>
              </div>
            </div>
          </Section>

          <Section title="Meetingroom (nach Terminvereinbarung)">
            <p>Koblenz Zentrum, im Confluentis Business Center</p>
            <p>Josef-Görres-Platz 2</p>
            <p>56068 Koblenz</p>
          </Section>

          <Section title="Vertreten durch">
            <p>Manuel Potter</p>
          </Section>

          <Section title="Handelsregister">
            <p><span className="font-medium kc-legal__text">Registergericht:</span> Amtsgericht Koblenz</p>
            <p><span className="font-medium kc-legal__text">Registernummer:</span> HRB 26213</p>
          </Section>

          <Section title="Umsatzsteuer-ID">
            <p>
              Umsatzsteuer-Identifikationsnummer gemäß § 27a Umsatzsteuergesetz:
              <span className="font-medium kc-legal__stark ml-1">DE317883455</span>
            </p>
          </Section>

          <Section title="D-U-N-S® Nummer">
            <p>315046814</p>
          </Section>

          <Section title="Redaktionell Verantwortlicher">
            <p className="font-semibold kc-legal__stark">KOMPAGNON communications BP GmbH</p>
            <p>Manuel Potter</p>
            <p>Marienfelder Straße 52</p>
            <p>56070 Koblenz</p>
          </Section>

          <Section title="EU-Streitschlichtung">
            <p>
              Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{' '}
              <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="kc-legal__link hover:underline">
                ec.europa.eu/consumers/odr
              </a>
              . Unsere E-Mail-Adresse finden Sie oben im Impressum.
            </p>
          </Section>

          <Section title="Verbraucherstreitbeilegung / Universalschlichtungsstelle">
            <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
          </Section>

          <Section title="Haftung für Inhalte">
            <p>
              Als Diensteanbieter sind wir gemäß § 7 Abs. 1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich.
              Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen
              oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.
            </p>
            <p>
              Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt.
              Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich.
              Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.
            </p>
          </Section>

          <Section title="Haftung für Links">
            <p>
              Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben.
              Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten
              ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt
              der Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar.
            </p>
            <p>
              Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung
              nicht zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.
            </p>
          </Section>

          <Section title="Urheberrecht">
            <p>
              Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht.
              Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes
              bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind
              nur für den privaten, nicht kommerziellen Gebrauch gestattet.
            </p>
            <p>
              Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet.
              Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung
              aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir
              derartige Inhalte umgehend entfernen.
            </p>
          </Section>

          <Section title="Weitere Büroadresse">
            <p>
              Wir sind ebenfalls erreichbar im Herzen der Stadt Koblenz, am Görresplatz 2 im CBC Confluentis Business Center.
              Für Termine vor Ort bitten wir um vorherige Ankündigung, um Sie dort zu empfangen.
            </p>
          </Section>

          <div className="pt-4 border-t kc-legal__linie">
            <p className="text-xs kc-legal__leise">Stand: 2026</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t kc-legal__linie py-6 mt-8">
        <div className="max-w-3xl mx-auto px-6 flex justify-between items-center text-xs kc-legal__leise">
          <span>© 2026 KOMPAGNON communications BP GmbH</span>
          <div className="flex gap-4">
            <Link to="/impressum" className="hover:opacity-70">Impressum</Link>
            <Link to="/datenschutz" className="hover:opacity-70">Datenschutz</Link>
            <Link to="/barrierefreiheit" className="hover:opacity-70">Barrierefreiheit</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h2 className="text-lg font-bold kc-legal__stark mb-3 pb-2 border-b kc-legal__linie">{title}</h2>
      <div className="kc-legal__text space-y-2 text-sm leading-relaxed">{children}</div>
    </section>
  );
}
