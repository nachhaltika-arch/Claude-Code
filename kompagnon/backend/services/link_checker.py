"""
Link checker for broken links on published websites.
Integrates with QA checks.
"""
import requests
from typing import Dict, List
from urllib.parse import urljoin, urlparse
import re


class LinkChecker:
    """Check for broken links on a website."""

    TIMEOUT = 5  # seconds
    EXTERNAL_TIMEOUT = 10  # seconds
    MAX_LINKS_TO_CHECK = 100  # Limit for performance

    @staticmethod
    def check_links(website_url: str) -> Dict:
        """
        Check all links on a website.

        Args:
            website_url: Root URL to check

        Returns:
            {
                'total_links_checked': int,
                'broken_links': [
                    {'url': str, 'status_code': int, 'page': str}
                ],
                'external_errors': [
                    {'url': str, 'error': str}
                ],
                'is_healthy': bool,
                'error_count': int,
            }
        """
        try:
            if not website_url.startswith(("http://", "https://")):
                website_url = f"https://{website_url}"

            # Get all links from homepage
            links = LinkChecker._extract_links(website_url)
            broken_links = []
            external_errors = []
            checked_count = 0

            for link in links[: LinkChecker.MAX_LINKS_TO_CHECK]:
                checked_count += 1

                # Check if internal or external
                if LinkChecker._is_internal(link, website_url):
                    # Check internal link (on same domain)
                    full_url = urljoin(website_url, link)
                    status = LinkChecker._check_url(full_url)

                    if status >= 400:
                        broken_links.append(
                            {
                                "url": full_url,
                                "status_code": status,
                                "page": "homepage",
                            }
                        )
                else:
                    # Check external link
                    status = LinkChecker._check_url(link, timeout=LinkChecker.EXTERNAL_TIMEOUT)
                    if status >= 400 or status == 0:
                        external_errors.append(
                            {
                                "url": link,
                                "error": f"Status {status}" if status > 0 else "Timeout or connection error",
                            }
                        )

            return {
                "total_links_checked": checked_count,
                "broken_links": broken_links,
                "external_errors": external_errors,
                "is_healthy": len(broken_links) == 0,
                "error_count": len(broken_links) + len(external_errors),
            }

        except Exception as e:
            return {
                "total_links_checked": 0,
                "broken_links": [],
                "external_errors": [{"url": "N/A", "error": str(e)}],
                "is_healthy": False,
                "error_count": 1,
            }

    @staticmethod
    def _extract_links(url: str) -> List[str]:
        """Extract all links from a page."""
        try:
            response = requests.get(url, timeout=LinkChecker.TIMEOUT)
            response.raise_for_status()

            # Extract href attributes
            links = re.findall(r'href=["\'](.*?)["\']', response.text)
            # Filter out anchors and empty links
            return [link for link in links if link and not link.startswith("#")]

        except Exception:
            return []

    @staticmethod
    def _is_internal(link: str, base_url: str) -> bool:
        """Check if link is internal (same domain)."""
        if link.startswith("http"):
            return urlparse(link).netloc == urlparse(base_url).netloc
        return True  # Relative links are internal

    @staticmethod
    def _check_url(url: str, timeout: int = 5) -> int:
        """Check if URL is accessible. Returns HTTP status code or 0 on error."""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code
        except requests.Timeout:
            return 0
        except Exception:
            return 0

    @staticmethod
    def get_mock_check(website_url: str) -> Dict:
        """Return mock link check for testing."""
        return {
            "total_links_checked": 28,
            "broken_links": [
                {
                    "url": "https://example.de/old-service",
                    "status_code": 404,
                    "page": "homepage",
                },
                {
                    "url": "https://example.de/team/john",
                    "status_code": 301,
                    "page": "team page",
                },
            ],
            "external_errors": [
                {
                    "url": "https://partner-website.com/integration",
                    "error": "Timeout or connection error",
                }
            ],
            "is_healthy": False,
            "error_count": 3,
        }
