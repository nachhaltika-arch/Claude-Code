"""Die neun Seiten des Auditberichts — je eine Funktion.

Am 2026-08-30 aus `pdf_generator.py` herausgeloest (L-25). Dort standen sie
als **eine** Funktion mit 574 Zeilen, zwei Dritteln der Datei. Der Eintrag
hatte den Schnitt bewusst aufgeschoben, mit einem guten Grund: Die dreissig
vorhandenen Tests pruefen Bausteine, aber **ob das PDF danach noch gleich
aussieht, sagte keiner** — und der Bericht geht an Kunden.

Diese Gegenprobe steht seit dem 22.08.2026 (`tests/test_pdf_unveraendert.py`):
Sie haelt den Textinhalt in seiner Reihenfolge fest, abgegriffen dort, wo der
Bericht fertig ist und das Zeichnen beginnt. Erst mit ihr war der Schnitt
verantwortbar.

**Jede Seite gibt ihre Flowables zurueck, statt in eine gemeinsame Liste zu
schreiben.** Am Kopf jeder Funktion steht damit, **wovon** die Seite abhaengt —
und keine kann eine andere beeinflussen. Der Zusammenbau steht in
`pdf_generator.generate_audit_report`.

**Was der Vergleichstest nicht sieht:** Layout. Schriftgroessen, Abstaende und
Farben stehen in den Stilen, nicht im Text. Ein Umbau, der Text und
Reihenfolge erhaelt, kann das PDF trotzdem haesslich machen; die Sichtpruefung
eines erzeugten PDF ersetzt er nicht.
"""
import json
from datetime import datetime
from io import BytesIO

from services.pdf_bausteine import (
    BASE_TABLE_STYLE, BLOCKER_LABELS, FONT_BOLD, FONT_NORMAL, KC_BORDER,
    KC_DANGER, KC_DARK, KC_LIGHT, KC_MID, KC_SUCCESS, KC_TEXT_60,
    KC_WARNING, KC_WHITE, KeepTogether, LEGAL_COL_WIDTHS, LEGAL_ROWS,
    PageBreak, Paragraph, ParagraphStyle, RLImage, STATUS_ERFUELLT,
    STATUS_FARBEN, STATUS_OFFEN, STATUS_UNBEKANNT, STATUS_ZEICHEN, Spacer,
    TA_CENTER, TA_LEFT, Table, TableStyle, _category_table_style,
    _clean_text, _marken_band, _safe, _status_color, _stil_ohne_kopfzeile,
    _stufen_abzeichen, branche_fuer_protokoll, brand, build_scorecard,
    colors, generate_donut_chart, generate_radar_chart, geo_pruefpunkte,
    logger, mm, radar_beschriftung, rechtstabelle_zellen,
    roadmap_massnahmen,
)

__all__ = [
    "seite_befunde", "seite_deckblatt", "seite_diagramme", "seite_geo",
    "seite_protokoll", "seite_recht", "seite_roadmap", "seite_scorecard",
    "seite_zertifikat",
]


def seite_deckblatt(*,
    styles,
    total,
    level,
    company,
    url,
    date_str,
    created,
) -> list:
    """Deckblatt — Punktzahl, Stufe, Betrieb.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 1: COVER ──────────────────────────────────────
    #
    # Die Punktzahl stand hier als <font size="48"> in einem Absatz mit
    # leading=14. Die Glyphen liefen damit aus ihrer Zeilenbox heraus, und das
    # Stufen-Abzeichen darunter zeichnete quer durch die Zahl — auf jedem
    # bisher versendeten PDF war die Bewertung halb verdeckt. Die Zahl bekommt
    # jetzt einen eigenen Stil mit passendem Zeilenabstand.
    story.append(_marken_band(styles))
    story.append(Spacer(1, 26*mm))
    story.append(Paragraph("HOMEPAGE STANDARD", styles["KCTitle"]))
    story.append(Paragraph(
        f"Audit- und Zertifizierungsrahmen {created.year}", styles["KCSubtitle"]))
    story.append(Spacer(1, 18*mm))

    story.append(Paragraph(
        f'{total}<font size="20" color="{KC_TEXT_60.hexval()}"> / 100</font>',
        styles["KCScore"]))
    story.append(Spacer(1, 8*mm))
    story.append(_stufen_abzeichen(level))
    story.append(Spacer(1, 14*mm))

    story.append(Paragraph(f"<b>{company}</b>", styles["KCCenter"]))
    story.append(Paragraph(f'<font color="{KC_TEXT_60.hexval()}">{url}</font>',
                           styles["KCCenter"]))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f'<font color="{KC_TEXT_60.hexval()}">Auditdatum: {date_str}<br/>'
        f'Auditor: KOMPAGNON Communications</font>', styles["KCCenter"]))

    story.append(PageBreak())


    return story


def seite_recht(*,
    styles,
) -> list:
    """Die rechtlichen Grundlagen der Bewertung.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 2: LEGAL OVERVIEW ──────────────────────────────
    story.append(Paragraph("Rechtliche Grundlagen", styles["KCHeading"]))
    story.append(Paragraph(
        "Die folgenden Gesetze und Standards bilden die Grundlage f\u00fcr die Bewertung.",
        styles["KCBody"],
    ))

    legal_table = Table(
        rechtstabelle_zellen(),
        colWidths=LEGAL_COL_WIDTHS,
    )
    legal_table.setStyle(_category_table_style(len(LEGAL_ROWS)))
    story.append(legal_table)
    story.append(Spacer(1, 8*mm))

    # BFSG notice box
    bfsg_text = (
        f'<font color="{KC_DARK.hexval()}"><b>Hinweis zum BFSG:</b></font> '
        "Ab dem 28. Juni 2025 gilt das Barrierefreiheitsst\u00e4rkungsgesetz (BFSG) "
        "auch f\u00fcr private Anbieter digitaler Produkte und Dienstleistungen. "
        "Websites m\u00fcssen die WCAG 2.1 Level AA Kriterien erf\u00fcllen."
    )
    bfsg_data = [[Paragraph(bfsg_text, styles["KCBody"])]]
    bfsg_box = Table(bfsg_data, colWidths=[160*mm])
    bfsg_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), KC_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, KC_BORDER),
    ]))
    story.append(bfsg_box)

    story.append(PageBreak())


    return story


def seite_scorecard(*,
    styles,
    total,
    level,
    items,
    sources,
    blocker_keys,
    coverage,
    audit_data,
) -> list:
    """Die Bewertungsmatrix — je Kategorie und Kriterium.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 3: SCORECARD ───────────────────────────────────
    story.append(Paragraph("Bewertungsmatrix", styles["KCHeading"]))

    if blocker_keys:
        blocker_text = "<br/>".join(
            f"\u2022 {_clean_text(BLOCKER_LABELS.get(b, b))}" for b in blocker_keys)
        blocker_box = Table([[Paragraph(
            f'<b>Rechtliche Ausschlusskriterien</b><br/>{blocker_text}<br/>'
            f'<font size="8">Diese Punkte begrenzen die Bewertung unabh\u00e4ngig '
            f'von der erreichten Punktzahl.</font>',
            styles["KCBody"])]], colWidths=[160*mm])
        blocker_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEA")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBEFORE", (0, 0), (0, -1), 3, KC_DANGER),
        ]))
        story.append(blocker_box)
        story.append(Spacer(1, 5*mm))

    # Über wie viele Seiten geurteilt wurde. Ohne diese Zeile liest jemand
    # eine Note von heute wie eine von vor dem 21.08.2026 — damals bewertete
    # das Audit ausschließlich die Startseite.
    geprueft = audit_data.get("seiten_geprueft") or 1
    gefunden = audit_data.get("seiten_gefunden")
    if geprueft > 1:
        umfang = f"Bewertet wurden {geprueft} Seiten dieser Website"
        if gefunden and gefunden > geprueft:
            umfang += f" von {gefunden} gefundenen"
        story.append(Paragraph(
            f'<font size="8" color="{KC_TEXT_60.hexval()}">{umfang}.</font>',
            styles["KCBody"]))
        story.append(Spacer(1, 3*mm))

    if coverage is not None and coverage < 100:
        story.append(Paragraph(
            # \u202f (schmales gesch. Leerzeichen) fehlt in Helvetica und kam
            # als schwarzes Kaestchen zwischen Zahl und Prozentzeichen heraus.
            # \u00a0 steht in WinAnsi und haelt genauso zusammen.
            f'<font size="8" color="{KC_TEXT_60.hexval()}">{coverage}\u00a0% der Kriterien konnten '
            f'gepr\u00fcft werden. Nicht erhobene Kriterien sind als \u201enicht erhoben\u201c '
            f'ausgewiesen und flie\u00dfen nicht in die Bewertung ein.</font>',
            styles["KCBody"]))
        story.append(Spacer(1, 3*mm))

    sc_header, sc_rows = build_scorecard(items, sources, styles)

    # Summenzeile.
    #
    # Hier stand `level[:15]` in der Statusspalte — aus „Homepage Standard
    # Bronze" wurde „Homepage Standa", abgeschnitten in einer 14 mm breiten
    # Spalte, sodass der Text sichtbar aus der Tabelle lief. Dazu erwischte die
    # Schleife unten diese Zeile als Kategoriekopf und legte ein SPAN ueber die
    # Spalten 0 bis 3, was die Maximalpunkte verschluckte. Die Stufe steht auf
    # dem Deckblatt und auf der letzten Seite; hier gehoert sie nicht hin.
    gesamt_zeile = [
        Paragraph(f'<font color="{KC_WHITE.hexval()}"><b>GESAMTERGEBNIS</b></font>',
                  styles["KCBold"]),
        "", "", "100",
        Paragraph(f'<font color="{KC_WHITE.hexval()}"><b>{total}</b></font>',
                  styles["KCBold"]),
        "",
    ]
    sc_rows.append(gesamt_zeile)

    sc_table = Table(
        [sc_header] + sc_rows,
        # Zusammen 170 mm — die volle Breite zwischen den Raendern. Vorher
        # standen hier 132 mm, also lagen gut 30 mm brach, waehrend „nicht
        # erhoben" rechts aus der Statusspalte lief.
        colWidths=[14*mm, 71*mm, 22*mm, 13*mm, 20*mm, 30*mm],
        repeatRows=1,
    )
    n = len(sc_rows)
    sc_style = list(BASE_TABLE_STYLE)
    for i in range(1, n + 1):
        row_data = sc_rows[i - 1]
        letzte = i == n
        # Kategoriekopf — erkennbar am Paragraph in der ersten Spalte. Die
        # Summenzeile sieht genauso aus und muss ausgenommen werden.
        if isinstance(row_data[0], Paragraph) and not letzte:
            sc_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(brand.INFO_BG)))
            sc_style.append(("SPAN", (0, i), (3, i)))
        elif not letzte and i % 2 == 0:
            sc_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
        if isinstance(row_data[-1], str) and row_data[-1] in STATUS_ZEICHEN.values():
            sc_style.append(("TEXTCOLOR", (-1, i), (-1, i), _status_color(row_data[-1])))
            sc_style.append(("FONTNAME", (-1, i), (-1, i), FONT_BOLD))
            sc_style.append(("ALIGN", (-1, i), (-1, i), "CENTER"))

    sc_style.append(("BACKGROUND", (0, n), (-1, n), KC_DARK))
    sc_style.append(("TEXTCOLOR", (0, n), (-1, n), KC_WHITE))
    sc_style.append(("SPAN", (0, n), (2, n)))
    sc_table.setStyle(TableStyle(sc_style))
    story.append(sc_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f'Legende: <font color="{KC_SUCCESS.hexval()}"><b>{STATUS_ZEICHEN["konform"]}</b></font> konform '
        f'&nbsp;·&nbsp; <font color="{KC_WARNING.hexval()}"><b>{STATUS_ZEICHEN["teilweise"]}</b></font> teilweise konform '
        f'&nbsp;·&nbsp; <font color="{KC_DANGER.hexval()}"><b>{STATUS_ZEICHEN["offen"]}</b></font> nicht konform '
        f'&nbsp;·&nbsp; „nicht erhoben" fließt nicht in die Bewertung ein',
        styles["KCSmall"],
    ))

    story.append(PageBreak())


    return story


def seite_protokoll(*,
    styles,
    total,
    company,
    url,
    city,
    date_str,
    categories,
    audit_data,
) -> list:
    """Das Auditprotokoll — Betrieb, Technik, Summe.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 4: AUDIT PROTOCOL ──────────────────────────────
    story.append(Paragraph("Auditprotokoll", styles["KCHeading"]))

    proto_data = [
        ["Website-URL", url],
        ["Auftraggeber / Unternehmen", company],
        ["Branche", branche_fuer_protokoll(audit_data)],
        ["Stadt", _safe(city, "k.A.")],
        ["Auditdatum", date_str],
        ["Auditor/in", "KOMPAGNON Communications"],
        ["Audittyp", "Erst-Audit"],
    ]
    proto_table = Table(proto_data, colWidths=[50*mm, 110*mm])
    proto_table.setStyle(TableStyle(_stil_ohne_kopfzeile(len(proto_data))))
    story.append(proto_table)
    story.append(Spacer(1, 8*mm))

    # Hosting analysis
    story.append(Paragraph("Technische Pr\u00fcfergebnisse", styles["KCHeading"]))
    ssl_ok = audit_data.get("ssl_ok", False)
    mobile = audit_data.get("mobile_score", 0) or 0
    lcp = audit_data.get("lcp_value")
    cls_val = audit_data.get("cls_value")

    tech_data = [
        ["Pr\u00fcfung", "Ergebnis"],
        ["SSL-Zertifikat", "Vorhanden" if ssl_ok else "Nicht vorhanden"],
        ["HTTPS aktiv", "Ja" if ssl_ok else "Nein"],
        ["Mobile-Score", f"{mobile} / 100"],
        ["LCP", f"{lcp:.1f}s" if lcp else "k.A."],
        ["CLS", f"{cls_val:.3f}" if cls_val else "k.A."],
    ]
    tech_table = Table(tech_data, colWidths=[50*mm, 110*mm])
    tech_table.setStyle(_category_table_style(len(tech_data) - 1))
    story.append(tech_table)
    story.append(Spacer(1, 8*mm))

    # Score summary
    story.append(Paragraph("Pr\u00fcfergebnis je Kategorie", styles["KCHeading"]))
    sum_data = [["Kategorie", "Ergebnis"]]
    for kategorie in categories:
        beschriftung = f"{kategorie.get('label', '')} (max. {kategorie.get('nominal_max', 0)})"
        if kategorie.get("max", 0) < kategorie.get("nominal_max", 0):
            beschriftung += " – teilweise prüfbar"
        sum_data.append([_clean_text(beschriftung),
                         f"{kategorie.get('score', 0)} / {kategorie.get('max', 0)}"])
    sum_data.append(["GESAMTERGEBNIS (normiert)", f"{total} / 100"])

    sum_table = Table(sum_data, colWidths=[110*mm, 50*mm])
    sum_style = list(BASE_TABLE_STYLE)
    sum_style.append(("ALIGN", (1, 0), (1, -1), "RIGHT"))
    sum_style.append(("BACKGROUND", (0, -1), (-1, -1), KC_DARK))
    sum_style.append(("TEXTCOLOR", (0, -1), (-1, -1), KC_WHITE))
    for i in range(1, len(sum_data) - 1):
        if i % 2 == 0:
            sum_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
    sum_table.setStyle(TableStyle(sum_style))
    story.append(sum_table)
    story.append(Spacer(1, 8*mm))


    return story


def seite_diagramme(*,
    categories,
    audit_data,
) -> list:
    """Netz- und Ringdiagramm ueber die Kategorien.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── CHARTS: Radar + Donut ───────────────────────────────
    try:
        radar_axes = [
            (radar_beschriftung(_clean_text(k.get("label", ""))),
             round((k.get("score", 0) / k["max"]) * 10, 1) if k.get("max") else 0)
            for k in categories
        ]
        keyword_positions = audit_data.get("keyword_positions") or {}
        if isinstance(keyword_positions, str):
            try:
                keyword_positions = json.loads(keyword_positions)
            except Exception:
                keyword_positions = {}

        caption_style = ParagraphStyle(
            "ChartCaption", fontName=FONT_NORMAL, fontSize=8,
            textColor=KC_TEXT_60, alignment=TA_CENTER,
        )

        # Der Ring kommt nur, wenn es Keyword-Daten gibt. Fehlten sie, zeichnete
        # er vier gleiche Viertel mit „25 %" — eine erfundene Verteilung, die
        # der Empfaenger als Messergebnis liest.
        donut_png = generate_donut_chart(keyword_positions)

        if donut_png:
            chart_w = 72 * mm
            chart_table = Table(
                [[RLImage(BytesIO(generate_radar_chart(radar_axes)),
                          width=chart_w, height=chart_w),
                  RLImage(BytesIO(donut_png), width=chart_w, height=chart_w)],
                 [Paragraph("Zielerreichung je Bereich", caption_style),
                  Paragraph("Keyword-Positionen", caption_style)]],
                colWidths=[chart_w + 4*mm, chart_w + 4*mm],
            )
        else:
            # Ohne zweites Diagramm stand das Radar klein und links angeschlagen
            # neben einer halbleeren Seite. Allein darf es groesser und mittig.
            chart_w = 105 * mm
            chart_table = Table(
                [[RLImage(BytesIO(generate_radar_chart(radar_axes)),
                          width=chart_w, height=chart_w)],
                 [Paragraph("Zielerreichung je Bereich", caption_style)],
                 [Paragraph(
                     "Keyword-Positionen werden in dieser Analyse nicht erhoben.",
                     caption_style)]],
                colWidths=[chart_w + 8*mm],
            )
        chart_table.hAlign = "CENTER"
        chart_table.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(chart_table)
    except Exception as chart_fehler:  # noqa: BLE001
        # Diagramme sind Beiwerk und duerfen das PDF nicht kippen — aber
        # lautlos verschwinden sollen sie auch nicht.
        logger.warning(f"Diagramme nicht erzeugt: {chart_fehler}")

    story.append(PageBreak())


    return story


def seite_befunde(*,
    styles,
    top_issues,
    recommendations,
    ai_summary,
) -> list:
    """Befunde und Empfehlungen im Klartext.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 5: ISSUES & RECOMMENDATIONS ────────────────────
    story.append(Paragraph("Ma\u00dfnahmen & Empfehlungen", styles["KCHeading"]))

    if top_issues:
        story.append(Paragraph(f'<font color="{KC_DANGER.hexval()}"><b>Kritische M\u00e4ngel</b></font>', styles["KCBody"]))
        issue_rows = [["Nr.", "Mangel"]]
        for i, issue in enumerate(top_issues, 1):
            issue_rows.append([str(i), Paragraph(str(issue), styles["KCBody"])])
        issue_table = Table(issue_rows, colWidths=[12*mm, 148*mm])
        issue_style = list(BASE_TABLE_STYLE)
        issue_style[1] = ("FONTSIZE", (0, 0), (-1, 0), 9)
        issue_style.append(("BACKGROUND", (0, 0), (-1, 0), KC_DANGER))
        issue_table.setStyle(TableStyle(issue_style))
        story.append(issue_table)
        story.append(Spacer(1, 6*mm))

    if recommendations:
        story.append(Paragraph(f'<font color="{KC_SUCCESS.hexval()}"><b>Empfehlungen</b></font>', styles["KCBody"]))
        rec_rows = [["Prio.", "Ma\u00dfnahme"]]
        prio_labels = ["hoch", "hoch", "mittel", "mittel", "niedrig"]
        for i, rec in enumerate(recommendations):
            prio = prio_labels[i] if i < len(prio_labels) else "niedrig"
            rec_rows.append([prio, Paragraph(str(rec), styles["KCBody"])])
        rec_table = Table(rec_rows, colWidths=[18*mm, 142*mm])
        rec_style = list(BASE_TABLE_STYLE)
        rec_style.append(("BACKGROUND", (0, 0), (-1, 0), KC_SUCCESS))
        rec_table.setStyle(TableStyle(rec_style))
        story.append(rec_table)
        story.append(Spacer(1, 6*mm))

    if ai_summary:
        story.append(Paragraph("Bewertung durch KOMPAGNON", styles["KCHeading"]))
        ai_box = [[Paragraph(ai_summary, styles["KCBody"])]]
        ai_table = Table(ai_box, colWidths=[160*mm])
        ai_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), KC_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, KC_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(ai_table)

    story.append(PageBreak())


    return story


def seite_geo(*,
    styles,
    audit_data,
) -> list:
    """GEO und KI-Sichtbarkeit.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 6: GEO & KI-SICHTBARKEIT ───────────────────────
    story.append(Paragraph("GEO \u0026 KI-Sichtbarkeit", styles["KCHeading"]))
    story.append(Paragraph(
        "KI-Suchsysteme wie ChatGPT, Google AI Overview oder Perplexity crawlen Websites "
        "nach eigenen Regeln. Die folgenden Prüfpunkte zeigen, wie gut die Website für "
        "diese neuen Sichtbarkeitskanäle aufgestellt ist.",
        styles["KCBody"],
    ))
    story.append(Spacer(1, 4*mm))

    # Farben wie in der Bewertungsmatrix, damit derselbe Status gleich
    # aussieht. Wortstatus statt Haekchen: Helvetica kennt ✓ und ✗ nicht,
    # die Spalte blieb dadurch in jedem bisherigen Bericht leer.
    # **Eigener Name, nicht `STATUS_FARBEN`.** Der Block hiess bis zum
    # 30.08.2026 wie die Zuordnung im Modulkopf und verdeckte sie — in einer
    # 574-Zeilen-Funktion faellt das niemandem auf, in einer Datei mit neun
    # Funktionen meldet es `ruff` sofort (F811). Der Schnitt hat es sichtbar
    # gemacht, nicht verursacht.
    GEO_STATUS_FARBEN = {
        STATUS_ERFUELLT: "#27ae60",
        STATUS_OFFEN: "#e74c3c",
        STATUS_UNBEKANNT: KC_TEXT_60.hexval(),
    }

    def _geo_status_zelle(status):
        return Paragraph(
            f'<font color="{GEO_STATUS_FARBEN[status]}"><b>{status}</b></font>',
            ParagraphStyle("GeoStatus", fontName=FONT_BOLD, fontSize=9,
                           leading=11, alignment=TA_CENTER),
        )

    geo_header = ["Prüfpunkt", "Status", "Empfehlung"]
    geo_rows = [
        [
            punkt["pruefpunkt"],
            _geo_status_zelle(punkt["status"]),
            Paragraph(_clean_text(punkt["empfehlung"]), styles["KCZelle"])
            if punkt["empfehlung"]
            else Paragraph(
                f'<font color="{KC_TEXT_60.hexval()}">'
                f'{_clean_text(punkt["hinweis"])}</font>', styles["KCZelle"]),
        ]
        for punkt in geo_pruefpunkte(audit_data)
    ]

    geo_table = Table(
        [geo_header] + geo_rows,
        colWidths=[55*mm, 30*mm, 75*mm],
    )
    geo_style = list(BASE_TABLE_STYLE)
    for i in range(1, len(geo_rows) + 1):
        if i % 2 == 0:
            geo_style.append(("BACKGROUND", (0, i), (-1, i), KC_LIGHT))
        geo_style.append(("ALIGN", (1, i), (1, i), "CENTER"))
        geo_style.append(("VALIGN", (1, i), (1, i), "MIDDLE"))
    geo_table.setStyle(TableStyle(geo_style))
    story.append(geo_table)
    story.append(Spacer(1, 6*mm))

    # GEO info box
    geo_info = (
        '<b>Was ist llms.txt?</b> Eine neue Konvention (ähnlich robots.txt) die KI-Systemen '
        'mitteilt, welche Inhalte für das Training oder die Antwortgenerierung genutzt werden '
        'dürfen. Websites mit llms.txt werden von ChatGPT, Claude \u0026 Co. bevorzugt zitiert.'
    )
    geo_box = Table([[Paragraph(geo_info, styles["KCBody"])]], colWidths=[160*mm])
    geo_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(brand.INFO_BG)),
        ("BOX", (0, 0), (-1, -1), 0.5, KC_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(geo_box)

    story.append(PageBreak())


    return story


def seite_roadmap(*,
    styles,
    level,
    items,
    audit_data,
) -> list:
    """Die Massnahmen — aus dem Befund, nicht aus einer Liste.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── PAGE 7: MASSNAHMEN-ROADMAP ───────────────────────────
    story.append(Paragraph("Ma\u00dfnahmen-Roadmap", styles["KCHeading"]))
    story.append(Paragraph(
        "Basierend auf den Audit-Ergebnissen empfehlen wir folgende Umsetzungsreihenfolge:",
        styles["KCBody"],
    ))
    story.append(Spacer(1, 6*mm))

    # Die Massnahmen kommen aus dem Befund statt aus einer festen Liste:
    # `roadmap_massnahmen` nennt nur, was gemessen wurde und offen ist. Vorher
    # stand "robots.txt: GPTBot-Blockierung entfernen" in jedem Bericht, auch
    # fuer eine robots.txt, die niemanden sperrt.
    massnahmen = roadmap_massnahmen(audit_data)

    quick_wins = list(massnahmen["sofort"])
    mobile_ps = audit_data.get("mobile_score") or 0
    if mobile_ps and mobile_ps < 50:
        quick_wins.append("Bilder komprimieren \u0026 Lazy Load aktivieren")
    if not quick_wins:
        quick_wins.append("Audit-Score weiter optimieren \u0026 Inhalte aktualisieren")

    midterm = list(massnahmen["mittelfristig"])
    if level == "Nicht konform":
        midterm.append("SSL, Datenschutzerkl\u00e4rung und Impressum pr\u00fcfen \u0026 korrigieren")

    longterm = list(massnahmen["langfristig"])

    def _roadmap_box(title, items, bg_color, border_color, phase_label):
        """Build a single phase box as a Table."""
        header_para = Paragraph(
            f'<font color="white"><b>{phase_label} — {title}</b></font>',
            ParagraphStyle("RoadmapHeader", fontName=FONT_BOLD, fontSize=11,
                           textColor=KC_WHITE, alignment=TA_LEFT),
        )
        header_row = Table([[header_para]], colWidths=[160*mm])
        header_row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(border_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        item_rows = []
        for item in items:
            item_rows.append([
                Paragraph(f"\u2022 {_clean_text(item)}", styles["KCBody"]),
            ])
        body = Table(item_rows, colWidths=[160*mm])
        body.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
        ]))
        return KeepTogether([header_row, body])

    story.append(_roadmap_box(
        "Quick Wins (Woche 1\u20132)", quick_wins,
        bg_color=brand.SUCCESS_BG, border_color=brand.SUCCESS, phase_label="Phase 1",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Mittelfristig (Monat 1\u20133)", midterm,
        bg_color=brand.INFO_BG, border_color=brand.MID, phase_label="Phase 2",
    ))
    story.append(Spacer(1, 5*mm))
    story.append(_roadmap_box(
        "Langfristig (Monat 3\u20136)", longterm,
        bg_color=brand.SURFACE, border_color=brand.DARK, phase_label="Phase 3",
    ))

    story.append(PageBreak())


    return story


def seite_zertifikat(*,
    styles,
    total,
    level,
    url,
    date_str,
) -> list:
    """Die Zertifizierungsseite mit den Unterschriften.

    Gibt die Flowables dieser Seite zurueck, statt in eine
    gemeinsame Liste zu schreiben: Wer sie liest, sieht am Kopf,
    **wovon** die Seite abhaengt, und keine der neun Funktionen
    kann eine andere beeinflussen.
    """
    story = []

    # ── LAST PAGE: CERTIFICATION ────────────────────────────
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("Zertifizierungsaussage", styles["KCTitle"]))
    story.append(Spacer(1, 10*mm))

    story.append(_stufen_abzeichen(level))
    story.append(Spacer(1, 10*mm))

    cert_text = (
        f"Hiermit wird best\u00e4tigt, dass die gepr\u00fcfte Website "
        f"<b>{url}</b> zum Zeitpunkt des Audits am <b>{date_str}</b> "
        f"den Anforderungen des <b>{level}</b> "
        f"entspricht und eine Gesamtbewertung von <b>{total} / 100 Punkten</b> "
        f"erzielt hat."
    )
    story.append(Paragraph(cert_text, styles["KCBody"]))
    story.append(Spacer(1, 20*mm))

    # Signature lines
    sig_data = [["Ort, Datum", "Auditor/in: KOMPAGNON", "Auftraggeber"]]
    sig_table = Table(sig_data, colWidths=[53*mm, 54*mm, 53*mm])
    sig_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, KC_DARK),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NORMAL),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
    ]))
    story.append(sig_table)


    return story
