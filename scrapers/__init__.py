"""Scrapers package initialization."""
from .base_scraper import BaseScraper, Event
from .actiac_scraper import ActiacScraper
from .afcea_scraper import AfceaScraper

__all__ = ['BaseScraper', 'Event', 'ActiacScraper', 'AfceaScraper']
