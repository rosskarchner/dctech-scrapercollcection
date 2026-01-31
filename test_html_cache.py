#!/usr/bin/env python3
"""Test HTML caching functionality."""
import tempfile
import time
from datetime import datetime, timedelta
from html_cache import HTMLCache
from pathlib import Path


def test_cache_set_and_get():
    """Test basic cache set and get operations."""
    print("Testing cache set and get...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTMLCache(cache_dir=tmpdir)
        
        url = "https://example.com/test"
        content = b"<html>Test content</html>"
        
        # Set cache
        cache.set(url, content)
        
        # Get from cache
        cached_content = cache.get(url)
        assert cached_content == content, "Cached content should match original"
        
        print("  ✓ Cache set and get works")
    print()


def test_cache_miss():
    """Test cache miss for non-existent URLs."""
    print("Testing cache miss...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTMLCache(cache_dir=tmpdir)
        
        # Try to get non-existent URL
        result = cache.get("https://example.com/nonexistent")
        assert result is None, "Non-existent URL should return None"
        
        print("  ✓ Cache miss returns None")
    print()


def test_cache_expiration():
    """Test that cache entries expire after 1 day."""
    print("Testing cache expiration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTMLCache(cache_dir=tmpdir)
        
        url = "https://example.com/test"
        content = b"<html>Test content</html>"
        
        # Set cache
        cache.set(url, content)
        
        # Manually modify the timestamp to make it old
        cache_key = cache._get_cache_key(url)
        old_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
        cache.metadata[cache_key]['timestamp'] = old_timestamp
        cache._save_metadata()
        
        # Try to get - should return None because it's expired
        result = cache.get(url)
        assert result is None, "Expired cache entry should return None"
        
        print("  ✓ Cache expiration works")
    print()


def test_cache_stats():
    """Test cache statistics."""
    print("Testing cache statistics...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTMLCache(cache_dir=tmpdir)
        
        # Add some entries
        cache.set("https://example.com/1", b"<html>Content 1</html>")
        cache.set("https://example.com/2", b"<html>Content 2</html>")
        
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 2, "Should have 2 total entries"
        assert stats['valid_entries'] == 2, "Should have 2 valid entries"
        assert stats['expired_entries'] == 0, "Should have 0 expired entries"
        assert stats['total_size_bytes'] > 0, "Should have non-zero size"
        
        print(f"  ✓ Cache stats: {stats['total_entries']} entries, {stats['total_size_bytes']} bytes")
    print()


def test_clear_expired():
    """Test clearing expired cache entries."""
    print("Testing clear expired...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = HTMLCache(cache_dir=tmpdir)
        
        # Add entries
        cache.set("https://example.com/1", b"<html>Content 1</html>")
        cache.set("https://example.com/2", b"<html>Content 2</html>")
        
        # Make one entry expired
        cache_key1 = cache._get_cache_key("https://example.com/1")
        old_timestamp = (datetime.now() - timedelta(days=2)).isoformat()
        cache.metadata[cache_key1]['timestamp'] = old_timestamp
        cache._save_metadata()
        
        # Clear expired
        cache.clear_expired()
        
        stats = cache.get_stats()
        assert stats['total_entries'] == 1, "Should have 1 entry after clearing expired"
        
        # The expired entry should be gone
        result = cache.get("https://example.com/1")
        assert result is None, "Expired entry should be cleared"
        
        # The valid entry should still be there
        result = cache.get("https://example.com/2")
        assert result is not None, "Valid entry should still be cached"
        
        print("  ✓ Expired entries cleared successfully")
    print()


def test_cache_persistence():
    """Test that cache persists across instances."""
    print("Testing cache persistence...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create first cache instance
        cache1 = HTMLCache(cache_dir=tmpdir)
        cache1.set("https://example.com/test", b"<html>Test</html>")
        
        # Create second cache instance (should load from disk)
        cache2 = HTMLCache(cache_dir=tmpdir)
        result = cache2.get("https://example.com/test")
        
        assert result == b"<html>Test</html>", "Cache should persist across instances"
        
        print("  ✓ Cache persists across instances")
    print()


def main():
    """Run all cache tests."""
    print("="*60)
    print("Running HTML Cache Tests")
    print("="*60 + "\n")
    
    try:
        test_cache_set_and_get()
        test_cache_miss()
        test_cache_expiration()
        test_cache_stats()
        test_clear_expired()
        test_cache_persistence()
        
        print("="*60)
        print("All cache tests passed! ✓")
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
