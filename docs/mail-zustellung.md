# Zustellung von E-Mails — was ankommt und was nicht

**Angelegt:** 2026-08-14
**Betrifft:** `backend/routers/mail_events.py`, `backend/services/brevo_mail.py`,
`backend/services/email.py`, `frontend/src/pages/LeadProfile.jsx`

---

## 0. Der Anlass

Am 14.08.2026 wies ein Empfängerserver eine Mail ab:

```
554 5.7.1 Service unavailable; Client host [77.32.148.24] blocked
using bl.spamcop.net
```

Die IP gehört nicht uns und nicht Render. Der Rückwärts-Eintrag lautet
`gx.d.sender-sib.com` — `sib` steht für Sendinblue, den früheren Namen von
Brevo. Es ist also eine der **geteilten Versand-IPs des Mailanbieters**, und
sie stand zu dem Zeitpunkt auf der SpamCop-Liste. Barracuda und SORBS führten
sie nicht; Spamhaus ließ sich über einen öffentlichen Resolver nicht abfragen.

Geteilte IPs werden gelistet, wenn irgendein Kunde desselben Anbieters
Beschwerden verursacht. SpamCop-Einträge laufen von selbst aus, meist innerhalb
eines Tages. Betroffen sind nur Empfänger, deren Server SpamCop abfragen — viele
Firmenserver tun das, die großen Freemail-Anbieter meist nicht.

## 1. Warum das Werkzeug trotzdem „gesendet" anzeigte

Der Weg einer Mail ist: Anwendung → Brevo → Empfänger. `send_email()` gibt
zurück, was der **erste** Schritt ergab; Brevo hatte die Mail angenommen, also
war der Versand aus Sicht der Anwendung erfolgreich. Die Ablehnung kam erst
danach und erreichte die Anwendung nie.

Bei einem Akquisekanal ist das die teuerste Art von Fehler: Anschreiben laufen
ins Leere, und niemand erfährt es. Aufgefallen ist es nur, weil eine
Fehlermeldung von Hand weitergereicht wurde.

## 2. Was gebaut ist

**Der Webhook.** `POST /api/mail-events/brevo/{secret}` nimmt Brevos
Ereignismeldungen entgegen. Abgelegt werden ausschließlich Störungen —
`hard_bounce`, `soft_bounce`, `blocked`, `spam`, `invalid_email`, `error`.
Zustellungen, Öffnungen und Klicks werden mit 200 quittiert und verworfen; sie
würden die Tabelle fluten, ohne eine Frage zu beantworten, die hier jemand
stellt.

**Die Absicherung.** Brevo signiert seine Webhooks nicht — es gibt keinen
Header, gegen den sich prüfen ließe. Deshalb steht ein Geheimnis in der
Adresse (`BREVO_WEBHOOK_SECRET`), verglichen wird zeitkonstant. Ist kein
Geheimnis hinterlegt, bleibt der Endpunkt **geschlossen**: eine halb
eingerichtete Umgebung darf nicht offenstehen und sich mit erfundenen
Störungen füllen lassen.

**Gegen Doppelzählung.** Brevo wiederholt Zustellversuche. Aus Ereignis-ID,
Nachrichten-ID, Ereignisart, Adresse und Zeitstempel entsteht ein
Erkennungszeichen; ist es bekannt, wird nichts angelegt. Zwei Einträge sähen
aus wie zwei Ausfälle.

**Die Zuordnung.** Über die Adresse wird der passende Lead gesucht. Findet sich
keiner, wird die Meldung trotzdem behalten — sie ist auch ohne Lead wertvoll.

**Die Anzeige.** Die Kundenkartei (`LeadProfile.jsx`) zeigt über allem einen
Hinweis, sobald es zu diesem Lead eine Störung gibt: Art, Adresse, Zeitpunkt,
der Klartext des Empfängerservers und die Versand-IP. Dauerhafte Störungen
(`hard_bounce`, `blocked`, `invalid_email`, `spam`) erscheinen rot,
vorübergehende gelb — der Unterschied entscheidet, ob Nachfassen überhaupt Sinn
hat.

## 3. Einrichtung — zwei Schritte

1. **Geheimnis setzen.** In Render auf beiden Servern eine Umgebungsvariable
   `BREVO_WEBHOOK_SECRET` mit einem langen Zufallswert anlegen (etwa
   `openssl rand -hex 32`). Für Staging und Produktiv **verschiedene** Werte,
   sonst schreibt der eine Server in die Kartei des anderen.

2. **Webhook in Brevo eintragen.** Im Brevo-Konto unter *Transactional →
   Settings → Webhooks* eine Adresse anlegen:

   ```
   https://claude-code-znq2.onrender.com/api/mail-events/brevo/<geheimnis>
   ```

   Für Staging entsprechend `kompagnon-backend-staging.onrender.com`.
   Anzuhaken sind: *Hard bounce*, *Soft bounce*, *Blocked*, *Spam*,
   *Invalid email*, *Error*. Zustellungen und Öffnungen bitte **nicht** —
   sie werden ohnehin verworfen und kosten nur Aufrufe.

Solange Schritt 1 fehlt, antwortet der Endpunkt auf jeden Aufruf mit 403. Das
ist Absicht und kein Fehler.

## 4. Offen

- **Die Absenderdomain ist ungeklärt.** Der Standardabsender im Code ist
  `noreply@kompagnon.group`, das Frontend nennt an 16 Stellen
  `info@kompagnon.eu`, `config.py` hat als Vorgabe `info@kompagnon.de`. Ob die
  tatsächlich versendende Domain in Brevo mit SPF und DKIM hinterlegt ist, war
  von außen nicht prüfbar. Fehlt das, wird auch abgelehnt, wenn die IP wieder
  sauber ist — und dann hilft kein Webhook.
- **Dauerhaft unzustellbare Adressen werden nicht gesperrt.** Der Hinweis
  erscheint, weitere Mails gehen trotzdem raus. Ob nach einem `hard_bounce`
  automatisch nichts mehr an diese Adresse versendet werden soll, ist eine
  Entscheidung — technisch wäre es eine Abfrage vor dem Versand.
- **Eine eigene Versand-IP** bei Brevo wäre der bauliche Ausweg aus der
  geteilten Reputation. Sie kostet, muss eingewöhnt werden und lohnt erst ab
  einer gewissen Menge.
