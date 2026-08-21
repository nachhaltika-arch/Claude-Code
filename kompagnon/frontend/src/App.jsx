import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { VersandProvider } from './context/VersandContext';

import Dashboard from './pages/Dashboard';
// Hiess LeadPipeline und zeigte Projekte — der Name im Code war
// derselbe Irrtum wie die Adresse.
import Projektpipeline from './pages/Projektpipeline';
import ProjectDetail from './pages/ProjectDetail';
import OnlineFertigEditor from './components/OnlineFertigEditor';
import Checklists from './pages/Checklists';
import ContactImport from './pages/ContactImport';
import MassExport from './pages/MassExport';
import Tickets from './pages/Tickets';
import CustomerProjects from './pages/CustomerProjects';
import ProductDevelopment from './pages/ProductDevelopment';
import FeedbackButton from './components/FeedbackButton';
import AuditTool from './pages/AuditTool';
import AkquiseWidget from './pages/AkquiseWidget';
import LeadProfile from './pages/LeadProfile';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AdminUsers from './pages/AdminUsers';
import TwoFactorSetup from './pages/TwoFactorSetup';
import Settings from './pages/Settings';
import ProductEditor from './pages/ProductEditor';
import RoleManagement from './pages/RoleManagement';
import SettingsLayout from './components/SettingsLayout';
import ResetPassword from './pages/ResetPassword';
import Academy from './pages/Academy';
import AcademyCourseNew from './pages/AcademyCourse';   // neue 2-Spalten-Version (.js)
import AcademyAdmin from './pages/AcademyAdmin';
import AcademyAdminCourse from './pages/AcademyAdminCourse';
import AcademyAdminLesson from './pages/AcademyAdminLesson';
import AcademyCertificate from './pages/AcademyCertificate';
import Betriebe from './pages/Betriebe';
import CustomerDashboard from './pages/CustomerDashboard';
import DomainImport from './pages/DomainImport';
import ScraperControl from './pages/ScraperControl';
import KasWebsite from './pages/KasWebsite';
import CustomerPortal from './pages/CustomerPortal';
import Checkout from './pages/Checkout';
import CheckoutSuccess from './pages/CheckoutSuccess';
import PaketSeite from './pages/PaketSeite';
import CustomerDetail from './pages/CustomerDetail';
import KundenPortal from './pages/KundenPortal';
import QRGenerator from './pages/QRGenerator';
import TemplateLibrary from './pages/TemplateLibrary';
import TemplateEditor from './pages/TemplateEditor';
import ComponentLibrary from './pages/ComponentLibrary';
import NewsletterDesigner from './components/NewsletterDesigner';
import Newsletter from './pages/Newsletter';
import PortalLogin from './pages/PortalLogin';
import Fehlerprotokoll from './pages/Fehlerprotokoll';
import Impressum from './pages/Impressum';
import Datenschutz from './pages/Datenschutz';
import Barrierefreiheit from './pages/Barrierefreiheit';
import WebhookDashboard from './pages/WebhookDashboard';
import RetainerDashboard from './pages/RetainerDashboard';
import SupportTickets from './pages/customer/SupportTickets';
import Freigaben from './pages/customer/Freigaben';
import MeineRechnungen from './pages/customer/MeineRechnungen';
import Deals from './pages/Deals';
import CampaignManager from './pages/CampaignManager';
import PageManager from './pages/PageManager';
import PublicPageEditor from './pages/PublicPageEditor';
import PageTemplateEditor from './pages/PageTemplateEditor';
import ContentApprovalPage from './pages/ContentApprovalPage';
import MobileVertrieb  from './pages/MobileVertrieb';

import AppLayout from './components/Layout/AppLayout';

// ── Route Guards ──

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/app/dashboard" replace />;
  return children;
}

/**
 * Alte Einzelansicht-Adresse `/app/leads/:leadId` auf die neue umlenken —
 * mitsamt Kennung. Ohne das würde ein geteilter Link auf die Liste fallen und
 * der Empfänger müsste den Betrieb wieder suchen.
 */
function LeadRedirect() {
  const { leadId } = useParams();
  return <Navigate to={`/app/betriebe/${leadId}`} replace />;
}

function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', color: 'var(--text-tertiary)' }}>
        Laden...
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  // Kunde role: redirect to own card if they try to access restricted pages
  if (user.role === 'kunde' && roles && !roles.includes('kunde')) {
    return <Navigate to={user.lead_id ? `/app/usercards/${user.lead_id}` : '/app/dashboard'} replace />;
  }
  if (roles) {
    // Superadmin inherits admin access — gets in anywhere admin does
    const effectiveRoles = roles.includes('admin') && !roles.includes('superadmin')
      ? [...roles, 'superadmin']
      : roles;
    if (!effectiveRoles.includes(user.role)) return <Navigate to="/app/dashboard" replace />;
  }
  return children;
}

// ── Dashboard: redirect Kunde to /app/usercards/:id, else regular Dashboard ──

function DashboardRoute() {
  const { user } = useAuth();
  if (user?.role === 'kunde') {
    if (user.lead_id) return <Navigate to={`/app/usercards/${user.lead_id}`} replace />;
    // Kunde without linked card
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', gap: 16, textAlign: 'center', padding: 24 }}>
        <div style={{ fontSize: 32 }}>📋</div>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kartei noch nicht verknüpft</h2>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', maxWidth: 400, margin: 0 }}>
          Ihre Kundenkartei wurde noch nicht verknüpft. Bitte kontaktieren Sie KOMPAGNON.
        </p>
        <a href="mailto:info@kompagnon.eu" style={{ background: 'var(--brand-primary)', color: 'var(--text-on-brand)', padding: '10px 24px', borderRadius: 'var(--radius-md)', textDecoration: 'none', fontSize: 14, fontWeight: 600 }}>
          Kontakt aufnehmen
        </a>
      </div>
    );
  }
  return <Dashboard />;
}

// ── Main App ──

/**
 * Lenkt jede alte `/app/akademie/…`-Adresse auf ihre Entsprechung in
 * `/app/academy/…`. Zwei Bildschirme haben keine: der zweite Kurseditor
 * (seine Felder erscheinen nirgends) und der alte Lektions-Spieler. Sie
 * landen beim nächstgelegenen Ziel, das es gibt.
 */
function AkademieUmleitung() {
  const { pathname, search } = useLocation();
  const rest = pathname.replace(/^\/app\/akademie/, '');

  const ziel = (() => {
    if (rest.startsWith('/admin/modul/')) return '/app/academy/admin';
    if (rest === '/admin/neu') return '/app/academy/admin/course/new';

    const kursEditor = rest.match(/^\/admin\/(\d+)$/);
    if (kursEditor) return `/app/academy/admin/course/${kursEditor[1]}`;

    const kurs = rest.match(/^\/kurs\/(\d+)$/);
    if (kurs) return `/app/academy/${kurs[1]}`;

    // Den alten Lektions-Spieler gibt es nicht mehr; der Kurs ist der Ort,
    // von dem aus man die Lektion ohnehin öffnet.
    if (rest.startsWith('/lektion/')) return '/app/academy';

    return `/app/academy${rest}`;
  })();

  return <Navigate to={ziel + search} replace />;
}

function App() {
  return (
    <Router>
      <AuthProvider>
       <VersandProvider>
        <Routes>
          {/* ── Auth-Seiten — kein Marketing mehr ── */}
          <Route path="/login"          element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register"       element={<PublicRoute><Register /></PublicRoute>} />
          <Route path="/reset-password" element={<PublicRoute><ResetPassword /></PublicRoute>} />

          {/* ── Kundenportal (bleibt auf Render) ── */}
          <Route path="/portal/login"  element={<PortalLogin />} />
          <Route path="/kundenportal"  element={<PortalLogin />} />

          {/* ── Rechtliches ──
            * Beide Seiten lagen seit jeher in `pages/`, hingen aber an keiner
            * Adresse: Es gab ein Impressum, zu dem kein Weg fuehrte. Der Fuss
            * des Kundenportals zeigte stattdessen auf `kompagnon.eu` — eine
            * dritte Domain neben der, auf der der Kunde gerade stand
            * (UX-19, 18.08.2026). */}
          <Route path="/impressum"        element={<Impressum />} />
          <Route path="/datenschutz"      element={<Datenschutz />} />
          <Route path="/barrierefreiheit" element={<Barrierefreiheit />} />
          <Route path="/portal/:token" element={<CustomerPortal />} />

          {/* ── Der Bestellweg ──────────────────────────────────────────────
            * Bis zum 21.08.2026 gab es diese vier Routen **nicht** (L-64).
            * `Checkout.jsx`, `CheckoutSuccess.jsx` und die drei Paketseiten
            * lagen im Quellbaum, wurden von nichts importiert und erreichten
            * nicht einmal das ausgelieferte Buendel. Wer auf „Paket waehlen"
            * klickte oder den Bestelllink aus der Angebotsmail oeffnete,
            * landete ueber die Auffangroute auf `/login` — und nach bezahlter
            * Rechnung ebenso, denn `create_checkout` schickt Stripe auf
            * `/checkout/success` zurueck.
            *
            * Oeffentlich und ohne Anmeldung: Wer kaufen will, hat noch kein
            * Konto. Das Konto entsteht erst beim Zahlungseingang
            * (`_handle_successful_payment`). */}
          <Route path="/paket/:slug"       element={<PaketSeite />} />
          <Route path="/checkout"          element={<Checkout />} />
          <Route path="/checkout/success"  element={<CheckoutSuccess />} />
          <Route path="/checkout/:package" element={<Checkout />} />

          {/* ── Funktionale Seiten (Token-basiert — müssen auf Render bleiben) ──
            * `/abnahme/:projectId` stand hier, war aber nicht token-basiert:
            * Die Seite trug keinen Nachweis und rief zwei Endpunkte auf, die
            * eine Anmeldung verlangen. Sie konnte nie funktionieren, und
            * verlinkt hat sie niemand — weder eine Mail noch eine andere
            * Seite. Entfernt am 17.08.2026. Die Abnahme wird im Innendienst
            * unter Projekt → Abnahme eingetragen. */}
          <Route path="/approve-content/:token"    element={<ContentApprovalPage />} />
          <Route path="/academy/certificate/:code" element={<AcademyCertificate />} />

          {/* ── Online-Fertig-Editor — jetzt Default für /app/projects/:id ──
            * Vollbild, eigene KASSidebar, ausserhalb des AppLayout.
            * /app/projects/:id              → Default (neu)
            * /app/projects/:id/online-fertig → Alias (alte URL, bleibt aktiv)
            * Der Legacy-ProzessFlowV3 ist auf /app/projects/:id/legacy
            * umgezogen (siehe AppLayout-Block weiter unten). */}
          <Route
            path="/app/projects/:id"
            element={
              <PrivateRoute roles={['admin', 'auditor']}>
                <OnlineFertigEditor />
              </PrivateRoute>
            }
          />
          <Route
            path="/app/projects/:id/online-fertig"
            element={
              <PrivateRoute roles={['admin', 'auditor']}>
                <OnlineFertigEditor />
              </PrivateRoute>
            }
          />

          {/* App — authenticated, with Navbar/Sidebar */}
          <Route path="/app" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardRoute />} />
            <Route path="usercards/:id" element={<PrivateRoute><CustomerDashboard /></PrivateRoute>} />
            {/* Vertriebspipeline durch Deals ersetzt — alte URL leitet weiter */}
            <Route path="sales" element={<Navigate to="/app/deals" replace />} />
            <Route path="deals" element={<PrivateRoute roles={['admin', 'auditor']}><Deals /></PrivateRoute>} />
            <Route path="campaigns" element={<PrivateRoute roles={['admin']}><CampaignManager /></PrivateRoute>} />
            <Route path="pages" element={<PrivateRoute roles={['admin']}><PageManager /></PrivateRoute>} />
            <Route path="pages/templates/:id/editor" element={<PrivateRoute roles={['admin']}><PageTemplateEditor /></PrivateRoute>} />
            <Route path="pages/:pageId/editor" element={<PrivateRoute roles={['admin']}><PublicPageEditor /></PrivateRoute>} />
            {/* Betriebe — das Objekt heisst seit 2026-08-16 ueberall so, auch
              * in der Adresszeile. Die alten Adressen leiten weiter: Es gibt
              * Lesezeichen, geteilte Links und Mails, die darauf zeigen. */}
            <Route path="betriebe" element={<PrivateRoute roles={['admin', 'auditor']}><Betriebe /></PrivateRoute>} />
            <Route path="betriebe/:leadId" element={<PrivateRoute roles={['admin', 'auditor']}><LeadProfile /></PrivateRoute>} />
            <Route path="companies" element={<Navigate to="/app/betriebe" replace />} />
            <Route path="widget" element={<PrivateRoute roles={['admin']}><AkquiseWidget /></PrivateRoute>} />
            {/* Die Projektpipeline lag unter /app/leads und zeigte Projekte.
              * Das Menue war richtig beschriftet, die Adresse nicht — was
              * genuegte, um bei der Pruefung am 16.08. einen Fehlbefund zu
              * erzeugen. Jetzt heisst die Adresse, was sie liefert. */}
            <Route path="projektpipeline" element={<PrivateRoute roles={['admin', 'auditor']}><Projektpipeline /></PrivateRoute>} />
            <Route path="leads" element={<Navigate to="/app/projektpipeline" replace />} />
            <Route path="leads/:leadId" element={<LeadRedirect />} />
            <Route path="projects" element={<PrivateRoute roles={['admin', 'auditor']}><CustomerProjects /></PrivateRoute>} />
            {/* Legacy ProzessFlowV3 (das alte Vollbild mit 12 Schritten) —
              * der frühere Default ist auf /legacy umgezogen, weil
              * /app/projects/:id jetzt den Online-Fertig-Editor zeigt. */}
            <Route path="projects/:id/legacy" element={<PrivateRoute roles={['admin', 'auditor']}><ProjectDetail /></PrivateRoute>} />
            <Route path="checklists" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            <Route path="checklists/:projectId" element={<PrivateRoute roles={['admin', 'auditor']}><Checklists /></PrivateRoute>} />
            {/* „Kunden" war der zweite Bildschirm mit denselben Firmen — bessere
              * Gestaltung, aber ohne Menueeintrag und mit nur 50 der 61
              * Betriebe, weil das `limit` fehlte. Zusammengelegt am 2026-08-17;
              * die Adresse leitet weiter, es gibt Lesezeichen darauf.
              * Die Einzelansicht `customers/:id` bleibt — sie zeigt etwas
              * anderes als die Liste. */}
            <Route path="customers" element={<Navigate to="/app/betriebe" replace />} />
            <Route path="customers/:customerId" element={<PrivateRoute roles={['admin']}><CustomerDetail /></PrivateRoute>} />
            <Route path="import" element={<PrivateRoute roles={['admin', 'auditor']}><DomainImport /></PrivateRoute>} />
            <Route path="scraper" element={<PrivateRoute roles={['admin']}><ScraperControl /></PrivateRoute>} />
            <Route path="export" element={<PrivateRoute roles={['admin', 'auditor']}><MassExport /></PrivateRoute>} />
            <Route path="audit" element={<PrivateRoute><AuditTool /></PrivateRoute>} />
            <Route path="profile" element={<Profile />} />
            <Route path="2fa-setup" element={<TwoFactorSetup />} />
            <Route path="admin/users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />
            <Route path="tickets" element={<PrivateRoute roles={['admin', 'auditor']}><Tickets /></PrivateRoute>} />
            <Route path="product" element={<PrivateRoute roles={['admin']}><ProductDevelopment /></PrivateRoute>} />
            <Route path="product-editor" element={<PrivateRoute roles={['admin']}><ProductEditor /></PrivateRoute>} />
            <Route path="qr-generator" element={<PrivateRoute roles={['admin']}><QRGenerator /></PrivateRoute>} />
            <Route path="webhooks" element={<PrivateRoute roles={['admin']}><WebhookDashboard /></PrivateRoute>} />
            <Route path="retainer" element={<PrivateRoute roles={['admin']}><RetainerDashboard /></PrivateRoute>} />
            {/* Hier stand `ProductManager`. Er war gegen eine **andere**
              * Produkt-Schnittstelle geschrieben: deutsche Feldnamen
              * (`beschreibung`, `preis_einmalig`, `ist_live`), die Kennung
              * statt des Slugs, und zwei Knoepfe auf Endpunkte, die es nicht
              * gibt (`stripe-connect`, `toggle-live`). Die Tabelle heisst
              * `short_desc`, `price_brutto`, `status` — jedes Feld war leer,
              * jedes Speichern wirkungslos.
              *
              * `ProductEditor` passt zur Schnittstelle, kennt den Slug und
              * ruft die echte Stripe-Synchronisierung auf — er hatte nur
              * keinen Menuepunkt. Der Menuepunkt „Pakete" fuehrt jetzt
              * dorthin (21.08.2026, M4). */}
            <Route path="products" element={<PrivateRoute roles={['admin']}><ProductEditor /></PrivateRoute>} />
            {/* `products/editor` war eine zweite Adresse für denselben
              * Bildschirm wie `product-editor` — von nirgends verlinkt.
              * Entfernt am 17.08.2026 (UX-17). Wer die Adresse kannte, kommt
              * über Einstellungen → Produkteditor an dieselbe Seite. */}
            <Route path="newsletter" element={<PrivateRoute><Newsletter /></PrivateRoute>} />
            <Route path="newsletter/editor/:id" element={<PrivateRoute><NewsletterDesigner /></PrivateRoute>} />
            {/* Academy — neue Routen */}
            <Route path="portal" element={<PrivateRoute roles={['kunde']}><KundenPortal /></PrivateRoute>} />
            <Route path="support" element={<PrivateRoute><SupportTickets /></PrivateRoute>} />
            <Route path="freigaben" element={<PrivateRoute><Freigaben /></PrivateRoute>} />
            <Route path="rechnungen" element={<PrivateRoute><MeineRechnungen /></PrivateRoute>} />
            <Route path="academy" element={<Academy />} />
            <Route path="academy/:id" element={<AcademyCourseNew />} />
            <Route path="academy/admin" element={<PrivateRoute roles={['admin']}><AcademyAdmin /></PrivateRoute>} />
            <Route path="academy/admin/course/new" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="academy/admin/course/:courseId" element={<PrivateRoute roles={['admin']}><AcademyAdminCourse /></PrivateRoute>} />
            <Route path="academy/admin/lesson/new" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            <Route path="academy/admin/lesson/:lessonId" element={<PrivateRoute roles={['admin']}><AcademyAdminLesson /></PrivateRoute>} />
            {/* Die Akademie hatte zwei Adressräume — und das waren keine
              * Aliasse: Hinter `akademie/admin/:id` lag ein anderer Kurseditor
              * als hinter `academy/admin/course/:id`, und der Modul-Editor war
              * nur über den alten Pfad erreichbar. Ein Klick auf „Bearbeiten"
              * wechselte den Raum, ohne dass man es sah (UX-42, 18.08.2026).
              *
              * Die alten Adressen bleiben gültig — als Weiterleitung, damit
              * Lesezeichen und alte Links nicht ins Leere laufen. */}
            <Route path="akademie/*" element={<AkademieUmleitung />} />

            {/* Mobile hub pages */}
            {/* `m-vertrieb` war eine zweite Adresse fuer denselben Bildschirm,
              * von nirgends verlinkt — entfernt am 18.08.2026. Die Mobilleiste
              * fuehrt auf `/app/vertrieb`. */}
            <Route path="vertrieb"    element={<PrivateRoute roles={['admin','auditor']}><MobileVertrieb /></PrivateRoute>} />
            {/* `m-leads`, `m-projekte` und `m-settings` standen hier, ohne dass
              * irgendetwas auf sie zeigte — und sie doppelten, was es schon
              * gibt: `/app/settings` rendert eine eigene Mobilansicht, die
              * uebrigen Ziele stehen direkt in der Mobilleiste. Entfernt am
              * 18.08.2026 (UX-43). */}

            {/* Settings with sub-navigation */}
            {/* Was der Server nicht verarbeiten konnte — L-10. */}
            <Route path="fehler" element={<PrivateRoute roles={['admin']}><Fehlerprotokoll /></PrivateRoute>} />

            <Route path="settings" element={<SettingsLayout />}>
              <Route index element={<Navigate to="/app/settings/profile" replace />} />
              <Route path="profile" element={<Settings tab="profile" />} />
              <Route path="security" element={<Settings tab="security" />} />
              <Route path="roles" element={<PrivateRoute roles={['admin']}><RoleManagement /></PrivateRoute>} />
              <Route path="users" element={<PrivateRoute roles={['admin']}><AdminUsers /></PrivateRoute>} />
              <Route path="system" element={<PrivateRoute roles={['admin']}><Settings tab="system" /></PrivateRoute>} />
              <Route path="kas-website" element={<PrivateRoute roles={['admin', 'superadmin']}><KasWebsite /></PrivateRoute>} />
              <Route path="notifications" element={<Settings tab="notifications" />} />
              <Route path="subscription" element={<PrivateRoute roles={['admin']}><Settings tab="subscription" /></PrivateRoute>} />
              <Route path="templates" element={<PrivateRoute roles={['admin']}><TemplateLibrary /></PrivateRoute>} />
              <Route path="component-library" element={<PrivateRoute roles={['admin']}><ComponentLibrary /></PrivateRoute>} />
            </Route>
            {/* Template Editor — fullscreen, outside settings layout */}
            <Route path="settings/templates/:id" element={<PrivateRoute roles={['admin']}><TemplateEditor /></PrivateRoute>} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
        <FeedbackButton />
        <Toaster
          position="top-right"
          gutter={8}
          toastOptions={{
            duration: 4000,
            style: {
              fontFamily: 'var(--font-sans)',
              fontSize: 12,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              borderRadius: 'var(--r-md)',
              maxWidth: 380,
              padding: '12px 14px',
              border: '0.5px solid',
            },
            success: {
              duration: 3000,
              style: {
                background: 'var(--success-bg)',
                color: 'var(--success)',
                borderColor: 'rgba(0,135,90,0.3)',
              },
              icon: '✓',
            },
            error: {
              duration: 6000,
              style: {
                background: 'var(--error-bg)',
                color: 'var(--error)',
                borderColor: 'rgba(192,57,43,0.3)',
              },
              icon: '✕',
            },
          }}
        />
       </VersandProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
