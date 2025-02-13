const { default: ActivityTracker } = require('../../../extension/chromium/scripts/background/tracker.js');

// Mock the ES modules that tracker uses
jest.mock('../../../extension/chromium/scripts/handlers/tabs.js', () => ({
    handleTabActivated: jest.fn(),
    handleTabUpdated: jest.fn()
}));

jest.mock('../../../extension/chromium/scripts/handlers/windows.js', () => ({
    handleWindowFocus: jest.fn()
}));

jest.mock('../../../extension/chromium/scripts/storage/local.js', () => ({
    saveActivity: jest.fn(),
    getStoredActivities: jest.fn().mockResolvedValue([])
}));

jest.mock('../../../extension/chromium/scripts/storage/sync.js', () => ({
    syncToServer: jest.fn().mockResolvedValue(true)
}));

describe('Background Activity Tracker', () => {
    let tracker;
    let getStoredActivities;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.spyOn(console, 'error').mockImplementation(() => {});
        
        getStoredActivities = require('../../../extension/chromium/scripts/storage/local.js').getStoredActivities;
        
        // Setup chrome API mocks
        global.chrome = {
            storage: {
                local: {
                    get: jest.fn().mockResolvedValue({ isTracking: true }),
                    set: jest.fn().mockResolvedValue()
                }
            },
            tabs: {
                onActivated: {
                    addListener: jest.fn()
                },
                onUpdated: {
                    addListener: jest.fn()
                },
                get: jest.fn(),
                query: jest.fn()
            },
            windows: {
                onFocusChanged: {
                    addListener: jest.fn()
                },
                WINDOW_ID_NONE: -1
            },
            alarms: {
                create: jest.fn(),
                onAlarm: {
                    addListener: jest.fn()
                }
            },
            runtime: {
                onInstalled: {
                    addListener: jest.fn()
                },
                onSuspend: {
                    addListener: jest.fn()
                }
            }
        };

        tracker = new ActivityTracker();
    });

    describe('Initialization', () => {
        test('sets up all required listeners', () => {
            expect(chrome.tabs.onActivated.addListener).toHaveBeenCalled();
            expect(chrome.tabs.onUpdated.addListener).toHaveBeenCalled();
            expect(chrome.windows.onFocusChanged.addListener).toHaveBeenCalled();
            expect(chrome.alarms.create).toHaveBeenCalledWith('syncData', { periodInMinutes: 5 });
        });

        test('recovers from crash correctly', async () => {
            const crashedTracker = new ActivityTracker();
            await crashedTracker.recoverFromCrash();
            expect(chrome.storage.local.get).toHaveBeenCalledWith('isTracking');
        });
    });

    describe('Tab Event Handling', () => {
        test('handles tab activation', async () => {
            const mockTab = {
                id: 1,
                windowId: 1,
                url: 'https://example.com',
                title: 'Test'
            };
            chrome.tabs.get.mockResolvedValue(mockTab);

            const listener = chrome.tabs.onActivated.addListener.mock.calls[0][0];
            await listener({ tabId: 1, windowId: 1 });

            expect(chrome.tabs.get).toHaveBeenCalledWith(1);
        });

        test('ignores tab events when tracking is disabled', async () => {
            tracker.isTracking = false;
            const listener = chrome.tabs.onActivated.addListener.mock.calls[0][0];
            await listener({ tabId: 1, windowId: 1 });

            expect(chrome.tabs.get).not.toHaveBeenCalled();
        });
    });

    describe('Window Event Handling', () => {
        test('handles window focus change', async () => {
            const mockTab = {
                id: 1,
                windowId: 1,
                url: 'https://example.com'
            };
            chrome.tabs.query.mockResolvedValue([mockTab]);

            const listener = chrome.windows.onFocusChanged.addListener.mock.calls[0][0];
            await listener(1);

            expect(chrome.tabs.query).toHaveBeenCalledWith({
                active: true,
                windowId: 1
            });
        });

        test('ignores WINDOW_ID_NONE', async () => {
            const listener = chrome.windows.onFocusChanged.addListener.mock.calls[0][0];
            await listener(chrome.windows.WINDOW_ID_NONE);

            expect(chrome.tabs.query).not.toHaveBeenCalled();
        });
    });

    describe('Data Syncing', () => {
        test('syncs data on alarm', async () => {
            getStoredActivities.mockResolvedValueOnce([{ url: 'https://example.com' }]);
            
            const listener = chrome.alarms.onAlarm.addListener.mock.calls[0][0];
            await listener({ name: 'syncData' });

            expect(getStoredActivities).toHaveBeenCalled();
        });

        test('handles empty activity list', async () => {
            getStoredActivities.mockResolvedValue([]);

            const listener = chrome.alarms.onAlarm.addListener.mock.calls[0][0];
            await listener({ name: 'syncData' });

            expect(chrome.storage.local.set).not.toHaveBeenCalled();
        });
    });

    describe('Error Handling', () => {
        test('handles tab activation errors', async () => {
            chrome.tabs.get.mockRejectedValue(new Error('Tab error'));
            
            const listener = chrome.tabs.onActivated.addListener.mock.calls[0][0];
            await listener({ tabId: 1, windowId: 1 });

            expect(console.error).toHaveBeenCalled();
        });

        test('handles window focus errors', async () => {
            chrome.tabs.query.mockRejectedValue(new Error('Window error'));

            const listener = chrome.windows.onFocusChanged.addListener.mock.calls[0][0];
            await listener(1);

            expect(console.error).toHaveBeenCalled();
        });
    });
});