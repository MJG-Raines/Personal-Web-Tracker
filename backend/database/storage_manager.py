import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import json
from enum import Enum
from ..core.activity_tracker import BrowserType, PlatformType

class StorageManager:
    """
    Handles all database operations for activity tracking.
    Uses SQLite3 with platform-specific optimizations.
    """
    
    def __init__(self, platform_type: str, engine_type: str, db_path: str = "activity.db"):
        self.platform_type = platform_type
        self.engine_type = engine_type
        self.db_path = Path(db_path)
        self.connection = None
        self._setup_database()
        
    def _setup_database(self):
        """Sets up SQLite database with proper configuration"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA journal_mode=WAL")  # Better concurrency
            self._create_tables()
        except Exception as e:
            logging.error(f"Database setup failed: {str(e)}")
            raise
        
    def _create_tables(self):
        """Creates tables with indexes based on platform type"""
        with self.connection:
            # Main activity table
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    duration REAL NOT NULL,
                    platform_type TEXT NOT NULL,
                    engine_type TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add indexes based on platform
            if self.platform_type == "desktop":
                self.connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url 
                    ON activities(url)
                """)
                self.connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_times 
                    ON activities(start_time, end_time)
                """)
            else:
                # Minimal index for mobile
                self.connection.execute("""
                    CREATE INDEX IF NOT EXISTS idx_basic 
                    ON activities(start_time)
                """)

    def save_activity(self, activity_data: Dict) -> bool:
        """Saves a single activity record"""
        try:
            with self.connection:
                self.connection.execute("""
                    INSERT INTO activities (
                        url, start_time, end_time, duration,
                        platform_type, engine_type, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_data['url'],
                    activity_data['start_time'],
                    activity_data['end_time'],
                    activity_data['duration'],
                    self.platform_type,
                    self.engine_type,
                    activity_data['is_active']
                ))
            return True
        except Exception as e:
            logging.error(f"Failed to save activity: {str(e)}")
            return False

    def get_activities(self, start_time: float, end_time: float) -> List[Dict]:
        """Gets activities within a time range"""
        try:
            cursor = self.connection.execute("""
                SELECT * FROM activities 
                WHERE start_time >= ? AND end_time <= ?
                ORDER BY start_time DESC
            """, (start_time, end_time))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get activities: {str(e)}")
            return []

    def cleanup_old_data(self):
        """Cleans up old data based on platform type"""
        try:
            days_to_keep = 7 if self.platform_type == "mobile" else 30
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 86400)
            
            print(f"\nCutoff time: {datetime.fromtimestamp(cutoff_time)}")
            
            cursor = self.connection.execute("SELECT start_time FROM activities")
            times = cursor.fetchall()
            print(f"Current times in DB: {[datetime.fromtimestamp(t[0]) for t in times]}")
            
            with self.connection:
                self.connection.execute("""
                    DELETE FROM activities WHERE start_time < ?
                """, (cutoff_time,))

                cursor = self.connection.execute("SELECT COUNT(*) FROM activities")
                count = cursor.fetchone()[0]
                print(f"Records after deletion: {count}")
                
                
        except Exception as e:
            logging.error(f"Failed to cleanup old data: {str(e)}")

    def close(self):
        """Properly closes the database connection"""
        if self.connection:
            self.connection.close()