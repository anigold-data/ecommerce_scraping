from .base_scraper import BaseScraper
import re
import os

class TescoScraper(BaseScraper):
    """Tesco-specific scraper implementation"""

    def __init__(self):
        super().__init__('Tesco', base_delay=3, jitter=1)

    def extract_product_data(self, soup, url):
        product_data = {}

        # Product name
        try:
            product_data['name'] = soup.select_one('h1.product-details-tile__title').get_text(strip=True)
        except Exception as e:
            self.logger.warning("Could not extract product name")
            product_data['name'] = None

        # Current price
        try:
            price_elem = soup.select_one('div.price-control-wrapper span.value')
            if price_elem:
                product_data['current_price'] = float(price_elem.text.strip('£').replace(',', ''))
            else:
                product_data['current_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract current price")
            product_data['current_price'] = None

        # Original price
        try:
            orig_price = soup.select_one('div.price-control-wrapper span.strike-through')
            if orig_price:
                product_data['original_price'] = float(orig_price.text.strip('£').replace(',', ''))
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
            availability = soup.select_one('div.stock-wrapper span.stock-message')
            if availability:
                text = availability.get_text(strip=True).lower()
                product_data['in_stock'] = 'out of stock' not in text and 'unavailable' not in text
            else:
                product_data['in_stock'] = True
        except Exception as e:
            self.logger.warning("Could not determine stock status")
            product_data['in_stock'] = None

        # Product ID (TPNB - Tesco Product Number)
        try:
            product_id = re.search(r'TPNB: (\d+)', soup.get_text())
            product_data['product_id'] = product_id.group(1) if product_id else None
        except Exception as e:
            self.logger.warning("Could not extract product ID")
            product_data['product_id'] = None

        # Rating
        try:
            rating_elem = soup.select_one('div.review-overview span.average-rating')
            if rating_elem:
                product_data['rating'] = float(rating_elem.text.strip())
            else:
                product_data['rating'] = None
        except Exception as e:
            self.logger.warning("Could not extract rating")
            product_data['rating'] = None

        # Reviews
        try:
            review_count = soup.select_one('div.review-overview a.review-count')
            if review_count:
                count_text = review_count.get_text(strip=True)
                product_data['review_count'] = int(re.search(r'(\d+)', count_text).group(1))
            else:
                product_data['review_count'] = 0
        except Exception as e:
            self.logger.warning("Could not extract review count")
            product_data['review_count'] = 0

        # Brand
        try:
            brand = soup.select_one('a.product-brand')
            product_data['brand'] = brand.get_text(strip=True) if brand else None
        except Exception as e:
            self.logger.warning("Could not extract brand")
            product_data['brand'] = None

        # Features - product description points
        try:
            description = soup.select('div.product-info-block.section ul.product-features li')
            product_data['features'] = [li.get_text(strip=True) for li in description if li.get_text(strip=True)]
        except Exception as e:
            self.logger.warning("Could not extract features")
            product_data['features'] = []

        # Additional Tesco-specific data: price per unit
        try:
            unit_price = soup.select_one('span.price-per-quantity-weight')
            if unit_price:
                product_data['unit_price'] = unit_price.get_text(strip=True)
            else:
                product_data['unit_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract unit price")
            product_data['unit_price'] = None

        # Clubcard Price (if applicable)
        try:
            clubcard_price = soup.select_one('span.offer-text:contains("Clubcard Price")')
            if clubcard_price:
                price_value = soup.select_one('span.clubcard-price-value')
                product_data['clubcard_price'] = float(price_value.text.strip('£').replace(',', '')) if price_value else None
            else:
                product_data['clubcard_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract Clubcard price")
            product_data['clubcard_price'] = None

        return product_data