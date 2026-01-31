"""Scraper for AFCEA events."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import re
from .base_scraper import BaseScraper, Event


class AfceaScraper(BaseScraper):
    """Scraper for AFCEA events."""
    
    # Maximum number of pages to scrape as a safety limit to prevent infinite loops
    # AFCEA currently has ~12 pages, so 50 provides a generous buffer
    MAX_PAGES = 50
    
    def __init__(self, cache=None):
        super().__init__(
            name="AFCEA",
            url="https://www.afcea.org/events"
        )
        self.cache = cache
    
    def _fetch_url(self, url: str, headers: dict) -> bytes:
        """Fetch URL with caching support.
        
        Args:
            url: URL to fetch
            headers: HTTP headers to use
        
        Returns:
            Response content as bytes
        """
        # Try to get from cache first
        if self.cache:
            cached_content = self.cache.get(url)
            if cached_content is not None:
                return cached_content
        
        # Cache miss - fetch from network
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Store in cache if available
        if self.cache:
            self.cache.set(url, response.content)
        
        return response.content
    
    def scrape(self) -> List[Event]:
        """Scrape events from AFCEA website with pagination support."""
        events = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Start with the first page
            page_num = 0
            
            while page_num < self.MAX_PAGES:
                # Construct URL for the current page
                if page_num == 0:
                    page_url = self.url
                else:
                    page_url = f"{self.url}?page={page_num}"
                
                print(f"Scraping page {page_num + 1}: {page_url}")
                
                content = self._fetch_url(page_url, headers)
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all event items on the page
                # Try multiple selectors based on AFCEA's structure
                event_items = []
                
                # Primary: Look for event-listing/event-item class
                event_items = soup.find_all('div', class_=re.compile('event-listing|event-item|event'))
                
                if not event_items:
                    # Try calendar items
                    event_items = soup.find_all('div', class_=re.compile('calendar|cal-item'))
                
                if not event_items:
                    # Try article elements
                    event_items = soup.find_all('article')
                
                if not event_items:
                    # Try views-row (common CMS pattern)
                    event_items = soup.find_all('div', class_='views-row')
                
                if not event_items:
                    # Fallback: Look for any container with event information
                    event_items = soup.find_all('div', class_=re.compile('view-content|content|list'))
                
                page_event_count = 0
                for item in event_items:
                    try:
                        event = self._parse_event_item(item)
                        if event:
                            events.append(event)
                            page_event_count += 1
                    except Exception as e:
                        print(f"Error parsing event item: {e}")
                        continue
                
                print(f"Found {page_event_count} events on page {page_num + 1}")
                
                # Check if there's a next page
                pager = soup.find('nav', class_='pager')
                if pager:
                    next_link = pager.find('a', rel='next')
                    if next_link and next_link.get('href'):
                        page_num += 1
                    else:
                        print("No next page found, stopping pagination")
                        break
                else:
                    # No pager found, this is likely a single-page result or we've reached the end
                    if not event_items:
                        print(f"No pagination and no events found on page {page_num + 1}, stopping")
                    else:
                        print("No pagination found, assuming single-page result")
                    break
            
            print(f"Found {len(events)} total events from {self.name} across {page_num + 1} pages")
            
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return events
    
    def _parse_event_item(self, item) -> Event:
        """Parse a single event item from the HTML."""
        # Extract title
        title_elem = item.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile('title|heading|event-title|name'))
        if not title_elem:
            title_elem = item.find(['h1', 'h2', 'h3', 'h4'])
        
        if not title_elem:
            # Sometimes title is in a link
            title_elem = item.find('a', class_=re.compile('title|heading'))
        
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        
        # Skip if title doesn't look like an event
        if not title or len(title) < 5:
            return None
        
        # Extract date
        date_elem = item.find('time')
        if not date_elem:
            date_elem = item.find(class_=re.compile('date|time|event-date'))
        
        date_str = None
        if date_elem:
            date_str = date_elem.get_text(strip=True)
            # Also check for datetime attribute
            if not date_str and date_elem.get('datetime'):
                date_str = date_elem.get('datetime')
        
        if not date_str:
            # Look for date patterns in the entire item text
            text = item.get_text()
            # Match various date formats including short dates like "2/6"
            date_patterns = [
                r'(\w+\s+\d{1,2},?\s+\d{4})',  # February 6, 2026
                r'(\d{1,2}/\d{1,2}/\d{2,4})',   # 2/6/2026 or 2/6/26
                r'(\d{1,2}/\d{1,2})',           # 2/6
                r'(\w+\s+\d{1,2})',             # February 6
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    date_str = date_match.group(1)
                    break
        
        if not date_str:
            return None
        
        # Parse date
        start_date = self._parse_date(date_str)
        if not start_date:
            return None
        
        # Extract location
        location = ""
        location_elem = item.find(class_=re.compile('location|venue|address|event-location'))
        if location_elem:
            location = location_elem.get_text(strip=True)
        else:
            # Look for common location patterns
            text = item.get_text()
            location_patterns = [
                r'(Reston[,\s]*VA)',
                r'(Arlington[,\s]*VA)',
                r'(Washington[,\s]*DC)',
                r'(NOVA)',
            ]
            for pattern in location_patterns:
                location_match = re.search(pattern, text, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1)
                    break
        
        # Extract URL
        url = ""
        link_elem = item.find('a', href=True)
        if link_elem:
            url = link_elem['href']
            if url.startswith('/'):
                url = 'https://www.afcea.org' + url
        
        # Extract description
        description = ""
        desc_elem = item.find(class_=re.compile('description|summary|body|event-description'))
        if desc_elem:
            description = desc_elem.get_text(strip=True)[:500]  # Limit to 500 chars
        
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
