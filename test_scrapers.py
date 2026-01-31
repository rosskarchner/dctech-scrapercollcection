#!/usr/bin/env python3
"""Test script to validate scraper components."""
from datetime import datetime
from scrapers.base_scraper import Event
from scrapers.afcea_scraper import AfceaScraper
from feed_generator import FeedGenerator
from scrape import is_dmv_event


def test_event_creation():
    """Test Event object creation."""
    print("Testing Event creation...")
    event = Event(
        title="Test Event",
        start_date=datetime(2026, 3, 18),
        location="Reston, VA",
        description="A test event",
        url="https://example.com"
    )
    assert event.title == "Test Event"
    assert event.location == "Reston, VA"
    print("✓ Event creation works\n")


def test_dmv_filtering():
    """Test DMV location filtering."""
    print("Testing DMV location filtering...")
    
    # Test events that should be included (MD, DC, VA)
    dmv_events = [
        Event("Event 1", datetime(2026, 3, 18), location="Reston, VA"),
        Event("Event 2", datetime(2026, 3, 18), location="Washington, DC"),
        Event("Event 3", datetime(2026, 3, 18), location="Ellicott City, MD"),
        Event("Event 4", datetime(2026, 3, 18), location="Arlington VA"),
        Event("Event 5", datetime(2026, 3, 18), location="Maryland"),
        Event("Event 6", datetime(2026, 3, 18), location="Virginia"),
        Event("Event 7", datetime(2026, 3, 18), location="Annapolis Junction, MD 20701"),
        Event("Event 8", datetime(2026, 3, 18), location="National Defense University, Washington, DC"),
    ]
    
    for event in dmv_events:
        result = is_dmv_event(event)
        assert result, f"Failed: {event.location} should be in DMV"
        print(f"  ✓ '{event.location}' is correctly identified as DMV")
    
    # Test events that should be excluded
    non_dmv_events = [
        Event("Event 1", datetime(2026, 3, 18), location="San Diego, CA"),
        Event("Event 2", datetime(2026, 3, 18), location="Colorado Springs, CO"),
        Event("Event 3", datetime(2026, 3, 18), location="Tampa, FL"),
        Event("Event 4", datetime(2026, 3, 18), location="Burlington, MA"),
        Event("Event 5", datetime(2026, 3, 18), location="Ramstein, Germany"),
        Event("Event 6", datetime(2026, 3, 18), location="Ottawa, ON"),
        Event("Event 7", datetime(2026, 3, 18), location="Web"),
        Event("Event 8", datetime(2026, 3, 18), location=""),
    ]
    
    for event in non_dmv_events:
        result = is_dmv_event(event)
        assert not result, f"Failed: {event.location} should NOT be in DMV"
        print(f"  ✓ '{event.location}' is correctly identified as non-DMV")
    
    print()


def test_date_parsing():
    """Test date parsing in scrapers."""
    print("Testing date parsing...")
    
    afcea = AfceaScraper()
    test_dates_afcea = [
        ("February 6, 2026", datetime(2026, 2, 6)),
        ("2/6/2026", datetime(2026, 2, 6)),
    ]
    
    for date_str, expected in test_dates_afcea:
        result = afcea._parse_date(date_str)
        assert result == expected, f"Failed to parse {date_str}"
        print(f"  ✓ Parsed '{date_str}' → {result}")
    
    print()


def test_feed_generation():
    """Test iCal feed generation."""
    print("Testing iCal feed generation...")
    
    events = [
        Event(
            title="AFCEA NOVA February Luncheon",
            start_date=datetime(2026, 2, 6, 12, 0),
            location="Reston, VA",
            description="Monthly luncheon",
            url="https://www.afcea.org/event/456"
        ),
    ]
    
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        output_file = feed_gen.generate_feed(events, "Test", "test.ics")
        
        assert os.path.exists(output_file), "Feed file not created"
        
        # Check file content
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'BEGIN:VCALENDAR' in content
            assert 'AFCEA NOVA February Luncheon' in content
            print(f"  ✓ Generated feed at {output_file}")
            print(f"  ✓ Feed contains {len(events)} events")
    
    print()


def main():
    """Run all tests."""
    print("="*60)
    print("Running Event Scraper Tests")
    print("="*60 + "\n")
    
    try:
        test_event_creation()
        test_dmv_filtering()
        test_date_parsing()
        test_feed_generation()
        
        print("="*60)
        print("All tests passed! ✓")
        print("="*60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
