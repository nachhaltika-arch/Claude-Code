"""
SSRF-Schutz: Validiert URLs bevor der Server sie abruft.
Blockiert private IPs, interne Dienste und gefährliche Schemas.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException

ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",   # AWS / GCP Metadata
    "metadata.google.internal",
    "169.254.170.2",     # ECS Metadata
    "100.100.100.200",   # Alibaba Cloud Metadata
}

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),       # Private A
    ipaddress.ip_network("172.16.0.0/12"),    # Private B
    ipaddress.ip_network("192.168.0.0/16"),   # Private C
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ipaddress.ip_network("::1/128"),           # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 Private
]


def validate_url(url: str) -> str:
    """
    Validiert eine URL gegen SSRF-Angriffe.
    Gibt die URL zurück wenn sicher, wirft HTTPException wenn nicht.
    """
    if not url or not isinstance(url, str):
        raise HTTPException(400, "Ungültige URL")

    parsed = urlparse(url)

    # Schema prüfen
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise HTTPException(400, f"URL-Schema '{parsed.scheme}' nicht erlaubt")

    # Hostname prüfen
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(400, "URL hat keinen gültigen Hostnamen")

    if hostname.lower() in BLOCKED_HOSTS:
        raise HTTPException(400, "Diese URL ist nicht erreichbar")

    # DNS auflösen und IP prüfen
    try:
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                raise HTTPException(400, "Diese URL ist nicht erreichbar")
    except HTTPException:
        raise
    except Exception:
        # DNS-Auflösung fehlgeschlagen — ablehnen
        raise HTTPException(400, "URL konnte nicht aufgelöst werden")

    return url
