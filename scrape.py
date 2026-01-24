#!/usr/bin/env python3
"""Main script to run all scrapers and generate iCal feeds."""
import sys
from scrapers import ActiacScraper, AfceaScraper
from feed_generator import FeedGenerator


def main():
    """Run all scrapers and generate feeds."""
    # Initialize scrapers
    scrapers = [
        ActiacScraper(),
        AfceaScraper(),
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
            
            if events:
                print(f"\nExtracted events:")
                for i, event in enumerate(events, 1):
                    print(f"{i}. {event.title}")
                    print(f"   Date: {event.start_date.strftime('%B %d, %Y')}")
                    print(f"   Location: {event.location}")
                    print()
                
                # Generate iCal feed
                filename = scraper.get_feed_filename()
                feed_gen.generate_feed(events, scraper.name, filename)
                total_events += len(events)
            else:
                print(f"No events found for {scraper.name}")
        
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
