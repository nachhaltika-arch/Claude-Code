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
   https://api.kompagnon.group/api/mail-events/brevo/<geheimnis>
   ```

   Für Staging entsprechend `kompagnon-backend-staging.onrender.com`.

   **Nicht** die alte Adresse `claude-code-znq2.onrender.com` eintragen, auch
   wenn Brevo sie heute noch akzeptiert: Sie verschwindet mit dem Umzug nach
   Frankfurt (L-34). `api.kompagnon.group` zeigt derzeit auf denselben Dienst
   und übersteht den Umzug — das ist der ganze Zweck der eigenen Domain.
   Anzuhaken sind: *Hard bounce*, *Soft bounce*, *Blocked*, *Spam*,
   *Invalid email*, *Error*. Zustellungen und Öffnungen bitte **nicht** —
   sie werden ohnehin verworfen und kosten nur Aufrufe.

Solange Schritt 1 fehlt, antwortet der Endpunkt auf jeden Aufruf mit 403. Das
ist Absicht und kein Fehler.

## 4. Die Absenderdomains — geprüft am 2026-08-14

Geprüft im öffentlichen DNS, nicht im Brevo-Konto: SPF, DKIM, DMARC und der
Verifizierungseintrag sind öffentlich, und Brevos Anzeige spiegelt nur, ob
diese Einträge existieren.

| | kompagnon.group | kompagnon.eu | kompagnon.de |
|---|---|---|---|
| bei Brevo verifiziert (`brevo-code`) | **ja** | nein | nein |
| DKIM für Brevo (`brevo1`/`brevo2`) | **ja, auflösend** | nein | nein |
| SPF | ohne Brevo (`~all`) | ohne Brevo (`-all`) | **keiner** |
| DMARC | `p=none`, Berichte an Brevo | `p=none`, strikt ausgerichtet | **keiner** |

**Der tatsächlich sendende Absender ist sauber eingerichtet.** Der
Standardabsender des Codes ist `noreply@kompagnon.group`, und diese Domain ist
bei Brevo verifiziert; die beiden DKIM-Verweise `brevo1._domainkey` und
`brevo2._domainkey` lösen über `b1/b2.kompagnon-group.dkim.brevo.com` auf echte
Schlüssel bei `brevo17`/`brevo18.dkim.brevo.com` auf. Damit ist die
DKIM-Ausrichtung gegeben, und die trägt DMARC allein — ein SPF-Eintrag für
Brevo wird nicht gebraucht, solange Brevo seinen eigenen Rückweg verwendet.

**Der Bounce lag also nicht an der Domain**, sondern allein an der geteilten
Versand-IP auf der SpamCop-Liste. Die ursprüngliche Vermutung war falsch.

Zwei Funde daneben, beide ohne Eile:

- **`kompagnon.eu` trägt einen DKIM-Schlüssel am Wurzeleintrag** — ein
  `v=DKIM1; k=rsa; p=…` direkt auf `kompagnon.eu` statt unter
  `<selektor>._domainkey.kompagnon.eu`. Dort liest ihn kein Prüfer; er tut
  nichts. Rest einer früheren Einrichtung, gehört weg.
- **`kompagnon.de` ist ungeschützt**: kein SPF, kein DMARC. In ihrem Namen kann
  jeder fälschen. Wenn die Domain nie versendet, kostet ein `v=spf1 -all` plus
  `p=reject` nichts und schließt das.

Und der Punkt, der offen bleibt: **`kompagnon.eu` ist nicht bei Brevo
authentifiziert und hat ein hartes `-all`.** Ginge je etwas über Brevo mit
Absender `@kompagnon.eu` raus, gäbe es weder ausgerichtetes DKIM noch SPF —
DMARC schlüge fehl, derzeit folgenlos, weil `p=none` gilt. Ob das passiert,
hängt an `system_settings.smtp_sender_email` im Produktivsystem; dorthin
reichte der Zugang nicht. Schnellster Weg zur Antwort: in einer Mail aus dem
Werkzeug den Absender im Kopf nachsehen. Steht dort `@kompagnon.group`, ist
alles in Ordnung.

## 5. Offen
- **Dauerhaft unzustellbare Adressen werden nicht gesperrt.** Der Hinweis
  erscheint, weitere Mails gehen trotzdem raus. Ob nach einem `hard_bounce`
  automatisch nichts mehr an diese Adresse versendet werden soll, ist eine
  Entscheidung — technisch wäre es eine Abfrage vor dem Versand.
- **Eine eigene Versand-IP** bei Brevo wäre der bauliche Ausweg aus der
  geteilten Reputation. Sie kostet, muss eingewöhnt werden und lohnt erst ab
  einer gewissen Menge.
