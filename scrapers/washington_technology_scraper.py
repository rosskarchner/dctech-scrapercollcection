"""Scraper for Washington Technology events."""
import re
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, Event


class WashingtonTechnologyScraper(BaseScraper):
    """Scraper for Washington Technology events."""

    def __init__(self, cache=None):
        super().__init__(
            name="Washington Technology",
            url="https://www.washingtontechnology.com/events/",
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
        """Scrape upcoming events from Washington Technology."""
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

            upcoming_section = self._find_upcoming_section(soup)
            if not upcoming_section:
                print("No upcoming section found")
                return events

            event_items = upcoming_section.find_all("section", class_="river-item")
            today = datetime.now().date()

            for item in event_items:
                event = self._parse_event_item(item)
                if not event:
                    continue
                if event.start_date.date() < today:
                    continue
                events.append(event)

            print(f"Found {len(events)} upcoming events from {self.name}")

        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()

        return events

    @staticmethod
    def _find_upcoming_section(soup) -> Optional[BeautifulSoup]:
        """Find the section containing upcoming events."""
        for section in soup.find_all("section", class_="river"):
            title = section.find("h1", class_="river-title")
            if title and title.get_text(strip=True).lower() == "upcoming":
                return section
        return None

    def _parse_event_item(self, item) -> Optional[Event]:
        """Parse a single Washington Technology event card."""
        title_link = item.find("a", class_="river-item-title-link")
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        if not title:
            return None

        url = title_link.get("href", "").strip()
        if not url:
            return None

        date_elem = item.find("p", class_="river-item-dek")
        date_text = date_elem.get_text(" ", strip=True) if date_elem else ""
        start_date = self._parse_date_text(date_text)
        if not start_date:
            return None

        location = ""
        label = item.find("p", class_="river-item-label")
        if label:
            location_span = label.find("span")
            if location_span:
                location = location_span.get_text(" ", strip=True)

        description = date_text[:500] if date_text else ""

        return Event(
            title=title,
            start_date=start_date,
            location=location,
            description=description,
            url=url,
        )

    @staticmethod
    def _parse_date_text(date_text: str) -> Optional[datetime]:
        """Parse event date/time text from card body."""
        if not date_text:
            return None

        normalized = re.sub(r"\s+", " ", date_text).strip()
        date_match = re.search(
            r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+)?"
            r"([A-Za-z]{3,9}\s+\d{1,2}(?:,\s*\d{4})?)",
            normalized,
        )
        if not date_match:
            return None

        date_part = date_match.group(1).strip()
        now = datetime.now()

        parsed_date = None
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                parsed_date = datetime.strptime(date_part, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            for fmt in ("%B %d", "%b %d"):
                try:
                    parsed_date = datetime.strptime(
                        f"{date_part}, {now.year}", f"{fmt}, %Y"
                    )
                    if parsed_date.date() < now.date():
                        parsed_date = parsed_date.replace(year=now.year + 1)
                    break
                except ValueError:
                    continue

        if not parsed_date:
            return None

        time_match = re.search(r"(\d{1,2}:\d{2}\s*[APap][Mm])", normalized)
        if time_match:
            try:
                parsed_time = datetime.strptime(
                    time_match.group(1).upper().replace("  ", " "), "%I:%M %p"
                )
                parsed_date = parsed_date.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute,
                    second=0,
                    microsecond=0,
                )
            except ValueError:
                pass

        return parsed_date
