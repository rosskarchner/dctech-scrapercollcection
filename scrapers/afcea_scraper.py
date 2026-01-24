"""Scraper for AFCEA events."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
import re
from .base_scraper import BaseScraper, Event


class AfceaScraper(BaseScraper):
    """Scraper for AFCEA events."""
    
    def __init__(self):
        super().__init__(
            name="AFCEA",
            url="https://www.afcea.org/events"
        )
    
    def scrape(self) -> List[Event]:
        """Scrape events from AFCEA website."""
        events = []
        
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all event items on the page
            # AFCEA typically uses specific classes for event listings
            event_items = soup.find_all('div', class_=re.compile('event|item'))
            
            if not event_items:
                # Try alternative selectors
                event_items = soup.find_all('article')
            
            if not event_items:
                event_items = soup.find_all('div', class_='views-row')
            
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
        title_elem = item.find(['h2', 'h3', 'h4'], class_=re.compile('title|heading|name'))
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
            # Match formats like "2/6" or "February 6" or "Feb 6"
            date_match = re.search(r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?|\w+ \d{1,2},? \d{4})', text)
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
            location_match = re.search(r'(Reston|Arlington|Washington|DC|Virginia|VA|NOVA)', text, re.IGNORECASE)
            if location_match:
                location = location_match.group(1)
        
        # Extract URL
        url = ""
        link_elem = item.find('a', href=True)
        if link_elem:
            url = link_elem['href']
            if url.startswith('/'):
                url = 'https://www.afcea.org' + url
        
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
        
        # If year is missing, assume current year or next year
        current_year = datetime.now().year
        
        # Common date formats
        formats = [
            '%B %d, %Y',  # February 6, 2026
            '%b %d, %Y',  # Feb 6, 2026
            '%B %d %Y',   # February 6 2026
            '%b %d %Y',   # Feb 6 2026
            '%m/%d/%Y',   # 2/6/2026
            '%m/%d/%y',   # 2/6/26
            '%Y-%m-%d',   # 2026-02-06
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try without year and add current/next year
        formats_no_year = [
            '%B %d',  # February 6
            '%b %d',  # Feb 6
            '%m/%d',  # 2/6
        ]
        
        for fmt in formats_no_year:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Add year
                result = parsed.replace(year=current_year)
                # If date is in the past, use next year
                if result < datetime.now():
                    result = result.replace(year=current_year + 1)
                return result
            except ValueError:
                continue
        
        # Try to extract date from longer strings
        for pattern in [r'(\w+ \d{1,2},? \d{4})', r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)']:
            match = re.search(pattern, date_str)
            if match:
                extracted = match.group(1)
                return self._parse_date(extracted)
        
        return None
