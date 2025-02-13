export default {
    testEnvironment: 'jsdom',
    transform: {
        '^.+\\.js$': ['babel-jest', { 
            presets: [['@babel/preset-env', { targets: { node: 'current' } }]],
            plugins: ['@babel/plugin-transform-modules-commonjs']
        }]
    },
    moduleDirectories: [
        'node_modules',
        'extension/chromium/scripts'
    ],
    setupFiles: [
        './tests/extension/setup.js'
    ],
    moduleNameMapper: {
        '^(\\.{1,2}/.*)\\.js$': '$1'
    }
}