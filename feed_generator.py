"""Generate iCal feeds from scraped events."""
from icalendar import Calendar, Event as ICalEvent
from datetime import datetime
from typing import List
from scrapers.base_scraper import Event
import os
import hashlib


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
        
        for event in events:
            ical_event = ICalEvent()
            ical_event.add('summary', event.title)
            ical_event.add('dtstart', event.start_date)
            ical_event.add('dtend', event.end_date)
            
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
