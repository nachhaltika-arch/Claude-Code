"""
Website screenshot service using external APIs (no Playwright needed).
Fallback chain: ScreenshotOne → Thum.io → Microlink.
"""
import base64
import logging
import os
import urllib.parse
from io import BytesIO

import httpx

logger = logging.getLogger(__name__)


async def capture_screenshot(url: str) -> str:
    """Capture screenshot via external API. Returns base64 JPEG or empty string."""
    if not url.startswith("http"):
        url = "https://" + url

    # 1. ScreenshotOne (best quality, needs API key)
    api_key = os.getenv("SCREENSHOTONE_KEY", "")
    if api_key:
        result = await _screenshot_screenshotone(url, api_key)
        if result:
            return result

    # 2. Thum.io (free, no key)
    result = await _screenshot_thumio(url)
    if result:
        return result

    # 3. Microlink (free, 100 req/day)
    result = await _screenshot_microlink(url)
    if result:
        return result

    logger.warning(f"All screenshot methods failed for {url}")
    return ""


async def _screenshot_screenshotone(url: str, api_key: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get("https://api.screenshotone.com/take", params={
                "access_key": api_key, "url": url, "viewport_width": 1280, "viewport_height": 720,
                "format": "jpg", "image_quality": 75, "block_cookie_banners": "true",
                "block_ads": "true", "delay": 2, "full_page": "false",
            })
            if res.status_code == 200:
                return await _resize_image(res.content)
    except Exception as e:
        logger.warning(f"ScreenshotOne: {e}")
    return ""


async def _screenshot_thumio(url: str) -> str:
    try:
        encoded = urllib.parse.quote(url, safe="")
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            res = await client.get(f"https://image.thum.io/get/width/1280/crop/720/png/{encoded}")
            if res.status_code == 200 and len(res.content) > 5000:
                return await _resize_image(res.content)
    except Exception as e:
        logger.warning(f"Thum.io: {e}")
    return ""


async def _screenshot_microlink(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get("https://api.microlink.io", params={
                "url": url, "screenshot": "true", "meta": "false", "embed": "screenshot.url",
            })
            if res.status_code == 200:
                screenshot_url = res.json().get("data", {}).get("screenshot", {}).get("url", "")
                if screenshot_url:
                    img_res = await client.get(screenshot_url)
                    if img_res.status_code == 200:
                        return await _resize_image(img_res.content)
    except Exception as e:
        logger.warning(f"Microlink: {e}")
    return ""


async def _resize_image(image_bytes: bytes) -> str:
    """Resize to 640x360 JPEG, return base64."""
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((640, 360), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, "JPEG", quality=72)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return base64.b64encode(image_bytes).decode("utf-8")


def get_screenshot_data_url(base64_str: str) -> str:
    if not base64_str:
        return ""
    return f"data:image/jpeg;base64,{base64_str}"
