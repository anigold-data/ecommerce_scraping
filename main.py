import os
import time
import random
import logging
import requests

from scrapers.amazon_scraper import AmazonScraper
from scrapers.walmart_scraper import WalmartScraper
from scrapers.newegg_scraper import NeweggScraper
from scrapers.target_scraper import TargetScraper
from proxy_manager import ProxyManager

# Define where to save JSON files
DATA_DIR = os.path.join(os.getcwd(), "data")

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger('main')
    logger.info("Starting e-commerce scrapers")

    # Ensure data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Initialize ProxyManager
    proxy_manager = ProxyManager()

    # Product URLs
    product_urls = {
        'amazon': [
            'https://www.amazon.co.uk/Apple-iPhone-Pro-Max-256/dp/B0DGHZ1MC2?th=1',
            'https://www.amazon.co.uk/Google-Pixel-Pro-Unlocked-Smartphone/dp/B0D7V12BWR?th=1',
            'https://www.amazon.co.uk/Samsung-Smartphone-Storage-Included-Titanium/dp/B0DR374YZM?th=1'
        ],
        'walmart': [
            'https://www.walmart.com/ip/Apple-AirPods-Pro-2-Wireless-Earbuds-Active-Noise-Cancellation-Hearing-Aid-Feature/5689919121',
            'https://www.walmart.com/browse/electronics/samsung-65-inch-tvs/3944_1060825_1939756_7136694_5563567',
            'https://www.walmart.com/ip/Instant-Pot-DUO60-V4-6-Quart-Duo-Electric-Pressure-Cooker-Slow-Cooker/45918917',
            'https://www.walmart.com/ip/MSI-Katana-15-6-inch-144Hz-Gaming-Laptop-Intel-Core-i7-13620H-NVIDIA-GeForce-RTX-4050-16GB-DDR5-1TB-SSD-Black-2024/5152138788'
        ],
        'newegg': [
            'https://www.newegg.com/p/N82E16868110291',
            'https://www.newegg.com/p/N82E16868110306',
            'https://www.newegg.com/p/380-0027-000M7',
            'https://www.newegg.com/asus-rog-strix-z590-e-gaming-wifi/p/N82E16813119367'
        ],
        'target': [
            'https://www.target.com/p/apple-watch-series-8-stainless-steel-case/-/A-93179365',
            'https://www.target.com/p/apple-airpods-4/-/A-85978618',
            'https://www.target.com/p/hamilton-beach-12cup-programmable-hot-38-iced-coffee-maker-49620/-/A-91992748',
            'https://www.target.com/p/keurig-k-elite-single-serve-k-cup-pod-coffee-maker-with-iced-coffee-setting/-/A-53737584'
        ]
    }

    while True:
        try:
            # ---- Amazon (Uses BaseScraper - session managed internally)
            amazon_scraper = AmazonScraper()
            for url in product_urls['amazon']:
                amazon_scraper.get_product(url)  # get_product handles fetch + save

            # ---- Walmart
            walmart_session = proxy_manager.get_session()
            walmart_scraper = WalmartScraper(walmart_session)
            for url in product_urls['walmart']:
                walmart_scraper.fetch_product(url)

            # ---- Newegg
            newegg_session = proxy_manager.get_session()
            newegg_scraper = NeweggScraper(newegg_session)
            for url in product_urls['newegg']:
                if random.random() < 0.3:
                    newegg_session = proxy_manager.get_session()
                    newegg_scraper.session = newegg_session
                newegg_scraper.fetch_product(url)

            # ---- Target
            target_session = proxy_manager.get_session()
            target_scraper = TargetScraper(target_session)
            for url in product_urls['target']:
                target_scraper.fetch_product(url)

            # ---- Sleep before next cycle
            sleep_time = random.uniform(3600, 4200)
            logger.info(f"Scraping complete. Sleeping for {sleep_time/60:.1f} minutes")
            time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {str(e)}")
            time.sleep(300)  # wait 5 minutes before retry

if __name__ == "__main__":
    main()
