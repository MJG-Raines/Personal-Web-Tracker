// Import handlers and storage using CommonJS
const { handleTabActivated, handleTabUpdated } = require('../handlers/tabs');
const { handleWindowFocus } = require('../handlers/windows');
const { saveActivity, getStoredActivities } = require('../storage/local');
const { syncToServer } = require('../storage/sync');

class ActivityTracker {
    constructor() {
        this.currentTab = null;
        this.isTracking = true;
        this.lastSync = Date.now();
        this.setupListeners();
    }

    setupListeners() {
        // Tab activation
        chrome.tabs.onActivated.addListener(async (activeInfo) => {
            if (!this.isTracking) return;
            
            try {
                const tab = await chrome.tabs.get(activeInfo.tabId);
                await handleTabActivated({
                    tabId: tab.id,
                    windowId: tab.windowId,
                    url: tab.url,
                    title: tab.title,
                    timestamp: Date.now()
                });
            } catch (error) {
                console.error('Error handling tab activation:', error);
            }
        });

        // Tab updates (URL changes)
        chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
            if (!this.isTracking || !changeInfo.url) return;
            
            try {
                await handleTabUpdated({
                    tabId: tab.id,
                    windowId: tab.windowId,
                    url: changeInfo.url,
                    title: tab.title,
                    timestamp: Date.now()
                });
            } catch (error) {
                console.error('Error handling tab update:', error);
            }
        });

        // Window focus changes
        chrome.windows.onFocusChanged.addListener(async (windowId) => {
            if (!this.isTracking || windowId === chrome.windows.WINDOW_ID_NONE) return;
            
            try {
                const tabs = await chrome.tabs.query({ active: true, windowId });
                if (tabs.length > 0) {
                    const tab = tabs[0];
                    await handleWindowFocus({
                        tabId: tab.id,
                        windowId: windowId,
                        url: tab.url,
                        title: tab.title,
                        timestamp: Date.now(),
                        hasFocus: true
                    });
                }
            } catch (error) {
                console.error('Error handling window focus:', error);
            }
        });

        // Set up periodic sync
        chrome.alarms.create('syncData', { periodInMinutes: 5 });
        chrome.alarms.onAlarm.addListener(async (alarm) => {
            if (alarm.name === 'syncData') {
                await this.syncData();
            }
        });
    }

    async syncData() {
        try {
            const activities = await getStoredActivities();
            if (activities.length > 0) {
                const success = await syncToServer(activities);
                if (success) {
                    this.lastSync = Date.now();
                    // Clear synced activities
                    await chrome.storage.local.set({ activities: [] });
                }
            }
        } catch (error) {
            console.error('Error syncing data:', error);
        }
    }

    async toggleTracking(enabled) {
        this.isTracking = enabled;
        await chrome.storage.local.set({ isTracking: enabled });
        
        // If tracking is disabled, sync remaining data
        if (!enabled) {
            await this.syncData();
        }
    }

    async handleError(error, context) {
        console.error(`Error in ${context}:`, error);
        
        // Store error for debugging
        const errors = await chrome.storage.local.get('errors') || { errors: [] };
        errors.push({
            timestamp: Date.now(),
            context,
            message: error.message
        });
        await chrome.storage.local.set({ errors });
    }

    // Recovery methods
    async recoverFromCrash() {
        try {
            // Get last known state
            const { isTracking } = await chrome.storage.local.get('isTracking');
            this.isTracking = isTracking ?? true;

            // Force sync after crash
            await this.syncData();
        } catch (error) {
            console.error('Error recovering from crash:', error);
        }
    }
}

// Initialize tracker
const tracker = new ActivityTracker();

// Handle installation/update
chrome.runtime.onInstalled.addListener(async (details) => {
    if (details.reason === 'install') {
        // Set initial settings
        await chrome.storage.local.set({
            isTracking: true,
            activities: [],
            errors: []
        });
    } else if (details.reason === 'update') {
        // Handle any necessary data migrations
        await tracker.recoverFromCrash();
    }
});

// Handle unload/shutdown
chrome.runtime.onSuspend.addListener(async () => {
    await tracker.syncData();
});

// Export for testing
module.exports = ActivityTracker;