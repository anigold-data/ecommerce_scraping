#### ETL Process Implementation

import pandas as pd
import logging
from datetime import datetime
import json
import os
from database import get_db_connection, insert_product, insert_price, insert_reviews

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ETL")

class ProductETL:
    """ETL pipeline for product data"""
    
    def __init__(self, db_connection=None):
        """Initialize ETL pipeline"""
        self.db_connection = db_connection
        if not db_connection:
            logger.info("No database connection provided, will establish when needed")
            
    def _get_db_connection(self):
        """Get database connection if not already established"""
        if not self.db_connection:
            logger.info("Establishing database connection")
            self.db_connection = get_db_connection()
        return self.db_connection
    
    def transform_product_data(self, raw_data, standardize_fields=True):
        """
        Transform raw product data into standardized format
        
        Args:
            raw_data (dict): Raw product data from scraper
            standardize_fields (bool): Whether to standardize field names
            
        Returns:
            dict: Transformed product data
        """
        if not raw_data:
            logger.warning("Received empty raw data")
            return None
            
        try:
            # Create a copy to avoid modifying the original
            data = raw_data.copy()
            
            # Ensure required fields exist
            required_fields = ['name', 'product_id', 'retailer', 'url']
            for field in required_fields:
                if field not in data or not data[field]:
                    logger.warning(f"Missing required field: {field}")
                    if field != 'product_id':  # product_id might be generated later
                        return None
            
            # Standardize field names if requested
            if standardize_fields:
                field_mapping = {
                    'title': 'name',
                    'productName': 'name',
                    'price': 'current_price',
                    'currentPrice': 'current_price',
                    'sale_price': 'current_price',
                    'listPrice': 'original_price',
                    'regular_price': 'original_price',
                    'list_price': 'original_price',
                    'msrp': 'original_price',
                    'availability': 'in_stock',
                    'inStock': 'in_stock',
                    'is_available': 'in_stock',
                    'productId': 'product_id',
                    'asin': 'product_id',
                    'sku': 'product_id',
                    'store': 'retailer',
                    'vendor': 'retailer',
                    'link': 'url',
                    'productUrl': 'url',
                    'stars': 'rating',
                    'averageRating': 'rating',
                    'reviewCount': 'review_count',
                    'numReviews': 'review_count',
                    'brand_name': 'brand',
                    'manufacturer': 'brand'
                }
                
                # Apply mapping
                for old_key, new_key in field_mapping.items():
                    if old_key in data and old_key != new_key:
                        if new_key not in data or not data[new_key]:
                            data[new_key] = data[old_key]
                        # Don't delete the original key as it might be needed elsewhere
            
            # Handle data types
            # Price
            if 'current_price' in data and data['current_price'] is not None:
                if isinstance(data['current_price'], str):
                    data['current_price'] = self._clean_price(data['current_price'])
                data['current_price'] = round(float(data['current_price']), 2)
            
            if 'original_price' in data and data['original_price'] is not None:
                if isinstance(data['original_price'], str):
                    data['original_price'] = self._clean_price(data['original_price'])
                data['original_price'] = round(float(data['original_price']), 2)
            
            # Calculate discount if not present
            if 'current_price' in data and 'original_price' in data:
                if data['current_price'] and data['original_price']:
                    if 'discount_percentage' not in data:
                        if data['original_price'] > data['current_price']:
                            discount = data['original_price'] - data['current_price']
                            discount_pct = (discount / data['original_price']) * 100
                            data['discount'] = round(discount, 2)
                            data['discount_percentage'] = round(discount_pct, 1)
                        else:
                            data['discount'] = 0
                            data['discount_percentage'] = 0
            
            # Ensure boolean for in_stock
            if 'in_stock' in data:
                if isinstance(data['in_stock'], str):
                    data['in_stock'] = data['in_stock'].lower() in ['true', 'yes', 'y', 'in stock', 'instock', '1']
            
            # Rating
            if 'rating' in data and data['rating'] is not None:
                if isinstance(data['rating'], str):
                    try:
                        data['rating'] = float(data['rating'].split()[0])
                    except:
                        # Try to extract numeric part with regex
                        import re
                        match = re.search(r'(\d+(\.\d+)?)', data['rating'])
                        if match:
                            data['rating'] = float(match.group(1))
                        else:
                            data['rating'] = None
            
            # Review count
            if 'review_count' in data and data['review_count'] is not None:
                if isinstance(data['review_count'], str):
                    data['review_count'] = self._extract_number(data['review_count'])
            
            # Ensure timestamp
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Extract category if possible
            if 'category' not in data and 'breadcrumbs' in data:
                if isinstance(data['breadcrumbs'], list) and len(data['breadcrumbs']) > 1:
                    data['category'] = data['breadcrumbs'][1]  # Often the second element is the main category
            
            return data
            
        except Exception as e:
            logger.error(f"Error transforming product data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _clean_price(self, price_str):
        """Clean price string to float"""
        if not price_str:
            return None
            
        try:
            # Remove currency symbols, commas, and whitespace
            import re
            numeric_str = re.sub(r'[^\d.]', '', price_str)
            return float(numeric_str)
        except:
            return None
    
    def _extract_number(self, text):
        """Extract number from text"""
        if not text:
            return 0
            
        import re
        match = re.search(r'(\d+[,\d]*)', text)
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
    
    def load_to_database(self, transformed_data):
        """
        Load transformed data into database
        
        Args:
            transformed_data (dict): Transformed product data
            
        Returns:
            bool: Success or failure
        """
        if not transformed_data:
            logger.warning("No data to load to database")
            return False
            
        try:
            conn = self._get_db_connection()
            
            # Split data into separate tables
            product_data = {
                'product_id': transformed_data.get('product_id'),
                'retailer': transformed_data.get('retailer'),
                'name': transformed_data.get('name'),
                'brand': transformed_data.get('brand'),
                'category': transformed_data.get('category'),
                'url': transformed_data.get('url')
            }
            
            price_data = {
                'current_price': transformed_data.get('current_price'),
                'original_price': transformed_data.get('original_price'),
                'discount_percentage': transformed_data.get('discount_percentage'),
                'in_stock': transformed_data.get('in_stock'),
                'timestamp': transformed_data.get('timestamp')
            }
            
            review_data = {
                'rating': transformed_data.get('rating'),
                'review_count': transformed_data.get('review_count'),
                'timestamp': transformed_data.get('timestamp')
            }
            
            # Insert into database
            product_id = insert_product(conn, product_data)
            if product_id:
                price_data['product_id'] = product_id
                review_data['product_id'] = product_id
                
                price_id = insert_price(conn, price_data)
                review_id = insert_reviews(conn, review_data)
                
                logger.info(f"Successfully loaded product {product_data['name']} to database")
                return True
            else:
                logger.error(f"Failed to insert product {product_data['name']} to database")
                return False
                
        except Exception as e:
            logger.error(f"Error loading data to database: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_raw_data(self, raw_data, save_to_db=True):
        """
        Process raw data through the ETL pipeline
        
        Args:
            raw_data (dict): Raw product data from scraper
            save_to_db (bool): Whether to save to database
            
        Returns:
            dict: Transformed data
        """
        transformed_data = self.transform_product_data(raw_data)
        
        if transformed_data and save_to_db:
            self.load_to_database(transformed_data)
            
        return transformed_data
    
    def process_file(self, filename, save_to_db=True):
        """
        Process raw data from JSON file
        
        Args:
            filename (str): JSON file path
            save_to_db (bool): Whether to save to database
            
        Returns:
            dict: Transformed data
        """
        try:
            with open(filename, 'r') as f:
                raw_data = json.load(f)
            
            return self.process_raw_data(raw_data, save_to_db)
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            return None
    
    def process_directory(self, directory, save_to_db=True):
        """
        Process all JSON files in directory
        
        Args:
            directory (str): Directory path
            save_to_db (bool): Whether to save to database
            
        Returns:
            int: Number of successfully processed files
        """
        if not os.path.isdir(directory):
            logger.error(f"Not a valid directory: {directory}")
            return 0
            
        success_count = 0
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                result = self.process_file(filepath, save_to_db)
                if result:
                    success_count += 1
        
        logger.info(f"Processed {success_count} files from {directory}")
        return success_count
    
if __name__ == "__main__":
    etl = ProductETL()
    etl.process_directory("C:/Users/adeda/OneDrive/Desktop/Ecommerce_Scraping/data")