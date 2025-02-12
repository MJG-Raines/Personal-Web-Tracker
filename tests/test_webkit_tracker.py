import pytest
from datetime import datetime
import os
from backend.core.browsers.webkit_tracker import WebKitTracker
from backend.core.activity_tracker import BrowserType, PlatformType

@pytest.fixture
def desktop_tracker():
    """Creates a desktop Safari tracker"""
    tracker = WebKitTracker(platform_type=PlatformType.DESKTOP.value, db_path="test_desktop.db")
    yield tracker
    if os.path.exists("test_desktop.db.state"):
        os.remove("test_desktop.db.state")

@pytest.fixture
def ios_tracker():
    """Creates an iOS Safari tracker"""
    tracker = WebKitTracker(platform_type=PlatformType.MOBILE.value, db_path="test_mobile.db")
    yield tracker
    if os.path.exists("test_mobile.db.state"):
        os.remove("test_mobile.db.state")

@pytest.fixture
def sample_tab():
    """Sample tab data for testing"""
    return {
        'url': 'https://example.com',
        'tab_id': 'tab1',
        'window_id': 'window1'
    }

def test_browser_type_initialization():
    """Tests correct browser type assignment"""
    desktop = WebKitTracker(PlatformType.DESKTOP.value)
    assert desktop.browser_type == BrowserType.WEBKIT_DESKTOP.value
    
    mobile = WebKitTracker(PlatformType.MOBILE.value)
    assert mobile.browser_type == BrowserType.WEBKIT_MOBILE.value

def test_restricted_mode_default():
    """Tests that Safari starts in restricted mode"""
    tracker = WebKitTracker(PlatformType.DESKTOP.value)
    assert tracker.restricted_mode == True

def test_handle_tab_activated(desktop_tracker, sample_tab):
    """Tests tab activation handling"""
    assert desktop_tracker.handle_tab_activated(sample_tab) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    assert desktop_tracker.last_active['browser_type'] == BrowserType.WEBKIT_DESKTOP.value

def test_handle_tab_updated(desktop_tracker, sample_tab):
    """Tests tab URL update handling"""
    desktop_tracker.handle_tab_activated(sample_tab)
    
    updated_tab = sample_tab.copy()
    updated_tab['url'] = 'https://example.com/updated'
    assert desktop_tracker.handle_tab_updated(updated_tab) == True
    assert desktop_tracker.last_active['url'] == updated_tab['url']

def test_private_browsing_handling(desktop_tracker, sample_tab):
    """Tests private browsing mode handling"""
    # Normal mode
    assert desktop_tracker.handle_tab_activated(sample_tab) == True
    
    # Private mode
    private_tab = sample_tab.copy()
    private_tab['private'] = True
    assert desktop_tracker._is_tracking_allowed(private_tab) == False

def test_ios_specific_handling(ios_tracker):
    """Tests iOS-specific adaptations"""
    ios_tab = {
        'url': 'https://example.com',
        'ios_tab_id': 'ios123',
        'window_id': 'window1'
    }
    adapted_tab = ios_tracker._adapt_for_ios(ios_tab)
    assert adapted_tab['tab_id'].startswith('ios_')
    assert adapted_tab['tab_id'] == 'ios_ios123'

def test_visibility_change(desktop_tracker, sample_tab):
    """Tests visibility change handling"""
    # Tab becomes visible
    assert desktop_tracker.handle_visibility_change(sample_tab, True) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    
    # Tab becomes invisible
    assert desktop_tracker.handle_visibility_change(sample_tab, False) == True
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs

def test_window_focus(desktop_tracker, sample_tab):
    """Tests window focus handling"""
    # Window gains focus
    assert desktop_tracker.handle_window_focus(sample_tab, True) == True
    assert desktop_tracker.last_active['url'] == sample_tab['url']
    
    # Window loses focus
    assert desktop_tracker.handle_window_focus(sample_tab, False) == True
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs

def test_tracking_restrictions(desktop_tracker, sample_tab):
    """Tests tracking restriction handling"""
    # Force restricted mode
    desktop_tracker.restricted_mode = True
    
    # Should still work with explicit consent (default in our implementation)
    assert desktop_tracker._is_tracking_allowed(sample_tab) == True
    
    # Test with private browsing
    private_tab = sample_tab.copy()
    private_tab['private'] = True
    assert desktop_tracker._is_tracking_allowed(private_tab) == False

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
        'window_id': 'window1'
    }
    assert desktop_tracker.handle_tab_activated(second_tab) == True
    
    # Verify first tab is no longer active
    assert sample_tab['tab_id'] not in desktop_tracker.active_tabs
    assert desktop_tracker.last_active['url'] == second_tab['url']