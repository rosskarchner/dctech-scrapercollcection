# GitHub Pages Setup

To enable GitHub Pages for hosting the iCal feeds, follow these steps:

## 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on **Settings** (top right)
3. In the left sidebar, click **Pages**
4. Under **Source**, select:
   - Source: `GitHub Actions`
5. Click **Save**

## 2. Wait for Deployment

GitHub will automatically build and deploy your site. This usually takes 1-2 minutes.

You can check the deployment status in the **Actions** tab.

## 3. Access Your Feeds

Once deployed, your iCal feeds will be available at:

- Main page: `https://[username].github.io/dctech-scrapercollcection/`
- ACTIAC feed: `https://[username].github.io/dctech-scrapercollcection/actiac.ics`
- AFCEA feed: `https://[username].github.io/dctech-scrapercollcection/afcea.ics`

Replace `[username]` with your GitHub username.

## 4. Run the Scraper

### Manual Run

You can manually trigger the scraper workflow:

1. Go to the **Actions** tab
2. Click on **Scrape Events and Update Feeds** workflow
3. Click **Run workflow**
4. Select the branch and click **Run workflow**

### Automatic Runs

The scraper runs automatically every day at 6 AM UTC.

## 5. Subscribe to Feeds

Once the feeds are generated and published, users can subscribe to them in their calendar applications:

### Google Calendar
1. Open Google Calendar
2. Click the **+** next to "Other calendars"
3. Select **From URL**
4. Paste the feed URL
5. Click **Add calendar**

### Apple Calendar
1. Open Calendar app
2. Go to **File** → **New Calendar Subscription**
3. Paste the feed URL
4. Click **Subscribe**
5. Choose update frequency and click **OK**

### Outlook
1. Open Outlook Calendar
2. Click **Add calendar**
3. Select **Subscribe from web**
4. Paste the feed URL
5. Name the calendar and click **Import**

## Troubleshooting

### Feeds not updating
- Check the Actions tab for workflow run status
- Ensure GitHub Pages is enabled with "GitHub Actions" as the source (Settings → Pages)

### GitHub Pages not working
- Verify that GitHub Pages is enabled in repository settings with "GitHub Actions" as the source
- Check the workflow runs in the Actions tab for deployment errors
- Wait a few minutes for GitHub to deploy the site after a successful workflow run

### No events found
- The scrapers may need adjustment based on website changes
- Check the workflow logs in the Actions tab for error messages
- Websites may have changed their HTML structure
