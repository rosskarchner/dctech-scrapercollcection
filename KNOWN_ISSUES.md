# Known Issues

## ACTIAC Website Access

**Issue**: The ACTIAC website (actiac.org) is currently blocking automated scraper access with a 403 Forbidden error.

**Root Cause**: The website uses Cloudflare bot protection that prevents automated HTTP requests.

**Status**: The scraper code is fully implemented with enhanced extraction capabilities and ready to work once access is granted.

**Current Behavior**:
```
⚠️  ACTIAC website is blocking automated access (403 Forbidden)
   This is likely due to Cloudflare bot protection.
   The scraper implements multiple extraction methods:
   - JSON-LD from Cvent event pages
   - Add-to-calendar URL parsing
   - Standard HTML parsing
   Once access is granted, these methods will work automatically.
```

**Enhanced Scraper Features** (Ready to use once access is granted):

1. **Cvent Event Page Support**
   - Automatically follows links to Cvent event pages
   - Extracts structured JSON-LD data with full event details
   - Handles Event and EventSeries schema types

2. **Add-to-Calendar Link Parsing**
   - Parses Google Calendar, Outlook, and .ics links
   - Extracts event details from URL parameters
   - Supports various calendar link formats

3. **Standard HTML Parsing**
   - Multiple selector strategies for event listings
   - Flexible date format parsing
   - Location and description extraction

**Testing**:
```bash
# Test the enhanced extraction capabilities
python3 test_actiac_enhanced.py
```

All extraction methods are tested and working with sample data. See `test_actiac_enhanced.py` for examples.

**Possible Solutions**:

1. **Contact ACTIAC** to request whitelisting for GitHub Actions IP ranges
2. **Use a headless browser** (Playwright/Selenium) to bypass bot detection
3. **Check for alternatives**:
   - API endpoint if available
   - RSS/Atom feed
   - Calendar export feature

**Workaround**: 
The framework continues to work with other scrapers (AFCEA is working correctly). When ACTIAC access is resolved, events will automatically be extracted using all available methods.

## AFCEA - Working ✓

The AFCEA scraper is functioning correctly and extracting events successfully.

**Sample Output**:
- Rocky Mountain Cyberspace Symposium (RMCS26) - Feb 2, 2026
- WEST Conference and Exhibition - Feb 10, 2026  
- Navy Information Warfare Industry - Mar 18, 2026
- Small Business Breakfast - Jan 27, 2026 (Reston, VA)
- And more...

## Testing

To test the scrapers:
```bash
python3 scrape.py
```

The framework will continue to work with available sources and gracefully handle blocked sites.
