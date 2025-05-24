import re  
import os  
from .base_scraper import BaseScraper

class AmazonScraper(BaseScraper):
    """Amazon-specific scraper implementation"""
    
    def __init__(self):
        super().__init__('Amazon', base_delay=10, jitter=3)
    
    def extract_product_data(self, soup, url):
        product_data = {}
        
        # Product name
        try:
            product_data['name'] = soup.select_one('#productTitle').get_text(strip=True)  
        except (AttributeError, TypeError):
            self.logger.warning("Could not extract product name")
            product_data['name'] = None
            
        # Current price
        try:
            price_element = (
                soup.select_one('.a-price .a-offscreen') or
                soup.select_one('#priceblock_ourprice') or
                soup.select_one('#priceblock_dealprice') or
                soup.select_one('.a-price-whole') 
            )
            if price_element:
                product_data['current_price'] = self.clean_price(price_element.text)
            else:
                product_data['current_price'] = None
        except (AttributeError, TypeError):
            self.logger.warning("Could not extract current price")
            product_data['current_price'] = None
            
        # Original price
        try:
            original_price_element = soup.select_one('.a-text-price .a-offscreen')
            if original_price_element:
                product_data['original_price'] = self.clean_price(original_price_element.text)
            else:
                product_data['original_price'] = product_data['current_price']
        except (AttributeError, TypeError):
            product_data['original_price'] = product_data['current_price']
        
        # Discount calculation
        if (
            product_data['current_price'] 
            and product_data['original_price'] 
            and product_data['original_price'] > product_data['current_price']
        ):
            discount = product_data['original_price'] - product_data['current_price']
            discount_pct = (discount / product_data['original_price']) * 100
            product_data['discount'] = round(discount, 2)
            product_data['discount_percentage'] = round(discount_pct, 1)
        else:
            product_data['discount'] = 0
            product_data['discount_percentage'] = 0
        
        # Availability
        try:
            availability_element = soup.select_one('#availability')
            if availability_element:
                availability_text = availability_element.get_text(strip=True).lower() 
                product_data['in_stock'] = 'in stock' in availability_text
            else:
                add_to_cart_button = soup.select_one('#add-to-cart-button')
                product_data['in_stock'] = add_to_cart_button is not None
        except (AttributeError, TypeError):
            product_data['in_stock'] = None
        
        # Product ID (ASIN)
        try:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})/?', url)
            if asin_match:
                product_data['product_id'] = asin_match.group(1)
            else:
                for element in soup.select('input[name="ASIN"], input[name="asin"]'):
                    product_data['product_id'] = element.get('value')
                    break
        except Exception as e:
            self.logger.exception("Error extracting ASIN from page") 
        
        # Fallback if no product ID found
        if not product_data.get('product_id'):  
            product_data['product_id'] = self.extract_product_id(url)  
        
        # Ratings
        try:
            rating_element = soup.select_one('#acrPopover')
            if rating_element:
                rating_text = rating_element.get('title', '')
                rating_match = re.search(r'(\d+\.\d+)', rating_text)
                product_data['rating'] = float(rating_match.group(1)) if rating_match else None
            else:
                product_data['rating'] = None

            review_count_element = soup.select_one('#acrCustomerReviewText')
            if review_count_element:
                review_text = review_count_element.get_text(strip=True)
                count_match = re.search(r'([\d,]+)', review_text)
                product_data['review_count'] = int(count_match.group(1).replace(',', '')) if count_match else 0
            else:
                product_data['review_count'] = 0
        except (AttributeError, TypeError):
            product_data['rating'] = None
            product_data['review_count'] = 0
        
        # Brand
        try:
            brand_element = soup.select_one('#bylineInfo')
            if brand_element:
                brand_text = brand_element.get_text(strip=True) 
                brand_match = re.search(r'(?:by|brand:)[:\s]*(.*)', brand_text, re.IGNORECASE)  
                product_data['brand'] = brand_match.group(1).strip() if brand_match else brand_text
            else:
                product_data['brand'] = None
        except (AttributeError, TypeError):
            product_data['brand'] = None
        
        # Product features
        try:
            feature_bullets = soup.select('#feature-bullets li')
            product_data['features'] = [
                bullet.get_text(strip=True)
                for bullet in feature_bullets
                if bullet.get_text(strip=True)  
            ]
        except Exception as e:
            self.logger.exception("Failed to extract features")  
            product_data['features'] = []
        
        return product_data
