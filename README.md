# DC Tech Event Scraper Collection

A Python framework for scraping multiple websites for events on a schedule with GitHub Actions, and publishing the results as iCal feeds hosted on GitHub Pages.

## Supported Sites

- **AFCEA** - https://www.afcea.org/events
- **AIGA DC** - https://dc.aiga.org/upcoming-events
- **DefenseScoop** - https://defensescoop.com/attend
- **Refresh DC** - https://www.eventbrite.com/o/1039770801
- **NOVAAR** - https://novaar.org/drupal10/calendar_event

## Features

- Automated daily scraping via GitHub Actions
- iCal (.ics) feed generation for each site
- **Location filtering** - Only includes events in MD, DC, or VA (DMV area)
- Easy to extend with new scrapers
- GitHub Pages hosting for feeds
- Robust HTML parsing with multiple fallback selectors

## Quick Start

### Initial Setup

1. **Enable GitHub Pages** (see [SETUP.md](SETUP.md) for detailed instructions)
   - Go to Settings → Pages
   - Set source to "GitHub Actions"

2. **Run the scraper for the first time**
   - Go to Actions tab → "Scrape Events and Update Feeds"
   - Click "Run workflow"

3. **Access your feeds**
   - Main page: `https://[username].github.io/dctech-scrapercollcection/`
   - AFCEA: `https://[username].github.io/dctech-scrapercollcection/afcea.ics`

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run scrapers locally
python scrape.py

# Run tests
python test_scrapers.py
```

The generated iCal feeds will be saved in the `output/` directory.

## Automated Runs

The scrapers run automatically nightly at 3 AM EST via GitHub Actions. You can also trigger a manual run from the Actions tab.

## Adding a New Scraper

1. Create a new scraper class in `scrapers/` that inherits from `BaseScraper`
2. Implement the `scrape()` method to extract events
3. Add the scraper to the list in `scrape.py`
4. Update `docs/index.html` to include the new feed

Example:

```python
from .base_scraper import BaseScraper, Event

class MyScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="MyOrg",
            url="https://example.org/events"
        )
    
    def scrape(self) -> List[Event]:
        # Implement scraping logic here
        events = []
        # ... scraping code ...
        return events
```

## Project Structure

```
dctech-scrapercollcection/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py    # Base scraper class and Event model
│   └── afcea_scraper.py   # AFCEA scraper
├── docs/
│   └── index.html         # GitHub Pages landing page
├── output/                # Generated .ics files (git-ignored)
├── feed_generator.py      # iCal feed generation
├── scrape.py             # Main orchestration script
├── test_scrapers.py      # Test suite
├── requirements.txt      # Python dependencies
├── SETUP.md             # Detailed setup instructions
└── .github/
    └── workflows/
        └── scrape.yml    # GitHub Actions workflow
```

## Location Filtering

The scraper automatically filters events to only include those in the DMV (DC, Maryland, Virginia) area. Events are included if their location contains:
- **DC** - District of Columbia or Washington, DC
- **MD** - Maryland (state abbreviation or full name)
- **VA** - Virginia (state abbreviation or full name)

Events from other states or countries are excluded from the generated feeds. This filtering is applied in `scrape.py` using the `is_dmv_event()` function.

## Subscribing to Feeds

Users can subscribe to the generated feeds in their calendar applications:

- **Google Calendar**: Settings → Add calendar → From URL
- **Apple Calendar**: File → New Calendar Subscription
- **Outlook**: Calendar → Add calendar → Subscribe from web

See [SETUP.md](SETUP.md) for detailed subscription instructions.

## Troubleshooting

See [SETUP.md](SETUP.md) for common issues and solutions.

## License

This project is open source and available for anyone to use and modify.