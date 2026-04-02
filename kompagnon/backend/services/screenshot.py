import httpx
import base64
import os
import logging
from io import BytesIO
from urllib.parse import quote, urlparse

logger = logging.getLogger(__name__)


def build_screenshot_url(target_url: str):
    """Validate and encode a URL for thum.io. Returns None if URL is invalid."""
    parsed = urlparse(target_url)
    if parsed.scheme not in ('http', 'https'):
        return None
    if not parsed.netloc:
        return None
    encoded = quote(target_url, safe='')
    return f"https://image.thum.io/get/width/1280/crop/720/{encoded}"


async def capture_screenshot(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url

    result = await _screenshot_thumio(url)
    if result:
        return result

    result = await _screenshot_microlink(url)
    if result:
        return result

    logger.warning(f"Screenshot fehlgeschlagen: {url}")
    return ""


async def _screenshot_thumio(url: str) -> str:
    thumb_url = build_screenshot_url(url)
    if not thumb_url:
        logger.warning(f"Thum.io: Ungültige URL übersprungen: {url}")
        return ""
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            res = await client.get(thumb_url)
            if res.status_code == 200 and len(res.content) > 5000:
                return await _resize(res.content)
            if res.status_code in (400, 404, 500):
                logger.warning(f"Thum.io HTTP {res.status_code} für URL: {url}")
                return ""
    except Exception as e:
        logger.warning(f"Thum.io Fehler: {e}")
    return ""


async def _screenshot_microlink(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get("https://api.microlink.io", params={
                "url": url, "screenshot": "true", "meta": "false",
            })
            if res.status_code == 200:
                img_url = res.json().get("data", {}).get("screenshot", {}).get("url", "")
                if img_url:
                    img = await client.get(img_url)
                    if img.status_code == 200:
                        return await _resize(img.content)
    except Exception as e:
        logger.warning(f"Microlink Fehler: {e}")
    return ""


async def _resize(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((640, 360), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, "JPEG", quality=72)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return base64.b64encode(image_bytes).decode()
