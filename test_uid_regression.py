#!/usr/bin/env python3
"""Regression test for duplicate UID issue reported in the problem statement."""
from datetime import datetime
from scrapers.base_scraper import Event
from feed_generator import FeedGenerator
import tempfile
import re


def unfold_ical_lines(content):
    """Unfold iCal lines according to RFC 5545.
    
    Lines that start with a space or tab are continuations of the previous line.
    """
    lines = content.split('\n')
    unfolded = []
    for line in lines:
        # Remove \r if present
        line = line.rstrip('\r')
        if line.startswith(' ') or line.startswith('\t'):
            # This is a continuation line
            if unfolded:
                unfolded[-1] += line[1:]  # Append without the leading space
        else:
            unfolded.append(line)
    return unfolded


def test_duplicate_uid_regression():
    """
    Test that simulates the original duplicate UID problem.
    
    The problem statement mentioned duplicate UIDs on lines 6, 43, 52, and 97.
    This suggests there were at least 4 events that had duplicate UIDs.
    This test creates a scenario where events could have duplicate UIDs
    with the old hash() implementation.
    """
    print("Testing duplicate UID regression...")
    
    # Create events that might have hash collisions
    # Using the same date and similar attributes
    events = [
        Event(
            title="AFCEA Monthly Luncheon",
            start_date=datetime(2026, 2, 6, 12, 0),
            location="Reston, VA",
            description="Monthly networking luncheon",
            url="https://www.afcea.org/event/feb-luncheon"
        ),
        Event(
            title="AFCEA Tech Forum",
            start_date=datetime(2026, 2, 6, 14, 0),
            location="Reston, VA",
            description="Technology forum",
            url="https://www.afcea.org/event/tech-forum"
        ),
        Event(
            title="AFCEA Leadership Dinner",
            start_date=datetime(2026, 2, 6, 18, 0),
            location="Arlington, VA",
            description="Leadership dinner event",
            url="https://www.afcea.org/event/leadership-dinner"
        ),
        Event(
            title="AFCEA Industry Day",
            start_date=datetime(2026, 2, 6, 9, 0),
            location="Washington, DC",
            description="Industry showcase",
            url="https://www.afcea.org/event/industry-day"
        ),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        output_file = feed_gen.generate_feed(events, "AFCEA", "afcea.ics")
        
        # Read and parse the iCal file
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Unfold lines according to RFC 5545
        unfolded_lines = unfold_ical_lines(content)
        
        # Extract all UIDs
        uid_pattern = r'^UID:(.+)$'
        uids = []
        for line in unfolded_lines:
            match = re.match(uid_pattern, line)
            if match:
                uids.append(match.group(1))
        
        print(f"  Total events: {len(events)}")
        print(f"  Total UIDs found: {len(uids)}")
        print(f"  UIDs:")
        for i, uid in enumerate(uids, 1):
            print(f"    {i}. {uid}")
        
        # Check for duplicates
        unique_uids = set(uids)
        print(f"  Unique UIDs: {len(unique_uids)}")
        
        if len(uids) != len(unique_uids):
            duplicates = [uid for uid in uids if uids.count(uid) > 1]
            print(f"  ✗ FAILED: Found duplicate UIDs!")
            print(f"  Duplicates: {set(duplicates)}")
            raise AssertionError(f"UIDs are not unique! Found {len(uids) - len(unique_uids)} duplicates")
        
        # Verify all UIDs are present
        assert len(uids) == len(events), f"Expected {len(events)} UIDs, found {len(uids)}"
        
        print(f"  ✓ PASSED: All {len(uids)} UIDs are unique")
        
        # Validate iCal format
        assert 'BEGIN:VCALENDAR' in content
        assert 'END:VCALENDAR' in content
        assert content.count('BEGIN:VEVENT') == len(events)
        assert content.count('END:VEVENT') == len(events)
        print(f"  ✓ PASSED: iCal format is valid")
    
    print()


def test_uid_format():
    """Test that UID format conforms to RFC 5545."""
    print("Testing UID format compliance...")
    
    event = Event(
        title="Test Event",
        start_date=datetime(2026, 3, 18, 10, 0),
        location="Test Location",
        description="Test Description",
        url="https://example.com/test"
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        output_file = feed_gen.generate_feed([event], "TestScraper", "test.ics")
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Unfold lines according to RFC 5545
        unfolded_lines = unfold_ical_lines(content)
        
        # Extract UID
        uid_pattern = r'^UID:(.+)$'
        uids = []
        for line in unfolded_lines:
            match = re.match(uid_pattern, line)
            if match:
                uids.append(match.group(1))
        
        assert len(uids) == 1, f"Expected 1 UID, found {len(uids)}"
        uid = uids[0]
        
        print(f"  Generated UID: {uid}")
        
        # Check UID format
        # RFC 5545: UID should be globally unique and typically includes @ symbol
        assert '@' in uid, "UID should contain @ symbol for domain"
        assert len(uid) > 10, "UID should be reasonably long"
        
        # SHA-256 hash is 64 characters, plus @dctech-events
        expected_parts = uid.split('@')
        assert len(expected_parts) == 2, "UID should have format hash@domain"
        assert len(expected_parts[0]) == 64, "Hash part should be 64 characters (SHA-256)"
        assert expected_parts[1] == 'dctech-events', "Domain should be dctech-events"
        
        print(f"  ✓ PASSED: UID format is RFC 5545 compliant")
    
    print()


def test_uid_with_missing_fields():
    """Test that UID generation handles missing optional fields."""
    print("Testing UID generation with missing fields...")
    
    # Create events with missing optional fields
    events = [
        Event(
            title="Event with no location or URL",
            start_date=datetime(2026, 3, 18, 10, 0),
            location="",
            description="Test event",
            url=""
        ),
        Event(
            title="Event with location only",
            start_date=datetime(2026, 3, 18, 12, 0),
            location="Reston, VA",
            description="Test event",
            url=""
        ),
        Event(
            title="Event with URL only",
            start_date=datetime(2026, 3, 18, 14, 0),
            location="",
            description="Test event",
            url="https://example.com/event"
        ),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        output_file = feed_gen.generate_feed(events, "TestScraper", "test.ics")
        
        # Extract UIDs
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Unfold lines according to RFC 5545
        unfolded_lines = unfold_ical_lines(content)
        
        uid_pattern = r'^UID:(.+)$'
        uids = []
        for line in unfolded_lines:
            match = re.match(uid_pattern, line)
            if match:
                uids.append(match.group(1))
        
        assert len(uids) == len(events), f"Expected {len(events)} UIDs, found {len(uids)}"
        
        # All UIDs should be unique
        assert len(set(uids)) == len(uids), "All UIDs should be unique even with missing fields"
        
        print(f"  ✓ PASSED: Generated {len(uids)} unique UIDs with missing fields")
        for i, uid in enumerate(uids, 1):
            print(f"    {i}. {uid}")
    
    print()


def main():
    """Run all regression tests."""
    print("="*60)
    print("Running UID Regression Tests")
    print("="*60 + "\n")
    
    try:
        test_duplicate_uid_regression()
        test_uid_format()
        test_uid_with_missing_fields()
        
        print("="*60)
        print("All regression tests passed! ✓")
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
