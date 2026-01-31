#!/usr/bin/env python3
"""Main script to run all scrapers and generate iCal feeds."""
import sys
import re
import logging
from scrapers import AfceaScraper
from feed_generator import FeedGenerator
from html_cache import HTMLCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)


def is_dmv_event(event) -> bool:
    """Check if an event is in the DMV area (DC, MD, or VA).
    
    Args:
        event: Event object with a location field
    
    Returns:
        True if the event location contains DC, MD, or VA, False otherwise
    """
    if not event.location:
        return False
    
    location = event.location.upper()
    
    # Check for state abbreviations or full names
    # Use word boundaries to avoid false matches (e.g., "MADE" containing "MD")
    patterns = [
        r'\bDC\b',           # District of Columbia
        r'\bMD\b',           # Maryland
        r'\bVA\b',           # Virginia
        r'\bMARYLAND\b',
        r'\bVIRGINIA\b',
        r'\bWASHINGTON,?\s*DC\b',
    ]
    
    for pattern in patterns:
        if re.search(pattern, location):
            return True
    
    return False


def main():
    """Run all scrapers and generate feeds."""
    # Initialize HTML cache
    cache = HTMLCache(cache_dir=".cache/html")
    
    # Clear expired entries at the start
    cache.clear_expired()
    
    # Print cache statistics
    stats = cache.get_stats()
    print(f"Cache initialized: {stats['valid_entries']} valid entries, {stats['total_size_bytes']} bytes")
    
    # Initialize scrapers with cache
    scrapers = [
        AfceaScraper(cache=cache),
    ]
    
    # Initialize feed generator
    feed_gen = FeedGenerator(output_dir="output")
    
    print("Starting event scraping...\n")
    
    # Run each scraper and generate feed
    total_events = 0
    for scraper in scrapers:
        print(f"\n{'='*60}")
        print(f"Scraping {scraper.name} from {scraper.url}")
        print('='*60)
        
        try:
            events = scraper.scrape()
            
            # Filter events to only include MD, DC, or VA locations
            filtered_events = [event for event in events if is_dmv_event(event)]
            
            if events:
                print(f"\nExtracted {len(events)} total events")
                print(f"Filtered to {len(filtered_events)} events in MD, DC, or VA\n")
            
            if filtered_events:
                print(f"Events in MD, DC, or VA:")
                for i, event in enumerate(filtered_events, 1):
                    print(f"{i}. {event.title}")
                    print(f"   Date: {event.start_date.strftime('%B %d, %Y')}")
                    print(f"   Location: {event.location}")
                    print()
                
                # Generate iCal feed
                filename = scraper.get_feed_filename()
                feed_gen.generate_feed(filtered_events, scraper.name, filename)
                total_events += len(filtered_events)
            else:
                print(f"No events found in MD, DC, or VA for {scraper.name}")
        
        except Exception as e:
            print(f"Error processing {scraper.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"Scraping complete! Total events: {total_events}")
    print('='*60)
    
    return 0 if total_events > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
