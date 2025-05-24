import os
import re
import time
import json
import random
import logging
import requests
import datetime
from bs4 import BeautifulSoup
DATA_DIR = r"C:\Users\adeda\OneDrive\Desktop\Ecommerce_Scraping\data"

class WalmartScraper:
    def __init__(self, session, base_delay=5.0, delay_variance=2.0):
        self.session = session
        self.base_delay = base_delay
        self.delay_variance = delay_variance
        self.logger = logging.getLogger('WalmartScraper')
        
        # Add more robust headers to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    def fetch_product(self, url):
        """Fetch and parse product data from Walmart."""
        try:
            delay = self.base_delay + random.uniform(0, self.delay_variance)
            self.logger.info(f"Fetching {url} (delay: {delay:.2f}s)")
            time.sleep(delay)
            
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # More robust product name extraction using multiple possible selectors
            product_name = None
            name_selectors = [
                'h1[data-automation="product-title"]',
                'h1.prod-ProductTitle',
                'h1.f3.b.lh-copy.dark-gray.mb1.mt2',
                'h1.lh-copy'
            ]
            
            for selector in name_selectors:
                name_element = soup.select_one(selector)
                if name_element:
                    product_name = name_element.get_text().strip()
                    break
                    
            if not product_name:
                self.logger.warning("Could not extract product name")
            
            # More robust price extraction
            price = None
            price_selectors = [
                'span[data-automation="buybox-price"]',
                'span.price-characteristic',
                'span[itemprop="price"]',
                '[data-testid="price-value"]',
                'span.w_PgZ'
            ]
            
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    # Handle various price formats
                    price_text = price_element.get_text().strip()
                    # Remove currency symbols and convert to float
                    price_text = re.sub(r'[^\d.]', '', price_text)
                    try:
                        price = float(price_text)
                        break
                    except ValueError:
                        continue
            
            if not price:
                self.logger.warning("Could not extract price")
                
            # Extract product image
            image_url = None
            image_selectors = [
                'img[data-testid="primary-image"]',
                'img.hover-zoom-hero-image',
                'img[data-automation="hero-image"]'
            ]
            
            for selector in image_selectors:
                img_element = soup.select_one(selector)
                if img_element and img_element.get('src'):
                    image_url = img_element.get('src')
                    break
            
            # Extract availability
            in_stock = False
            stock_selectors = [
                'button[data-testid="add-to-cart-button"]',
                'button.add-to-cart-btn',
                '[data-testid="fulfillment-add-to-cart"]'
            ]
            
            for selector in stock_selectors:
                stock_element = soup.select_one(selector)
                if stock_element and not "disabled" in stock_element.get('class', []):
                    in_stock = True
                    break
            
            # Product ID extraction from URL
            product_id = None
            if '/ip/' in url:
                product_id = url.split('/ip/')[1].split('/')[1] if '/ip/' in url else None
            
            # Compile product data
            product_data = {
                'url': url,
                'source': 'Walmart',
                'product_id': product_id,
                'name': product_name,
                'price': price,
                'currency': 'USD',
                'image_url': image_url,
                'in_stock': in_stock,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save product data
            filename = f"Walmart_{product_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2)
            
            self.logger.info(f"Saved product data to {filepath}")
            return product_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
