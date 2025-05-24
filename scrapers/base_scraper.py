import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import os
import json
from datetime import datetime
from urllib.parse import urlparse
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

class BaseScraper(ABC):
    """Base scraper class with common functionality"""
    
    def __init__(self, retailer_name, base_delay=5, jitter=2, save_dir=r"C:\Users\adeda\OneDrive\Desktop\Ecommerce_Scraping\data"):
        """
        Initialize the base scraper
        
        Args:
            retailer_name (str): Name of the retailer
            base_delay (int): Base delay between requests in seconds
            jitter (int): Random jitter to add to delay in seconds
        """
        self.retailer_name = retailer_name
        self.base_delay = base_delay
        self.jitter = jitter
        self.save_dir = save_dir  # ✅ Set save_dir here
        os.makedirs(save_dir, exist_ok=True)  # ✅ Create the folder if it doesn't exist
        self.session = requests.Session()
        self.logger = logging.getLogger(f"{retailer_name}Scraper")
        
        # Set common headers
        self.session.headers.update({
            'User-Agent': 'PriceAnalysisProject/1.0 (Academic Research; contact@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Cache to avoid re-scraping the same URL frequently
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour in seconds
    
    def get_page(self, url, use_cache=True):
        """
        Fetch a page with rate limiting and caching
        
        Args:
            url (str): URL to fetch
            use_cache (bool): Whether to use cached response if available
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            # Check cache first
            now = time.time()
            if use_cache and url in self.cache and now - self.cache[url]['timestamp'] < self.cache_expiry:
                self.logger.info(f"Using cached response for {url}")
                return BeautifulSoup(self.cache[url]['content'], 'html.parser')
            
            # Add jitter to delay to avoid detection
            delay = self.base_delay + random.uniform(0, self.jitter)
            self.logger.info(f"Fetching {url} (delay: {delay:.2f}s)")
            
            # Wait before making request
            time.sleep(delay)
            
            # Make request
            response = self.session.get(url, timeout=(5, 30))
            
            # Check response status
            if response.status_code == 200:
                # Update cache
                self.cache[url] = {
                    'content': response.content,
                    'timestamp': now
                }
                return BeautifulSoup(response.content, 'html.parser')
            elif response.status_code == 429:
                # Too many requests - back off significantly
                self.logger.warning(f"Rate limited (429) for {url}. Backing off.")
                time.sleep(60)  # 1 minute backoff
                return None
            else:
                self.logger.error(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def clean_price(self, price_str):
        """
        Clean and convert price string to float
        
        Args:
            price_str (str): Price string to clean
            
        Returns:
            float: Cleaned price or None if invalid
        """
        if not price_str:
            return None
            
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = price_str.replace('$', '').replace('£', '').replace('€', '')
            cleaned = cleaned.replace(',', '').strip()
            
            # Handle ranges by taking the lower price
            if ' - ' in cleaned:
                cleaned = cleaned.split(' - ')[0]
                
            # Convert to float
            return float(cleaned)
        except ValueError:
            self.logger.warning(f"Could not parse price: {price_str}")
            return None
    
    def extract_product_id(self, url):
        """
        Extract product ID from URL
        
        Args:
            url (str): Product URL
            
        Returns:
            str: Product ID or None if not found
        """
        # This is a placeholder - each retailer will implement specific logic
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        
        # Try to find a product ID in the path
        for part in path_parts:
            if part.isalnum() and len(part) > 5:
                return part
                
        return None
        
    @abstractmethod
    def extract_product_data(self, soup, url):
        """
        Extract product data from page
        
        Args:
            soup (BeautifulSoup): Parsed HTML page
            url (str): Product URL
            
        Returns:
            dict: Extracted product data
        """
        pass
        
    def get_product(self, url):
        """
        Get product data from URL
        
        Args:
            url (str): Product URL
            
        Returns:
            dict: Product data or None if failed
        """
        soup = self.get_page(url)
        if not soup:
            return None
            
        try:
            product_data = self.extract_product_data(soup, url)
            
            # Add metadata
            product_data.update({
                'retailer': self.retailer_name,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'product_id': product_data.get('product_id') or self.extract_product_id(url)
            })
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error extracting product data from {url}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
    def save_to_json(self, product_data, filename=None):
        """
        Save product data to JSON file
        
        Args:
            product_data (dict): Product data to save
            filename (str): Optional filename, defaults to retailer_productid.json
        """
        if not filename:
            product_id = product_data.get('product_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.retailer_name}_{product_id}_{timestamp}.json"
    
        filepath = os.path.join(self.save_dir, filename)  # ✅ Save to correct directory

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2)
            
        self.logger.info(f"Saved product data to {filepath}")

    def rotate_user_agent(self):
        """Rotate User-Agent to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        # Always append our identifier for ethical scraping
        selected = random.choice(user_agents)
        self.session.headers['User-Agent'] = f"{selected} (PriceAnalysisProject/1.0; contact@example.com)"
        self.logger.info(f"Rotated User-Agent: {self.session.headers['User-Agent']}")

    def handle_captcha(self, soup):
        """Check if page contains a CAPTCHA and handle it"""
        # Check for common CAPTCHA indicators
        captcha_indicators = [
            'captcha' in soup.text.lower(),
            soup.select_one('form input[name*="captcha"]') is not None,
            'robot' in soup.text.lower() and 'check' in soup.text.lower(),
            'verify' in soup.text.lower() and 'human' in soup.text.lower()
        ]
        
        if any(captcha_indicators):
            self.logger.warning("CAPTCHA detected! Implementing backoff strategy")
            wait_time = 5 * 60  # 5 minutes
            self.logger.info(f"Backing off for {wait_time} seconds")
            time.sleep(wait_time)
            self.rotate_user_agent()
            return True
        
        return False

    def exponential_backoff(self, attempt, base_delay=5):
        """Implement exponential backoff for retries"""
        max_delay = 60 * 5  # 5 minutes maximum
        delay = min(max_delay, base_delay * (2 ** attempt) + random.uniform(0, 10))
        self.logger.info(f"Exponential backoff: Waiting {delay:.2f}s (attempt {attempt+1})")
        time.sleep(delay)