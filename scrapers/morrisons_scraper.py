from .base_scraper import BaseScraper
import re
import os

class MorrisonsScraper(BaseScraper):
    """Morrisons-specific scraper implementation"""

    def __init__(self):
        super().__init__('Morrisons', base_delay=3.5, jitter=1.5)

    def extract_product_data(self, soup, url):
        product_data = {}

        # Product name
        try:
            product_data['name'] = soup.select_one('h1.bop-title').get_text(strip=True)
        except Exception as e:
            self.logger.warning("Could not extract product name")
            product_data['name'] = None

        # Current price
        try:
            price_pounds = soup.select_one('span.bop-price__current')
            price_pence = soup.select_one('span.bop-price__decimals')
            if price_pounds and price_pence:
                pounds = price_pounds.get_text(strip=True).replace('£', '')
                pence = price_pence.get_text(strip=True)
                product_data['current_price'] = float(f"{pounds}.{pence}")
            else:
                product_data['current_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract current price")
            product_data['current_price'] = None

        # Original price
        try:
            was_price = soup.select_one('span.bop-price__was')
            if was_price:
                was_price_text = was_price.get_text(strip=True)
                was_price_match = re.search(r'£(\d+\.\d+)', was_price_text)
                if was_price_match:
                    product_data['original_price'] = float(was_price_match.group(1))
                else:
                    product_data['original_price'] = product_data['current_price']
            else:
                product_data['original_price'] = product_data['current_price']
        except Exception as e:
            self.logger.warning("Could not extract original price")
            product_data['original_price'] = product_data['current_price']

        # Discount
        if product_data['current_price'] and product_data['original_price']:
            diff = product_data['original_price'] - product_data['current_price']
            product_data['discount'] = round(diff, 2)
            product_data['discount_percentage'] = round((diff / product_data['original_price']) * 100, 1)
        else:
            product_data['discount'] = 0
            product_data['discount_percentage'] = 0

        # Availability
        try:
            availability = soup.select_one('.bop-stock__message')
            if availability:
                text = availability.get_text(strip=True).lower()
                product_data['in_stock'] = 'out of stock' not in text and 'unavailable' not in text
            else:
                product_data['in_stock'] = True
        except Exception as e:
            self.logger.warning("Could not determine stock status")
            product_data['in_stock'] = None

        # Product ID
        try:
            # Try to extract from URL
            product_id = re.search(r'/product/(\d+)', url)
            if not product_id:
                # Or try from the page content
                product_id_elem = soup.select_one('span.bop-sku')
                if product_id_elem:
                    product_id_text = product_id_elem.get_text(strip=True)
                    product_id = re.search(r'(\d+)', product_id_text)
            
            product_data['product_id'] = product_id.group(1) if product_id else None
        except Exception as e:
            self.logger.warning("Could not extract product ID")
            product_data['product_id'] = None

        # Rating
        try:
            rating_elem = soup.select_one('.bop-stars__rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'([\d.]+)', rating_text)
                product_data['rating'] = float(rating_match.group(1)) if rating_match else None
            else:
                product_data['rating'] = None
        except Exception as e:
            self.logger.warning("Could not extract rating")
            product_data['rating'] = None

        # Reviews
        try:
            reviews_elem = soup.select_one('span.bop-reviews__count')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_match = re.search(r'(\d+)', reviews_text)
                product_data['review_count'] = int(reviews_match.group(1)) if reviews_match else 0
            else:
                product_data['review_count'] = 0
        except Exception as e:
            self.logger.warning("Could not extract review count")
            product_data['review_count'] = 0

        # Brand
        try:
            brand_elem = soup.select_one('div.bop-brand')
            product_data['brand'] = brand_elem.get_text(strip=True) if brand_elem else None
        except Exception as e:
            self.logger.warning("Could not extract brand")
            product_data['brand'] = None

        # Features - product description points
        try:
            description = soup.select('div.bop-description ul li')
            product_data['features'] = [li.get_text(strip=True) for li in description if li.get_text(strip=True)]
            
            # If no list items found, try paragraph text
            if not product_data['features']:
                desc_text = soup.select_one('div.bop-description')
                if desc_text:
                    product_data['features'] = [desc_text.get_text(strip=True)]
        except Exception as e:
            self.logger.warning("Could not extract features")
            product_data['features'] = []

        # Unit price
        try:
            unit_price_elem = soup.select_one('span.bop-price__per-unit')
            product_data['unit_price'] = unit_price_elem.get_text(strip=True) if unit_price_elem else None
        except Exception as e:
            self.logger.warning("Could not extract unit price")
            product_data['unit_price'] = None

        # More Card Price (Morrisons loyalty program pricing)
        try:
            more_card_price_elem = soup.select_one('span.bop-price__more-card')
            if more_card_price_elem:
                more_card_price_text = more_card_price_elem.get_text(strip=True)
                more_card_price_match = re.search(r'£(\d+\.\d+)', more_card_price_text)
                product_data['more_card_price'] = float(more_card_price_match.group(1)) if more_card_price_match else None
            else:
                product_data['more_card_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract More Card price")
            product_data['more_card_price'] = None

        return product_data