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

class TargetScraper:
    def __init__(self, session, base_delay=5.0, delay_variance=2.0):
        self.session = session
        self.base_delay = base_delay
        self.delay_variance = delay_variance
        self.logger = logging.getLogger('TargetScraper')
        
        # Add more robust headers
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
        """Fetch and parse product data from Target."""
        try:
            delay = self.base_delay + random.uniform(0, self.delay_variance)
            self.logger.info(f"Fetching {url} (delay: {delay:.2f}s)")
            time.sleep(delay)
            
            response = self.session.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product ID from URL
            product_id = None
            if '/-/A-' in url:
                product_id = url.split('/-/A-')[1].split('/')[0]
            
            # More robust product name extraction
            product_name = None
            name_selectors = [
                'h1[data-test="product-title"]',
                'h1.Heading__StyledHeading-sc-1mp23s9-0',
                'h1.Heading',
                'span[data-test="product-title"]'
            ]
            
            for selector in name_selectors:
                name_element = soup.select_one(selector)
                if name_element:
                    product_name = name_element.get_text().strip()
                    break
                    
            # Handle dynamic content (Target often uses React/JavaScript)
            # Look for JSON data in script tags
            script_data = None
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if '@type' in data and data['@type'] == 'Product':
                        script_data = data
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Extract price from script data if available
            price = None
            if script_data and 'offers' in script_data:
                try:
                    price_str = script_data['offers']['price']
                    price = float(price_str)
                except (KeyError, ValueError):
                    pass
            
            # Fallback to DOM parsing for price
            if not price:
                price_selectors = [
                    'span[data-test="product-price"]',
                    'span.style__PriceFontSize-sc-17wlxvr-0',
                    'div[data-test="product-price"] span'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text().strip()
                        # Remove currency symbols and convert to float
                        price_text = re.sub(r'[^\d.]', '', price_text)
                        try:
                            price = float(price_text)
                            break
                        except ValueError:
                            continue
            
            # Extract product image
            image_url = None
            if script_data and 'image' in script_data:
                image_url = script_data['image']
            
            if not image_url:
                img_selectors = [
                    'img[data-test="product-image"]',
                    'img.ProductImageCarousel__CarouselImage'
                ]
                
                for selector in img_selectors:
                    img_element = soup.select_one(selector)
                    if img_element and img_element.get('src'):
                        image_url = img_element.get('src')
                        break
            
            # Extract availability
            in_stock = False
            if script_data and 'offers' in script_data and 'availability' in script_data['offers']:
                in_stock = 'InStock' in script_data['offers']['availability']
            else:
                stock_selectors = [
                    'button[data-test="shipItButton"]',
                    'button[data-test="orderPickupButton"]',
                    'div[data-test="fulfillment"]'
                ]
                
                for selector in stock_selectors:
                    stock_element = soup.select_one(selector)
                    if stock_element and not "disabled" in stock_element.get('class', []):
                        in_stock = True
                        break
            
            # Compile product data
            product_data = {
                'url': url,
                'source': 'Target',
                'product_id': product_id,
                'name': product_name,
                'price': price,
                'currency': 'USD',
                'image_url': image_url,
                'in_stock': in_stock,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save product data
            filename = f"Target_{product_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2)
            
            self.logger.info(f"Saved product data to {filepath}")
            return product_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None