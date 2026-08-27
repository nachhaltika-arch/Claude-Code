"""
Schutz gegen Server-Side Request Forgery (SSRF).

Das Audit holt jede eingegebene URL serverseitig ab. Da der Start-Endpunkt
öffentlich ist und über das Einbett-Widget auf fremden Landingpages erreichbar
sein soll, kann sonst jeder den Server dazu bringen, interne Adressen
abzurufen — Cloud-Metadaten (169.254.169.254), die Datenbank auf localhost,
oder Dienste im privaten Netz.

Geprüft wird nicht die Zeichenkette, sondern die aufgelöste IP-Adresse: ein
Angreifer kann einen öffentlichen Namen auf 127.0.0.1 zeigen lassen. Ebenso
wird jede Weiterleitung einzeln geprüft, weil sonst der erste Hop harmlos und
das Ziel intern wäre.
"""
import ipaddress
import logging
import socket
from typing import List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_PORTS = (80, 443, 8080, 8443)
MAX_REDIRECTS = 5

# Namen, die nie geprüft werden müssen, weil sie per Definition lokal sind.
BLOCKED_HOSTNAMES = frozenset({
    "localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback",
    "metadata", "metadata.google.internal", "instance-data",
})


class UnsafeUrlError(ValueError):
    """Die URL zeigt auf ein nicht öffentlich erreichbares Ziel."""


#: NAT64 nach RFC 6052 — das allgemeine Praefix und das netzeigene.
#: In einem Netz ohne IPv4 verpackt der Aufloeser die echte IPv4 in die
#: letzten 32 Bit einer IPv6-Adresse.
NAT64_PRAEFIXE = (
    ipaddress.ip_network("64:ff9b::/96"),
    ipaddress.ip_network("64:ff9b:1::/48"),
)


def _hinter_nat64(ip):
    """Die IPv4, die in einer NAT64-Adresse steckt — oder `None`.

    **Warum das noetig ist (26.08.2026).** `ganz-neu.de` loeste auf diesem
    Rechner auf `64:ff9b::88f3:515c` auf: `88f3:515c` ist `136.243.81.92`,
    ein gewoehnlicher Server. Python fuehrt das Praefix als `is_reserved`,
    und der Schutz lehnte deshalb ab — mit der Begruendung „zeigt auf eine
    interne Adresse", also dem Gegenteil dessen, was zutraf.

    In einem Netz mit DNS64 (Mobilfunk, viele Firmennetze) haette die
    Analyse damit **jede** Kundenwebsite abgelehnt. Der Schutz urteilte
    ueber die Huelle statt ueber das Ziel.

    Ausgepackt wird nur; beurteilt wird danach nach denselben Regeln.
    `64:ff9b::7f00:1` traegt `127.0.0.1` und bleibt gesperrt.
    """
    if not isinstance(ip, ipaddress.IPv6Address):
        return None
    if not any(ip in netz for netz in NAT64_PRAEFIXE):
        return None
    return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)


def _is_public_ip(ip: ipaddress._BaseAddress) -> bool:
    innen = _hinter_nat64(ip)
    if innen is not None:
        return _is_public_ip(innen)

    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
        or ip.is_reserved or ip.is_unspecified
    )


def resolve_host(hostname: str) -> List[str]:
    """Alle IP-Adressen eines Hostnamens — IPv4 und IPv6."""
    infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    return sorted({info[4][0] for info in infos})


def check_url(url: str) -> Tuple[bool, Optional[str]]:
    """Prüft eine einzelne URL. Gibt (ok, Begründung) zurück."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL nicht lesbar"

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, f"Nur http und https erlaubt, nicht '{parsed.scheme}'"

    hostname = (parsed.hostname or "").lower().strip(".")
    if not hostname:
        return False, "Kein Hostname in der URL"
    if hostname in BLOCKED_HOSTNAMES:
        return False, "Lokale Adresse nicht erlaubt"

    port = parsed.port
    if port is not None and port not in ALLOWED_PORTS:
        return False, f"Port {port} nicht erlaubt"

    # Direkt notierte IP-Adressen
    try:
        ip = ipaddress.ip_address(hostname)
        return (True, None) if _is_public_ip(ip) else (False, "Interne IP-Adresse nicht erlaubt")
    except ValueError:
        pass

    # Hostname auflösen und JEDE Adresse prüfen — eine private genügt zum Ablehnen
    try:
        addresses = resolve_host(hostname)
    except socket.gaierror:
        return False, "Domain nicht auflösbar"
    except Exception as e:  # noqa: BLE001
        return False, f"Namensauflösung fehlgeschlagen: {type(e).__name__}"

    if not addresses:
        return False, "Domain hat keine IP-Adresse"

    for address in addresses:
        try:
            if not _is_public_ip(ipaddress.ip_address(address)):
                return False, "Domain zeigt auf eine interne Adresse"
        except ValueError:
            return False, "Unlesbare IP-Adresse in der Namensauflösung"

    return True, None


def assert_safe_url(url: str) -> None:
    """Wie check_url, wirft aber bei Ablehnung."""
    ok, reason = check_url(url)
    if not ok:
        raise UnsafeUrlError(reason or "URL nicht erlaubt")


def is_same_host(url: str, base_url: str) -> bool:
    """Ob eine URL auf denselben Host zeigt wie die Ausgangs-URL.

    Unterseiten werden nur auf der geprüften Domain abgerufen — sonst könnte
    ein Link im HTML den Abruf doch wieder auf ein internes Ziel lenken.
    """
    try:
        return (urlparse(url).hostname or "").lower() == (urlparse(base_url).hostname or "").lower()
    except Exception:  # noqa: BLE001
        return False


async def fetch_guarded(client, url: str, **kwargs):
    """Abruf mit Prüfung jeder einzelnen Weiterleitung.

    httpx würde Weiterleitungen intern verfolgen — dann wäre nur der erste Hop
    geprüft und ein Redirect auf 127.0.0.1 käme trotzdem durch.
    """
    kwargs.pop("follow_redirects", None)
    current = url

    for _ in range(MAX_REDIRECTS + 1):
        assert_safe_url(current)
        response = await client.get(current, follow_redirects=False, **kwargs)

        if response.status_code not in (301, 302, 303, 307, 308):
            return response

        location = response.headers.get("location")
        if not location:
            return response
        current = str(response.url.join(location))

    raise UnsafeUrlError(f"Mehr als {MAX_REDIRECTS} Weiterleitungen")
