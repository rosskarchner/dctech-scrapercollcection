"""Generate iCal feeds from scraped events."""
from icalendar import Calendar, Event as ICalEvent
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo
from scrapers.base_scraper import Event
import os
import hashlib

# All scraped events are for DC-area happenings; scrapers store naive
# datetimes representing this local time. Without an explicit timezone,
# the iCal spec treats them as "floating" times, and calendar clients
# (e.g. GNOME Calendar) fall back to interpreting them as UTC, shifting
# events by several hours (a midnight event appears at 8pm the day before).
EVENT_TIMEZONE = ZoneInfo("America/New_York")


class FeedGenerator:
    """Generate iCal feeds from events."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_feed(self, events: List[Event], scraper_name: str, filename: str) -> str:
        """Generate an iCal feed from a list of events.
        
        Args:
            events: List of Event objects to include in the feed
            scraper_name: Name of the scraper (used in calendar name)
            filename: Output filename for the .ics file
        
        Returns:
            Path to the generated .ics file
        """
        cal = Calendar()
        cal.add('prodid', f'-//DC Tech Events - {scraper_name}//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', f'{scraper_name} Events')
        cal.add('x-wr-caldesc', f'Events from {scraper_name}')
        cal.add('x-wr-timezone', str(EVENT_TIMEZONE))

        for event in events:
            ical_event = ICalEvent()
            ical_event.add('summary', event.title)
            ical_event.add('dtstart', self._localize(event.start_date))
            ical_event.add('dtend', self._localize(event.end_date))
            
            if event.location:
                ical_event.add('location', event.location)
            
            if event.description:
                ical_event.add('description', event.description)
            
            if event.url:
                ical_event.add('url', event.url)
            
            # Generate a unique ID for the event using deterministic hashing
            # Key UIDs off of date and URL for stability across runs
            # Use SHA-256 for better collision resistance
            uid_source = f"{event.start_date.isoformat()}|{event.url or ''}|{scraper_name}"
            uid_hash = hashlib.sha256(uid_source.encode('utf-8')).hexdigest()
            uid = f"{uid_hash}@dctech-events"
            ical_event.add('uid', uid)
            
            # Add timestamp
            ical_event.add('dtstamp', datetime.now())
            
            cal.add_component(ical_event)
        
        # Write to file
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'wb') as f:
            f.write(cal.to_ical())
        
        print(f"Generated feed: {output_path} with {len(events)} events")
        return output_path

    @staticmethod
    def _localize(dt: datetime) -> datetime:
        """Attach the DC-area timezone to a naive datetime, leaving aware ones untouched."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=EVENT_TIMEZONE)
        return dt
