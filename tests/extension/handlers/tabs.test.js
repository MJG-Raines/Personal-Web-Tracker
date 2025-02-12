const { handleTabActivated, handleTabUpdated, handleTabVisibility } = require('../../../extension/chromium/scripts/handlers/tabs.js');
const { saveActivity } = require('../../../extension/chromium/scripts/storage/local.js');

jest.mock('../../../extension/chromium/scripts/storage/local.js');

describe('Tab Handlers', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        saveActivity.mockResolvedValue(true);
    });

    describe('handleTabActivated', () => {
        const validTabInfo = {
            tabId: 1,
            windowId: 1,
            url: 'https://example.com',
            title: 'Example Site',
            timestamp: Date.now()
        };

        test('handles valid tab activation', async () => {
            const result = await handleTabActivated(validTabInfo);
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'activation',
                tabId: validTabInfo.tabId,
                url: validTabInfo.url
            }));
        });

        test('rejects invalid tab info', async () => {
            const invalidTabInfo = {
                url: 'https://example.com'
            };
            const result = await handleTabActivated(invalidTabInfo);
            expect(result).toBe(false);
            expect(saveActivity).not.toHaveBeenCalled();
        });
    });

    describe('handleTabUpdated', () => {
        const validUpdateInfo = {
            tabId: 1,
            windowId: 1,
            url: 'https://example.com/updated',
            title: 'Updated Site',
            timestamp: Date.now(),
            previousUrl: 'https://example.com'
        };

        test('handles valid URL update', async () => {
            const result = await handleTabUpdated(validUpdateInfo);
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'update',
                url: validUpdateInfo.url,
                previousUrl: validUpdateInfo.previousUrl
            }));
        });

        test('rejects invalid update info', async () => {
            const invalidUpdateInfo = {
                url: 'https://example.com'
            };
            const result = await handleTabUpdated(invalidUpdateInfo);
            expect(result).toBe(false);
            expect(saveActivity).not.toHaveBeenCalled();
        });
    });

    describe('handleTabVisibility', () => {
        const validTabInfo = {
            tabId: 1,
            windowId: 1,
            url: 'https://example.com',
            title: 'Example Site',
            timestamp: Date.now()
        };

        test('handles tab becoming visible', async () => {
            const result = await handleTabVisibility(validTabInfo, true);
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'visibility',
                isVisible: true
            }));
        });

        test('handles tab becoming hidden', async () => {
            const result = await handleTabVisibility(validTabInfo, false);
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'visibility',
                isVisible: false
            }));
        });
    });
});