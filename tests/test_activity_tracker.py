import pytest
from datetime import datetime
import json
import os
from backend.core.activity_tracker import ActivityTracker, BrowserType, PlatformType

@pytest.fixture
def tracker():
    """Creates a fresh tracker for each test"""
    tracker = ActivityTracker("test.db")
    yield tracker
    # Cleanup after tests
    if os.path.exists("test.db.state"):
        os.remove("test.db.state")

@pytest.fixture
def sample_tab_info():
    """Sample tab data for testing"""
    return {
        'url': 'https://example.com',
        'browser_type': BrowserType.CHROMIUM_DESKTOP.value,
        'platform_type': PlatformType.DESKTOP.value,
        'tab_id': 'tab1',
        'window_id': 'window1'
    }

def test_track_tab_change(tracker, sample_tab_info):
    """Tests basic tab tracking functionality"""
    assert tracker.track_tab_change(sample_tab_info) == True
    assert tracker.last_active == sample_tab_info
    assert sample_tab_info['tab_id'] in tracker.active_tabs

def test_invalid_tab_info(tracker):
    """Tests handling of invalid tab data"""
    invalid_info = {'url': 'https://example.com'}  # Missing required fields
    assert tracker.track_tab_change(invalid_info) == False

def test_state_persistence(tracker, sample_tab_info):
    """Tests if state is saved and loaded correctly"""
    tracker.track_tab_change(sample_tab_info)
    
    # Create new tracker instance
    new_tracker = ActivityTracker("test.db")
    assert new_tracker.active_tabs != {}
    assert new_tracker.last_active is not None

def test_multiple_tab_changes(tracker, sample_tab_info):
    """Tests handling multiple tab changes"""
    tracker.track_tab_change(sample_tab_info)
    
    # Switch to new tab
    new_tab = sample_tab_info.copy()
    new_tab.update({
        'url': 'https://example.org',
        'tab_id': 'tab2'
    })
    tracker.track_tab_change(new_tab)
    
    # Original tab should be inactive
    assert 'tab1' not in tracker.active_tabs
    assert tracker.last_active == new_tab

def test_platform_specific_behavior(tracker):
    """Tests different platform behaviors"""
    mobile_tab = {
        'url': 'https://example.com',
        'browser_type': BrowserType.CHROMIUM_MOBILE.value,
        'platform_type': PlatformType.MOBILE.value,
        'tab_id': 'tab1',
        'window_id': 'window1'
    }
    
    desktop_tab = {
        'url': 'https://example.com',
        'browser_type': BrowserType.CHROMIUM_DESKTOP.value,
        'platform_type': PlatformType.DESKTOP.value,
        'tab_id': 'tab2',
        'window_id': 'window1'
    }
    
    assert tracker.track_tab_change(mobile_tab) == True
    assert tracker.track_tab_change(desktop_tab) == True

def test_crash_recovery(tracker, sample_tab_info):
    """Tests recovery after simulated crash"""
    tracker.track_tab_change(sample_tab_info)
    
    # Simulate crash by corrupting state file
    with open("test.db.state", 'w') as f:
        f.write("corrupted data")
    
    # New tracker should handle corrupted state
    new_tracker = ActivityTracker("test.db")
    assert new_tracker.active_tabs == {}
    assert new_tracker.last_active is None