import Vue from 'vue'
import App from './App.vue'
import store from './store.js'
import VueScrollmagic from 'vue-scrollmagic'
import httpVueLoader from 'http-vue-loader'
import VModal from 'vue-js-modal'
import * as utils from './utils.js'
import VueAnalytics from 'vue-analytics'
// import MobileDetect from 'mobile-detect'
import 'lodash'
import VueYoutube from 'vue-youtube'
// import 'leaflet-polylinedecorator'

import D3Network from './components/D3Network.vue'
import D3PlusNetwork from './components/D3PlusNetwork.vue'
import D3PlusRingNetwork from './components/D3PlusRingNetwork.vue'
import EntityInfobox from './components/EntityInfobox.vue'
import EntityInfoboxModal from './components/EntityInfoboxModal.vue'
import Essay from './components/Essay.vue'
import Header from './components/Header.vue'
import EssayIndex from './components/EssayIndex.vue'
import IIIFSideBySide from './components/IIIFSideBySide.vue'
import OpenSeadragonViewer from './components/OpenSeadragonViewer.vue'
import KnightlabTimeline from './components/KnightlabTimeline.vue'
import LeafletTimeDimension from './components/LeafletTimeDimension.vue'
import PlantSpecimenViewer from './components/PlantSpecimenViewer.vue'
import SiteFooter from './components/Footer.vue'
import StoriiiesViewer from './components/StoriiiesViewer.vue'
import Tabulator from './components/Tabulator.vue'
import VideoPlayer from './components/VideoPlayer.vue'
import Viewer from './components/Viewer.vue'
import VisNetwork from './components/VisNetwork.vue'

const baseComponentIndex = [
  { name: 'd3Network', src: '/components/D3Network.vue', component: D3Network, selectors: ['tag:d3-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'd3PlusNetwork', src: '/components/D3PlusNetwork.vue', component: D3PlusNetwork, selectors: ['tag:d3plus-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'd3PlusRingNetwork', src: '/components/D3PlusRingNetwork.vue', component: D3PlusRingNetwork, selectors: ['tag:d3plus-ring-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'entityInfobox', src: '/components/EntityInfobox.vue', component: EntityInfobox},
  { name: 'entityInfoboxModal', src: '/components/EntityInfoboxModal.vue', component: EntityInfoboxModal},
  { name: 'essay', src: '/components/Essay.vue', component: Essay, type: 'content', layouts: ['default', 'vertical', 'horizontal']},
  { name: 'essayHeader', src: '/components/Header.vue', component: Header, type: 'header', layouts: ['default', 'vertical', 'horizontal']},
  { name: 'essayIndex', src: '/components/EssayIndex.vue', component: EssayIndex, type: 'content', layouts: ['index']},
  { name: 'iiifSideBySide', src: '/components/IIIFSideBySide.vue', component: IIIFSideBySide, selectors: ['tag:iiif-compare'], icon: 'fa-file-image', label: 'Image compare'},
  { name: 'imageViewer', src: '/components/OpenSeadragonViewer', component: OpenSeadragonViewer, selectors: ['tag:image'], icon: 'fa-file-image', label: 'Images'},
  { name: 'indexHeader', src: '/components/Header.vue', component: Header, type: 'header', layouts: ['index']},
  { name: 'knightlabTimeline', src: '/components/KnightlabTimeline.vue', component: KnightlabTimeline, selectors: ['tag:knightlab-timeline'], icon: 'fa-history', label: 'Knightlab Timeline'},
  { name: 'mapViewer', src: '/components/LeafletTimeDimension.vue', component: LeafletTimeDimension, selectors: ['tag:map'], icon: 'fa-map-marker-alt', label: 'Map'},
  { name: 'plantSpecimenViewer', src: '/components/PlantSpecimenViewer.vue', component: PlantSpecimenViewer, selectors: ['tag:plant-specimen'], icon: 'fa-seedling', label: 'Plant Specimens'},
  { name: 'siteFooter', src: '/components/Footer.vue', component: SiteFooter},
  { name: 'storiiiesViewer', src: '/components/StoriiiesViewer.vue', component: StoriiiesViewer, selectors: ['tag:storiiies'], icon: 'fa-book', label: 'Storiiies Viewer'},
  { name: 'tabulator', src: '/components/Tabulator.vue', component: Tabulator, selectors: ['tag:tabulator'], icon: 'fa-table', label: 'Tabulator'},
  { name: 'videoPlayer', src: '/components/VideoPlayer.vue', component: VideoPlayer, selectors: ['tag:video'], icon: 'fa-video', label: 'Videos'},
  { name: 'viewer', src: '/components/Viewer.vue', component: Viewer },
  { name: 'visNetwork', src: '/components/VisNetwork.vue', component: VisNetwork, selectors: ['tag:vis-network'], icon: 'fa-chart-network', label: 'Networks'}
]

console.log(window.location)
let baseURL = ''
let staticBase = ''
if (window.location.hostname.indexOf('.github.io') > 0) {
  baseURL = 'https://exp.visual-essays.app'
  staticBase = `/${window.location.pathname.split('/')[1]}`
}
console.log(`baseURL=${baseURL} staticBase=${staticBase}`)

const hash = window.location.hash || location.hash
let vm, siteInfo, jwt, qargs

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

// const md = new MobileDetect(window.navigator.userAgent)
// const isMobile = md.phone() !== null
// const isTouchDevice = md.phone() !== null || md.tablet() !== null

qargs = window.location.href.indexOf('?') > 0
  ? utils.parseQueryString(window.location.href.split('?')[1])
  : {}
if (qargs.token) {
  jwt = qargs.token
  window.localStorage.setItem('ghcreds', jwt)
} else {
  jwt = window.localStorage.getItem('ghcreds')
}

const checkJWTExpiration = async(jwt) => {
  let response = await fetch(`${baseURL}/jwt-expiration/${jwt}`)
  const expiration = parseInt(await response.text())
  const isExpired =  Date.now()/1000 >= expiration
  if (isExpired) window.localStorage.removeItem('ghcreds')
  return isExpired
}

async function getSiteInfo() {
  const resp = await fetch(`${baseURL}/site-info?href=${encodeURIComponent(window.location.href)}`)
  return await resp.json()
}

/*
const getBaseComponentsIndex = async() => {
  let response = await fetch(`${staticBase}/components/index.json`)
  let baseComponents = []
  const baseComponentsList = await response.json()
  baseComponentsList.forEach(comp => {
    if (comp.src.indexOf('http') !== 0) comp.src = `${staticBase}${comp.src}`
    baseComponents.push(comp)
  })
  return baseComponents
}
*/

const doRemoteRequests = async () => {
  const remoteRequests = [
    getSiteInfo(), 
    //getBaseComponentsIndex()
    Promise.resolve(baseComponentIndex)
  ]
  if (jwt !== null) remoteRequests.push(checkJWTExpiration(jwt))

  let responses = await Promise.all(remoteRequests)
  siteInfo = responses[0]
  let componentsIndex = responses[1]
  if (jwt !== null) {
    const jwtIsExpired = responses[responses.length-1]
    if (jwtIsExpired) jwt = null
  }

  if (!siteInfo.components) siteInfo.components = []

  Vue.use(VueAnalytics, {
    id: siteInfo.gaTrackingID
  })

  const components = {}
  const componentsList = [...siteInfo.components, ...componentsIndex]
  componentsList.forEach(component => {
    if (!components[component.name]) {
      if (!component.component) {
        component.component = httpVueLoader(component.src)
      }
      Vue.component(component.name, component.component)
      components[component.name] = component
    }
  })
  if (siteInfo.favicon) {
    let e = document.createElement('link')
    e.href = siteInfo.favicon
    e.rel = 'icon'
    e.type='image/x-icon'
    document.getElementsByTagName('head')[0].appendChild(e)
  }
  window.components = components
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

function initApp() {
  console.log('visual-essays.init')

  window.data = []
  document.querySelectorAll('script[data-ve-tags]').forEach((scr) => {
    eval(scr.text)
  })

  const components = { ...window.components }
  // Essay components
  window.data.filter(item => item.tag === 'component').forEach(customComponent => {
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

  vm.$store.dispatch('setAcct', siteInfo.acct)
  vm.$store.dispatch('setRepo', siteInfo.repo)
  vm.$store.dispatch('setMdPath', window.location.pathname)
  vm.$store.dispatch('setMdPath', window._essay)
  vm.$store.dispatch('setBranch', siteInfo.editBranch)

  vm.$store.dispatch('setJWT', jwt)
  vm.$store.dispatch('setHash', hash)

  vm.$store.dispatch('setItems', utils.prepItems(window.data.filter(item => item.tag !== 'component')))
  vm.$store.dispatch('setComponents', components)
  vm.$store.dispatch('setEssayHTML', document.getElementById('essay').innerHTML)
  vm.$store.dispatch('setSiteTitle', siteInfo.siteTitle)

  const essayConfig = vm.$store.getters.items.find(item => item.tag === 'config') || {}
  let layout = qargs.layout || essayConfig.layout || 'default'
  if (layout) layout = layout.replace(/^hc$/,'horizontal').replace(/^vtl$/,'vertical')
  vm.$store.dispatch('setLayout', layout)
  vm.$store.dispatch('setShowBanner', window.app === undefined && !(qargs.nobanner === 'true' || qargs.nobanner === ''))
  vm.$store.dispatch('setDebug', qargs.debug === 'true' || qargs.debug === '')

  console.log(vm.$store)

  if (window.app) {
    window.app.siteInfo = siteInfo
    console.log('window.app.siteInfo', window.app.siteInfo)
    window.app.jwt = jwt
    // window.app.qargs = qargs
    window.app.essayConfig = essayConfig
    // window.app.$store = vm.$store
  }
  vm.$store.dispatch('setEssayConfig', essayConfig)

  vm.$mount('#essay')
  if (window.app) {
    window.app.isLoaded = true
    window.vm = vm
  }
}

let current = undefined
const waitForContent = () => {
  // console.log(`waitForContent: current=${current} window._essay=${window._essay}`)
  const essayElem = document.getElementById('essay') // article
  if (!window._essay && essayElem && essayElem.innerText.length > 0) {
    window._essay = essayElem.dataset.name
  }
  if (current != window._essay) {
    current = window._essay
    if (vm) {
      vm = vm.$destroy()
    }
    initApp()
  }
}
