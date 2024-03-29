const webpack = require('webpack')
const path = require('path')
const VueLoaderPlugin = require('vue-loader/lib/plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
function resolve (dir) {
  return path.join(__dirname, '.', dir)
}

module.exports = (env, argv) => {
  config = {
    entry: {
      'visual-essays' : './main.js'
    },
    output: {
      path: path.resolve(__dirname, '../../js'),
      publicPath: '/lib/',
      // filename: argv.mode === 'production' ? `[name]-${BUNDLE_VERSION}.min.js` : `[name].js`
      filename: argv.mode === 'development' ? `[name].js` : `[name]${argv.hash ? '.'+argv.hash : ''}.min.js` 
    },
    resolve: {
      extensions: ['.js', '.vue', '.json'],
      alias: {
        'vue$': 'vue/dist/vue.esm.js',
        '@': resolve('src'),
      }
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          loader: 'vue-loader'
        },
        // this will apply to both plain `.js` files
        // AND `<script>` blocks in `.vue` files
        {
          test: /\.js$/,
          use: {
            loader: "babel-loader",
            options: {
              plugins: [
                '@babel/plugin-syntax-dynamic-import'
              ]
            }
          }
        },
        // this will apply to both plain `.css` files
        // AND `<style>` blocks in `.vue` files
        {
          test: /\.css$/,
          use: [
            'vue-style-loader',
            'css-loader'
          ]
        },
        {
          test: /\.scss$/,
          use: [
            'vue-style-loader',
            'css-loader',
            'sass-loader'
          ]
        },
        {
          test: /\.sass$/,
          use: [
            'vue-style-loader',
            'css-loader',
            'sass-loader'
          ]
        },
        {
          test: /\.styl(us)?$/,
          use: [
            'vue-style-loader',
            'css-loader',
            'stylus-loader'
          ]
        },
        {
          test: /\.(jpe?g|png|gif|woff|woff2|eot|ttf|svg)(\?[a-z0-9=.]+)?$/,
          loader: 'url-loader?limit=100000' 
        }
      ]
    },
    optimization: {
      usedExports: true
    },
    plugins: [
      new webpack.DefinePlugin({
        VERSION: JSON.stringify(require('./package.json').version),
        BRANCH: JSON.stringify(process.env.BRANCH || 'develop')
      }),
      new VueLoaderPlugin(),
      // new BundleAnalyzerPlugin()
    ]
  }
  return config
}
