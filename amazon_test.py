# test_scrapers.py

from scrapers.amazon_scraper import AmazonScraper

def test_scraper(scraper_class, test_urls):
    """Test a scraper with a list of URLs"""
    scraper = scraper_class()
    
    for url in test_urls:
        print(f"Testing URL: {url}")
        product_data = scraper.get_product(url)
        
        if product_data:
            print(f"Successfully scraped: {product_data['name']}")
            print(f"Price: ${product_data['current_price']}")
            print(f"In Stock: {product_data['in_stock']}")
            print("---")

            # Save to JSON for inspection (optional)
            scraper.save_to_json(product_data)
        else:
            print(f"Failed to scrape: {url}")
            print("---")

# --- Test URLs ---
amazon_urls = [
    "https://www.amazon.co.uk/Apple-iPhone-Pro-Max-256/dp/B0DGHZ1MC2?th=1",
    "https://www.amazon.co.uk/Google-Pixel-Pro-Unlocked-Smartphone/dp/B0D7V12BWR?th=1",
    "https://www.amazon.co.uk/Samsung-Smartphone-Storage-Included-Titanium/dp/B0DR374YZM?th=1"
]

# --- Run Tests ---
print("\n--- Testing Amazon Scraper ---")
test_scraper(AmazonScraper, amazon_urls)
