"""Base scraper class for event scrapers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union
from datetime import date, datetime


class Event:
    """Represents a single event.

    start_date/end_date may be a `date` when only the day is known (no
    reliable time-of-day was found), or a `datetime` when a real time is
    known.
    """

    def __init__(self, title: str, start_date: Union[date, datetime], location: str = "",
                 description: str = "", url: str = "", end_date: Optional[Union[date, datetime]] = None):
        self.title = title
        self.start_date = start_date
        self.end_date = end_date or start_date
        self.location = location
        self.description = description
        self.url = url
    
    def __repr__(self):
        return f"Event(title='{self.title}', date={self.start_date}, location='{self.location}')"


class BaseScraper(ABC):
    """Base class for all event scrapers."""
    
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
    
    @abstractmethod
    def scrape(self) -> List[Event]:
        """Scrape events from the website. Must be implemented by subclasses."""
        pass
    
    def get_feed_filename(self) -> str:
        """Get the filename for the iCal feed."""
        return f"{self.name.lower().replace(' ', '_')}.ics"
