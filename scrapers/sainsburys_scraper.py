from .base_scraper import BaseScraper
import re
import os

class SainsburysScraper(BaseScraper):
    """Sainsbury's-specific scraper implementation"""

    def __init__(self):
        super().__init__('Sainsburys', base_delay=4, jitter=2)

    def extract_product_data(self, soup, url):
        product_data = {}

        # Product name
        try:
            product_data['name'] = soup.select_one('h1.pd__header').get_text(strip=True)
        except Exception as e:
            self.logger.warning("Could not extract product name")
            product_data['name'] = None

        # Current price
        try:
            price_elem = soup.select_one('div.pd__cost__total')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'£(\d+\.\d+)', price_text)
                if price_match:
                    product_data['current_price'] = float(price_match.group(1))
                else:
                    product_data['current_price'] = None
            else:
                product_data['current_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract current price")
            product_data['current_price'] = None

        # Original price
        try:
            was_price = soup.select_one('div.pd__cost__was-price')
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
            availability = soup.select_one('div.pd__availability')
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
            # Sainsbury's product pages often have the item code in the URL
            product_id = re.search(r'/([0-9]+)$', url)
            if product_id:
                product_data['product_id'] = product_id.group(1)
            else:
                # Try to find it in the page content
                product_id_elem = soup.select_one('p.pd__item-code')
                if product_id_elem:
                    product_id_text = product_id_elem.get_text(strip=True)
                    product_id_match = re.search(r'(\d+)', product_id_text)
                    product_data['product_id'] = product_id_match.group(1) if product_id_match else None
                else:
                    product_data['product_id'] = None
        except Exception as e:
            self.logger.warning("Could not extract product ID")
            product_data['product_id'] = None

        # Rating
        try:
            rating_elem = soup.select_one('div.pd__reviews-rating')
            if rating_elem and 'data-star-rating' in rating_elem.attrs:
                product_data['rating'] = float(rating_elem['data-star-rating'])
            else:
                product_data['rating'] = None
        except Exception as e:
            self.logger.warning("Could not extract rating")
            product_data['rating'] = None

        # Reviews
        try:
            reviews_elem = soup.select_one('div.pd__reviews-count')
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
            brand_elem = soup.select_one('span.pd__brand')
            product_data['brand'] = brand_elem.get_text(strip=True) if brand_elem else None
        except Exception as e:
            self.logger.warning("Could not extract brand")
            product_data['brand'] = None

        # Features - product description points
        try:
            features = soup.select('div.pd__description ul li')
            product_data['features'] = [li.get_text(strip=True) for li in features if li.get_text(strip=True)]
        except Exception as e:
            self.logger.warning("Could not extract features")
            product_data['features'] = []

        # Unit price
        try:
            unit_price_elem = soup.select_one('div.pd__cost__unit-price')
            product_data['unit_price'] = unit_price_elem.get_text(strip=True) if unit_price_elem else None
        except Exception as e:
            self.logger.warning("Could not extract unit price")
            product_data['unit_price'] = None

        # Nectar Price (Sainsbury's loyalty program pricing)
        try:
            nectar_price_elem = soup.select_one('div.pd__nectar-price')
            if nectar_price_elem:
                nectar_price_text = nectar_price_elem.get_text(strip=True)
                nectar_price_match = re.search(r'£(\d+\.\d+)', nectar_price_text)
                product_data['nectar_price'] = float(nectar_price_match.group(1)) if nectar_price_match else None
            else:
                product_data['nectar_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract Nectar price")
            product_data['nectar_price'] = None

        return product_data