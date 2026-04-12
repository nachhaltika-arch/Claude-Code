import qrcode
import base64
import io
import os
import secrets
from datetime import datetime, timedelta


def generate_token() -> str:
    """Generiert kryptografisch sicheren Token — 32 Bytes URL-sicher."""
    return secrets.token_urlsafe(32)


def token_expires_at() -> datetime:
    """Token läuft nach 30 Tagen ab."""
    return datetime.utcnow() + timedelta(days=30)


def generate_qr_code(url: str) -> str:
    """Erzeugt QR-Code als Base64-PNG."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#0F1E3A', back_color='white')

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return base64.b64encode(buf.getvalue()).decode('utf-8')


def get_portal_url(token: str) -> str:
    frontend_url = os.getenv('FRONTEND_URL', 'https://kompagnon-frontend.onrender.com')
    return f'{frontend_url}/portal/{token}'
