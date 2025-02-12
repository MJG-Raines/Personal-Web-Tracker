const { handleWindowFocus, handleWindowState, handleWindowCreated } = require('../../../extension/chromium/scripts/handlers/windows.js');
const { saveActivity } = require('../../../extension/chromium/scripts/storage/local.js');

jest.mock('../../../extension/chromium/scripts/storage/local.js');

describe('Window Handlers', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        saveActivity.mockResolvedValue(true);
    });

    const validWindowInfo = {
        tabId: 1,
        windowId: 1,
        url: 'https://example.com',
        title: 'Example Site',
        timestamp: Date.now()
    };

    describe('handleWindowFocus', () => {
        test('handles window gaining focus', async () => {
            const result = await handleWindowFocus({
                ...validWindowInfo,
                hasFocus: true
            });
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'window_focus',
                hasFocus: true
            }));
        });

        test('handles window losing focus', async () => {
            const result = await handleWindowFocus({
                ...validWindowInfo,
                hasFocus: false
            });
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'window_focus',
                hasFocus: false
            }));
        });

        test('rejects invalid window info', async () => {
            const result = await handleWindowFocus({
                url: 'https://example.com'
            });
            expect(result).toBe(false);
            expect(saveActivity).not.toHaveBeenCalled();
        });
    });

    describe('handleWindowState', () => {
        test('handles window maximized state', async () => {
            const result = await handleWindowState(validWindowInfo, 'maximized');
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'window_state',
                windowState: 'maximized'
            }));
        });

        test('handles window minimized state', async () => {
            const result = await handleWindowState(validWindowInfo, 'minimized');
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'window_state',
                windowState: 'minimized'
            }));
        });

        test('rejects invalid window info', async () => {
            const result = await handleWindowState({
                url: 'https://example.com'
            }, 'maximized');
            expect(result).toBe(false);
            expect(saveActivity).not.toHaveBeenCalled();
        });
    });

    describe('handleWindowCreated', () => {
        test('handles new window creation', async () => {
            const result = await handleWindowCreated(validWindowInfo);
            expect(result).toBe(true);
            expect(saveActivity).toHaveBeenCalledWith(expect.objectContaining({
                type: 'window_created'
            }));
        });

        test('rejects invalid window info', async () => {
            const result = await handleWindowCreated({
                url: 'https://example.com'
            });
            expect(result).toBe(false);
            expect(saveActivity).not.toHaveBeenCalled();
        });
    });
}); 