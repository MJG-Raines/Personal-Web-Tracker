const MAX_SYNC_ERRORS = 5;

async function syncToServer(activities) {
    try {
        const { syncErrors = 0 } = await chrome.storage.local.get('syncErrors');
        
        if (syncErrors >= MAX_SYNC_ERRORS) {
            console.error('Too many sync errors, backing off');
            return false;
        }

        const response = await fetch('YOUR_API_ENDPOINT', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(activities)
        });

        if (response.ok) {
            // Reset error count on success
            await chrome.storage.local.set({ syncErrors: 0 });
            return true;
        }

        await handleSyncError(new Error('Sync failed'));
        return false;
    } catch (error) {
        await handleSyncError(error);
        return false;
    }
}

async function handleSyncError(error) {
    try {
        const { syncErrors = 0 } = await chrome.storage.local.get('syncErrors');
        await chrome.storage.local.set({ syncErrors: syncErrors + 1 });
    } catch (storageError) {
        console.error('Failed to handle sync error:', storageError);
    }
}

module.exports = {
    syncToServer,
    handleSyncError
};