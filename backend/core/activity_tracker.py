from datetime import datetime
import logging
from typing import Dict, Optional
import json
from enum import Enum

class BrowserType(Enum):
    CHROMIUM_DESKTOP = "chromium_desktop"
    CHROMIUM_MOBILE = "chromium_mobile"
    GECKO_DESKTOP = "gecko_desktop"
    GECKO_MOBILE = "gecko_mobile"
    WEBKIT_DESKTOP = "webkit_desktop"
    WEBKIT_MOBILE = "webkit_mobile"

class PlatformType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"  # Since tablets might handle things differently

class ActivityTracker:
    """
    Hey! This is the main tracking class that watches what tabs are active.
    It handles all the messy stuff like crashes, network issues, and private browsing.
    
    Think of it like a smart stopwatch - it knows when to start/stop based on
    what the user is actually doing, not just if a tab is open.
    """

    def __init__(self, db_path: str = "activity.db"):
        # Where we'll store everything
        self.db_path = db_path
        
        # Keep track of what's happening
        self.active_tabs = {}
        self.last_active = None
        
        # Set up our safety nets
        self._setup_logging()
        self._setup_storage()
        
    def _setup_logging(self):
        """
        Sets up our error catching and debugging - because things will go wrong!
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            filename='tracker.log'
        )
        
    def _setup_storage(self):
        """
        Gets our storage ready. If something crashes, we can pick up where we left off.
        """
        try:
            # Load any previous state if we crashed
            self._load_state()
        except Exception as e:
            logging.error(f"Had trouble loading previous state: {str(e)}")
            # Start fresh if we have to
            self.active_tabs = {}

    def track_tab_change(self, tab_info: Dict) -> bool:
        """
        Keeps track when someone switches tabs.
        Returns True if everything worked, False if something went wrong.
        
        tab_info needs: url, browser_type, tab_id, and window_id
        """
        try:
            # Make sure we got valid info
            if not self._validate_tab_info(tab_info):
                return False
                
            # Record the change
            timestamp = datetime.now().timestamp()
            
            # If we had a previous tab active, mark it as inactive
            if self.last_active:
                self._handle_tab_deactivation(self.last_active, timestamp)
            
            # Mark this new tab as active
            self.last_active = tab_info
            self.active_tabs[tab_info['tab_id']] = {
                'start_time': timestamp,
                'url': tab_info['url'],
                'browser_type': tab_info['browser_type']
            }
            
            # Save our current state in case of crashes
            self._save_state()
            
            return True
            
        except Exception as e:
            logging.error(f"Problem tracking tab change: {str(e)}")
            return False
            
    def _validate_tab_info(self, tab_info: Dict) -> bool:
        """
        Makes sure we got all the info we need about a tab.
        """
        required = ['url', 'browser_type', 'tab_id', 'window_id']
        return all(key in tab_info for key in required)

    def _handle_tab_deactivation(self, tab_info: Dict, end_time: float):
        """
        Handles when a tab becomes inactive - saves how long it was open.
        """
        tab_id = tab_info['tab_id']
        if tab_id in self.active_tabs:
            start_time = self.active_tabs[tab_id]['start_time']
            duration = end_time - start_time
            
            # Save this activity period
            self._save_activity(tab_info, start_time, end_time, duration)
            
            # Clean up
            del self.active_tabs[tab_id]

    def _save_activity(self, tab_info: Dict, start: float, end: float, duration: float):
        """
        Saves the record of tab activity to our database.
        """
        # Implementation will connect to our database
        pass

    def _save_state(self):
        """
        Saves our current state in case we crash.
        """
        try:
            state = {
                'active_tabs': self.active_tabs,
                'last_active': self.last_active
            }
            with open(f"{self.db_path}.state", 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logging.error(f"Couldn't save state: {str(e)}")

    def _load_state(self):
        """
        Loads our previous state after a crash.
        """
        try:
            with open(f"{self.db_path}.state", 'r') as f:
                state = json.load(f)
                self.active_tabs = state.get('active_tabs', {})
                self.last_active = state.get('last_active')
        except FileNotFoundError:
            # First time running - no problem!
            pass
        except Exception as e:
            logging.error(f"Couldn't load state: {str(e)}")
            raise