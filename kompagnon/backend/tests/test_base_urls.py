"""Die beiden Adressen nach aussen — und wer sie benutzt.

Der Fehler, den diese Tests festhalten, ist immer derselbe: Eine fest
eingetragene Produktiv-Adresse als Rückfall. Sie scheitert nie laut. Sie ist
gültig, sie antwortet, nur bezieht sie sich auf ein anderes System als das,
das gerade läuft. Auf Staging gebaute Seiten zeigten so auf Produktiv-Dateien.
"""
from services import base_urls


# ── Die Rangfolge ─────────────────────────────────────────────────────

def test_eigene_einstellung_schlaegt_die_von_render(monkeypatch):
    # Arrange
    monkeypatch.setenv("API_BASE_URL", "https://api.kompagnon.group/")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://irgendwas.onrender.com")

    # Act / Assert — und der Schrägstrich am Ende fällt weg
    assert base_urls.api_base_url() == "https://api.kompagnon.group"


def test_ohne_eigene_einstellung_gilt_die_adresse_von_render(monkeypatch):
    """Render setzt ``RENDER_EXTERNAL_URL`` selbst — in jeder Umgebung richtig."""
    # Arrange — wie auf Staging: eigene Variable fehlt
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL",
                       "https://kompagnon-backend-staging.onrender.com")

    # Act / Assert
    assert base_urls.api_base_url() == \
        "https://kompagnon-backend-staging.onrender.com"


def test_leere_werte_zaehlen_als_nicht_gesetzt(monkeypatch):
    """Eine leere Variable ist in Render schnell angelegt und sagt nichts."""
    # Arrange
    monkeypatch.setenv("API_BASE_URL", "   ")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://echt.onrender.com")

    # Act / Assert
    assert base_urls.api_base_url() == "https://echt.onrender.com"


def test_die_oeffentliche_adresse_folgt_derselben_rangfolge(monkeypatch):
    # Arrange
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("FRONTEND_URL", "https://staging-frontend.example/")

    # Act / Assert
    assert base_urls.public_base_url() == "https://staging-frontend.example"


# ── Wer die Adresse benutzt ───────────────────────────────────────────

def test_die_bild_adressen_kommen_aus_derselben_quelle(monkeypatch):
    """``files.py`` hatte seine eigene Zeile mit der Produktiv-Adresse darin.

    Die Adressen aus dieser Liste landen im gespeicherten Seiteninhalt. Zeigen
    sie auf das falsche System, hängt das dort dauerhaft fest — auch wenn die
    Variable später richtig gesetzt wird.
    """
    from routers import files

    # Arrange
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://staging.example")

    # Act / Assert — dieselbe Funktion, nicht eine eigene Kopie
    assert files.api_base_url is base_urls.api_base_url
    assert files.api_base_url() == "https://staging.example"


def test_beide_rueckfaelle_sind_domains_die_uns_gehoeren():
    """Eine von Render vergebene Adresse als Rückfall überlebt keinen Umzug.

    Bis zum 16.08. standen hier `claude-code-znq2.onrender.com` und
    `kompagnon-frontend.onrender.com`. Beide verschwinden mit ihrem Dienst —
    und das Backend zieht nach Frankfurt (L-34). Ein Rückfall, der das nicht
    übersteht, ist ein Rückfall auf nichts.
    """
    # Assert
    assert base_urls.FALLBACK_API_BASE_URL == "https://api.kompagnon.group"
    assert base_urls.FALLBACK_PUBLIC_BASE_URL == "https://kas.kompagnon.group"


def test_keine_render_adresse_mehr_als_rueckfall():
    """Auch keine versteckte zweite — der Fehler wiederholt sich sonst."""
    # Arrange / Act
    rueckfaelle = (
        base_urls.FALLBACK_API_BASE_URL,
        base_urls.FALLBACK_PUBLIC_BASE_URL,
    )

    # Assert
    for wert in rueckfaelle:
        assert "onrender.com" not in wert, wert
