import { saveActivity } from '../storage/local.js';

/**
 * Validates window event data
 * @param {Object} windowInfo - Window information to validate
 * @returns {boolean} - Whether the window info is valid
 */
function isValidWindowInfo(windowInfo) {
    if (!windowInfo) return false;
    
    const requiredFields = ['tabId', 'windowId', 'url', 'timestamp'];
    return requiredFields.every(field => windowInfo[field] !== undefined);
}

/**
 * Handles window focus change events
 * @param {Object} windowInfo - Information about the window and active tab
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleWindowFocus(windowInfo) {
    try {
        if (!isValidWindowInfo(windowInfo)) {
            console.error('Invalid window info provided:', windowInfo);
            return false;
        }

        const activityData = {
            type: 'window_focus',
            tabId: windowInfo.tabId,
            windowId: windowInfo.windowId,
            url: windowInfo.url,
            title: windowInfo.title || '',
            timestamp: windowInfo.timestamp,
            hasFocus: windowInfo.hasFocus
        };

        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleWindowFocus:', error);
        return false;
    }
}

/**
 * Handles window state changes (minimize, maximize, etc.)
 * @param {Object} windowInfo - Information about the window
 * @param {string} state - New window state
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleWindowState(windowInfo, state) {
    try {
        if (!isValidWindowInfo(windowInfo)) {
            console.error('Invalid window info provided:', windowInfo);
            return false;
        }

        const activityData = {
            type: 'window_state',
            tabId: windowInfo.tabId,
            windowId: windowInfo.windowId,
            url: windowInfo.url,
            title: windowInfo.title || '',
            timestamp: windowInfo.timestamp,
            windowState: state
        };

        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleWindowState:', error);
        return false;
    }
}

/**
 * Handles window creation
 * @param {Object} windowInfo - Information about the new window
 * @returns {Promise<boolean>} - Whether handling succeeded
 */
async function handleWindowCreated(windowInfo) {
    try {
        if (!isValidWindowInfo(windowInfo)) {
            console.error('Invalid window info provided:', windowInfo);
            return false;
        }

        const activityData = {
            type: 'window_created',
            tabId: windowInfo.tabId,
            windowId: windowInfo.windowId,
            url: windowInfo.url,
            title: windowInfo.title || '',
            timestamp: windowInfo.timestamp
        };

        await saveActivity(activityData);
        return true;
    } catch (error) {
        console.error('Error in handleWindowCreated:', error);
        return false;
    }
}

export {
    handleWindowFocus,
    handleWindowState,
    handleWindowCreated
};