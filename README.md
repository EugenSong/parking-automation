# Parking Automation

An automated parking availability monitoring system that scrapes my apartment garage website and sends real-time notifications via Discord.

## Overview

I built this project to solve a daily frustration: checking multiple floors of my apartment's parking garage to find available spots. Instead of manually checking the parking website throughout the day, I automated the entire process using web scraping and cloud-based scheduling.

The system monitors floors 2-4 of my apartment garage every hour and sends me Discord notifications whether spots are available or not, giving me peace of mind and saving time.

## How It Works

1. **Web Scraping**: Uses Playwright to navigate the parking management website and extract real-time availability data from each floor
2. **Smart Monitoring**: Checks all floors (2-7) but only alerts for my preferred floors (2-4)
3. **Notifications**: Sends Discord webhook notifications with parking status
4. **Automated Scheduling**: Runs every hour via GitHub Actions cron schedule

## Tech Stack

- **Python 3.13** - Core scripting language
- **Playwright** - Headless browser automation for web scraping
- **GitHub Actions** - Cloud-based workflow automation and scheduling
- **Discord Webhooks** - Real-time push notifications
- **Git/GitHub** - Version control and hosting

## Key Design Decisions

### Why Discord?
I initially explored Twilio for SMS notifications, but encountered restrictions on personal use accounts. I then evaluated GatewayAPI, but discovered that alphanumeric sender IDs don't work for US phone numbers (they require 10DLC/toll-free numbers with campaign registration). Discord webhooks provided a **simple, free, and instant** notification solution with no setup overhead.

### Why GitHub Actions?
I needed a scheduling solution that didn't require keeping my computer running 24/7. GitHub Actions offers:
- **Free tier**: 2,000 minutes/month for private repos, unlimited for public repos
- **No infrastructure**: Runs in the cloud without needing a server
- **Built-in secrets management**: Secure storage for the Discord webhook URL
- **Simple cron scheduling**: Runs every hour with a standard cron expression

With hourly runs (~720 minutes/month), this stays well within the free tier.

### Why Playwright Over Selenium?
Playwright offers better async support, faster execution, and more reliable selectors for modern web applications. The parking website loads data dynamically, and Playwright's auto-waiting mechanisms handle this elegantly.

## Project Structure

```
parking-automation/
├── .github/
│   └── workflows/
│       └── parking-checker.yml    # GitHub Actions workflow definition
├── parking_checker_twilio.py      # Main scraping and notification script
├── requirements.txt               # Python dependencies
├── .gitignore                     # Excludes venv, cache files
└── README.md
```

## Setup

### Prerequisites
- GitHub account
- Discord server and webhook URL

### Installation

1. Clone the repository:
```bash
git clone https://github.com/EugenSong/parking-automation.git
cd parking-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set up Discord webhook:
   - Create a webhook in your Discord server (Server Settings → Integrations → Webhooks)
   - Add the webhook URL as a GitHub secret named `DISCORD_WEBHOOK_URL`

4. The GitHub Actions workflow will automatically run every hour

### Local Testing

To test locally, set the environment variable and run:
```bash
export DISCORD_WEBHOOK_URL="your-webhook-url"
python parking_checker_twilio.py
```

## Notification Examples

**When spots are available:**
```
🚗 Parking openings:
Floor 2: 3 of 82 spaces available
Floor 4: 1 of 114 spaces available
```

**When no spots available:**
```
❌ No spots available on floors 2-4
```

## Future Enhancements

- Add historical data tracking to identify peak availability times
- Implement smart notifications (only alert when availability changes)
- Support for multiple parking locations
- Add a simple dashboard for viewing trends

## Lessons Learned

- **SMS isn't always simple**: What seemed like a straightforward notification problem revealed significant complexity around carrier requirements and regulations
- **Free tiers are generous**: GitHub Actions and Discord webhooks provide more than enough for personal automation projects
- **Environment variables are critical**: Using GitHub Secrets keeps sensitive data secure while allowing the code to remain public
- **Web scraping requires patience**: Properly waiting for dynamic content is crucial for reliable automation

## License

MIT

---

*Built to automate the mundane and reclaim time for what matters.*
