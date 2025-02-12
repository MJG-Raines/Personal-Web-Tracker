const saveActivity = async (activity) => {
    try {
        const data = await chrome.storage.local.get('activities');
        const activities = data.activities || [];
        
        // Add new activity
        activities.push(activity);
        
        // Limit to 1000 most recent activities
        const limitedActivities = activities.slice(-1000);
        
        await chrome.storage.local.set({ activities: limitedActivities });
        return true;
    } catch (error) {
        console.error('Failed to save activity:', error);
        return false;
    }
};

const getStoredActivities = async () => {
    try {
        const data = await chrome.storage.local.get('activities');
        return data.activities || [];
    } catch (error) {
        console.error('Failed to get activities:', error);
        return [];
    }
};

module.exports = {
    saveActivity,
    getStoredActivities
};