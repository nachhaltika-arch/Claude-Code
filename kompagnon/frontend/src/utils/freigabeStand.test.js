import { istContentFreigegeben, istEntschieden, standJeSeite } from './freigabeStand';

/**
 * Zwei Fehler derselben Bauart, gefunden am 22.08.2026 — beide entstanden,
 * weil das Backend sein Format geändert hat und ein Leseort im Frontend
 * stehen blieb.
 *
 * Deshalb steht die Auswertung jetzt hier und nicht mehr zweimal inline:
 * `ProzessFlow.jsx` (Schrittfortschritt) und `customer/Freigaben.jsx`
 * (offen/erledigt) lasen dieselbe Spalte nach zwei verschiedenen Regeln,
 * und beide Regeln waren falsch.
 */

describe('istContentFreigegeben — Schritt „Content-Freigabe" in ProzessFlow', () => {
  test('das heutige Backend-Format zählt: ein Objekt mit status freigegeben', () => {
    // Arrange — genau das, was confirm_approval in content_freigaben schreibt
    const roh = JSON.stringify({
      startseite: { status: 'freigegeben', freigegeben_am: '22.08.2026 09:14' },
    });

    // Act & Assert
    expect(istContentFreigegeben(roh)).toBe(true);
  });

  test('der alte Wahrheitswert bleibt gültig — es gibt keine Migration', () => {
    expect(istContentFreigegeben(JSON.stringify({ startseite: true }))).toBe(true);
  });

  test('eine offene Anfrage ist keine Freigabe', () => {
    const roh = JSON.stringify({
      startseite: { status: 'angefragt', angefragt_am: '22.08.2026 09:00' },
    });

    expect(istContentFreigegeben(roh)).toBe(false);
  });

  test('eine Ablehnung ist keine Freigabe', () => {
    const roh = JSON.stringify({ startseite: { status: 'abgelehnt' } });

    expect(istContentFreigegeben(roh)).toBe(false);
  });

  test('eine von zwei Seiten genügt', () => {
    // Bewusst `some`, nicht `every` — das war die Regel vorher und bleibt es.
    // Ob fachlich alle angefragten Seiten nötig sind, ist eine eigene Frage.
    const roh = JSON.stringify({
      startseite: { status: 'freigegeben' },
      kontakt: { status: 'angefragt' },
    });

    expect(istContentFreigegeben(roh)).toBe(true);
  });

  test('das Objekt kommt auch ungeparst an — die Spalte ist mal Text, mal JSONB', () => {
    expect(istContentFreigegeben({ startseite: { status: 'freigegeben' } })).toBe(true);
  });

  test('leer, fehlend und kaputt sind alle „nicht freigegeben", nicht „Fehler"', () => {
    expect(istContentFreigegeben(null)).toBe(false);
    expect(istContentFreigegeben(undefined)).toBe(false);
    expect(istContentFreigegeben('')).toBe(false);
    expect(istContentFreigegeben('{}')).toBe(false);
    expect(istContentFreigegeben('{kein json')).toBe(false);
  });
});

describe('istEntschieden — offen/erledigt im Kundenportal', () => {
  test('freigegeben und abgelehnt sind entschieden', () => {
    expect(istEntschieden({ status: 'freigegeben' })).toBe(true);
    expect(istEntschieden({ status: 'abgelehnt' })).toBe(true);
  });

  test('angefragt ist offen — das war der Fehler', () => {
    // `Freigaben.jsx` filterte auf `status === 'ausstehend'`. Das Backend
    // schreibt aber „angefragt". Eine offene Anfrage landete dadurch unter
    // „bereits entschieden" und verschwand aus der Liste, die der Kunde
    // abarbeiten soll.
    expect(istEntschieden({ status: 'angefragt' })).toBe(false);
  });

  test('die alte Schreibweise „ausstehend" bleibt offen', () => {
    expect(istEntschieden({ status: 'ausstehend' })).toBe(false);
  });

  test('ohne Status ist nichts entschieden', () => {
    expect(istEntschieden({})).toBe(false);
    expect(istEntschieden(null)).toBe(false);
  });

  test('ein blosser Wahrheitswert aus der Altzeit gilt als freigegeben', () => {
    expect(istEntschieden(true)).toBe(true);
  });
});

describe('standJeSeite — der Freigaben-Reiter der Content-Werkstatt', () => {
  test('ohne Eintrag und ohne Inhalt: der Inhalt fehlt noch', () => {
    expect(standJeSeite(null, 'startseite', false)).toEqual(
      { zustand: 'ohne-inhalt', text: 'Content fehlt', anfragbar: false });
  });

  test('mit Inhalt, aber nie angefragt: anfragbar', () => {
    // Das war der Fehler bis zum 22.08.2026: Hier stand „Freigabe
    // ausstehend", obwohl niemand je gefragt hatte. Der Reiter zeigte einen
    // Zustand, den es nicht gab.
    expect(standJeSeite(null, 'startseite', true)).toEqual(
      { zustand: 'offen', text: 'Noch nicht angefragt', anfragbar: true });
  });

  test('angefragt: wartet auf den Kunden, nicht erneut anfragbar', () => {
    const roh = JSON.stringify({ startseite: { status: 'angefragt', angefragt_am: '22.08.2026 09:00' } });

    expect(standJeSeite(roh, 'startseite', true)).toEqual(
      { zustand: 'angefragt', text: 'Angefragt am 22.08.2026 09:00', anfragbar: false });
  });

  test('freigegeben', () => {
    const roh = JSON.stringify({ startseite: { status: 'freigegeben', freigegeben_am: '22.08.2026 11:30' } });

    expect(standJeSeite(roh, 'startseite', true)).toEqual(
      { zustand: 'freigegeben', text: 'Freigegeben am 22.08.2026 11:30', anfragbar: false });
  });

  test('abgelehnt: darf erneut angefragt werden', () => {
    // Nach einer Ablehnung wird der Text überarbeitet und neu vorgelegt —
    // sonst endet der Ablauf in einer Sackgasse.
    const roh = JSON.stringify({ startseite: { status: 'abgelehnt' } });

    expect(standJeSeite(roh, 'startseite', true)).toEqual(
      { zustand: 'abgelehnt', text: 'Abgelehnt', anfragbar: true });
  });

  test('eine andere Seite bleibt unberührt', () => {
    const roh = JSON.stringify({ kontakt: { status: 'freigegeben' } });

    expect(standJeSeite(roh, 'startseite', true).zustand).toBe('offen');
  });
});
