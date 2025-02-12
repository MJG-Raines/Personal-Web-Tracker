const { saveActivity, getStoredActivities } = require('../../../extension/chromium/scripts/storage/local.js');

describe('Local Storage Handler', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Clear chrome storage mock
        chrome.storage.local.get.mockReset();
        chrome.storage.local.set.mockReset();
    });

    describe('saveActivity', () => {
        const sampleActivity = {
            type: 'activation',
            tabId: 1,
            windowId: 1,
            url: 'https://example.com',
            timestamp: Date.now()
        };

        test('saves new activity to empty storage', async () => {
            chrome.storage.local.get.mockResolvedValue({ activities: [] });
            chrome.storage.local.set.mockResolvedValue();

            const result = await saveActivity(sampleActivity);
            
            expect(result).toBe(true);
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                activities: [sampleActivity]
            });
        });

        test('appends activity to existing activities', async () => {
            const existingActivity = {
                type: 'activation',
                tabId: 2,
                windowId: 1,
                url: 'https://example.org',
                timestamp: Date.now() - 1000
            };

            chrome.storage.local.get.mockResolvedValue({ 
                activities: [existingActivity] 
            });
            chrome.storage.local.set.mockResolvedValue();

            const result = await saveActivity(sampleActivity);
            
            expect(result).toBe(true);
            expect(chrome.storage.local.set).toHaveBeenCalledWith({
                activities: [existingActivity, sampleActivity]
            });
        });

        test('handles storage errors gracefully', async () => {
            chrome.storage.local.get.mockRejectedValue(new Error('Storage error'));
            
            const result = await saveActivity(sampleActivity);
            
            expect(result).toBe(false);
            expect(chrome.storage.local.set).not.toHaveBeenCalled();
        });

        test('limits stored activities to prevent overflow', async () => {
            // Create array of 1000 activities
            const manyActivities = Array(1000).fill().map((_, i) => ({
                type: 'activation',
                tabId: i,
                windowId: 1,
                url: `https://example${i}.com`,
                timestamp: Date.now() - i
            }));

            chrome.storage.local.get.mockResolvedValue({ 
                activities: manyActivities 
            });
            chrome.storage.local.set.mockResolvedValue();

            const result = await saveActivity(sampleActivity);
            
            expect(result).toBe(true);
            const savedActivities = chrome.storage.local.set.mock.calls[0][0].activities;
            expect(savedActivities.length).toBeLessThanOrEqual(1000);
            expect(savedActivities[savedActivities.length - 1]).toEqual(sampleActivity);
        });
    });

    describe('getStoredActivities', () => {
        test('retrieves stored activities', async () => {
            const storedActivities = [
                {
                    type: 'activation',
                    tabId: 1,
                    windowId: 1,
                    url: 'https://example.com',
                    timestamp: Date.now()
                }
            ];

            chrome.storage.local.get.mockResolvedValue({ activities: storedActivities });

            const result = await getStoredActivities();
            
            expect(result).toEqual(storedActivities);
        });

        test('returns empty array when no activities stored', async () => {
            chrome.storage.local.get.mockResolvedValue({});

            const result = await getStoredActivities();
            
            expect(result).toEqual([]);
        });

        test('handles storage errors gracefully', async () => {
            chrome.storage.local.get.mockRejectedValue(new Error('Storage error'));

            const result = await getStoredActivities();
            
            expect(result).toEqual([]);
        });
    });
});