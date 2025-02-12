from ...core.activity_tracker import ActivityTracker, BrowserType, PlatformType
from typing import Dict, Optional
import logging
from datetime import datetime

class GeckoTracker(ActivityTracker):
    """
    Activity tracker for Gecko-based browsers (Firefox)
    Handles Firefox-specific APIs and behaviors
    """
    
    def __init__(self, platform_type: str, db_path: str = "activity.db"):
        super().__init__(db_path)
        self.platform_type = platform_type
        self.browser_type = (BrowserType.GECKO_MOBILE.value if platform_type == PlatformType.MOBILE.value 
                           else BrowserType.GECKO_DESKTOP.value)
        self._setup_gecko_listeners()

    def _setup_gecko_listeners(self):
        """Sets up Firefox-specific event listeners"""
        try:
            # Firefox uses different API names than Chrome
            self._setup_tab_listeners()
            self._setup_window_listeners()
            self._setup_visibility_listeners()
        except Exception as e:
            logging.error(f"Failed to setup Gecko listeners: {str(e)}")
            raise

    def _setup_tab_listeners(self):
        """
        Sets up listeners for tab events.
        Firefox uses browser.tabs instead of chrome.tabs
        """
        pass

    def _setup_window_listeners(self):
        """
        Sets up listeners for window events.
        Firefox handles window focus differently than Chrome
        """
        pass

    def _setup_visibility_listeners(self):
        """
        Sets up listeners for visibility events.
        Firefox has additional permissions needed for visibility
        """
        pass

    def handle_tab_activated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab becomes active.
        Called by browser extension when tabs.onActivated fires.
        """
        try:
            if not self._handle_container_tabs(tab_info):
                return False
                
            tab_info['browser_type'] = self.browser_type
            tab_info['platform_type'] = self.platform_type
            return self.track_tab_change(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle tab activation: {str(e)}")
            return False

    def handle_tab_updated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab's URL changes.
        Firefox provides more detailed update info than Chrome
        """
        try:
            if not self._is_valid_update(tab_info):
                return False
                
            if not self._handle_container_tabs(tab_info):
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
        Firefox requires explicit permission for visibility
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
        Firefox provides additional window state information
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
        Firefox provides additional update properties
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
        Firefox calls it private browsing instead of incognito
        """
        return not tab_info.get('private', False)

    def _handle_container_tabs(self, tab_info: Dict) -> bool:
        """
        Handles Firefox container tabs.
        Returns True if tracking should proceed.
        """
        # Container tabs are a Firefox-specific feature
        container = tab_info.get('cookieStoreId', 'default')
        # Don't track private container tabs
        if container.startswith('private'):
            return False
        return True