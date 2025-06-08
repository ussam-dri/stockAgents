import sqlite3
import asyncio
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
import aiosqlite

class SQLiteConnection:
    def __init__(self, config: Dict):
        self.db_path = config.get('db_path', 'stock_management.db')
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the SQLite database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                self.logger.info("Testing database connection...")
                await db.execute("SELECT 1")
                self.logger.info("SQLite connection initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite connection: {e}")
            raise

    async def create_tables(self):
        """Create all required tables"""
        self.logger.info("Creating database tables...")
        async with aiosqlite.connect(self.db_path) as db:
            # Create products table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    category TEXT,
                    unit TEXT DEFAULT 'units',
                    reorder_level INTEGER DEFAULT 50,
                    reorder_quantity INTEGER DEFAULT 100,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create inventory table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id TEXT PRIMARY KEY,
                    current_stock INTEGER DEFAULT 0,
                    reserved_stock INTEGER DEFAULT 0,
                    available_stock INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
                )
            """)
            
            # Create stock_transactions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stock_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT,
                    transaction_type TEXT,
                    quantity INTEGER,
                    unit_cost REAL,
                    total_cost REAL,
                    supplier_id TEXT,
                    reference_number TEXT,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
                )
            """)
            
            await db.commit()
            self.logger.info("Tables created successfully.")

    async def seed_sample_data(self):
        """Seed sample data into the database"""
        self.logger.info("Seeding sample data...")
        async with aiosqlite.connect(self.db_path) as db:
            # Sample products
            products = [
                ('WIDGET_A', 'Widget A', 'Electronics', 'units', 50, 100),
                ('COMP_B', 'Component B', 'Electronics', 'units', 25, 50),
                ('MAT_C', 'Material C', 'Raw Materials', 'kg', 100, 200),
                ('TOOL_D', 'Tool D', 'Tools', 'units', 20, 40)
            ]
            
            # Insert products
            await db.executemany("""
                INSERT OR IGNORE INTO products 
                (product_id, product_name, category, unit, reorder_level, reorder_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, products)
            
            # Sample inventory
            inventory = [
                ('WIDGET_A', 100, 0, 100),
                ('COMP_B', 50, 0, 50),
                ('MAT_C', 200, 0, 200),
                ('TOOL_D', 40, 0, 40)
            ]
            
            # Insert inventory
            await db.executemany("""
                INSERT OR IGNORE INTO inventory 
                (product_id, current_stock, reserved_stock, available_stock)
                VALUES (?, ?, ?, ?)
            """, inventory)
            
            await db.commit()
            self.logger.info("Sample data seeded successfully.")

    async def get_current_stock(self) -> List[Dict]:
        """Fetch all current stock information"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute("""
                SELECT
                    p.product_id, p.product_name, p.category, p.unit,
                    i.current_stock, i.reserved_stock, i.available_stock, i.last_updated
                FROM products p
                JOIN inventory i ON p.product_id = i.product_id
                ORDER BY p.product_name
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_product_stock(self, product_id: str) -> Optional[Dict]:
        """Fetch stock information for a single product"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute("""
                SELECT
                    p.product_id, p.product_name, p.category, p.unit,
                    i.current_stock, i.reserved_stock, i.available_stock, i.last_updated
                FROM products p
                JOIN inventory i ON p.product_id = i.product_id
                WHERE p.product_id = ?
            """, (product_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_stock(self, product_id: str, quantity: int, operation: str = 'add'):
        """Update stock for a product"""
        async with aiosqlite.connect(self.db_path) as db:
            if operation == 'add':
                await db.execute("""
                    UPDATE inventory
                    SET current_stock = current_stock + ?,
                        available_stock = available_stock + ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (quantity, quantity, product_id))
            else:
                await db.execute("""
                    UPDATE inventory
                    SET current_stock = MAX(0, current_stock - ?),
                        available_stock = MAX(0, available_stock - ?),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE product_id = ?
                """, (quantity, quantity, product_id))
            await db.commit()

    async def close(self):
        """Close the database connection"""
        pass  # SQLite connections are automatically closed when the context manager exits 