"""Scraper for DefenseScoop events.

Parses the DefenseScoop /attend/ listing page for event URLs, then
follows each link to extract LD+JSON (schema.org/Event) structured data
from the individual event pages (typically hosted on upgather.com).
Falls back to the listing page HTML when LD+JSON is unavailable.
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dateutil_parser
from typing import List, Optional
import re
from .base_scraper import BaseScraper, Event


class DefenseScoopScraper(BaseScraper):
    """Scraper for DefenseScoop (Scoop News Group) events."""

    def __init__(self, cache=None):
        super().__init__(
            name="DefenseScoop",
            url="https://defensescoop.com/attend/",
        )
        self.cache = cache

    def _fetch_url(self, url: str, headers: dict) -> bytes:
        """Fetch URL with caching support."""
        if self.cache:
            cached_content = self.cache.get(url)
            if cached_content is not None:
                return cached_content

        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        if self.cache:
            self.cache.set(url, response.content)

        return response.content

    def scrape(self) -> List[Event]:
        """Scrape upcoming events from DefenseScoop.

        1. Fetch the listing page for event URLs and fallback metadata.
        2. Visit each event URL to extract LD+JSON structured data.
        """
        events = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        try:
            print(f"Fetching events page: {self.url}")
            content = self._fetch_url(self.url, headers)
            soup = BeautifulSoup(content, "html.parser")

            # Collect raw event stubs from the listing page
            stubs = []
            featured = self._parse_featured_stub(soup)
            if featured:
                stubs.append(featured)

            feed_section = soup.find("section", class_="events-page__feed")
            if feed_section:
                cards = feed_section.find_all(
                    "article", class_="event-card", recursive=False
                )
                if not cards:
                    cards = feed_section.find_all("article", class_="event-card")
                for card in cards:
                    stub = self._parse_card_stub(card)
                    if stub:
                        stubs.append(stub)

            # Enrich each stub with LD+JSON from the event detail page
            for stub in stubs:
                # Skip virtual events early to avoid unnecessary requests
                if self._is_virtual(stub.get("location", "")):
                    print(f"  ⊘ Skipping virtual: {stub['title']}")
                    continue
                event = self._enrich_with_ldjson(stub, headers)
                if event:
                    events.append(event)

            print(f"Found {len(events)} upcoming events from {self.name}")

        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()

        return events

    # ------------------------------------------------------------------
    # Listing-page parsers (produce fallback stubs)
    # ------------------------------------------------------------------

    def _parse_featured_stub(self, soup) -> Optional[dict]:
        """Extract stub data from the featured event section."""
        section = soup.find("section", class_="featured-event")
        if not section:
            return None

        title_elem = section.find(class_="featured-event__title")
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)
        if not title:
            return None

        date_elem = section.find(class_="featured-event__date")
        date_str = date_elem.get_text(strip=True) if date_elem else ""

        loc_elem = section.find(class_="featured-event__location")
        location = loc_elem.get_text(strip=True) if loc_elem else ""

        url = ""
        link = section.find("a", href=True)
        if link:
            url = link["href"]

        return {
            "title": title,
            "date_str": date_str,
            "location": location,
            "url": url,
        }

    def _parse_card_stub(self, card) -> Optional[dict]:
        """Extract stub data from an event-card article."""
        title_elem = card.find(class_="event-card__title")
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)
        if not title:
            return None

        date_elem = card.find(class_="event-card__date")
        date_str = date_elem.get_text(strip=True) if date_elem else ""

        loc_elem = card.find(class_="event-card__location")
        location = loc_elem.get_text(strip=True) if loc_elem else ""

        url = ""
        link = title_elem.find("a", href=True)
        if link:
            url = link["href"]

        return {
            "title": title,
            "date_str": date_str,
            "location": location,
            "url": url,
        }

    # ------------------------------------------------------------------
    # LD+JSON enrichment
    # ------------------------------------------------------------------

    def _enrich_with_ldjson(self, stub: dict, headers: dict) -> Optional[Event]:
        """Try to fetch LD+JSON from the event URL; fall back to stub data."""
        url = stub.get("url", "")
        if url:
            try:
                event = self._parse_ldjson_page(url, headers)
                if event:
                    if self._is_virtual(event.location):
                        print(f"  ⊘ Skipping virtual: {event.title}")
                        return None
                    print(f"  ✓ LD+JSON: {event.title}")
                    return event
            except Exception as e:
                print(f"  ✗ LD+JSON failed for {url}: {e}")

        # Fall back to listing-page data
        start_date, end_date = self._parse_date_range(stub.get("date_str", ""))
        if not start_date:
            return None
        return Event(
            title=stub["title"],
            start_date=start_date,
            end_date=end_date,
            location=stub.get("location", ""),
            url=url,
        )

    def _parse_ldjson_page(self, url: str, headers: dict) -> Optional[Event]:
        """Fetch a page and extract schema.org/Event LD+JSON."""
        content = self._fetch_url(url, headers)
        soup = BeautifulSoup(content, "html.parser")

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue

            if data.get("@type") != "Event":
                continue

            start_date = self._parse_iso_date(data.get("startDate"))
            if not start_date:
                continue

            end_date = self._parse_iso_date(data.get("endDate"))
            location = self._extract_location(data.get("location", []))
            description = (data.get("description") or "").strip()

            return Event(
                title=data.get("name", "").strip(),
                start_date=start_date,
                end_date=end_date,
                location=location,
                description=description,
                url=url,
            )

        return None

    @staticmethod
    def _parse_iso_date(value: str) -> Optional[datetime]:
        """Parse an ISO 8601 date string."""
        if not value:
            return None
        try:
            return dateutil_parser.isoparse(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_location(location_data) -> str:
        """Build a human-readable location from LD+JSON location array."""
        if not location_data:
            return ""

        # location may be a single dict or a list
        if isinstance(location_data, dict):
            location_data = [location_data]

        for loc in location_data:
            if loc.get("@type") == "Place":
                name = loc.get("name", "")
                addr = loc.get("address", {})
                if isinstance(addr, dict):
                    parts = filter(None, [
                        addr.get("streetAddress"),
                        addr.get("addressLocality"),
                        addr.get("addressRegion"),
                        addr.get("postalCode"),
                    ])
                    addr_str = ", ".join(parts)
                    if name and addr_str:
                        return f"{name}, {addr_str}"
                    return name or addr_str
                return name

        # No physical Place found — check for VirtualLocation
        for loc in location_data:
            if loc.get("@type") == "VirtualLocation":
                return "Virtual Event"

        return ""

    # ------------------------------------------------------------------
    # Fallback date parsing (listing page text)
    # ------------------------------------------------------------------

    def _parse_date_range(self, date_str: str) -> tuple:
        """Parse date strings from the listing page, including ranges.

        Handles: 'Apr 2, 2026', 'Apr 13 - 17, 2026', 'Mar 30 - Apr 2, 2026'
        Returns (start_date, end_date). end_date may be None.
        """
        if not date_str:
            return None, None

        date_str = date_str.strip()

        # Range within same month: "Apr 13 - 17, 2026"
        m = re.match(
            r"(\w{3,9})\s+(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s+(\d{4})", date_str
        )
        if m:
            month, d1, d2, year = m.groups()
            return (
                self._parse_single_date(f"{month} {d1}, {year}"),
                self._parse_single_date(f"{month} {d2}, {year}"),
            )

        # Range across months: "Mar 30 - Apr 2, 2026"
        m = re.match(
            r"(\w{3,9})\s+(\d{1,2})\s*[-–]\s*(\w{3,9})\s+(\d{1,2}),?\s+(\d{4})",
            date_str,
        )
        if m:
            m1, d1, m2, d2, year = m.groups()
            return (
                self._parse_single_date(f"{m1} {d1}, {year}"),
                self._parse_single_date(f"{m2} {d2}, {year}"),
            )

        return self._parse_single_date(date_str), None

    @staticmethod
    def _is_virtual(location: str) -> bool:
        """Return True if the location indicates a virtual/online event."""
        if not location:
            return False
        return bool(re.search(r'\bvirtual\b', location, re.IGNORECASE))

    @staticmethod
    def _parse_single_date(date_str: str) -> Optional[datetime]:
        """Parse a single date string."""
        date_str = date_str.strip()
        for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
