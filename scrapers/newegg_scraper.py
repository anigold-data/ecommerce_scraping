import os
import re
import time
import json
import random
import logging
import requests
import datetime
import string
from bs4 import BeautifulSoup
DATA_DIR = r"C:\Users\adeda\OneDrive\Desktop\Ecommerce_Scraping\data"

class NeweggScraper:
    def __init__(self, session, base_delay=5.0, delay_variance=2.0):
        self.session = session
        self.base_delay = base_delay
        self.delay_variance = delay_variance
        self.logger = logging.getLogger('NeweggScraper')
        
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.58'
        ]
        
    def get_random_headers(self):
        """Generate random headers to avoid detection."""
        user_agent = random.choice(self.user_agents)
        
        return {
            'User-Agent': user_agent,
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
            'Referer': 'https://www.newegg.com/',
            # Add cookies to appear more like a real user
            'Cookie': 'NID=511=' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=72))
        }
    
    def fetch_product(self, url):
        """Fetch and parse product data from Newegg with anti-blocking measures."""
        try:
            delay = self.base_delay + random.uniform(0, self.delay_variance)
            self.logger.info(f"Fetching {url} (delay: {delay:.2f}s)")
            time.sleep(delay)
            
            # Add more randomized delay to mimic human behavior
            time.sleep(random.uniform(1, 3))
            
            # Use rotating headers
            headers = self.get_random_headers()
            
            # Use a session with cookies to maintain state
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for CAPTCHA or anti-bot challenges
            if 'robot' in response.text.lower() or 'captcha' in response.text.lower():
                self.logger.error(f"Detected anti-bot protection for {url}")
                return None
            
            # Extract product ID from URL
            product_id = None
            if '/p/' in url:
                product_id = url.split('/p/')[1].split('/')[0]
            
            # Product name extraction
            product_name = None
            name_selectors = [
                'h1.product-title',
                'h1[itemprop="name"]',
                'h1.product-name'
            ]
            
            for selector in name_selectors:
                name_element = soup.select_one(selector)
                if name_element:
                    product_name = name_element.get_text().strip()
                    break
            
            # Price extraction
            price = None
            price_selectors = [
                'li.price-current',
                'span.price-current-label + span.price-current-value',
                'li.price-current strong',
                'span[data-testid="item-price"]'
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
            
            # Extract availability
            in_stock = False
            stock_selectors = [
                'div.product-inventory strong',
                'div.product-inventory',
                'div.product-buy'
            ]
            
            for selector in stock_selectors:
                stock_element = soup.select_one(selector)
                if stock_element:
                    stock_text = stock_element.get_text().lower()
                    if 'in stock' in stock_text:
                        in_stock = True
                        break
            
            # Also check "Add to cart" button
            add_buttons = soup.select('button.btn-primary')
            for button in add_buttons:
                button_text = button.get_text().lower()
                if 'add to cart' in button_text:
                    in_stock = True
                    break
            
            # Extract product image
            image_url = None
            img_selectors = [
                'div.mainSlide img',
                'div.swiper-zoom-container img',
                'div.product-view-img-original img'
            ]
            
            for selector in img_selectors:
                img_element = soup.select_one(selector)
                if img_element and img_element.get('src'):
                    image_url = img_element.get('src')
                    break
            
            # Compile product data
            product_data = {
                'url': url,
                'source': 'Newegg',
                'product_id': product_id,
                'name': product_name,
                'price': price,
                'currency': 'USD',
                'image_url': image_url,
                'in_stock': in_stock,
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save product data
            filename = f"Newegg_{product_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2)
            
            self.logger.info(f"Saved product data to {filepath}")
            return product_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None