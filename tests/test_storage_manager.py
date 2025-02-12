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
def mobile_storage():
    """Creates a mobile test database"""
    storage = StorageManager(
        platform_type=PlatformType.MOBILE.value,
        engine_type=BrowserType.CHROMIUM_MOBILE.value,
        db_path="test_mobile_activities.db"
    )
    yield storage
    storage.close()
    # Cleanup
    if os.path.exists("test_mobile_activities.db"):
        os.remove("test_mobile_activities.db")
    if os.path.exists("test_mobile_activities.db-wal"):
        os.remove("test_mobile_activities.db-wal")
    if os.path.exists("test_mobile_activities.db-shm"):
        os.remove("test_mobile_activities.db-shm")

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
    """Tests data cleanup with mobile platform"""
    # Force mobile platform for stricter cleanup (7 days)
    storage.platform_type = "mobile"
    
    # Add old activity (15 days old)
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
    assert len(all_activities) == 1  # Only recent activity should remain

def test_platform_specific_cleanup(storage, mobile_storage, sample_activity):
    """Tests cleanup behavior across platforms"""
    # Create 10-day old activity
    ten_days_old = datetime.now() - timedelta(days=10)
    old_activity = {
        'url': 'https://old.example.com',
        'start_time': ten_days_old.timestamp(),
        'end_time': ten_days_old.timestamp() + 60,
        'duration': 60,
        'is_active': False
    }
    
    # Test mobile cleanup (7 days retention)
    mobile_storage.save_activity(old_activity)
    mobile_storage.save_activity(sample_activity)
    mobile_storage.cleanup_old_data()
    mobile_activities = mobile_storage.get_activities(0, datetime.now().timestamp() + 3600)
    assert len(mobile_activities) == 1  # 10-day old activity should be cleaned up
    
    # Test desktop cleanup (30 days retention)
    storage.save_activity(old_activity)
    storage.save_activity(sample_activity)
    storage.cleanup_old_data()
    desktop_activities = storage.get_activities(0, datetime.now().timestamp() + 3600)
    assert len(desktop_activities) == 2  # 10-day old activity should be retained

def test_engine_compatibility(storage):
    """Tests data handling across different browser engines"""
    engines = [
        BrowserType.CHROMIUM_DESKTOP.value,
        BrowserType.GECKO_DESKTOP.value,
        BrowserType.WEBKIT_DESKTOP.value
    ]
    
    for engine in engines:
        storage.engine_type = engine
        activity = {
            'url': f'https://test-{engine}.com',
            'start_time': datetime.now().timestamp(),
            'end_time': datetime.now().timestamp() + 60,
            'duration': 60,
            'is_active': True
        }
        assert storage.save_activity(activity) == True
    
    # Verify all engine data was saved
    activities = storage.get_activities(0, datetime.now().timestamp() + 3600)
    assert len(activities) == len(engines)
    saved_engines = set(a['engine_type'] for a in activities)
    assert saved_engines == set(engines)

def test_concurrent_access(storage, sample_activity):
    """Tests database handling of concurrent access"""
    # Create second connection to same database
    storage2 = StorageManager(
        platform_type=PlatformType.DESKTOP.value,
        engine_type=BrowserType.CHROMIUM_DESKTOP.value,
        db_path="test_activities.db"
    )
    
    try:
        # Save from first connection
        assert storage.save_activity(sample_activity) == True
        
        # Save from second connection
        activity2 = sample_activity.copy()
        activity2['url'] = 'https://example2.com'
        assert storage2.save_activity(activity2) == True
        
        # Verify both records exist
        activities = storage.get_activities(0, datetime.now().timestamp() + 3600)
        assert len(activities) == 2
        urls = set(a['url'] for a in activities)
        assert urls == set(['https://example.com', 'https://example2.com'])
    
    finally:
        storage2.close()

def test_platform_switching(storage, sample_activity):
    """Tests data handling when switching platforms"""
    # Save as desktop
    assert storage.save_activity(sample_activity) == True
    
    # Switch to mobile
    storage.platform_type = PlatformType.MOBILE.value
    
    # Save another activity
    activity2 = sample_activity.copy()
    activity2['url'] = 'https://mobile.example.com'
    assert storage.save_activity(activity2) == True
    
    # Verify both platforms' data exists
    activities = storage.get_activities(0, datetime.now().timestamp() + 3600)
    assert len(activities) == 2
    platforms = set(a['platform_type'] for a in activities)
    assert platforms == set([PlatformType.DESKTOP.value, PlatformType.MOBILE.value])

def test_connection_handling(storage, sample_activity):
    """Tests proper connection handling"""
    storage.close()
    # Create new connection attempt after close
    with pytest.raises(Exception):
        storage.connection.execute("SELECT 1") 