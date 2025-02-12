import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from backend.database.storage_manager import StorageManager
from backend.core.activity_tracker import BrowserType, PlatformType

@pytest.fixture
def storage():
    """Creates a test database for each test"""
    storage = StorageManager(
        platform_type=PlatformType.DESKTOP.value,
        engine_type=BrowserType.CHROMIUM_DESKTOP.value,
        db_path="test_activities.db"
    )
    yield storage
    storage.close()
    # Cleanup test database
    if os.path.exists("test_activities.db"):
        os.remove("test_activities.db")
    if os.path.exists("test_activities.db-wal"):
        os.remove("test_activities.db-wal")
    if os.path.exists("test_activities.db-shm"):
        os.remove("test_activities.db-shm")

@pytest.fixture
def sample_activity():
    """Sample activity data for testing"""
    now = datetime.now().timestamp()
    return {
        'url': 'https://example.com',
        'start_time': now,
        'end_time': now + 60,
        'duration': 60,
        'is_active': True
    }

def test_database_setup(storage):
    """Tests if database is properly initialized"""
    assert os.path.exists("test_activities.db")
    
    # Check if tables are created
    cursor = storage.connection.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='activities'
    """)
    assert cursor.fetchone() is not None

def test_save_activity(storage, sample_activity):
    """Tests saving activity data"""
    assert storage.save_activity(sample_activity) == True
    
    # Verify data was saved
    cursor = storage.connection.execute("SELECT * FROM activities")
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == sample_activity['url']

def test_get_activities(storage, sample_activity):
    """Tests retrieving activity data"""
    storage.save_activity(sample_activity)
    
    activities = storage.get_activities(
        start_time=sample_activity['start_time'] - 10,
        end_time=sample_activity['end_time'] + 10
    )
    assert len(activities) == 1
    assert activities[0]['url'] == sample_activity['url']

def test_cleanup_old_data(storage, sample_activity):
    """Tests data cleanup based on platform"""
    # Force mobile platform for stricter cleanup (7 days)
    storage.platform_type = "mobile"
    
    # Add old activity
    old_time = datetime.now() - timedelta(days=15)
    old_activity = {
        'url': 'https://old.example.com',
        'start_time': old_time.timestamp(),
        'end_time': old_time.timestamp() + 60,
        'duration': 60,
        'is_active': False
    }
    storage.save_activity(old_activity)
    storage.save_activity(sample_activity)
    
    # Clean up old data
    storage.cleanup_old_data()
    
    # Get all activities after cleanup
    all_activities = storage.get_activities(
        start_time=0,
        end_time=datetime.now().timestamp() + 3600
    )
    assert len(all_activities) == 1  # Should only have the recent activity

def test_platform_specific_behavior():
    """Tests different platform configurations"""
    # Mobile storage
    mobile_storage = StorageManager(
        platform_type=PlatformType.MOBILE.value,
        engine_type=BrowserType.CHROMIUM_MOBILE.value,
        db_path="test_mobile.db"
    )
    
    # Check mobile-specific optimizations
    cursor = mobile_storage.connection.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND sql LIKE '%idx_basic%'
    """)
    assert cursor.fetchone() is not None
    
    mobile_storage.close()
    os.remove("test_mobile.db")

def test_connection_handling(storage, sample_activity):
    """Tests proper connection handling"""
    storage.close()
    # Create new connection attempt after close
    with pytest.raises(Exception):  # SQLite might raise different exceptions
        storage.connection.execute("SELECT 1")