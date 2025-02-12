from ...core.activity_tracker import ActivityTracker, BrowserType, PlatformType
from typing import Dict, Optional
import logging
from datetime import datetime

class ChromiumTracker(ActivityTracker):
    """
    Activity tracker for Chromium-based browsers (Chrome, Brave, Edge, etc.)
    Handles Chromium-specific APIs and behaviors
    """
    
    def __init__(self, platform_type: str, db_path: str = "activity.db"):
        super().__init__(db_path)
        self.platform_type = platform_type
        self.browser_type = (BrowserType.CHROMIUM_MOBILE.value if platform_type == PlatformType.MOBILE.value 
                           else BrowserType.CHROMIUM_DESKTOP.value)
        self._setup_chromium_listeners()

    def _setup_chromium_listeners(self):
        """Sets up Chromium-specific event listeners"""
        try:
            # Chrome-specific API calls would go here
            # These will be implemented through browser extension
            self._setup_tab_listeners()
            self._setup_window_listeners()
            self._setup_visibility_listeners()
        except Exception as e:
            logging.error(f"Failed to setup Chromium listeners: {str(e)}")
            raise

    def _setup_tab_listeners(self):
        """
        Sets up listeners for tab events.
        This will be called by the browser extension.
        """
        pass

    def _setup_window_listeners(self):
        """
        Sets up listeners for window events.
        This will be called by the browser extension.
        """
        pass

    def _setup_visibility_listeners(self):
        """
        Sets up listeners for visibility events.
        This will be called by the browser extension.
        """
        pass

    def handle_tab_activated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab becomes active.
        Called by browser extension when chrome.tabs.onActivated fires.
        """
        try:
            tab_info['browser_type'] = self.browser_type
            tab_info['platform_type'] = self.platform_type
            return self.track_tab_change(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle tab activation: {str(e)}")
            return False

    def handle_tab_updated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab's URL changes.
        Called by browser extension when chrome.tabs.onUpdated fires.
        """
        try:
            if not self._is_valid_update(tab_info):
                return False
                
            tab_info['browser_type'] = self.browser_type
            tab_info['platform_type'] = self.platform_type
            return self.track_tab_change(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle tab update: {str(e)}")
            return False

    def handle_visibility_change(self, tab_info: Dict, is_visible: bool) -> bool:
        """
        Handles document visibility changes.
        Called by browser extension when visibilitychange fires.
        """
        try:
            if not is_visible:
                self._handle_tab_deactivation(tab_info, datetime.now().timestamp())
                return True
            return self.handle_tab_activated(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle visibility change: {str(e)}")
            return False

    def handle_window_focus(self, tab_info: Dict, has_focus: bool) -> bool:
        """
        Handles window focus changes.
        Called by browser extension when window focus changes.
        """
        try:
            if not has_focus:
                self._handle_tab_deactivation(tab_info, datetime.now().timestamp())
                return True
            return self.handle_tab_activated(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle window focus: {str(e)}")
            return False

    def _is_valid_update(self, tab_info: Dict) -> bool:
        """
        Validates tab update information.
        Ensures we're not tracking unnecessary updates.
        """
        required_fields = ['url', 'tab_id', 'window_id']
        if not all(field in tab_info for field in required_fields):
            return False
            
        # Check if this is a real URL change
        if self.last_active and self.last_active.get('url') == tab_info['url']:
            return False
            
        return True

    def _handle_private_mode(self, tab_info: Dict) -> bool:
        """
        Handles tracking in private/incognito mode.
        Returns True if tracking should proceed.
        """
        # Respect browser's private mode settings
        return not tab_info.get('incognito', False)