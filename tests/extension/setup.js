// Mock Chrome Extension API
global.chrome = {
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
    storage: {
        local: {
            get: jest.fn(),
            set: jest.fn()
        }
    },
    runtime: {
        onInstalled: {
            addListener: jest.fn()
        },
        onSuspend: {
            addListener: jest.fn()
        }
    },
    alarms: {
        create: jest.fn(),
        onAlarm: {
            addListener: jest.fn()
        }
    }
};