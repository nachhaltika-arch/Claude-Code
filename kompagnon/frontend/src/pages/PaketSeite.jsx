import { useParams, Navigate } from 'react-router-dom';

import PackageStarter from './PackageStarter';
import PackageKompagnon from './PackageKompagnon';
import PackagePremium from './PackagePremium';

/**
 * Die Weiche hinter `/paket/:slug`.
 *
 * Lücke L-64: Diese Adresse stand in `public_pages` als **live**, im Router
 * gab es sie nicht, und die Auffangroute schickte jeden Aufruf auf `/login` —
 * auch den Bestelllink, den der Innendienst aus der Angebotsmail kopiert.
 *
 * Für drei Pakete gibt es eine gebaute Seite. Ein Produkt kann aber jeden
 * Slug tragen (`ProductEditor` zeigt „URL: /paket/…" beim Anlegen), und für
 * die gibt es keine. **Statt eines Fehlers führt der Weg dann direkt zur
 * Kasse** — die kommt mit jedem Produkt zurecht, das auf `live` steht.
 * Lieber ohne Werbeseite bestellen können als gar nicht.
 */
const SEITEN = {
  starter: PackageStarter,
  kompagnon: PackageKompagnon,
  premium: PackagePremium,
};

export default function PaketSeite() {
  const { slug } = useParams();
  const Seite = SEITEN[slug];

  if (Seite) return <Seite />;
  return <Navigate to={`/checkout/${slug}`} replace />;
}
