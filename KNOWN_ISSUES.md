# Known Issues

## ACTIAC Website Access

**Issue**: The ACTIAC website (actiac.org) is currently blocking automated scraper access with a 403 Forbidden error.

**Root Cause**: The website uses bot protection (likely Cloudflare or similar WAF) that prevents automated HTTP requests.

**Status**: The scraper code is fully implemented and ready to work, but the website needs to allow automated access.

**Current Behavior**:
```
⚠️  ACTIAC website is blocking automated access (403 Forbidden)
   This is likely due to bot protection on their website.
   The scraper code is ready, but the site needs to allow automated access.
```

**Possible Solutions**:

1. **Contact ACTIAC** to request whitelisting for the GitHub Actions IP ranges or user agent
2. **Use a headless browser** (Playwright/Selenium) instead of simple HTTP requests
3. **Check for alternatives**:
   - API endpoint if available
   - RSS/Atom feed
   - Calendar export feature

**Workaround**: 
The framework continues to work with other scrapers (AFCEA is working correctly). When ACTIAC access is resolved, events will automatically be included in the next scheduled run.

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
