const { syncToServer, handleSyncError } = require('../../../extension/chromium/scripts/storage/sync.js');

describe('Sync Storage Handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Setup default mock return values
        chrome.storage.local.get.mockResolvedValue({ syncErrors: 0 });
        chrome.storage.local.set.mockResolvedValue();
    });

    describe('syncToServer', () => {
        const sampleActivities = [
            {
                type: 'activation',
                tabId: 1,
                windowId: 1,
                url: 'https://example.com',
                timestamp: Date.now()
            }
        ];

        test('syncs activities successfully', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });

            const result = await syncToServer(sampleActivities);
            
            expect(result).toBe(true);
            expect(fetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(sampleActivities)
                })
            );
        });

        test('handles network errors gracefully', async () => {
            global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
            chrome.storage.local.get.mockResolvedValue({ syncErrors: 0 });

            const result = await syncToServer(sampleActivities);
            
            expect(result).toBe(false);
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                syncErrors: 1
            });
        });

        test('backs off after multiple failures', async () => {
            global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
            chrome.storage.local.get.mockResolvedValue({ syncErrors: 5 });

            const result = await syncToServer(sampleActivities);
            
            expect(result).toBe(false);
            // Should not attempt sync after too many failures
            expect(fetch).not.toHaveBeenCalled();
        });

        test('resets error count after successful sync', async () => {
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });
            chrome.storage.local.get.mockResolvedValue({ syncErrors: 2 });

            const result = await syncToServer(sampleActivities);
            
            expect(result).toBe(true);
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                syncErrors: 0
            });
        });
    });

    describe('handleSyncError', () => {
        test('increments error count', async () => {
            chrome.storage.local.get.mockResolvedValue({ syncErrors: 1 });

            await handleSyncError(new Error('Test error'));
            
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                syncErrors: 2
            });
        });

        test('initializes error count if none exists', async () => {
            chrome.storage.local.get.mockResolvedValue({});

            await handleSyncError(new Error('Test error'));
            
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                syncErrors: 1
            });
        });
    });
});