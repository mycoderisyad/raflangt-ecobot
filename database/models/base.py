"""
Database Base Manager
Core database connection and initialization
"""

import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database connections and operations"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv("DATABASE_PATH", "database/ecobot.db")

        self.db_path = db_path
        self.ensure_database_directory()
        self.init_database()

    def ensure_database_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

    def init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Users table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone_number TEXT UNIQUE NOT NULL,
                        name TEXT,
                        address TEXT,
                        registration_status TEXT DEFAULT 'pending',
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_messages INTEGER DEFAULT 0,
                        total_images INTEGER DEFAULT 0,
                        points INTEGER DEFAULT 0,
                        role TEXT DEFAULT 'warga',
                        is_active BOOLEAN DEFAULT 1,
                        preferences TEXT  -- JSON string for user preferences
                    )
                """
                )

                # Waste classifications table
                cursor.execute(
                    """
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
                """
                )

                # User interactions table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_phone TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        message_content TEXT,
                        response_content TEXT,
                        success BOOLEAN DEFAULT 1,
                        response_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_phone) REFERENCES users (phone_number)
                    )
                """
                )

                # Collection points table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS collection_points (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        accepted_waste_types TEXT NOT NULL,  -- JSON array
                        schedule TEXT NOT NULL,
                        contact TEXT,
                        description TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Collection schedules table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS collection_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        location_name TEXT NOT NULL,
                        address TEXT NOT NULL,
                        schedule_day TEXT NOT NULL,
                        schedule_time TEXT NOT NULL,
                        waste_types TEXT NOT NULL,  -- JSON array
                        contact TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # System logs table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        module TEXT,
                        user_phone TEXT,
                        extra_data TEXT,  -- JSON string
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_users_phone 
                    ON users (phone_number)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_users_role 
                    ON users (role)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_classifications_user_date 
                    ON waste_classifications (user_phone, created_at)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_interactions_user_date 
                    ON user_interactions (user_phone, created_at)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_logs_date 
                    ON system_logs (created_at)
                """
                )

                conn.commit()
                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise

    def execute_update(self, query: str, params: tuple = None):
        """Execute an update/insert/delete query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution error: {str(e)}")
            raise
