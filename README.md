# DC Tech Event Scraper Collection

A Python framework for scraping multiple websites for events on a schedule with GitHub Actions, and publishing the results as iCal feeds hosted on GitHub Pages.

## Supported Sites

- **ACTIAC** - https://www.actiac.org/upcoming-events
- **AFCEA** - https://www.afcea.org/events

## Features

- Automated daily scraping via GitHub Actions
- iCal (.ics) feed generation for each site
- Easy to extend with new scrapers
- GitHub Pages hosting for feeds

## Usage

### Manual Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run scrapers
python scrape.py
```

The generated iCal feeds will be saved in the `output/` directory.

### Automated Runs

The scrapers run automatically daily at 6 AM UTC via GitHub Actions. You can also trigger a manual run from the Actions tab.

## Adding a New Scraper

1. Create a new scraper class in `scrapers/` that inherits from `BaseScraper`
2. Implement the `scrape()` method to extract events
3. Add the scraper to the list in `scrape.py`

## iCal Feeds

Once generated, the iCal feeds can be accessed at:
- `output/actiac.ics`
- `output/afcea.ics`

These feeds can be imported into calendar applications like Google Calendar, Apple Calendar, or Outlook.

## Development

The project structure:
```
dctech-scrapercollcection/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py    # Base scraper class
│   ├── actiac_scraper.py  # ACTIAC scraper
│   └── afcea_scraper.py   # AFCEA scraper
├── feed_generator.py      # iCal feed generation
├── scrape.py             # Main script
├── requirements.txt      # Python dependencies
└── .github/
    └── workflows/
        └── scrape.yml    # GitHub Actions workflow
```