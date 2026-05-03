"""Scraper for NOVAAR (Northern Virginia Association of Rocketry) calendar events."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
import re
from .base_scraper import BaseScraper, Event


class NovaaScraper(BaseScraper):
    """Scraper for NOVAAR calendar events."""
    
    def __init__(self, cache=None):
        super().__init__(
            name="NOVAAR",
            url="https://novaar.org/drupal10/calendar_event/"
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
        response = requests.get(url, timeout=30, headers=headers, verify=False)
        response.raise_for_status()
        
        # Store in cache if available
        if self.cache:
            self.cache.set(url, response.content)
        
        return response.content
    
    def scrape(self) -> List[Event]:
        """Scrape events from NOVAAR calendar."""
        events = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            print(f"Scraping {self.url}")
            
            content = self._fetch_url(self.url, headers)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all event links in the calendar view
            # The calendar displays events as links within a table
            event_links = soup.find_all('a', href=re.compile(r'/drupal10/node/\d+'))
            
            # Track seen event URLs to avoid duplicates
            seen_urls = set()
            
            for link in event_links:
                href = link.get('href', '')
                
                # Only process node links (events)
                if '/drupal10/node/' not in href:
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    event_url = f"https://novaar.org{href}"
                else:
                    event_url = href
                
                # Skip if we've already processed this event
                if event_url in seen_urls:
                    continue
                
                seen_urls.add(event_url)
                
                try:
                    event = self._fetch_and_parse_event(event_url, headers)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error parsing event from {event_url}: {e}")
                    continue
            
            print(f"Found {len(events)} events from {self.name}")
            
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return events
    
    def _fetch_and_parse_event(self, event_url: str, headers: dict) -> Optional[Event]:
        """Fetch and parse a single event from its node page."""
        try:
            content = self._fetch_url(event_url, headers)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Skip non-event pages
            body = soup.find('body')
            if not body or 'page-node-type-event' not in body.get('class', []):
                return None
            
            # Extract title from page title tag or h1
            title = None
            
            # Try page title first
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text(strip=True)
                # Remove the " | Northern Virginia Association of Rocketry" part
                if '|' in page_title:
                    title = page_title.split('|')[0].strip()
                else:
                    title = page_title
            
            # Fallback to h1 if title not found
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            if not title or len(title) < 3:
                return None
            
            # Extract date
            date_field = soup.find('div', class_='field--name-field-date-event')
            start_date = None
            
            if date_field:
                time_elem = date_field.find('time')
                if time_elem:
                    datetime_str = time_elem.get('datetime')
                    if datetime_str:
                        try:
                            start_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        except:
                            pass
            
            if not start_date:
                return None
            
            # Extract end time if available
            end_date = start_date
            time_field = soup.find('div', class_='field--name-field-time')
            if time_field:
                time_text = time_field.get_text(strip=True)
                # Parse time range like "10:00 am ~ 05:00 pm"
                if '~' in time_text:
                    times = time_text.split('~')
                    if len(times) == 2:
                        end_time_str = times[1].strip()
                        try:
                            # Parse end time and apply to the same date
                            end_time = datetime.strptime(end_time_str, '%I:%M %p').time()
                            end_date = start_date.replace(
                                hour=end_time.hour,
                                minute=end_time.minute,
                                second=0
                            )
                        except:
                            pass
            
            # Extract location
            location = "Great Meadow, VA"  # Default NOVAAR location
            body = soup.find('div', class_='field--name-body')
            if body:
                body_text = body.get_text(strip=True)
                # Check for location mentions
                if 'Great Meadow' in body_text:
                    location = "Great Meadow, VA"
                elif 'Meadow' in body_text:
                    location = "Great Meadow, VA"
                elif 'meeting' in body_text.lower():
                    location = "NOVAAR Meeting, VA"
            
            # Extract description
            description = ""
            if body:
                description = body.get_text(strip=True)[:500]
            
            return Event(
                title=title,
                start_date=start_date,
                end_date=end_date,
                location=location,
                description=description,
                url=event_url
            )
            
        except Exception as e:
            print(f"Error fetching event from {event_url}: {e}")
            return None
