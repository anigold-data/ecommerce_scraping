# E-Commerce Price Scraper

This project scrapes product information from major e-commerce sites (Amazon, Walmart, Newegg, Target), supports proxy rotation, and includes an ETL pipeline to clean and load data into a database.

---

## Project Structure

```
ecommerce_scraping/
│
├── scrapers/
│   ├── amazon_scraper.py       # Inherits BaseScraper
│   ├── walmart_scraper.py      # Uses ProxyManager
│   ├── newegg_scraper.py       # Uses ProxyManager
│   ├── target_scraper.py       # Uses ProxyManager
│   ├── base_scraper.py         # Abstract scraper with caching, delay, anti-bot headers
│   └── proxy_manager.py        # Manages free/rotating proxies
│
├── data/                       # Output directory for JSON files
├── database/			 # Output directory for database files
├── etl.py                      # Extract-Transform-Load pipeline
├── database.py                 # DB connection & insert functions
├── main.py                     # Main runner for scraping all sites
└── scraper.log                 # Log file
```

---

## How It Works

- `AmazonScraper` inherits a `BaseScraper` class that includes:
  - Retry handling
  - Rate limiting
  - Header rotation
  - CAPTCHA/backoff detection
- `WalmartScraper`, `NeweggScraper`, and `TargetScraper` are standalone and use sessions created by `ProxyManager`.

---

## Running the Scraper

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your `data/` folder exists:
```bash
mkdir data
```

3. Run the main scraper:
```bash
python main.py
```

This will run Amazon without proxies, and other retailers with rotating proxy sessions.

---

## ETL Pipeline

To transform and load scraped data into a database:

```python
from etl import ProductETL
etl = ProductETL()
etl.process_directory("data")
```

---

## Proxy Handling

proxy_manager.py uses free proxies from https://proxy-list.download/. You can update this to use a paid provider for better stability. 
Each retailer scraper (except Amazon) can be configured to use a rotating proxy session to avoid detection.

---

## Supported Retailers
| Retailer | Status | Notes |
|----------|--------|----------------------------------|
| Amazon   | Stable | Uses anti-bot delays and headers |
| Walmart  | Proxy  | Fails without proxy; rotating proxy used |
| Newegg   | Proxy  | Requires proxy for stability |
| Target   | Proxy  | Requires proxy; may block often |

---

## Ethical Use

- Respect each retailer's `robots.txt`
- Use responsibly: add delays, rotate proxies, and do not overload servers
- For academic and personal research only

---

## Contact

Built by Opeyemi(MSc Big Data Analytics, Backend & Data Engineering Enthusiast) for automated product monitoring, price analytics, and ETL-based analysis.

https://github.com/anigold-data/ecommerce_scraping.git
