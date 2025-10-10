# B3 Futures Data Scraper

Automated daily scraper for Brazilian stock exchange (B3) futures settlement prices.

## What it does

- Scrapes all futures contracts from B3 daily at 23:00 UTC
- Saves historical data to SQLite database (`b3_futures.db`)
- Includes DI1 (interest rate futures), commodities, currencies, indices, and more

## Files

- `scraper.py` - Main scraping script
- `b3_futures.db` - SQLite database with all historical data
- `.github/workflows/daily_scrape.yml` - GitHub Actions automation

## Data Source

https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-ajustes-do-pregao-enUS.asp

## Database Schema

**Table:** `all_futures`

| Column | Description |
|--------|-------------|
| Commodity | Contract name (e.g., "DI1 - 1-day Interbank Deposits") |
| Contract_Month | Maturity month (e.g., "J27" = January 2027) |
| Previous_Price | Previous settlement price |
| Current_Price | Current settlement price |
| Variation | Daily change |
| Settlement_Value | Settlement value in BRL |
| download_date | Date scraped (YYYY-MM-DD) |
| download_time | Time scraped (HH:MM:SS) |

## Quick Queries
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('b3_futures.db')

# Get all DI1 contracts
df = pd.read_sql("SELECT * FROM all_futures WHERE Commodity LIKE '%DI1%'", conn)

# Get latest data
df = pd.read_sql("""
    SELECT * FROM all_futures 
    WHERE download_date = (SELECT MAX(download_date) FROM all_futures)
""", conn)

# Get specific date
df = pd.read_sql("SELECT * FROM all_futures WHERE download_date = '2025-10-10'", conn)

conn.close()
