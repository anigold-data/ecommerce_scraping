import sqlite3
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Database")

# Database configuration
DB_DIR = os.path.join(os.getcwd(), "database")
DB_PATH = os.path.join(DB_DIR, "amazon_products.db")

def get_db_connection():
    """Establish connection to SQLite database"""
    try:
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        create_tables(conn)
        
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def create_tables(conn):
    """Create necessary database tables if they don't exist"""
    try:
        cursor = conn.cursor()
        
        # Products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE,
            retailer TEXT,
            name TEXT,
            brand TEXT,
            category TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Prices table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            current_price REAL,
            original_price REAL,
            discount_percentage REAL,
            in_stock BOOLEAN,
            timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        # Reviews table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            rating REAL,
            review_count INTEGER,
            timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        conn.commit()
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        conn.rollback()

def insert_product(conn, product_data):
    """
    Insert product into database
    
    Args:
        conn: Database connection
        product_data (dict): Product data
        
    Returns:
        int: Product ID or None if failed
    """
    try:
        cursor = conn.cursor()
        
        # Check if product already exists
        cursor.execute(
            "SELECT id FROM products WHERE product_id = ? AND retailer = ?",
            (product_data.get('product_id'), product_data.get('retailer'))
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing product
            product_id = result[0]
            cursor.execute(
                """
                UPDATE products
                SET name = ?, brand = ?, category = ?, url = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    product_data.get('name'),
                    product_data.get('brand'),
                    product_data.get('category'),
                    product_data.get('url'),
                    datetime.now().isoformat(),
                    product_id
                )
            )
        else:
            # Insert new product
            cursor.execute(
                """
                INSERT INTO products
                (product_id, retailer, name, brand, category, url)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_data.get('product_id'),
                    product_data.get('retailer'),
                    product_data.get('name'),
                    product_data.get('brand'),
                    product_data.get('category'),
                    product_data.get('url')
                )
            )
            product_id = cursor.lastrowid
            
        conn.commit()
        logger.info(f"Product {'updated' if result else 'inserted'} successfully: {product_data.get('name')}")
        return product_id
        
    except Exception as e:
        logger.error(f"Error inserting product: {str(e)}")
        conn.rollback()
        return None

def insert_price(conn, price_data):
    """
    Insert price into database
    
    Args:
        conn: Database connection
        price_data (dict): Price data
        
    Returns:
        int: Price ID or None if failed
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO prices
            (product_id, current_price, original_price, discount_percentage, in_stock, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                price_data.get('product_id'),
                price_data.get('current_price'),
                price_data.get('original_price'),
                price_data.get('discount_percentage'),
                price_data.get('in_stock', 0),
                price_data.get('timestamp', datetime.now().isoformat())
            )
        )
        
        price_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Price inserted successfully for product ID: {price_data.get('product_id')}")
        return price_id
        
    except Exception as e:
        logger.error(f"Error inserting price: {str(e)}")
        conn.rollback()
        return None

def insert_reviews(conn, review_data):
    """
    Insert review statistics into database
    
    Args:
        conn: Database connection
        review_data (dict): Review data
        
    Returns:
        int: Review ID or None if failed
    """
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO reviews
            (product_id, rating, review_count, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (
                review_data.get('product_id'),
                review_data.get('rating'),
                review_data.get('review_count'),
                review_data.get('timestamp', datetime.now().isoformat())
            )
        )
        
        review_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Review stats inserted successfully for product ID: {review_data.get('product_id')}")
        return review_id
        
    except Exception as e:
        logger.error(f"Error inserting review stats: {str(e)}")
        conn.rollback()
        return None

# Optional: Function to get product data by ID or other criteria
def get_product(conn, product_id=None, retailer=None, name=None):
    """Get product data from database"""
    try:
        cursor = conn.cursor()
        
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
            
        if retailer:
            query += " AND retailer = ?"
            params.append(retailer)
            
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
            
        cursor.execute(query, params)
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}")
        return []

# Function to get price history for a product
def get_price_history(conn, product_id):
    """Get price history for a product"""
    try:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM prices
            WHERE product_id = ?
            ORDER BY timestamp DESC
            """,
            (product_id,)
        )
        
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error getting price history: {str(e)}")
        return []