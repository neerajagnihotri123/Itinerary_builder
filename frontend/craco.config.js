// Load configuration from environment or config file
const path = require('path');

// Environment variable overrides
const config = {
  disableHotReload: true, // Force disable hot reload for stability
};

module.exports = {
  devServer: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: "all",
    historyApiFallback: true,
    hot: false, // Disable hot reloading
    liveReload: false, // Disable live reloading
    headers: {
      "Access-Control-Allow-Origin": "*",
    }
  },
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {
      
      // Always disable hot reload for stability
      // Remove hot reload related plugins
      webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
        return !(plugin.constructor.name === 'HotModuleReplacementPlugin');
      });
      
      // Disable watch mode completely for stability
      webpackConfig.watch = false;
      webpackConfig.watchOptions = {
        ignored: /.*/, // Ignore all files to prevent auto-refresh
        poll: false,
        aggregateTimeout: 5000,
      };
      
      // Disable hot module replacement
      if (webpackConfig.entry && Array.isArray(webpackConfig.entry)) {
        webpackConfig.entry = webpackConfig.entry.filter(entry => 
          !entry.includes('webpack-hot-middleware') && 
          !entry.includes('webpack/hot/dev-server')
        );
      }
      
      return webpackConfig;
    },
  },
};