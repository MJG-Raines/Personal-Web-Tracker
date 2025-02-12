from ...core.activity_tracker import ActivityTracker, BrowserType, PlatformType
from typing import Dict, Optional
import logging
from datetime import datetime

class WebKitTracker(ActivityTracker):
    """
    Activity tracker for WebKit-based browsers (Safari)
    Handles Safari's strict privacy and platform-specific restrictions
    """
    
    def __init__(self, platform_type: str, db_path: str = "activity.db"):
        super().__init__(db_path)
        self.platform_type = platform_type
        self.browser_type = (BrowserType.WEBKIT_MOBILE.value if platform_type == PlatformType.MOBILE.value 
                           else BrowserType.WEBKIT_DESKTOP.value)
        self.restricted_mode = True  # Safari starts restricted by default
        self._setup_webkit_listeners()

    def _setup_webkit_listeners(self):
        """Sets up Safari-specific event listeners with privacy restrictions"""
        try:
            # Safari requires explicit user permission for each feature
            self._setup_tab_listeners()
            self._setup_window_listeners()
            self._setup_visibility_listeners()
            self._check_permissions()
        except Exception as e:
            logging.error(f"Failed to setup WebKit listeners: {str(e)}")
            raise

    def _check_permissions(self):
        """
        Verifies required permissions and sets restricted mode accordingly.
        Safari requires explicit permission checks before API usage.
        """
        try:
            # Real implementation will check Safari's permission API
            # For now, assume restricted mode
            self.restricted_mode = True
            logging.info("Operating in restricted mode due to Safari privacy settings")
        except Exception as e:
            logging.error(f"Permission check failed: {str(e)}")
            self.restricted_mode = True

    def _setup_tab_listeners(self):
        """
        Sets up listeners for tab events.
        Safari has limited tab visibility across windows.
        """
        pass

    def _setup_window_listeners(self):
        """
        Sets up listeners for window events.
        Safari restricts cross-window communication.
        """
        pass

    def _setup_visibility_listeners(self):
        """
        Sets up listeners for visibility events.
        Safari has stricter visibility tracking rules.
        """
        pass

    def handle_tab_activated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab becomes active.
        Respects Safari's privacy restrictions.
        """
        try:
            if not self._is_tracking_allowed(tab_info):
                return False
                
            tab_info['browser_type'] = self.browser_type
            tab_info['platform_type'] = self.platform_type
            
            # Handle iOS/macOS differences
            if self.platform_type == PlatformType.MOBILE.value:
                tab_info = self._adapt_for_ios(tab_info)
            
            return self.track_tab_change(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle tab activation: {str(e)}")
            return False

    def handle_tab_updated(self, tab_info: Dict) -> bool:
        """
        Handles when a tab's URL changes.
        Safari provides limited URL information for privacy.
        """
        try:
            if not self._is_tracking_allowed(tab_info):
                return False
                
            if not self._is_valid_update(tab_info):
                return False
                
            tab_info['browser_type'] = self.browser_type
            tab_info['platform_type'] = self.platform_type
            
            if self.platform_type == PlatformType.MOBILE.value:
                tab_info = self._adapt_for_ios(tab_info)
                
            return self.track_tab_change(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle tab update: {str(e)}")
            return False

    def handle_visibility_change(self, tab_info: Dict, is_visible: bool) -> bool:
        """
        Handles document visibility changes.
        Safari has aggressive tab unloading.
        """
        try:
            if not self._is_tracking_allowed(tab_info):
                return False
                
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
        Safari limits cross-window visibility.
        """
        try:
            if not self._is_tracking_allowed(tab_info):
                return False
                
            if not has_focus:
                self._handle_tab_deactivation(tab_info, datetime.now().timestamp())
                return True
            return self.handle_tab_activated(tab_info)
        except Exception as e:
            logging.error(f"Failed to handle window focus: {str(e)}")
            return False

    def _is_tracking_allowed(self, tab_info: Dict) -> bool:
        """
        Checks if tracking is allowed based on Safari's privacy settings.
        Returns False if tracking is restricted.
        """
        if self.restricted_mode:
            if not self._is_explicit_consent_given(tab_info):
                return False
                
        if self._is_private_browsing(tab_info):
            return False
            
        return True

    def _is_explicit_consent_given(self, tab_info: Dict) -> bool:
        """
        Checks if user has given explicit consent for tracking this domain.
        Safari requires explicit consent per domain.
        """
        # Real implementation will check Safari's consent API
        return True  # For testing, assume consent given

    def _is_private_browsing(self, tab_info: Dict) -> bool:
        """
        Checks if tab is in private browsing mode.
        Safari provides minimal info in private mode.
        """
        return tab_info.get('private', False)

    def _is_valid_update(self, tab_info: Dict) -> bool:
        """
        Validates tab update information.
        Safari provides limited tab information.
        """
        required_fields = ['url', 'tab_id', 'window_id']
        if not all(field in tab_info for field in required_fields):
            return False
            
        if self.last_active and self.last_active.get('url') == tab_info['url']:
            return False
            
        return True

    def _adapt_for_ios(self, tab_info: Dict) -> Dict:
        """
        Adapts tab information for iOS-specific behaviors.
        iOS Safari has different tab management.
        """
        # Handle iOS-specific tab data
        if 'ios_tab_id' in tab_info:
            tab_info['tab_id'] = f"ios_{tab_info['ios_tab_id']}"
            
        return tab_info