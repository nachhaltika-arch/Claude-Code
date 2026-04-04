import React from 'react';
import { Link } from 'react-router-dom';

export default function Barrierefreiheit() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-kompagnon-900 text-white py-12">
        <div className="max-w-3xl mx-auto px-6">
          <div onClick={() => window.history.back()} className="text-kompagnon-300 text-sm cursor-pointer hover:text-white mb-4 flex items-center gap-2">
            ← Zurück
          </div>
          <h1 className="text-3xl font-extrabold">Barrierefreiheitserklärung</h1>
          <p className="text-kompagnon-300 mt-2 text-sm">Gemäß Barrierefreiheitsstärkungsgesetz (BFSG)</p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="card card-body space-y-8">

          <S title="Angaben zum Dienstleistungserbringer">
            <p className="font-semibold text-slate-900">KOMPAGNON communications BP GmbH</p>
            <p>Marienfelder Straße 52</p>
            <p>56070 Koblenz</p>
          </S>

          <S title="Allgemeine Beschreibung der Dienstleistung">
            <p>
              Wir bieten Ihnen Service in den Bereichen Webdesign und Online-Shops und digitale Medien.
            </p>
          </S>

          <S title="Erläuterungen zur Durchführung der Dienstleistung">
            <p>
              Wir bieten Ihnen auf unserer Webseite Informationen in den Bereichen Webdesign und
              Online-Shops und digitale Medien.
            </p>
          </S>

          <S title="Stand der Vereinbarkeit mit den Anforderungen">
            <p>
              Die oben genannte Dienstleistung ist <strong>teilweise</strong> mit dem
              Barrierefreiheitsstärkungsgesetz (BFSG) vereinbar.
            </p>
            <p className="mt-3 font-medium text-slate-800">
              Folgende Teile/Inhalte/Funktionen der Dienstleistung sind nicht barrierefrei:
            </p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>Einige Kontrastverhältnisse sind nicht optimal.</li>
              <li>PDF-Dokumente sind nicht immer mit einem Screenreader bedienbar.</li>
              <li>Eine Tastaturbedienbarkeit ist nicht für alle Bereiche gewährleistet.</li>
            </ul>
          </S>

          <S title="Nicht barrierefreie Teile der Dienstleistung – Umsetzungsfristen">
            <p>
              Wir sind darum bemüht, Kontrastverhältnisse bis Ende 2026 optimal zu gestalten. Wir
              arbeiten daran, die Anmeldung zum Newsletter zeitnah barrierefrei anbieten zu können.
              Eine genaue Angabe können wir momentan nicht machen.
            </p>
          </S>

          <S title="Erstellung der Barrierefreiheitserklärung">
            <p>Datum der Erstellung der Barrierefreiheitserklärung: <strong>23.03.2026</strong></p>
            <p>
              Datum der letzten Überprüfung der o. g. Leistungen hinsichtlich der Anforderungen
              zur Barrierefreiheit: <strong>23.03.2026</strong>
            </p>
          </S>

          <S title="Einschätzung zum Stand der Barrierefreiheit">
            <p>
              Die Einschätzung zum Stand der Barrierefreiheit beruht auf unserer Selbsteinschätzung.
            </p>
          </S>

          <S title="Feedbackmöglichkeit und Kontaktangaben">
            <p className="font-semibold text-slate-900">KOMPAGNON communications BP GmbH</p>
            <p>Marienfelder Straße 52</p>
            <p>56070 Koblenz</p>
            <div className="space-y-1 mt-3">
              <p>
                E-Mail:{' '}
                <a href="mailto:info@kompagnon.eu" className="text-kompagnon-600 hover:underline">
                  info@kompagnon.eu
                </a>
              </p>
              <p>
                Telefon:{' '}
                <a href="tel:+4926188447700" className="text-kompagnon-600 hover:underline">
                  +49-261-88447-70
                </a>
              </p>
            </div>
          </S>

          <div className="pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-400">Stand: 23.03.2026</p>
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
