"""
Oracle Database Connection and Operations
Handles all database interactions for inventory management
"""

import cx_Oracle
import asyncio
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

class OracleConnection:
    def __init__(self, config: Dict):
        self.config = config
        self.connection_string = self._build_connection_string()
        self.pool = None
        self.logger = logging.getLogger(__name__)
        
    def _build_connection_string(self) -> str:
        """Build Oracle connection string"""
        return f"{self.config['username']}/{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['service_name']}"
        
    async def initialize(self):
        """Initialize connection pool"""
        try:
            # Create connection pool
            self.pool = cx_Oracle.create_pool(
                user=self.config['username'],
                password=self.config['password'],
                dsn=f"{self.config['host']}:{self.config['port']}/{self.config['service_name']}",
                min=self.config.get('min_connections', 2),
                max=self.config.get('max_connections', 10),
                increment=1,
                threaded=True
            )
            
            # Test connection
            await self.test_connection()
            self.logger.info("Oracle connection pool initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Oracle connection: {e}")
            raise
            
    async def test_connection(self):
        """Test database connection"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            
            if result[0] != 1:
                raise Exception("Database connection test failed")
                
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise Exception("Database pool not initialized")
            
        conn = None
        try:
            conn = self.pool.acquire()
            yield conn
        finally:
            if conn:
                self.pool.release(conn)
                
    async def get_current_stock(self) -> List[Dict]:
        """Get current stock levels for all products"""
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.unit,
            i.current_stock,
            i.reserved_stock,
            i.available_stock,
            i.last_updated
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        ORDER BY p.product_name
        """
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
    async def get_product_stock(self, product_id: str) -> Optional[Dict]:
        """Get stock information for specific product"""
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.unit,
            i.current_stock,
            i.reserved_stock,
            i.available_stock,
            i.last_updated
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = :product_id
        """
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, product_id=product_id)
            
            columns = [desc[0].lower() for desc in cursor.description]
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return dict(zip(columns, row))
            return None
            
    async def update_stock(self, product_id: str, quantity: int, operation: str = 'add'):
        """Update stock levels for a product"""
        if operation == 'add':
            query = """
            UPDATE inventory 
            SET current_stock = current_stock + :quantity,
                available_stock = available_stock + :quantity,
                last_updated = SYSDATE
            WHERE product_id = :product_id
            """
        else:  # subtract
            query = """
            UPDATE inventory 
            SET current_stock = GREATEST(0, current_stock - :quantity),
                available_stock = GREATEST(0, available_stock - :quantity),
                last_updated = SYSDATE
            WHERE product_id = :product_id
            """
            
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, product_id=product_id, quantity=quantity)
            conn.commit()
            cursor.close()
            
        self.logger.info(f"Updated stock for {product_id}: {operation} {quantity}")
        
    async def record_stock_transaction(self, transaction: Dict):
        """Record stock transaction for audit"""
        query = """
        INSERT INTO stock_transactions (
            transaction_id, product_id, transaction_type, quantity,
            unit_cost, total_cost, supplier_id, reference_number,
            transaction_date, notes
        ) VALUES (
            stock_trans_seq.NEXTVAL, :product_id, :transaction_type, :quantity,
            :unit_cost, :total_cost, :supplier_id, :reference_number,
            SYSDATE, :notes
        )
        """
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, **transaction)
            conn.commit()
            cursor.close()
            
    async def get_low_stock_items(self, threshold_multiplier: float = 1.0) -> List[Dict]:
        """Get items below their threshold levels"""
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            i.current_stock,
            p.reorder_level * :threshold_multiplier as threshold,
            p.reorder_quantity
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE i.current_stock <= (p.reorder_level * :threshold_multiplier)
        ORDER BY (i.current_stock / p.reorder_level) ASC
        """
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, threshold_multiplier=threshold_multiplier)
            
            columns = [desc[0].lower() for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
            
            return [dict(zip(columns, row)) for row in rows]
            
    async def create_tables(self):
        """Create necessary database tables"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id VARCHAR2(50) PRIMARY KEY,
                product_name VARCHAR2(200) NOT NULL,
                category VARCHAR2(100),
                unit VARCHAR2(20) DEFAULT 'units',
                reorder_level NUMBER DEFAULT 50,
                reorder_quantity NUMBER DEFAULT 100,
                created_date DATE DEFAULT SYSDATE,
                updated_date DATE DEFAULT SYSDATE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS inventory (
                product_id VARCHAR2(50) PRIMARY KEY,
                current_stock NUMBER DEFAULT 0,
                reserved_stock NUMBER DEFAULT 0,
                available_stock NUMBER DEFAULT 0,
                last_updated DATE DEFAULT SYSDATE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS stock_transactions (
                transaction_id NUMBER PRIMARY KEY,
                product_id VARCHAR2(50),
                transaction_type VARCHAR2(20),
                quantity NUMBER,
                unit_cost NUMBER(10,2),
                total_cost NUMBER(10,2),
                supplier_id VARCHAR2(50),
                reference_number VARCHAR2(100),
                transaction_date DATE DEFAULT SYSDATE,
                notes VARCHAR2(500),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
            """,
            """
            CREATE SEQUENCE IF NOT EXISTS stock_trans_seq
            START WITH 1
            INCREMENT BY 1
            NOCACHE
            """
        ]
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_sql in tables:
                try:
                    cursor.execute(table_sql)
                    conn.commit()
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        self.logger.error(f"Error creating table: {e}")
                        
            cursor.close()
            
    async def seed_sample_data(self):
        """Insert sample data for testing"""
        products = [
            ('WIDGET_A', 'Widget A', 'Electronics', 'units', 50, 100),
            ('COMP_B', 'Component B', 'Parts', 'units', 25, 50),
            ('MAT_C', 'Material C', 'Raw Materials', 'kg', 100, 200),
            ('TOOL_D', 'Tool D', 'Tools', 'units', 20, 40)
        ]
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert products
            for product in products:
                cursor.execute("""
                    MERGE INTO products p
                    USING (SELECT :1 as product_id FROM DUAL) src
                    ON (p.product_id = src.product_id)
                    WHEN NOT MATCHED THEN
                        INSERT (product_id, product_name, category, unit, reorder_level, reorder_quantity)
                        VALUES (:1, :2, :3, :4, :5, :6)
                """, product)
                
                # Insert inventory
                cursor.execute("""
                    MERGE INTO inventory i
                    USING (SELECT :1 as product_id FROM DUAL) src
                    ON (i.product_id = src.product_id)
                    WHEN NOT MATCHED THEN
                        INSERT (product_id, current_stock, available_stock)
                        VALUES (:1, :2, :2)
                """, (product[0], 45 if product[0] == 'WIDGET_A' else 
                             12 if product[0] == 'COMP_B' else
                             78 if product[0] == 'MAT_C' else 5))
                
            conn.commit()
            cursor.close()
            
        self.logger.info("Sample data seeded successfully")
        
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            self.logger.info("Database connection pool closed")