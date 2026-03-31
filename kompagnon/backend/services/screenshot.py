import httpx
import base64
import os
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


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
    try:
        import urllib.parse
        encoded = urllib.parse.quote(url, safe="")
        thumb_url = f"https://image.thum.io/get/width/1280/crop/720/{encoded}"
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            res = await client.get(thumb_url)
            if res.status_code == 200 and len(res.content) > 5000:
                return await _resize(res.content)
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
