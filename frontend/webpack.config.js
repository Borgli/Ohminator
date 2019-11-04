const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const HtmlWebpackPlugin = require("html-webpack-plugin");
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
    mode: 'development',
    entry: __dirname + '/src/index.js',
    output: {
        path: __dirname + '/dist/js',
        filename: 'main.js',
        publicPath: '/'
    },
    externals: {
      'config': JSON.stringify(require('./config.dev.json'))
    },
    devServer: {
        historyApiFallback: true
    },
    plugins: [
        new BundleTracker({
            path: __dirname,
            filename: 'webpack-stats.json'
        }),
        new MiniCssExtractPlugin({
            filename: 'css/styles.css'
        }),
        new HtmlWebpackPlugin({
            template: "src/index.html" //source html
        })
    ],
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                loaders: ['babel-loader']
            },
            {
                test: /\.scss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    {
                        loader: 'css-loader'
                    },
                    {
                        loader: 'sass-loader',
                        options: {
                            sourceMap: true,
                        }
                    }
                ]
            },
        ]
    }
};
