"""
Website screenshot service using Playwright headless Chromium.
Captures above-the-fold screenshot, resizes to 640x360, returns base64.
Gracefully returns "" if Playwright is not installed.
"""
import asyncio
import base64
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.info("Playwright not installed — screenshots disabled")


async def capture_screenshot(url: str) -> str:
    """Capture above-the-fold screenshot. Returns base64 JPEG or empty string."""
    if not HAS_PLAYWRIGHT:
        return ""

    if not url.startswith("http"):
        url = "https://" + url

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                       "--disable-gpu", "--no-first-run", "--no-zygote", "--single-process"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                locale="de-DE",
            )
            page = await context.new_page()

            # Hide cookie banners
            await page.add_init_script("""
                const s = document.createElement('style');
                s.textContent = '[class*="cookie"],[id*="cookie"],[class*="consent"],[id*="consent"],[class*="gdpr"],[id*="gdpr"],.cc-window,#cookielaw-info-bar,.cookiebanner,.cookie-notice{display:none!important}';
                document.head.appendChild(s);
            """)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)
                await page.evaluate("window.scrollTo(0, 0)")
                screenshot_bytes = await page.screenshot(
                    clip={"x": 0, "y": 0, "width": 1280, "height": 720},
                    type="jpeg", quality=75,
                )
            except Exception as e:
                logger.warning(f"Screenshot page error for {url}: {e}")
                screenshot_bytes = None
            finally:
                await browser.close()

            if not screenshot_bytes:
                return ""

            # Resize to 640x360
            try:
                from PIL import Image
                img = Image.open(BytesIO(screenshot_bytes))
                img = img.resize((640, 360), Image.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=70, optimize=True)
                screenshot_bytes = buffer.getvalue()
            except Exception as e:
                logger.warning(f"Screenshot resize error: {e}")

            return base64.b64encode(screenshot_bytes).decode("utf-8")

    except Exception as e:
        logger.warning(f"Screenshot failed for {url}: {e}")
        return ""


def get_screenshot_data_url(base64_str: str) -> str:
    if not base64_str:
        return ""
    return f"data:image/jpeg;base64,{base64_str}"
