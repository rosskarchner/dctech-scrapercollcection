#!/usr/bin/env python3
"""Test UID uniqueness in iCal feeds."""
from datetime import datetime
from scrapers.base_scraper import Event
from feed_generator import FeedGenerator
import tempfile
import os
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


def test_uid_uniqueness():
    """Test that UIDs are unique even for events on the same date."""
    print("Testing UID uniqueness...")
    
    # Create multiple events on the same date with different titles
    # This is a common scenario that could lead to hash collisions
    events = [
        Event(
            title="Event A",
            start_date=datetime(2026, 2, 6, 10, 0),
            location="Reston, VA",
            description="First event",
            url="https://example.com/event-a"
        ),
        Event(
            title="Event B",
            start_date=datetime(2026, 2, 6, 12, 0),
            location="Reston, VA",
            description="Second event",
            url="https://example.com/event-b"
        ),
        Event(
            title="Event C",
            start_date=datetime(2026, 2, 6, 14, 0),
            location="Reston, VA",
            description="Third event",
            url="https://example.com/event-c"
        ),
        Event(
            title="Event D",
            start_date=datetime(2026, 2, 6, 16, 0),
            location="Arlington, VA",
            description="Fourth event",
            url="https://example.com/event-d"
        ),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        output_file = feed_gen.generate_feed(events, "AFCEA", "test_afcea.ics")
        
        # Parse the generated iCal file and extract all UIDs
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Unfold lines according to RFC 5545
        unfolded_lines = unfold_ical_lines(content)
        
        # Extract UIDs from the file
        uids = []
        for line in unfolded_lines:
            if line.startswith('UID:'):
                uid = line.replace('UID:', '').strip()
                uids.append(uid)
        
        print(f"  Generated {len(uids)} UIDs for {len(events)} events")
        print(f"  UIDs: {uids}")
        
        # Check for uniqueness
        if len(uids) != len(set(uids)):
            # Found duplicates
            duplicate_uids = [uid for uid in uids if uids.count(uid) > 1]
            unique_duplicates = list(set(duplicate_uids))
            print(f"  ✗ Found duplicate UIDs: {unique_duplicates}")
            raise AssertionError(f"UIDs are not unique! Duplicates: {unique_duplicates}")
        
        # Verify all UIDs are present
        assert len(uids) == len(events), f"Expected {len(events)} UIDs, found {len(uids)}"
        
        print(f"  ✓ All {len(uids)} UIDs are unique")
    
    print()


def test_uid_stability():
    """Test that UIDs are stable across multiple generations."""
    print("Testing UID stability...")
    
    events = [
        Event(
            title="Test Event",
            start_date=datetime(2026, 3, 18, 10, 0),
            location="Reston, VA",
            description="Test event for UID stability",
            url="https://example.com/event"
        ),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        feed_gen = FeedGenerator(output_dir=tmpdir)
        
        # Generate feed twice
        output_file1 = feed_gen.generate_feed(events, "Test", "test1.ics")
        with open(output_file1, 'r') as f:
            content1 = f.read()
        
        # Unfold lines
        unfolded1 = unfold_ical_lines(content1)
            
        output_file2 = feed_gen.generate_feed(events, "Test", "test2.ics")
        with open(output_file2, 'r') as f:
            content2 = f.read()
        
        # Unfold lines
        unfolded2 = unfold_ical_lines(content2)
        
        # Extract UIDs
        uid1 = [line for line in unfolded1 if line.startswith('UID:')][0]
        uid2 = [line for line in unfolded2 if line.startswith('UID:')][0]
        
        # UIDs should be the same (excluding the timestamp)
        # Note: We compare the UIDs themselves, not the entire file content
        # because DTSTAMP will be different
        assert uid1 == uid2, f"UIDs should be stable: {uid1} != {uid2}"
        print(f"  ✓ UID is stable: {uid1}")
    
    print()


def main():
    """Run all UID tests."""
    print("="*60)
    print("Running UID Uniqueness Tests")
    print("="*60 + "\n")
    
    try:
        test_uid_uniqueness()
        test_uid_stability()
        
        print("="*60)
        print("All UID tests passed! ✓")
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
