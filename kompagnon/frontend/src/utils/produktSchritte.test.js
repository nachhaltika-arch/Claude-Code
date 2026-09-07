import { SCHRITTE } from '../components/KASSidebar';
import {
  NICHT_IM_PRODUKT, giltFuerProdukt, schritteFuerProdukt,
} from './produktSchritte';

describe('Die Schrittkette richtet sich nach dem Produkt', () => {
  test('Websprint Start zeigt keine Sitemap und keine drei Entwürfe', () => {
    // A16 und A19 — der Fall, an dem L-168 aufgefallen ist.
    expect(giltFuerProdukt('sitemap-ki', 'websprint_start')).toBe(false);
    expect(giltFuerProdukt('entwuerfe', 'websprint_start')).toBe(false);
  });

  test('was Start behält, ist genau das, was der Vertrag nennt', () => {
    const uebrig = schritteFuerProdukt(SCHRITTE, 'websprint_start').map((s) => s.id);
    // Aufbau, Technik, Abnahme — Phase 2 bis 5 des Datenblatts.
    ['briefing-unternehmen', 'audit', 'finales-design', 'netlify-deploy',
      'dns', 'qa', 'abnahme'].forEach((id) => expect(uebrig).toContain(id));
    expect(uebrig.length).toBe(SCHRITTE.length - NICHT_IM_PRODUKT.websprint_start.length);
  });

  test('ein unbekanntes Paket schließt nichts aus', () => {
    // Der Fehler fällt in die sichtbare Richtung: lieber ein Schritt zu viel.
    expect(schritteFuerProdukt(SCHRITTE, 'gibt_es_nicht')).toHaveLength(SCHRITTE.length);
    expect(schritteFuerProdukt(SCHRITTE, null)).toHaveLength(SCHRITTE.length);
    expect(schritteFuerProdukt(SCHRITTE, '')).toHaveLength(SCHRITTE.length);
  });

  test('jeder ausgeschlossene Schritt existiert überhaupt', () => {
    // Ein Ausschluss auf eine Kennung, die es nicht gibt, wirkt nie — und
    // wäre still. Genau die Bauart, an der schon `scrape_full_at` scheiterte.
    const bekannt = new Set(SCHRITTE.map((s) => s.id));
    Object.entries(NICHT_IM_PRODUKT).forEach(([produkt, ids]) => {
      ids.forEach((id) => expect([produkt, id, bekannt.has(id)]).toEqual([produkt, id, true]));
    });
  });

  test('jedes Bauprodukt hat einen Eintrag — auch einen leeren', () => {
    // Ein neues Produkt soll eine Entscheidung erzwingen, nicht still die
    // ganze Kette erben.
    ['websprint_start', 'websprint_relaunch', 'websprint_neubau',
      'websprint_system'].forEach((p) => {
      expect(Array.isArray(NICHT_IM_PRODUKT[p])).toBe(true);
    });
  });
});
