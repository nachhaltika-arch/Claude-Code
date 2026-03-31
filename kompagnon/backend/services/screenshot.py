"""
Website screenshot service using Playwright headless Chromium.
Captures above-the-fold screenshot, resizes to 640x360, returns base64.
Playwright Chromium must be installed at build time (render-build.sh).
"""
import asyncio
import base64
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


async def capture_screenshot(url: str) -> str:
    """Capture above-the-fold screenshot. Returns base64 JPEG or empty string."""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                       "--disable-gpu", "--single-process", "--no-zygote"],
            )
            page = await (await browser.new_context(viewport={"width": 1280, "height": 800})).new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.evaluate("window.scrollTo(0,0)")
            await asyncio.sleep(2)

            screenshot = await page.screenshot(
                clip={"x": 0, "y": 0, "width": 1280, "height": 720},
                type="jpeg", quality=75,
            )
            await browser.close()

            # Resize to 640x360
            try:
                from PIL import Image
                img = Image.open(BytesIO(screenshot))
                img = img.resize((640, 360), Image.LANCZOS)
                buf = BytesIO()
                img.save(buf, "JPEG", quality=70)
                screenshot = buf.getvalue()
            except Exception:
                pass

            return base64.b64encode(screenshot).decode()

    except Exception as e:
        logger.warning(f"Screenshot failed for {url}: {e}")
        return ""


def get_screenshot_data_url(base64_str: str) -> str:
    if not base64_str:
        return ""
    return f"data:image/jpeg;base64,{base64_str}"
