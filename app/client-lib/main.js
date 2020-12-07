import Vue from 'vue'
import App from './App.vue'
import store from './store.js'
import VueScrollmagic from 'vue-scrollmagic'
import httpVueLoader from 'http-vue-loader'
import VModal from 'vue-js-modal'
import * as utils from './utils.js'
import VueAnalytics from 'vue-analytics'
import MobileDetect from 'mobile-detect'
import 'lodash'
import VueYoutube from 'vue-youtube'
// import 'leaflet-polylinedecorator'

const codeBranch = BRANCH
const version = VERSION

let gaTrackingID = 'UA-125778965-6'

console.log(`visual-essays: version=${version} branch=${codeBranch}`)

const hash = window.location.hash || location.hash

console.log(window.location)
let baseurl = ''

const referrerUrl = document.referrer
if (referrerUrl) {
  console.log(`referrer=${referrerUrl}`)
  const referrer = utils.parseUrl(referrerUrl)
  console.log(referrer)
  if (referrer.host === 'github.com') {
    const referrerPath = referrer.pathname.slice(1).split('/')
    const ghAcct = referrerPath[0]
    const ghRepo = referrerPath[1]
    const ghBranch = referrerPath.length > 2 ? referrerPath[3] : 'main'
    const ghRoot = referrerPath.length > 3 ? referrerPath[4] === 'docs' ? referrerPath[4] : null : null
    const pathStart = ghRoot ? 5 : 4
    const pathEnd = referrerPath[referrerPath.length-1] === 'README.md' || referrerPath[referrerPath.length-1] === 'index.md' ? referrerPath.length-1 : referrerPath.length
    const ghPath = referrerPath.slice(pathStart, pathEnd).join('/').replace(/\.md$/, '')
    const redirect = (ghAcct === 'JSTOR-Labs' && ghRepo === 've-docs') 
      ? `https://docs.visual-essays.app/${ghPath}`
      : `${window.location.origin}${ghBranch === 'master' || ghBranch === 'main' ? '' : '/' + ghBranch}/${ghAcct}/${ghRepo}/${ghPath}`
    console.log(`redirect=${redirect}`)
    window.location = redirect
  }
}

const md = new MobileDetect(window.navigator.userAgent)
const isMobile = md.phone() !== null
const isTouchDevice = md.phone() !== null || md.tablet() !== null

const qargs = window.location.href.indexOf('?') > 0
  ? utils.parseQueryString(window.location.href.split('?')[1])
  : {}
let jwt = null
if (qargs.token) {
  jwt = qargs.token
  window.localStorage.setItem('ghcreds', jwt)
} else {
  jwt = window.localStorage.getItem('ghcreds')
}

const veSites = ['localhost', 'visual-essays.app', 'dev.visual-essays.app', 'exp.visual-essays.app']
let otherKnownSites = {
  'docs.visual-essays.app': {acct: 'jstor-labs', repo: 've-docs'},
  'plant-humanities.app': {acct: 'jstor-labs', repo: 'plant-humanities'},
  'dev.plant-humanities.app': {acct: 'jstor-labs', repo: 'plant-humanities'},
  'kent-maps.online': {acct: 'kent-map', repo: 'kent'},
  'dev.kent-maps.online': {acct: 'kent-map', repo: 'kent'}
}
function isGitpod(hostname) {
  window.location.hostname.length - window.location.hostname.indexOf('.gitpod.io') === 10
}

const reservedBranchNames = ['master', 'main', 'develop', 'staging']

function isKnownSite(hostname) {
  console.log('isKnownSite', veSites.indexOf(hostname), Object.keys(otherKnownSites).find(domain => hostname.indexOf(domain) >= 0))
  return veSites.indexOf(hostname) >= 0 ||
         Object.keys(otherKnownSites).find(domain => hostname.indexOf(domain) >= 0) !== undefined
}

function pageContext() {
  const _loc = window.location
  console.log(_loc)
  let _path = _loc.pathname.replace(/^\/essay/,'').slice(1).split('/')
  let _context = {
    acct: 'jstor-labs',
    branch: qargs.ref,
    isKnownSite: isKnownSite(_loc.hostname) || _loc.hostname.indexOf('github.io') > 0,
    codeBranch,
    browserRoot: '',
    mdRoot: '',
    path: null,
    repo: 've-content',
    site: _loc.hostname,
    siteTitle: '',
    service: isKnownSite(_loc.hostname) && _loc.hostname !== 'docs.visual-essays.app' ? _loc.origin : 'https://exp.visual-essays.app',
    isMobile,
    isTouchDevice,
    jwt,
    hash,
    referrer: document.referrer,
    qargs,
    content: {}
  }
  const isGithubCommitHash = RegExp(`[0-9a-f]{${_path[0].length}}`)
  const isGithubVersionTag = RegExp(`v?[0-9.]+$`)
  if (_path.length > 0) {
    if (_loc.hostname.indexOf('github.io') > 0) {
      _context.acct = _loc.hostname.split('.')[0]
      _context.repo = _loc.pathname.split('/')[1]
      _context.browserRoot = `/${_context.repo}`
      _path = _path.slice(1)
    } else if (reservedBranchNames.indexOf(_path[0]) >= 0) {
      _context.branch = _path[0]
      _context.browserRoot = `/${_path[0]}`
      _path = _path.slice(1)
    } else if ((_path[0].length === 8 || _path[0].length === 40) && isGithubCommitHash.test(_path[0])) {
      _context.branch = _path[0]
      _context.browserRoot = `/${_path[0]}`
      _path = _path.slice(1)
    } else if (isGithubVersionTag.test(_path[0])) {
      _context.branch = _path[0]
      _context.browserRoot = `/${_path[0]}`
      _path = _path.slice(1)
    } else if (_path[0][0] === '_') {
      _context.branch = _path[0].slice(1)
      _context.browserRoot = `/${_path[0]}`
      _path = _path.slice(1)
    }
  }
  if (veSites.indexOf(_context.site) >= 0) {
    if (_path.length >= 2) {
      _context.acct = _path[0]
      _context.repo = _path[1]
      _path = _path.slice(2)
      _context.browserRoot += `/${_context.acct}/${_context.repo}`
    }
  } else {
    // const _domain = _context.site.replace(/\.local$/,'').match(/[a-zA-Z-_\d]+\.[a-zA-Z-_\d]+$/)
    // if (otherKnownSites[_domain]) _context = { ..._context, ...otherKnownSites[_domain] }
    if (otherKnownSites[_context.site]) _context = { ..._context, ...otherKnownSites[_context.site] }
  }
  _context.path = `/${_path.join('/')}`
  return _context
}

const getRepoInfo = async () => {
  let resp = await fetch(`https://api.github.com/repos/${context.acct}/${context.repo}`)
  let repoInfo = await resp.json()
  return repoInfo
}

const checkJWTExpiration = async(jwt) => {
  let response = await fetch(`${context.service}/jwt-expiration/${jwt}`)
  const expiration = parseInt(await response.text())
  const isExpired =  Date.now()/1000 >= expiration
  if (isExpired) window.localStorage.removeItem('ghcreds')
  return isExpired
}

const getSiteConfig = async () => {
  let siteConfig = { components: [] }
  try {
    const configUrl = `${context.service}/config${window.location.pathname}${context.branch && context.branch !== 'main' ? '?ref='+context.branch : ''}`
    console.log(configUrl)
    let [ghpConfig, fromServer] = await Promise.all([
      fetch(`${baseurl}/config.json`),
      fetch(configUrl)
    ])
    console.log(`ghpConfig=${ghpConfig.ok} fromServer=${fromServer.ok}`)

    if (fromServer.ok) {
      siteConfig = { ...siteConfig, ...await fromServer.json() }
    }
    if (ghpConfig.ok) {
      // configUpdate = await ghpConfig.json()
      siteConfig = { ...siteConfig, ...await ghpConfig.json() }
      if (window.location.hostname.indexOf('github.io') > 0) context.ghPagesSite = true
    } 

    context.acct = siteConfig.acct
    context.repo = siteConfig.repo
    context.branch = context.branch === null ? siteConfig.publishedVersion || 'main' : context.branch

    console.log('siteConfig', siteConfig)

    /*
    const ghBaseurl = context.site === 'localhost' || context.site.indexOf(`.local`) == context.site.length - 6
      ? `${context.service}/static`
      : `https://raw.githubusercontent.com/${context.acct}/${context.repo}/${context.branch || 'main'}`
    */
    const ghBaseurl = `https://raw.githubusercontent.com/${context.acct}/${context.repo}/${context.branch || 'main'}`
    
    siteConfig.components.forEach(comp => {
      if (comp.src.indexOf('http') !== 0) {
        comp.src = `${ghBaseurl}${comp.src[0] === '/' ? '' : '/'}${comp.src}`
      }
    })
    const ghRoot = siteConfig.ghRoot || ''

    const configOptions = ['banner', 'favicon', 'logo']
    configOptions.forEach(option => {
      if (siteConfig[option] && siteConfig[option].indexOf('http') !== 0) {
        siteConfig[option] = siteConfig[option][0] === '/'
          ? `${ghBaseurl}${siteConfig[option]}`
          : `${ghBaseurl}${ghRoot}${siteConfig[option]}`
      }
    })
  } catch (e) {
    console.log('error in getSiteConfig', e)
  }
  return siteConfig
}
const baseComponentsIndex = async(componentsBaseURL) => {
  // let response = await fetch(`${componentsBaseURL}/components/index.json`)
  let response = await fetch(`${baseurl}/components/index.json`)
  let components = []
  const componentsList = await response.json()
  const base = window.location.origin
  console.log('base', window.location.origin)
  componentsList.forEach(comp => {
    if (comp.src.indexOf('http') !== 0) comp.src = `${base}/${comp.src}`
    components.push(comp)
  })
  return components
}

let context = pageContext()
console.log(context)

const doRemoteRequests = async () => {
  /*
  const componentsBaseURL = context.site === 'localhost' || context.site.indexOf(`.local`) == context.site.length - 6
    ? ''
    : `https://visual-essays.app`
    // : context.service
    */
  const remoteRequests = [
    baseComponentsIndex(),
    getSiteConfig(),
    getRepoInfo()
  ]

  if (jwt !== null) remoteRequests.push(checkJWTExpiration(jwt))

  let responses = await Promise.all(remoteRequests)
  let _components = responses[0]
  let _siteConfig = responses[1]
  let _repoInfo = responses[2]

  if (responses.length === 4) {
    const jwtIsExpired = responses[3]
    if (jwtIsExpired) jwt = null
  }

  context = { ...context, ..._siteConfig }
  // if (veSites.indexOf(context.site) >= 0 && context.branch == 'master') {
  //   context.branch = _repoInfo.default_branch
  // }
  context.components = {}
  if (_siteConfig.gaTrackingID) {
    gaTrackingID = [gaTrackingID, _siteConfig.gaTrackingID]
  }
  Vue.use(VueAnalytics, {
    id: gaTrackingID
  })

  const componentsList = [..._siteConfig.components, ..._components]
  componentsList.forEach(component => {
    if (!context.components[component.name]) {
      if (!component.component) {
        component.component = httpVueLoader(component.src)
      }
      Vue.component(component.name, component.component)
      context.components[component.name] = component
    }
  })
  if (_siteConfig.title) context.siteTitle = _siteConfig.title
  if (_siteConfig.favicon) {
    console.log(`favicon=${_siteConfig.favicon}`)
    let e = document.createElement('link')
    e.href = _siteConfig.favicon
    e.rel = 'icon'
    e.type='image/x-icon'
    document.getElementsByTagName('head')[0].appendChild(e)
  }
  window.context = context
}

doRemoteRequests()
.then(_ => { // eslint-disable-line no-unused-vars
  setInterval(() => waitForContent(), 250)
})


Vue.config.productionTip = false
Vue.config.devtools = true

Vue.use(httpVueLoader)
Vue.use(VueYoutube)

Vue.use(VueScrollmagic, {
  vertical: true,
  globalSceneOptions: {},
  loglevel: 2,
  refreshInterval: 100
})
Vue.use(VModal)

Vue.mixin({
  computed: {
    // allItems() { return store.getters.items },
    // components() { return store.getters.components },
    // groups() { return utils.groupItems(utils.itemsInElements(utils.elemIdPath(store.getters.activeElement), this.allItems), store.getters.componentSelectors) },
  },
  methods: {
    ...utils,
    load(url, callback) {
      let e
      if (url.split('.').pop() === 'js') {
          e = document.createElement('script')
          e.src = url
          e.type='text/javascript'
      } else {
          e = document.createElement('link')
          e.href = url
          e.rel='stylesheet'
      }
      e.addEventListener('load', callback)
      document.getElementsByTagName('head')[0].appendChild(e)
    },
    loadDependencies(dependencies, i, callback) {
      if (dependencies.length > 0) {
        this.load(dependencies[i], () => {
            if (i < dependencies.length-1) {
                this.loadDependencies(dependencies, i+1, callback) 
            } else {
                callback()
            }
        })
      }
    }
  }
})

let vm

let rtime
let timeout = false
const delta = 200

function setViewport() {
  const viewport = {
    height: Math.max(document.documentElement.clientHeight, window.innerHeight || 0),
    width: Math.max(document.documentElement.clientWidth, window.innerWidth || 0),
  }
  if (vm) {
    vm.$store.dispatch('setViewport', viewport)
  }
}

function resizeend() {
  if (new Date() - rtime < delta) {
    setTimeout(resizeend, delta)
  } else {
    timeout = false
    setViewport()
  }
}

function initApp() {
  console.log('visual-essays.init')

  window.data = []
  document.querySelectorAll('script[data-ve-tags]').forEach((scr) => {
    eval(scr.text)
  })

  const components = { ...context.components }
  // Essay components
  window.data.filter(item => item.tag === 'component').forEach(customComponent => {
    console.log('customComponent', customComponent)
    customComponent.name = customComponent.name || customComponent.label
    if (customComponent.selectors) {
      customComponent.selectors = customComponent.selectors.split('|')
    }
    if (!customComponent.component) {
      customComponent.component = httpVueLoader(customComponent.src)
    }
    Vue.component(customComponent.name, customComponent.component)
    components[customComponent.name] = customComponent
  })
  console.log('components', components)

  vm = new Vue({
    template: '<App/>',
    store,
    render: h => h(App)
  })
  // console.log(`geoJsonCache cache_size=${Object.keys(vm.$store.getters.geoJsonCache).length}`)

  vm.$store.dispatch('setAcct', context.acct)
  vm.$store.dispatch('setRepo', context.repo)
  vm.$store.dispatch('setBranch', context.branch)

  vm.$store.dispatch('setJWT', jwt)
  vm.$store.dispatch('setHash', hash)

  vm.$store.dispatch('setItems', utils.prepItems(window.data.filter(item => item.tag !== 'component')))
  vm.$store.dispatch('setComponents', components)
  // vm.$store.dispatch('setMdRoot', context.mdRoot)
  vm.$store.dispatch('setMdPath', `${context.mdRoot}/${window._essay}`)
  // vm.$store.dispatch('setMdPath', path())
  vm.$store.dispatch('setEssayHTML', document.getElementById('essay').innerHTML)
  vm.$store.dispatch('setSiteTitle', context.siteTitle)

  // vm.$store.dispatch('setViewerIsOpen', false)

  const essayConfig = vm.$store.getters.items.find(item => item.tag === 'config') || {}
  let layout = qargs.layout || essayConfig.layout || 'default'
  if (layout) layout = layout.replace(/^hc$/,'horizontal').replace(/^vtl$/,'vertical')
  vm.$store.dispatch('setLayout', layout)
  vm.$store.dispatch('setShowBanner', window.app === undefined && !(qargs.nobanner === 'true' || qargs.nobanner === ''))
  vm.$store.dispatch('setDebug', qargs.debug === 'true' || qargs.debug === '')

  if (window.app) {
    window.app.essayConfig = essayConfig
    window.app.libVersion = VERSION
    window.app.$store = vm.$store
  }
  vm.$store.dispatch('setEssayConfig', essayConfig)

  console.log('store',store)

  vm.$mount('#essay')
  if (window.app) {
    window.app.isLoaded = true
    window.vm = vm
  }

  setViewport()
  window.addEventListener('resize', () => {
    rtime = new Date()
    if (timeout === false) {
      timeout = true
      setTimeout(resizeend, delta)
    }
  })
}

let current = undefined
const waitForContent = () => {
  console.log(`waitForContent: current=${current} window._essay=${window._essay}`)
  const essayElem = document.getElementById('essay') // article
  if (!window._essay && essayElem && essayElem.innerText.length > 0) {
    window._essay = essayElem.dataset.name
    // console.log(`essay=${window._essay}`)
  }
  if (current != window._essay) {
    // console.log(`essay=${window._essay}`)
    current = window._essay
    if (vm) {
      vm = vm.$destroy()
    }
    initApp()
  }
}
