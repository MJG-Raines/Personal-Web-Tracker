import pytest
from datetime import datetime
import os
from backend.core.browsers.gecko_tracker import GeckoTracker
from backend.core.activity_tracker import BrowserType, PlatformType

@pytest.fixture
def desktop_tracker():
    """Creates a desktop Firefox tracker"""
    tracker = GeckoTracker(platform_type=PlatformType.DESKTOP.value, db_path="test_desktop.db")
    yield tracker
    if os.path.exists("test_desktop.db.state"):
        os.remove("test_desktop.db.state")

@pytest.fixture
def mobile_tracker():
    """Creates a mobile Firefox tracker"""
    tracker = GeckoTracker(platform_type=PlatformType.MOBILE.value, db_path="test_mobile.db")
    yield tracker
    if os.path.exists("test_mobile.db.state"):
        os.remove("test_mobile.db.state")

@pytest.fixture
def sample_tab():
    """Sample tab data for testing"""
    return {
        'url': 'https://example.com',
        'tab_id': 'tab1',
        'window_id': 'window1',
        'cookieStoreId': 'default'
    }

def test_browser_type_initialization():
    """Tests correct browser type assignment"""
    desktop = GeckoTracker(PlatformType.DESKTOP.value)
    assert desktop.browser_type == BrowserType.GECKO_DESKTOP.value
    
    mobile = GeckoTracker(PlatformType.MOBILE.value)
    assert mobile.browser_type == BrowserType.GECKO_MOBILE.value

def test_handle_tab_activated(desktop_tracker, sample_tab):
    """Tests tab activation handling"""
    assert desktop_tracker.handle_tab_activated(sample_tab) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    assert desktop_tracker.last_active['browser_type'] == BrowserType.GECKO_DESKTOP.value

def test_handle_tab_updated(desktop_tracker, sample_tab):
    """Tests tab URL update handling"""
    # First activation
    desktop_tracker.handle_tab_activated(sample_tab)
    
    # Update URL
    updated_tab = sample_tab.copy()
    updated_tab['url'] = 'https://example.com/updated'
    assert desktop_tracker.handle_tab_updated(updated_tab) == True
    assert desktop_tracker.last_active['url'] == updated_tab['url']

def test_ignore_same_url_update(desktop_tracker, sample_tab):
    """Tests that same-URL updates are ignored"""
    desktop_tracker.handle_tab_activated(sample_tab)
    # Try to update with same URL
    assert desktop_tracker.handle_tab_updated(sample_tab) == False

def test_handle_container_tabs(desktop_tracker, sample_tab):
    """Tests Firefox container tabs handling"""
    # Default container
    assert desktop_tracker._handle_container_tabs(sample_tab) == True
    
    # Private container
    private_container = sample_tab.copy()
    private_container['cookieStoreId'] = 'private-1'
    assert desktop_tracker._handle_container_tabs(private_container) == False
    
    # Custom container
    custom_container = sample_tab.copy()
    custom_container['cookieStoreId'] = 'custom-container-1'
    assert desktop_tracker._handle_container_tabs(custom_container) == True

def test_handle_visibility_change(desktop_tracker, sample_tab):
    """Tests visibility change handling"""
    # Tab becomes visible
    assert desktop_tracker.handle_visibility_change(sample_tab, True) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    
    # Tab becomes invisible
    assert desktop_tracker.handle_visibility_change(sample_tab, False) == True
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs

def test_handle_window_focus(desktop_tracker, sample_tab):
    """Tests window focus handling"""
    # Window gains focus
    assert desktop_tracker.handle_window_focus(sample_tab, True) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    
    # Window loses focus
    assert desktop_tracker.handle_window_focus(sample_tab, False) == True
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs

def test_private_mode_handling(desktop_tracker, sample_tab):
    """Tests private browsing mode handling"""
    # Normal mode
    assert desktop_tracker.handle_tab_activated(sample_tab) == True
    
    # Private mode
    private_tab = sample_tab.copy()
    private_tab['private'] = True
    assert desktop_tracker._handle_private_mode(private_tab) == False

def test_mobile_specific_behavior(mobile_tracker, sample_tab):
    """Tests mobile-specific behavior"""
    assert mobile_tracker.handle_tab_activated(sample_tab) == True
    assert mobile_tracker.last_active['browser_type'] == BrowserType.GECKO_MOBILE.value
    assert mobile_tracker.last_active['platform_type'] == PlatformType.MOBILE.value

def test_invalid_tab_info(desktop_tracker):
    """Tests handling of invalid tab information"""
    invalid_tab = {'url': 'https://example.com'}  # Missing required fields
    assert desktop_tracker.handle_tab_activated(invalid_tab) == False

def test_error_handling(desktop_tracker, sample_tab):
    """Tests error handling in various scenarios"""
    # Force an error by corrupting the tracker
    desktop_tracker.active_tabs = None
    assert desktop_tracker.handle_tab_activated(sample_tab) == False

def test_multiple_tab_switches(desktop_tracker, sample_tab):
    """Tests handling multiple tab switches"""
    # First tab
    assert desktop_tracker.handle_tab_activated(sample_tab) == True
    
    # Switch to second tab
    second_tab = {
        'url': 'https://example.org',
        'tab_id': 'tab2',
        'window_id': 'window1',
        'cookieStoreId': 'default'
    }
    assert desktop_tracker.handle_tab_activated(second_tab) == True
    
    # Verify first tab is no longer active
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs
    assert desktop_tracker.last_active['url'] == second_tab['url']