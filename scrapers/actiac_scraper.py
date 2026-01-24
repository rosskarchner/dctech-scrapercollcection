"""Scraper for ACTIAC events."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
import re
import json
from urllib.parse import urlparse, parse_qs
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = requests.get(self.url, timeout=30, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all event links on the page
            event_links = []
            
            # Look for all links that might be event pages
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                # Check if it's an event link (Cvent, self-hosted event pages, etc.)
                if any(pattern in href.lower() for pattern in ['event', 'cevent', 'cvent']):
                    if href.startswith('/'):
                        href = 'https://www.actiac.org' + href
                    event_links.append((href, link.get_text(strip=True)))
            
            print(f"Found {len(event_links)} potential event links")
            
            # Try to extract events from the main page first
            event_items = self._find_event_items(soup)
            for item in event_items:
                try:
                    event = self._parse_event_item(item)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error parsing event item: {e}")
                    continue
            
            # If we found event links, try to extract from those pages
            # (Limited to first few to avoid overwhelming the server)
            for event_url, title in event_links[:5]:
                try:
                    event = self._scrape_event_page(event_url, title, headers)
                    if event and event not in events:
                        events.append(event)
                except Exception as e:
                    print(f"Error scraping event page {event_url}: {e}")
                    continue
            
            print(f"Found {len(events)} events from {self.name}")
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"⚠️  {self.name} website is blocking automated access (403 Forbidden)")
                print(f"   This is likely due to Cloudflare bot protection.")
                print(f"   The scraper implements multiple extraction methods:")
                print(f"   - JSON-LD from Cvent event pages")
                print(f"   - Add-to-calendar URL parsing")
                print(f"   - Standard HTML parsing")
                print(f"   Once access is granted, these methods will work automatically.")
            else:
                print(f"HTTP Error scraping {self.name}: {e}")
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return events
    
    def _find_event_items(self, soup):
        """Find event items on the main page using multiple selectors."""
        event_items = []
        
        # Primary: Look for event-listing class
        event_items = soup.find_all('div', class_=re.compile('event-listing|event-item'))
        
        if not event_items:
            # Try views-row (Drupal common)
            event_items = soup.find_all('div', class_='views-row')
        
        if not event_items:
            # Try article nodes
            event_items = soup.find_all('article', class_=re.compile('node|event'))
        
        if not event_items:
            # Fallback: Look for any div with h2/h3 containing event info
            event_items = soup.find_all('div', class_=re.compile('view-content|content'))
        
        return event_items
    
    def _scrape_event_page(self, url: str, title_fallback: str, headers: dict) -> Event:
        """Scrape an individual event page.
        
        This handles:
        1. Cvent pages with JSON-LD structured data
        2. Self-hosted pages with add-to-calendar links
        """
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Try to extract JSON-LD data (common on Cvent)
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    event = self._parse_json_ld(data, url)
                    if event:
                        return event
                except:
                    continue
            
            # Method 2: Try to parse add-to-calendar links
            calendar_links = soup.find_all('a', href=lambda x: x and any(
                pattern in x.lower() for pattern in ['google.com/calendar', 'calendar.yahoo', 'outlook', '.ics']
            ))
            
            for link in calendar_links:
                href = link.get('href', '')
                if 'google.com/calendar' in href.lower():
                    event = self._parse_google_calendar_link(href, title_fallback)
                    if event:
                        return event
            
            # Method 3: Standard HTML parsing
            return self._parse_event_item(soup)
            
        except Exception as e:
            print(f"Error processing event page {url}: {e}")
            return None
    
    def _parse_json_ld(self, data: dict, url: str) -> Event:
        """Parse JSON-LD structured data to extract event information."""
        try:
            # Handle both single object and array
            if isinstance(data, list):
                data = data[0] if data else {}
            
            # Check if it's an Event type
            if data.get('@type') not in ['Event', 'EventSeries']:
                return None
            
            title = data.get('name', '')
            if not title:
                return None
            
            # Parse start date
            start_date_str = data.get('startDate', '')
            start_date = None
            if start_date_str:
                try:
                    # Handle ISO 8601 format
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                except:
                    start_date = self._parse_date(start_date_str)
            
            if not start_date:
                return None
            
            # Extract location
            location = ''
            location_data = data.get('location', {})
            if isinstance(location_data, dict):
                address = location_data.get('address', {})
                if isinstance(address, dict):
                    parts = []
                    if address.get('addressLocality'):
                        parts.append(address['addressLocality'])
                    if address.get('addressRegion'):
                        parts.append(address['addressRegion'])
                    location = ', '.join(parts)
                elif isinstance(address, str):
                    location = address
                elif location_data.get('name'):
                    location = location_data['name']
            elif isinstance(location_data, str):
                location = location_data
            
            # Extract description
            description = data.get('description', '')
            
            return Event(
                title=title,
                start_date=start_date,
                location=location,
                description=description[:500] if description else '',
                url=url
            )
            
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")
            return None
    
    def _parse_google_calendar_link(self, url: str, title_fallback: str) -> Event:
        """Parse Google Calendar add-to-calendar link parameters."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Extract text parameter which contains title and dates
            text = params.get('text', [''])[0] or title_fallback
            dates = params.get('dates', [''])[0]
            location = params.get('location', [''])[0]
            details = params.get('details', [''])[0]
            
            if not dates:
                return None
            
            # Parse dates (format: 20260318T100000/20260318T150000)
            date_parts = dates.split('/')
            if not date_parts:
                return None
            
            start_date_str = date_parts[0]
            # Parse YYYYMMDDTHHMMSS format
            try:
                if 'T' in start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y%m%dT%H%M%S')
                else:
                    start_date = datetime.strptime(start_date_str, '%Y%m%d')
            except:
                return None
            
            return Event(
                title=text,
                start_date=start_date,
                location=location,
                description=details[:500] if details else '',
                url=url
            )
            
        except Exception as e:
            print(f"Error parsing calendar link: {e}")
            return None
    
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
            # Match various date formats
            date_patterns = [
                r'(\w+\s+\d{1,2},?\s+\d{4})',  # March 18, 2026
                r'(\d{1,2}/\d{1,2}/\d{2,4})',   # 3/18/2026
                r'(\w+\s+\d{1,2})',             # March 18
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
                r'(Carahsoft Conference Center)',
                r'(Reston[,\s]*VA)',
                r'(Arlington[,\s]*VA)',
                r'(Washington[,\s]*DC)',
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
                url = 'https://www.actiac.org' + url
        
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
