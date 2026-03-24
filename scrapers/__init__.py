"""Scrapers package initialization."""
from .base_scraper import BaseScraper, Event
from .afcea_scraper import AfceaScraper
from .aiga_dc_scraper import AigaDcScraper
from .defensescoop_scraper import DefenseScoopScraper

__all__ = ['BaseScraper', 'Event', 'AfceaScraper', 'AigaDcScraper', 'DefenseScoopScraper']
