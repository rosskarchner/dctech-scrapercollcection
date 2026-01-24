#!/usr/bin/env python3
"""Test the enhanced ACTIAC scraper capabilities with sample data."""
from datetime import datetime
from scrapers.actiac_scraper import ActiacScraper
import json


def test_json_ld_parsing():
    """Test JSON-LD parsing from Cvent-style event pages."""
    print("Testing JSON-LD parsing...")
    
    scraper = ActiacScraper()
    
    # Sample JSON-LD data from a typical Cvent event page
    sample_json_ld = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Emerging Tech Demo Day 2026",
        "startDate": "2026-03-18T10:00:00",
        "endDate": "2026-03-18T15:00:00",
        "location": {
            "@type": "Place",
            "name": "Carahsoft Conference Center",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Reston",
                "addressRegion": "VA"
            }
        },
        "description": "Technology Solution Showcase and Exchange: Where government challenges meet ready solutions."
    }
    
    event = scraper._parse_json_ld(sample_json_ld, "https://www.cvent.com/events/example")
    
    if event:
        print(f"✓ Successfully parsed JSON-LD event:")
        print(f"  Title: {event.title}")
        print(f"  Date: {event.start_date}")
        print(f"  Location: {event.location}")
        print(f"  Description: {event.description[:60]}...")
    else:
        print("✗ Failed to parse JSON-LD")
    
    print()
    return event is not None


def test_google_calendar_link_parsing():
    """Test parsing Google Calendar add-to-calendar links."""
    print("Testing Google Calendar link parsing...")
    
    scraper = ActiacScraper()
    
    # Sample Google Calendar link with event data
    sample_link = (
        "https://www.google.com/calendar/render?action=TEMPLATE"
        "&text=Emerging+Tech+Demo+Day+2026"
        "&dates=20260318T100000/20260318T150000"
        "&location=Carahsoft+Conference+Center,+Reston,+VA"
        "&details=Technology+Solution+Showcase+and+Exchange"
    )
    
    event = scraper._parse_google_calendar_link(sample_link, "Fallback Title")
    
    if event:
        print(f"✓ Successfully parsed calendar link:")
        print(f"  Title: {event.title}")
        print(f"  Date: {event.start_date}")
        print(f"  Location: {event.location}")
        print(f"  Description: {event.description[:60]}...")
    else:
        print("✗ Failed to parse calendar link")
    
    print()
    return event is not None


def test_date_parsing():
    """Test various date format parsing."""
    print("Testing date parsing...")
    
    scraper = ActiacScraper()
    
    test_cases = [
        ("March 18, 2026", datetime(2026, 3, 18)),
        ("Mar 18, 2026", datetime(2026, 3, 18)),
        ("3/18/2026", datetime(2026, 3, 18)),
        ("2026-03-18", datetime(2026, 3, 18)),
    ]
    
    all_passed = True
    for date_str, expected in test_cases:
        result = scraper._parse_date(date_str)
        if result == expected:
            print(f"  ✓ '{date_str}' → {result}")
        else:
            print(f"  ✗ '{date_str}' → {result} (expected {expected})")
            all_passed = False
    
    print()
    return all_passed


def main():
    """Run all tests."""
    print("="*70)
    print("ACTIAC Enhanced Scraper Tests")
    print("="*70)
    print()
    
    results = []
    results.append(("JSON-LD Parsing", test_json_ld_parsing()))
    results.append(("Calendar Link Parsing", test_google_calendar_link_parsing()))
    results.append(("Date Parsing", test_date_parsing()))
    
    print("="*70)
    print("Test Results:")
    print("="*70)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    print()
    if all_passed:
        print("All tests passed! ✓")
        print()
        print("The enhanced scraper is ready to extract events from:")
        print("  1. Cvent event pages (via JSON-LD)")
        print("  2. Pages with Google Calendar links")
        print("  3. Standard HTML event listings")
        print()
        print("Once the ACTIAC website allows automated access,")
        print("these methods will work automatically.")
    else:
        print("Some tests failed.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
