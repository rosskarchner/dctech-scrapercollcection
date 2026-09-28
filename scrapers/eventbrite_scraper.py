"""Scraper for Eventbrite events via organizer ID."""
import requests
from datetime import datetime
from typing import List, Optional
import json
import re
from .base_scraper import BaseScraper, Event


class EventbriteScraper(BaseScraper):
    """Scraper for Eventbrite events from a specific organizer.

    Reads the organizer's profile page (e.g.
    https://www.eventbrite.com/o/{org_id}) and parses the upcoming events
    out of its embedded __NEXT_DATA__ JSON. Eventbrite's old
    /org/{id}/showmore/ JSON endpoint (previously used here) now returns a
    403 from CloudFront for non-browser requests; the profile page itself
    still renders normally and already contains the same event data
    server-side.
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    NEXT_DATA_RE = re.compile(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
    )

    def __init__(self, organizer_id: str, organizer_name: str = "Eventbrite", cache=None):
        """Initialize Eventbrite scraper.

        Args:
            organizer_id: Eventbrite organizer ID
            organizer_name: Display name for the organizer
            cache: Optional HTML cache for response caching
        """
        super().__init__(
            name=organizer_name,
            url=f"https://www.eventbrite.com/o/{organizer_id}"
        )
        self.organizer_id = organizer_id
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
        """Scrape upcoming events from the organizer's profile page."""
        events = []

        try:
            print(f"Scraping organizer page: {self.url}")
            content = self._fetch_url(self.url, self.HEADERS)

            match = self.NEXT_DATA_RE.search(content.decode('utf-8', errors='ignore'))
            if not match:
                print(f"Could not find event data on organizer page {self.url}")
                return events

            data = json.loads(match.group(1))
            page_props = data.get('props', {}).get('pageProps', {})

            if page_props.get('upcomingEventsFailed'):
                print(f"Eventbrite reported a failure loading events for organizer {self.organizer_id}")
                return events

            if page_props.get('hasMoreUpcoming'):
                print(
                    f"Warning: organizer {self.organizer_id} has more upcoming events than "
                    "this page shows; pagination isn't implemented, so some events may be missing"
                )

            raw_events = page_props.get('upcomingEvents', [])
            print(f"Found {len(raw_events)} upcoming events")

            for raw_event in raw_events:
                try:
                    event = self._parse_event(raw_event)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping {self.name}: {e}")

        return events

    def _parse_event(self, raw_event: dict) -> Optional[Event]:
        """Parse a single event from the organizer page's embedded JSON."""
        if raw_event.get('is_cancelled'):
            return None

        title = raw_event.get('name', '')
        if not title:
            return None

        start_date = self._combine_date_time(raw_event.get('start_date'), raw_event.get('start_time'))
        if not start_date:
            return None

        end_date = self._combine_date_time(raw_event.get('end_date'), raw_event.get('end_time')) or start_date

        location = ""
        venue = raw_event.get('primary_venue')
        if venue:
            venue_name = venue.get('name', '')
            venue_addr = venue.get('address', {}).get('localized_address_display', '')
            location = ', '.join(part for part in (venue_name, venue_addr) if part)

        description = (raw_event.get('summary') or '')[:500]
        url = raw_event.get('url', '')

        return Event(
            title=title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description,
            url=url
        )

    @staticmethod
    def _combine_date_time(date_str: Optional[str], time_str: Optional[str]):
        """Combine Eventbrite's separate date/time fields. Returns a
        datetime when a time is known, otherwise just a date."""
        if not date_str:
            return None
        try:
            if time_str:
                return datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
