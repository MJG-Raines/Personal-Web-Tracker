import { saveActivity } from '../storage/local.js';

/**
 * Validates tab data before processing
 * @param {Object} tabInfo - Tab information to validate
 * @returns {boolean} - Whether the tab info is valid
 */
function isValidTabInfo(tabInfo) {
    if (!tabInfo) return false;
    
    const requiredFields = ['tabId', 'windowId', 'url', 'timestamp'];
    return requiredFields.every(field => tabInfo[field] !== undefined);
}

/**
 * Checks if URL should be tracked
 * @param {string} url - URL to check
 * @returns {boolean} - Whether the URL should be tracked
 */
function isTrackableUrl(url) {
    if (!url) return false;
    
    // Don't track browser UI pages
    if (url.startsWith('chrome://') || 
        url.startsWith('chrome-extension://') ||
        url.startsWith('about:') ||
        url.startsWith('edge://') ||
        url.startsWith('brave://')) {
        return false;
    }
    
    return true;
}

/**
 * Handles tab activation events
 * @param {Object} tabInfo - Information about the activated tab
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleTabActivated(tabInfo) {
    try {
        if (!isValidTabInfo(tabInfo)) {
            console.error('Invalid tab info provided:', tabInfo);
            return false;
        }
        if (!isTrackableUrl(tabInfo.url)) {
            return false;
        }
        const activityData = {
            type: 'activation',
            tabId: tabInfo.tabId,
            windowId: tabInfo.windowId,
            url: tabInfo.url,
            title: tabInfo.title || '',
            timestamp: tabInfo.timestamp,
            duration: 0  // Will be calculated on deactivation
        };
        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleTabActivated:', error);
        return false;
    }
}

/**
 * Handles tab URL update events
 * @param {Object} tabInfo - Information about the updated tab
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleTabUpdated(tabInfo) {
    try {
        if (!isValidTabInfo(tabInfo)) {
            console.error('Invalid tab info provided:', tabInfo);
            return false;
        }
        if (!isTrackableUrl(tabInfo.url)) {
            return false;
        }
        const activityData = {
            type: 'update',
            tabId: tabInfo.tabId,
            windowId: tabInfo.windowId,
            url: tabInfo.url,
            title: tabInfo.title || '',
            timestamp: tabInfo.timestamp,
            previousUrl: tabInfo.previousUrl
        };
        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleTabUpdated:', error);
        return false;
    }
}

/**
 * Handles tab visibility changes
 * @param {Object} tabInfo - Information about the tab
 * @param {boolean} isVisible - Whether the tab is visible
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleTabVisibility(tabInfo, isVisible) {
    try {
        if (!isValidTabInfo(tabInfo)) {
            console.error('Invalid tab info provided:', tabInfo);
            return false;
        }
        if (!isTrackableUrl(tabInfo.url)) {
            return false;
        }
        const activityData = {
            type: 'visibility',
            tabId: tabInfo.tabId,
            windowId: tabInfo.windowId,
            url: tabInfo.url,
            title: tabInfo.title || '',
            timestamp: tabInfo.timestamp,
            isVisible: isVisible
        };
        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleTabVisibility:', error);
        return false;
    }
}

export {
    handleTabActivated,
    handleTabUpdated,
    handleTabVisibility
};