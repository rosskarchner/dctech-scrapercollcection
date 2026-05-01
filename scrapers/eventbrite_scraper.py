"""Scraper for Eventbrite events via organizer ID."""
import requests
from datetime import datetime
from typing import List, Optional
import json
from .base_scraper import BaseScraper, Event


class EventbriteScraper(BaseScraper):
    """Scraper for Eventbrite events from a specific organizer.
    
    Uses the same endpoint as the eb-to-ical converter:
    https://www.eventbrite.com/org/{org_id}/showmore/
    """
    
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
    
    def scrape(self) -> List[Event]:
        """Scrape events from Eventbrite using the showmore endpoint."""
        events = []
        
        for evt_type in ["future", "past"]:
            try:
                page_events = self._scrape_events_by_type(evt_type)
                events.extend(page_events)
            except Exception as e:
                print(f"Error scraping {evt_type} events: {e}")
                continue
        
        return events
    
    def _scrape_events_by_type(self, evt_type: str) -> List[Event]:
        """Scrape events of a specific type (future or past)."""
        events = []
        page = 1
        
        while page:
            try:
                # Use the same endpoint as eb-to-ical
                eb_url = f"https://www.eventbrite.com/org/{self.organizer_id}/showmore/?type={evt_type}&page={page}"
                
                print(f"Scraping {evt_type} events, page {page}: {eb_url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(eb_url, timeout=30, headers=headers)
                response.raise_for_status()
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from {eb_url}: {e}")
                    print(f"Response text: {response.text[:500]}")
                    break
                
                # Extract events from response
                if 'data' not in data or 'events' not in data['data']:
                    print(f"No events found in response for {evt_type}, page {page}")
                    break
                
                page_events = data['data']['events']
                print(f"Found {len(page_events)} events on {evt_type} page {page}")
                
                # Parse each event
                for event_data in page_events:
                    try:
                        event = self._parse_event_from_json(event_data)
                        if event:
                            events.append(event)
                    except Exception as e:
                        print(f"Error parsing event: {e}")
                        continue
                
                # Check if there's a next page
                has_next = data.get('data', {}).get('has_next_page', False)
                page = (page + 1) if has_next else None
                
            except requests.RequestException as e:
                print(f"Request error scraping {evt_type} events: {e}")
                break
            except Exception as e:
                print(f"Unexpected error scraping {evt_type} events: {e}")
                break
        
        print(f"Total {evt_type} events scraped: {len(events)}")
        return events
    
    def _parse_event_from_json(self, event_data: dict) -> Optional[Event]:
        """Parse an event from Eventbrite JSON response."""
        try:
            title = event_data.get('name', {}).get('text', '')
            if not title:
                return None
            
            # Parse start date
            start_str = event_data.get('start', {}).get('utc')
            if not start_str:
                return None
            
            start_date = self._parse_iso_datetime(start_str)
            if not start_date:
                return None
            
            # Parse end date
            end_str = event_data.get('end', {}).get('utc')
            end_date = self._parse_iso_datetime(end_str) if end_str else start_date
            
            # Extract location
            location = ""
            venue = event_data.get('venue', {})
            if venue:
                venue_name = venue.get('name', '')
                venue_addr = venue.get('address', {}).get('localized_address_display', '')
                location_parts = []
                if venue_name:
                    location_parts.append(venue_name)
                if venue_addr:
                    location_parts.append(venue_addr)
                location = ', '.join(location_parts)
            
            # Extract description and URL
            description = event_data.get('description', {}).get('text', '')[:500]
            url = event_data.get('url', '')
            
            return Event(
                title=title,
                start_date=start_date,
                end_date=end_date,
                location=location,
                description=description,
                url=url
            )
        except Exception as e:
            print(f"Error parsing event from JSON: {e}")
            return None
    
    def _parse_iso_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        try:
            if not datetime_str:
                return None
            
            # Handle ISO 8601 format: "2026-05-01T14:00:00Z"
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1] + '+00:00'
            
            # Try parsing with timezone
            try:
                return datetime.fromisoformat(datetime_str)
            except ValueError:
                # Try without timezone
                if 'T' in datetime_str:
                    return datetime.fromisoformat(datetime_str.split('+')[0].split('Z')[0])
                else:
                    return datetime.strptime(datetime_str, '%Y-%m-%d')
        except Exception as e:
            print(f"Error parsing datetime '{datetime_str}': {e}")
            return None


