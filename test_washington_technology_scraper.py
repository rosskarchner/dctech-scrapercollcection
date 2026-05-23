"""Tests for Washington Technology scraper."""
from datetime import datetime, timedelta

from scrapers.washington_technology_scraper import WashingtonTechnologyScraper


def test_washington_technology_scrapes_upcoming_section_only():
    """Scraper should only extract cards from the Upcoming section."""
    html = """
    <html>
      <body>
        <section class="river river-grid">
          <h1 class="river-title">Upcoming</h1>
          <div class="river-items row">
            <section class="river-item">
              <p class="river-item-label">Live Event | <span>Washington, DC</span></p>
              <h1 class="river-item-title">
                <a class="river-item-title-link" href="https://example.com/upcoming">
                  Upcoming Event
                </a>
              </h1>
              <p class="river-item-dek">Thursday, July 16, 2030, 8:00 am - 5:00 pm, ET</p>
            </section>
          </div>
        </section>
        <section class="river river-grid">
          <h1 class="river-title">Archived</h1>
          <div class="river-items row">
            <section class="river-item">
              <p class="river-item-label">Live Event | <span>Reston, VA</span></p>
              <h1 class="river-item-title">
                <a class="river-item-title-link" href="https://example.com/archived">
                  Archived Event
                </a>
              </h1>
              <p class="river-item-dek">January 4, 2030</p>
            </section>
          </div>
        </section>
      </body>
    </html>
    """

    scraper = WashingtonTechnologyScraper()
    scraper._fetch_url = lambda _url, _headers: html.encode("utf-8")

    events = scraper.scrape()

    assert len(events) == 1
    assert events[0].title == "Upcoming Event"
    assert events[0].location == "Washington, DC"
    assert events[0].url == "https://example.com/upcoming"


def test_washington_technology_date_parsing_rolls_forward_for_no_year():
    """Date parser should roll dates without year into the future when needed."""
    scraper = WashingtonTechnologyScraper()
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    text = f"{yesterday.strftime('%B')} {yesterday.day}, 8:00 am - 9:00 am, ET"

    parsed = scraper._parse_date_text(text)

    assert parsed is not None
    assert parsed.date() >= now.date()
