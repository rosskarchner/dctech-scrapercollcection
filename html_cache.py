"""HTML caching module for web scraping with daily expiration."""
import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

# Set up logger for this module
logger = logging.getLogger(__name__)


class HTMLCache:
    """Cache for HTML responses with daily expiration."""
    
    def __init__(self, cache_dir: str = ".cache/html"):
        """Initialize the HTML cache.
        
        Args:
            cache_dir: Directory to store cached HTML files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL.
        
        Args:
            url: URL to generate cache key for
        
        Returns:
            SHA256 hash of the URL as cache key
        """
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cached response.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Path to the cached file
        """
        return self.cache_dir / f"{cache_key}.html"
    
    def _is_expired(self, cache_key: str) -> bool:
        """Check if a cached entry is expired (older than 1 day).
        
        Args:
            cache_key: Cache key to check
        
        Returns:
            True if expired or doesn't exist, False otherwise
        """
        if cache_key not in self.metadata:
            return True
        
        cached_date = datetime.fromisoformat(self.metadata[cache_key]['timestamp'])
        age = datetime.now() - cached_date
        
        # Expire after 1 day
        return age > timedelta(days=1)
    
    def get(self, url: str) -> Optional[bytes]:
        """Get cached HTML content for a URL.
        
        Args:
            url: URL to retrieve from cache
        
        Returns:
            Cached HTML content as bytes, or None if not cached or expired
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        # Check if cache exists and is not expired
        if not cache_path.exists() or self._is_expired(cache_key):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                content = f.read()
            logger.info(f"Cache HIT: {url}")
            return content
        except IOError:
            return None
    
    def set(self, url: str, content: bytes):
        """Cache HTML content for a URL.
        
        Args:
            url: URL to cache
            content: HTML content to cache
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)
        
        # Write content to cache
        with open(cache_path, 'wb') as f:
            f.write(content)
        
        # Update metadata
        self.metadata[cache_key] = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'size': len(content)
        }
        self._save_metadata()
        
        logger.info(f"Cache SET: {url}")
    
    def clear_expired(self):
        """Remove all expired cache entries."""
        expired_keys = [key for key in self.metadata.keys() if self._is_expired(key)]
        
        for cache_key in expired_keys:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            del self.metadata[cache_key]
        
        if expired_keys:
            self._save_metadata()
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.metadata)
        total_size = sum(meta['size'] for meta in self.metadata.values())
        expired_count = sum(1 for key in self.metadata.keys() if self._is_expired(key))
        
        return {
            'total_entries': total_entries,
            'valid_entries': total_entries - expired_count,
            'expired_entries': expired_count,
            'total_size_bytes': total_size,
            'cache_dir': str(self.cache_dir)
        }
