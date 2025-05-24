from .base_scraper import BaseScraper
import re
import os

class CurrysScraper(BaseScraper):
    """Currys-specific scraper implementation"""

    def __init__(self):
        super().__init__('Currys', base_delay=4, jitter=2)

    def extract_product_data(self, soup, url):
        product_data = {}

        # Product name
        try:
            product_data['name'] = soup.select_one('h1.product-title').get_text(strip=True)
        except Exception as e:
            self.logger.warning("Could not extract product name")
            product_data['name'] = None

        # Current price
        try:
            price_elem = soup.select_one('span.current')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = re.search(r'£([\d,]+\.\d+)', price_text)
                if price:
                    product_data['current_price'] = float(price.group(1).replace(',', ''))
                else:
                    product_data['current_price'] = None
            else:
                product_data['current_price'] = None
        except Exception as e:
            self.logger.warning("Could not extract current price")
            product_data['current_price'] = None

        # Original price
        try:
            was_price = soup.select_one('span.was')
            if was_price:
                was_text = was_price.get_text(strip=True)
                was_price_match = re.search(r'£([\d,]+\.\d+)', was_text)
                if was_price_match:
                    product_data['original_price'] = float(was_price_match.group(1).replace(',', ''))
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
            availability = soup.select_one('.stock-status')
            if availability:
                text = availability.get_text(strip=True).lower()
                product_data['in_stock'] = 'out of stock' not in text and 'unavailable' not in text
            else:
                # Check for delivery options as alternative indicator
                delivery_options = soup.select_one('.delivery-available')
                product_data['in_stock'] = True if delivery_options else False
        except Exception as e:
            self.logger.warning("Could not determine stock status")
            product_data['in_stock'] = None

        # Product ID (SKU)
        try:
            # Currys usually has SKU in the page
            sku_elem = soup.select_one('.product-sku span')
            if sku_elem:
                sku_text = sku_elem.get_text(strip=True)
                product_data['product_id'] = sku_text
            else:
                # Alternative: Check URL or data attributes
                sku_match = re.search(r'(\d{10})', url)
                product_data['product_id'] = sku_match.group(1) if sku_match else None
        except Exception as e:
            self.logger.warning("Could not extract product ID")
            product_data['product_id'] = None

        # Rating
        try:
            rating_elem = soup.select_one('.rating')
            if rating_elem and 'data-rating' in rating_elem.attrs:
                product_data['rating'] = float(rating_elem['data-rating'])
            else:
                product_data['rating'] = None
        except Exception as e:
            self.logger.warning("Could not extract rating")
            product_data['rating'] = None

        # Reviews
        try:
            reviews_elem = soup.select_one('.review-count')
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
            brand_elem = soup.select_one('span.brand-name')
            product_data['brand'] = brand_elem.get_text(strip=True) if brand_elem else None
        except Exception as e:
            self.logger.warning("Could not extract brand")
            product_data['brand'] = None

        # Features
        try:
            features = soup.select('div.key-specs ul li')
            product_data['features'] = [li.get_text(strip=True) for li in features if li.get_text(strip=True)]
            
            # If no features found, try alternate structure
            if not product_data['features']:
                features = soup.select('div.description-content ul li')
                product_data['features'] = [li.get_text(strip=True) for li in features if li.get_text(strip=True)]
        except Exception as e:
            self.logger.warning("Could not extract features")
            product_data['features'] = []

        # Model number (Currys specific)
        try:
            model_elem = soup.select_one('.product-model span')
            product_data['model_number'] = model_elem.get_text(strip=True) if model_elem else None
        except Exception as e:
            self.logger.warning("Could not extract model number")
            product_data['model_number'] = None

        # Availability for collection
        try:
            collection = soup.select_one('.collection-available')
            product_data['collection_available'] = True if collection else False
        except Exception as e:
            self.logger.warning("Could not determine collection availability")
            product_data['collection_available'] = None

        # Availability for delivery
        try:
            delivery = soup.select_one('.delivery-available')
            product_data['delivery_available'] = True if delivery else False
        except Exception as e:
            self.logger.warning("Could not determine delivery availability")
            product_data['delivery_available'] = None

        # Care plan options (Currys specific)
        try:
            care_plans = soup.select('.care-plan-option')
            if care_plans:
                product_data['care_plans_available'] = True
                # Optional: extract care plan details
                care_plan_details = []
                for plan in care_plans:
                    plan_name = plan.select_one('.care-plan-name')
                    plan_price = plan.select_one('.care-plan-price')
                    if plan_name and plan_price:
                        care_plan_details.append({
                            'name': plan_name.get_text(strip=True),
                            'price': plan_price.get_text(strip=True)
                        })
                product_data['care_plan_details'] = care_plan_details
            else:
                product_data['care_plans_available'] = False
        except Exception as e:
            self.logger.warning("Could not determine care plan availability")
            product_data['care_plans_available'] = None

        return product_data