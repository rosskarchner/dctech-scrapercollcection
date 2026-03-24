"""Scraper for AIGA DC events via their RSS feed."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import re
from .base_scraper import BaseScraper, Event


class AigaDcScraper(BaseScraper):
    """Scraper for AIGA Washington, DC events.

    Fetches events from the AIGA DC RSS feed, then visits each event's
    detail page to extract precise start/end times from the embedded
    addtocalendar widget.
    """

    RSS_URL = "https://dc.aiga.org/ikit-feed/?type=events&post_types=ikit_event,ikit_event_internal"

    def __init__(self, cache=None):
        super().__init__(
            name="AIGA DC",
            url="https://dc.aiga.org/upcoming-events/?view=calendar",
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
        """Scrape events from the AIGA DC RSS feed and detail pages."""
        events = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        try:
            print(f"Fetching RSS feed: {self.RSS_URL}")
            content = self._fetch_url(self.RSS_URL, headers)
            soup = BeautifulSoup(content, "xml")

            items = soup.find_all("item")
            print(f"Found {len(items)} events in RSS feed")

            for item in items:
                try:
                    event = self._parse_rss_item(item, headers)
                    if event:
                        events.append(event)
                except Exception as e:
                    title = item.find("title")
                    title_text = title.get_text(strip=True) if title else "unknown"
                    print(f"Error parsing event '{title_text}': {e}")
                    continue

            print(f"Found {len(events)} total events from {self.name}")

        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()

        return events

    def _parse_rss_item(self, item, headers: dict) -> Optional[Event]:
        """Parse an RSS <item> and enrich with detail page data."""
        title_elem = item.find("title")
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)
        if not title:
            return None

        link_elem = item.find("link")
        url = link_elem.get_text(strip=True) if link_elem else ""

        # Extract plain-text description from RSS (strip HTML)
        desc_elem = item.find("description")
        description = ""
        if desc_elem:
            desc_html = desc_elem.get_text()
            desc_soup = BeautifulSoup(desc_html, "html.parser")
            description = desc_soup.get_text(separator=" ", strip=True)[:500]

        # Try to get precise date/time from the event detail page
        start_date = None
        end_date = None
        location = ""

        if url:
            try:
                detail = self._parse_detail_page(url, headers)
                start_date = detail.get("start_date")
                end_date = detail.get("end_date")
                location = detail.get("location", "")
            except Exception as e:
                print(f"  Could not fetch detail page for '{title}': {e}")

        # Fallback: parse date from RSS description HTML
        if not start_date and desc_elem:
            start_date = self._parse_date_from_description(desc_elem.get_text())

        if not start_date:
            print(f"  Skipping '{title}': no date found")
            return None

        # Default location for AIGA DC chapter events
        if not location or location == "...":
            location = "Washington, DC"

        return Event(
            title=title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description,
            url=url,
        )

    def _parse_detail_page(self, url: str, headers: dict) -> dict:
        """Extract structured event data from an event detail page.

        Looks for the addtocalendar widget which contains precise
        start/end times and timezone info.
        """
        result = {}
        content = self._fetch_url(url, headers)
        soup = BeautifulSoup(content, "html.parser")

        # The addtocalendar widget has structured date/time data
        atc = soup.find("span", class_="addtocalendar")
        if atc:
            start_var = atc.find("var", class_="atc_date_start")
            end_var = atc.find("var", class_="atc_date_end")
            loc_var = atc.find("var", class_="atc_location")

            if start_var:
                result["start_date"] = self._parse_atc_datetime(
                    start_var.get_text(strip=True)
                )
            if end_var:
                result["end_date"] = self._parse_atc_datetime(
                    end_var.get_text(strip=True)
                )
            if loc_var:
                loc_text = loc_var.get_text(strip=True)
                if loc_text and loc_text != "...":
                    result["location"] = loc_text

        # Fallback: parse from the event-date / event-time spans
        if "start_date" not in result:
            date_span = soup.find("span", class_="event-date")
            time_span = soup.find("span", class_="event-time")
            if date_span:
                date_text = date_span.get_text(strip=True)
                time_text = time_span.get_text(strip=True) if time_span else ""
                result["start_date"] = self._parse_display_datetime(
                    date_text, time_text
                )

        return result

    @staticmethod
    def _parse_atc_datetime(dt_str: str) -> Optional[datetime]:
        """Parse addtocalendar datetime format: '2026-04-14 13:00:00'."""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_display_datetime(
        date_str: str, time_str: str = ""
    ) -> Optional[datetime]:
        """Parse display-format date/time such as 'Tue, Apr 14, 2026' and '1:00 PM - 2:00 PM'.

        Returns the start datetime.
        """
        date_str = date_str.strip().rstrip(",")
        # Strip leading day-of-week like "Tue, "
        date_str = re.sub(r"^\w{3},?\s*", "", date_str)

        date_formats = [
            "%B %d, %Y",   # April 14, 2026
            "%b %d, %Y",   # Apr 14, 2026
            "%B %d %Y",
            "%b %d %Y",
            "%m/%d/%Y",
        ]

        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            return None

        # Try to parse start time from time string like "1:00 PM - 2:00 PM"
        if time_str:
            time_match = re.match(r"(\d{1,2}:\d{2}\s*[APap][Mm])", time_str.strip())
            if time_match:
                try:
                    t = datetime.strptime(time_match.group(1).strip(), "%I:%M %p")
                    parsed_date = parsed_date.replace(hour=t.hour, minute=t.minute)
                except ValueError:
                    pass

        return parsed_date

    @staticmethod
    def _parse_date_from_description(desc_html: str) -> Optional[datetime]:
        """Extract a date from the RSS description HTML.

        Looks for '<div class="item-date">Tuesday, April 14, 2026</div>'.
        """
        soup = BeautifulSoup(desc_html, "html.parser")
        date_div = soup.find("div", class_="item-date")
        if date_div:
            date_text = date_div.get_text(strip=True)
            # Strip day-of-week prefix
            date_text = re.sub(r"^\w+,\s*", "", date_text)
            for fmt in ("%B %d, %Y", "%b %d, %Y"):
                try:
                    return datetime.strptime(date_text.strip(), fmt)
                except ValueError:
                    continue
        return None
