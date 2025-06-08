import oracledb
import asyncio
import logging
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

# --- Configuration ---
# Configure logging to display informational messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Force Thin Mode if the Oracle Client is not installed.
# This is a workaround; python-oracledb defaults to Thin Mode if a client isn't found.
oracledb.defaults.thin = True


class OracleConnection:
    """
    An asynchronous wrapper for handling connections to an Oracle database
    using the python-oracledb library in Thin Mode.
    """

    def __init__(self, config: Dict):
        """
        Initializes the OracleConnection with database configuration.

        Args:
            config (Dict): A dictionary containing connection details:
                           'username', 'password', 'host', 'port', 'service_name',
                           'min_connections' (optional), 'max_connections' (optional).
        """
        self.config = config
        self.connection_string = self._build_connection_string()
        self.pool: Optional[oracledb.AsyncConnectionPool] = None
        self.logger = logging.getLogger(__name__)

    def _build_connection_string(self) -> str:
        """Builds the Oracle Easy Connect string."""
        return f"{self.config['host']}:{self.config['port']}/{self.config['service_name']}"

    async def initialize(self):
        """
        Initializes the asynchronous connection pool.
        The `create_pool_async` function is synchronous and returns an awaitable pool object.
        Therefore, it should not be awaited itself.
        """
        if self.pool:
            self.logger.info("Connection pool already initialized.")
            return

        try:
            # FIX: Removed 'await'. oracledb.create_pool_async() is a synchronous function
            # that returns an async pool object. It should not be awaited.
            self.pool = oracledb.create_pool_async(
                user=self.config['username'],
                password=self.config['password'],
                dsn=self.connection_string,
                min=self.config.get('min_connections', 2),
                max=self.config.get('max_connections', 10),
                increment=1
            )

            # Test the connection to ensure the pool is working
            self.logger.info("Testing database connection...")
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1 FROM DUAL")
                    result = await cursor.fetchone()
                    if not result or result[0] != 1:
                        raise Exception("Database connection test failed.")
            self.logger.info("Oracle connection pool initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Oracle connection pool: {e}")
            self.pool = None # Ensure pool is None on failure
            raise

    @asynccontextmanager
    async def get_connection(self):
        """
        Provides a database connection from the pool using an async context manager.
        """
        if not self.pool:
            raise Exception("Pool not initialized. Please call initialize() first.")
        try:
            async with self.pool.acquire() as connection:
                yield connection
        except Exception as e:
            self.logger.error(f"Failed to acquire connection from pool: {e}")
            raise

    async def get_current_stock(self) -> List[Dict]:
        """Fetches all current stock information."""
        query = """
        SELECT
            p.product_id, p.product_name, p.category, p.unit,
            i.current_stock, i.reserved_stock, i.available_stock, i.last_updated
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        ORDER BY p.product_name
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    async def get_product_stock(self, product_id: str) -> Optional[Dict]:
        """Fetches stock information for a single product."""
        query = """
        SELECT
            p.product_id, p.product_name, p.category, p.unit,
            i.current_stock, i.reserved_stock, i.available_stock, i.last_updated
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE p.product_id = :product_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, {'product_id': product_id})
                row = await cursor.fetchone()
                if row:
                    columns = [col[0].lower() for col in cursor.description]
                    return dict(zip(columns, row))
                return None

    async def update_stock(self, product_id: str, quantity: int, operation: str = 'add'):
        """Updates stock for a product, either adding or subtracting."""
        if operation == 'add':
            query = """
            UPDATE inventory
            SET current_stock = current_stock + :quantity,
                available_stock = available_stock + :quantity,
                last_updated = SYSTIMESTAMP
            WHERE product_id = :product_id
            """
        else: # 'subtract'
            query = """
            UPDATE inventory
            SET current_stock = GREATEST(0, current_stock - :quantity),
                available_stock = GREATEST(0, available_stock - :quantity),
                last_updated = SYSTIMESTAMP
            WHERE product_id = :product_id
            """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, {'quantity': quantity, 'product_id': product_id})
            await conn.commit()
        self.logger.info(f"Updated stock for {product_id}: {operation} {quantity}")

    async def record_stock_transaction(self, transaction: Dict):
        """Records a detailed stock transaction."""
        query = """
        INSERT INTO stock_transactions (
            transaction_id, product_id, transaction_type, quantity,
            unit_cost, total_cost, supplier_id, reference_number,
            transaction_date, notes
        ) VALUES (
            stock_trans_seq.NEXTVAL, :product_id, :transaction_type, :quantity,
            :unit_cost, :total_cost, :supplier_id, :reference_number,
            SYSTIMESTAMP, :notes
        )
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, transaction)
            await conn.commit()

    async def get_low_stock_items(self, threshold_multiplier: float = 1.0) -> List[Dict]:
        """Finds items where the current stock is at or below the reorder level."""
        query = """
        SELECT
            p.product_id, p.product_name, p.category,
            i.current_stock,
            (p.reorder_level * :threshold_multiplier) as threshold,
            p.reorder_quantity
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE i.current_stock <= (p.reorder_level * :threshold_multiplier)
        ORDER BY (i.current_stock / p.reorder_level) ASC
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, {'threshold_multiplier': threshold_multiplier})
                columns = [col[0].lower() for col in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    async def execute_plsql_block(self, block: str):
        """Executes a generic PL/SQL block, useful for DDL operations."""
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(block)
            self.logger.info("PL/SQL block executed successfully.")
        except oracledb.DatabaseError as e:
            # ORA-00955: name is already used by an existing object
            if "ORA-00955" in str(e):
                self.logger.warning(f"PL/SQL block skipped (object already exists): {e}")
            else:
                self.logger.error(f"Error executing PL/SQL block: {e}")
                raise

    # FIX: Renamed this method from setup_schema to create_tables
    async def create_tables(self):
        """Creates all required tables and sequences."""
        self.logger.info("Creating database tables and sequences...")
        ddl_blocks = {
            "products table": """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE products (
                        product_id VARCHAR2(50) PRIMARY KEY,
                        product_name VARCHAR2(200) NOT NULL,
                        category VARCHAR2(100),
                        unit VARCHAR2(20) DEFAULT ''units'',
                        reorder_level NUMBER DEFAULT 50,
                        reorder_quantity NUMBER DEFAULT 100,
                        created_date DATE DEFAULT SYSDATE,
                        updated_date DATE DEFAULT SYSDATE
                    )';
                EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF;
                END;
            """,
            "inventory table": """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE inventory (
                        product_id VARCHAR2(50) PRIMARY KEY,
                        current_stock NUMBER DEFAULT 0,
                        reserved_stock NUMBER DEFAULT 0,
                        available_stock NUMBER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT SYSTIMESTAMP,
                        CONSTRAINT fk_inv_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
                    )';
                EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF;
                END;
            """,
            "stock_transactions table": """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE stock_transactions (
                        transaction_id NUMBER PRIMARY KEY,
                        product_id VARCHAR2(50),
                        transaction_type VARCHAR2(20),
                        quantity NUMBER,
                        unit_cost NUMBER(10, 2),
                        total_cost NUMBER(10, 2),
                        supplier_id VARCHAR2(50),
                        reference_number VARCHAR2(100),
                        transaction_date TIMESTAMP DEFAULT SYSTIMESTAMP,
                        notes VARCHAR2(500),
                        CONSTRAINT fk_trans_product FOREIGN KEY (product_id) REFERENCES products(product_id)
                    )';
                EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF;
                END;
            """,
            "stock_trans_seq sequence": """
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE SEQUENCE stock_trans_seq START WITH 1 INCREMENT BY 1 NOCACHE';
                EXCEPTION WHEN OTHERS THEN IF SQLCODE != -955 THEN RAISE; END IF;
                END;
            """
        }

        for name, block in ddl_blocks.items():
            self.logger.info(f"Creating {name}...")
            await self.execute_plsql_block(block)
        self.logger.info("Table creation complete.")


    async def seed_sample_data(self):
        """Seeds the database with sample products and inventory levels."""
        self.logger.info("Seeding sample data...")
        products_to_seed = [
            ('WIDGET-A', 'Alpha Widget', 'Electronics', 'units', 50, 100, 45),
            ('COMP-B', 'Bravo Component', 'Parts', 'units', 25, 50, 12),
            ('MAT-C', 'Charlie Material', 'Raw Materials', 'kg', 100, 200, 78),
            ('TOOL-D', 'Delta Tool', 'Tools', 'units', 20, 40, 5)
        ]

        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                # Use executemany for efficiency
                product_sql = """
                    MERGE INTO products p
                    USING (SELECT :1 AS product_id, :2 AS product_name, :3 AS category, :4 AS unit, :5 AS reorder_level, :6 AS reorder_quantity FROM DUAL) src
                    ON (p.product_id = src.product_id)
                    WHEN NOT MATCHED THEN
                        INSERT (product_id, product_name, category, unit, reorder_level, reorder_quantity)
                        VALUES (src.product_id, src.product_name, src.category, src.unit, src.reorder_level, src.reorder_quantity)
                """
                inventory_sql = """
                    MERGE INTO inventory i
                    USING (SELECT :1 AS product_id, :2 AS initial_stock FROM DUAL) src
                    ON (i.product_id = src.product_id)
                    WHEN NOT MATCHED THEN
                        INSERT (product_id, current_stock, available_stock)
                        VALUES (src.product_id, src.initial_stock, src.initial_stock)
                """

                product_data = [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in products_to_seed]
                inventory_data = [(p[0], p[6]) for p in products_to_seed]
                
                await cursor.executemany(product_sql, product_data)
                self.logger.info(f"Seeded {cursor.rowcount} products.")

                await cursor.executemany(inventory_sql, inventory_data)
                self.logger.info(f"Seeded {cursor.rowcount} inventory records.")

            await conn.commit()
        self.logger.info("Sample data seeded successfully.")

    async def close(self):
        """Closes the connection pool gracefully."""
        if self.pool and self.pool.is_healthy:
            self.logger.info("Closing database connection pool...")
            await self.pool.close()
            self.logger.info("Database connection pool closed.")
            self.pool = None


async def main():
    """
    Main function to demonstrate the OracleConnection class.
    """
    db_config = {
        "username": "agent",
        "password": "agent",
        "host": "DESKTOP-VMJMGK8", # e.g., 'localhost' or an IP address
        "port": 1521,
        "service_name": "MYDB" # e.g., 'XEPDB1' for Oracle XE
    }

    db = OracleConnection(db_config)
    try:
        # Initialize the connection pool
        await db.initialize()

        # FIX: Call the renamed method
        # Set up the database schema (tables, sequences)
        await db.create_tables()

        # Seed the database with sample data
        await db.seed_sample_data()

        # --- Perform Operations ---
        print("\n--- Current Stock ---")
        stock = await db.get_current_stock()
        for item in stock:
            print(f"  {item['product_name']}: {item['current_stock']} {item['unit']}")

        print("\n--- Low Stock Items ---")
        low_stock = await db.get_low_stock_items()
        if low_stock:
            for item in low_stock:
                print(f"  WARNING: {item['product_name']} is low ({item['current_stock']} <= {item['threshold']})")
        else:
            print("  No items are below their reorder threshold.")
        
        print("\n--- Updating stock for 'Delta Tool' ---")
        await db.update_stock('TOOL-D', 25, operation='add')
        tool_d_stock = await db.get_product_stock('TOOL-D')
        print(f"  New stock for Tool D: {tool_d_stock['current_stock']}")


    except Exception as e:
        logging.error(f"An error occurred in the main application: {e}")
    finally:
        # Ensure the connection pool is closed
        if db.pool:
            await db.close()

if __name__ == "__main__":
    # To run this script, ensure you have python-oracledb installed:
    # pip install oracledb
    #
    # Then, update the db_config dictionary above and run the file.
    asyncio.run(main())
