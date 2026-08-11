"""
Tests für den SSRF-Schutz.

Der Audit-Start ist öffentlich erreichbar (Einbett-Widget auf fremden
Landingpages). Ohne diese Prüfung kann jeder den Server interne Adressen
abrufen lassen.
"""
import pytest

from services import url_guard
from services.url_guard import UnsafeUrlError, assert_safe_url, check_url, is_same_host


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/",
    "http://127.0.0.1:8000/admin",
    "https://localhost/",
    "http://169.254.169.254/latest/meta-data/",   # AWS-Metadaten
    "http://metadata.google.internal/",           # GCP-Metadaten
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://[::1]/",
    "http://0.0.0.0/",
])
def test_interne_ziele_werden_abgelehnt(url):
    ok, reason = check_url(url)
    assert ok is False, f"{url} wurde durchgelassen"
    assert reason


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "gopher://example.com/",
    "ftp://example.com/",
    "javascript:alert(1)",
])
def test_fremde_protokolle_werden_abgelehnt(url):
    ok, _ = check_url(url)
    assert ok is False


def test_ungewoehnlicher_port_wird_abgelehnt():
    ok, reason = check_url("http://example.com:5432/")
    assert ok is False
    assert "5432" in reason


def test_url_ohne_host_wird_abgelehnt():
    ok, _ = check_url("https:///pfad")
    assert ok is False


def test_oeffentliche_domain_wird_akzeptiert(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda h: ["93.184.216.34"])
    ok, reason = check_url("https://example.com/")
    assert ok is True
    assert reason is None


def test_domain_die_auf_localhost_zeigt_wird_abgelehnt(monkeypatch):
    """Ein Angreifer kann eine öffentliche Domain auf 127.0.0.1 zeigen lassen."""
    monkeypatch.setattr(url_guard, "resolve_host", lambda h: ["127.0.0.1"])
    ok, reason = check_url("https://boese.example/")
    assert ok is False
    assert "interne" in reason.lower()


def test_eine_private_adresse_unter_mehreren_genuegt_zur_ablehnung(monkeypatch):
    monkeypatch.setattr(url_guard, "resolve_host", lambda h: ["93.184.216.34", "10.0.0.1"])
    ok, _ = check_url("https://gemischt.example/")
    assert ok is False


def test_nicht_aufloesbare_domain_wird_abgelehnt(monkeypatch):
    import socket

    def _boom(host):
        raise socket.gaierror("unbekannt")

    monkeypatch.setattr(url_guard, "resolve_host", _boom)
    ok, reason = check_url("https://gibt-es-nicht.example/")
    assert ok is False
    assert "auflösbar" in reason


def test_assert_wirft_bei_unsicherer_url():
    with pytest.raises(UnsafeUrlError):
        assert_safe_url("http://169.254.169.254/")


def test_gleicher_host_wird_erkannt():
    assert is_same_host("https://example.com/impressum", "https://example.com/")
    assert is_same_host("https://EXAMPLE.com/x", "https://example.com/")


def test_fremder_host_wird_erkannt():
    assert not is_same_host("http://127.0.0.1/", "https://example.com/")
    assert not is_same_host("https://andere.de/impressum", "https://example.com/")
