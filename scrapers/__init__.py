"""Scrapers package initialization."""
from .base_scraper import BaseScraper, Event
from .afcea_scraper import AfceaScraper

__all__ = ['BaseScraper', 'Event', 'AfceaScraper']
