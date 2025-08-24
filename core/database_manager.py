"""
Database Manager Singleton
Centralized database connection management
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from core.utils import LoggerUtils


class DatabaseManager:
    """Singleton database manager for centralized connection handling"""

    _instance = None
    _connection = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        self.logger = LoggerUtils.get_logger(__name__)
        self.db_path = db_path or self._get_default_db_path()
        self._ensure_database_directory()
        self._initialized = True

    def _get_default_db_path(self) -> str:
        """Get default database path"""
        project_root = Path(__file__).parent.parent
        # Use existing database with AI agent long memory
        db_path = project_root / "database" / "ecobot.db"
        return str(db_path)

    def _ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Database directory ensured: {db_dir}")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection (creates if not exists)"""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
                self.logger.info(f"Database connection established: {self.db_path}")
            except Exception as e:
                self.logger.error(f"Failed to connect to database: {str(e)}")
                raise

        return self._connection

    def close_connection(self):
        """Close database connection"""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error(f"Error closing database connection: {str(e)}")

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute SELECT query"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()
            return cursor.rowcount

        except Exception as e:
            self.logger.error(f"Update execution error: {str(e)}")
            conn.rollback()
            raise

    def execute_many(self, query: str, params_list: list) -> int:
        """Execute multiple statements"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

        except Exception as e:
            self.logger.error(f"Batch execution error: {str(e)}")
            conn.rollback()
            raise

    def get_table_info(self, table_name: str) -> list:
        """Get table schema information"""
        try:
            query = "PRAGMA table_info(?)"
            return self.execute_query(query, (table_name,))
        except Exception as e:
            self.logger.error(f"Error getting table info for {table_name}: {str(e)}")
            return []

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except Exception as e:
            self.logger.error(f"Error checking table existence: {str(e)}")
            return False

    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            stats = {
                "db_path": self.db_path,
                "db_size": Path(self.db_path).stat().st_size
                if Path(self.db_path).exists()
                else 0,
                "tables": [],
            }

            # Get list of tables
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = self.execute_query(tables_query)

            for table in tables:
                table_name = table["name"]
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_result = self.execute_query(count_query)
                row_count = count_result[0]["count"] if count_result else 0

                stats["tables"].append({"name": table_name, "row_count": row_count})

            return stats

        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}

    def init_database(self):
        """Initialize database with required tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    name TEXT,
                    address TEXT,
                    role TEXT DEFAULT 'warga' CHECK (role IN ('admin', 'koordinator', 'warga')),
                    registration_status TEXT DEFAULT 'registered' CHECK (registration_status IN ('pending', 'registered', 'blocked')),
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    total_images INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    preferences TEXT
                )
            """)

            # Collection points table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_points (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('fixed', 'mobile', 'community')),
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    accepted_waste_types TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    contact TEXT,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Waste classifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS waste_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_phone TEXT NOT NULL,
                    waste_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    image_url TEXT,
                    classification_method TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_phone) REFERENCES users (phone_number)
                )
            """)

            # Collection schedules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    point_id TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (point_id) REFERENCES collection_points (id)
                )
            """)

            # User interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_phone TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_phone) REFERENCES users (phone_number)
                )
            """)

            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            """)

            conn.commit()
            self.logger.info("Database tables initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise

    def __del__(self):
        """Cleanup on deletion"""
        self.close_connection()


# Global instance getter
def get_database_manager(db_path: str = None) -> DatabaseManager:
    """Get global database manager instance"""
    return DatabaseManager(db_path)
