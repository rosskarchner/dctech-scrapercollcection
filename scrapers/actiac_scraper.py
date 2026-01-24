"""Scraper for ACTIAC events."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
import re
from .base_scraper import BaseScraper, Event


class ActiacScraper(BaseScraper):
    """Scraper for ACTIAC upcoming events."""
    
    def __init__(self):
        super().__init__(
            name="ACTIAC",
            url="https://www.actiac.org/upcoming-events"
        )
    
    def scrape(self) -> List[Event]:
        """Scrape events from ACTIAC website."""
        events = []
        
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all event items on the page
            # ACTIAC typically uses specific classes for event listings
            event_items = soup.find_all('div', class_='views-row')
            
            if not event_items:
                # Try alternative selectors
                event_items = soup.find_all('article', class_='node')
            
            for item in event_items:
                try:
                    event = self._parse_event_item(item)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error parsing event item: {e}")
                    continue
            
            print(f"Found {len(events)} events from {self.name}")
            
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
        
        return events
    
    def _parse_event_item(self, item) -> Event:
        """Parse a single event item from the HTML."""
        # Extract title
        title_elem = item.find(['h2', 'h3', 'h4'], class_=re.compile('title|heading'))
        if not title_elem:
            title_elem = item.find(['h2', 'h3', 'h4'])
        
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        # Extract date
        date_elem = item.find('time')
        if not date_elem:
            date_elem = item.find(class_=re.compile('date|time'))
        
        if not date_elem:
            # Look for date patterns in text
            text = item.get_text()
            date_match = re.search(r'(\w+ \d{1,2},? \d{4})', text)
            if date_match:
                date_str = date_match.group(1)
            else:
                return None
        else:
            date_str = date_elem.get_text(strip=True)
        
        # Parse date
        start_date = self._parse_date(date_str)
        if not start_date:
            return None
        
        # Extract location
        location = ""
        location_elem = item.find(class_=re.compile('location|venue|address'))
        if location_elem:
            location = location_elem.get_text(strip=True)
        else:
            # Look for common location patterns
            text = item.get_text()
            location_match = re.search(r'(Reston|Arlington|Washington|DC|Virginia|VA)', text, re.IGNORECASE)
            if location_match:
                location = location_match.group(1)
        
        # Extract URL
        url = ""
        link_elem = item.find('a', href=True)
        if link_elem:
            url = link_elem['href']
            if url.startswith('/'):
                url = 'https://www.actiac.org' + url
        
        # Extract description
        description = ""
        desc_elem = item.find(class_=re.compile('description|summary|body'))
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        return Event(
            title=title,
            start_date=start_date,
            location=location,
            description=description,
            url=url
        )
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        date_str = date_str.strip()
        
        # Common date formats
        formats = [
            '%B %d, %Y',  # March 18, 2026
            '%b %d, %Y',  # Mar 18, 2026
            '%B %d %Y',   # March 18 2026
            '%b %d %Y',   # Mar 18 2026
            '%m/%d/%Y',   # 03/18/2026
            '%Y-%m-%d',   # 2026-03-18
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try to extract date from longer strings
        for pattern in [r'(\w+ \d{1,2},? \d{4})', r'(\d{1,2}/\d{1,2}/\d{4})']:
            match = re.search(pattern, date_str)
            if match:
                extracted = match.group(1)
                for fmt in formats:
                    try:
                        return datetime.strptime(extracted, fmt)
                    except ValueError:
                        continue
        
        return None
