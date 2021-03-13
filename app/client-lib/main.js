import Vue from 'vue'
import App from './App.vue'
import store from './store.js'
import 'lodash'
import httpVueLoader from 'http-vue-loader'
import * as utils from './utils.js'
import VueScrollmagic from 'vue-scrollmagic'
import VueAnalytics from 'vue-analytics'
import VModal from 'vue-js-modal'
import VueYoutube from 'vue-youtube'
import tippy from 'tippy.js'
import 'tippy.js/dist/tippy.css'
import 'tippy.js/themes/light-border.css'

import D3Network from './components/D3Network.vue'
import D3PlusNetwork from './components/D3PlusNetwork.vue'
import D3PlusRingNetwork from './components/D3PlusRingNetwork.vue'
import EntityInfobox from './components/EntityInfobox.vue'
import EntityInfoboxModal from './components/EntityInfoboxModal.vue'
import ViewerPanel from './components/ViewerPanel.vue'
import Essay from './components/Essay.vue'
import Header from './components/Header.vue'
// import SimpleHeader from './components/SimpleHeader.vue'
import EssayIndex from './components/EssayIndex.vue'
import GraphicViewer from './components/GraphicViewer.vue'
import IIIFSideBySide from './components/IIIFSideBySide.vue'
import OpenSeadragonViewer from './components/OpenSeadragonViewer.vue'
// import PlantsIndexHeader from './components/PlantsIndexHeader.vue'
import PlantsIndexHeaderWithSearch from './components/PlantsIndexHeaderWithSearch.vue'
import KnightlabTimeline from './components/KnightlabTimeline.vue'
import LeafletTimeDimension from './components/LeafletTimeDimension.vue'
import PlantSpecimenViewer from './components/PlantSpecimenViewer.vue'
import Search from './components/Search.vue'
import SiteFooter from './components/Footer.vue'
import StoriiiesViewer from './components/StoriiiesViewer.vue'
import Tabulator from './components/Tabulator.vue'
import VideoPlayer from './components/VideoPlayer.vue'
import Viewer from './components/Viewer.vue'
import VisNetwork from './components/VisNetwork.vue'
import Citation from './components/Citation.vue'

Vue.component('search', Search)

// Vue.config.productionTip = false
Vue.config.devtools = true

const baseComponentIndex = [
  { name: 'd3Network', src: '/components/D3Network.vue', component: D3Network, selectors: ['tag:d3-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'd3PlusNetwork', src: '/components/D3PlusNetwork.vue', component: D3PlusNetwork, selectors: ['tag:d3plus-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'd3PlusRingNetwork', src: '/components/D3PlusRingNetwork.vue', component: D3PlusRingNetwork, selectors: ['tag:d3plus-ring-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'entityInfobox', src: '/components/EntityInfobox.vue', component: EntityInfobox},
  { name: 'entityInfoboxModal', src: '/components/EntityInfoboxModal.vue', component: EntityInfoboxModal},
  { name: 'viewerPanel', src: '/components/ViewerPanel.vue', component: ViewerPanel},
  { name: 'essay', src: '/components/Essay.vue', component: Essay, type: 'content', layouts: ['default', 'vertical', 'horizontal']},
  // { name: 'simpleHeader', src: '/components/SimpleHeader.vue', component: SimpleHeader, type: 'header', layouts: ['simple', 'default', 'index', 'vertical', 'horizontal']},
  { name: 'essayHeader', src: '/components/Header.vue', component: Header, type: 'header', layouts: ['default', 'vertical', 'horizontal']},
  { name: 'essayIndex', src: '/components/EssayIndex.vue', component: EssayIndex, type: 'content', layouts: ['index']},
  { name: 'iiifSideBySide', src: '/components/IIIFSideBySide.vue', component: IIIFSideBySide, selectors: ['tag:iiif-compare'], icon: 'fa-file-image', label: 'Image compare'},
  { name: 'imageViewer', src: '/components/OpenSeadragonViewer', component: OpenSeadragonViewer, selectors: ['tag:image'], icon: 'fa-file-image', label: 'Images'},
  { name: 'indexHeader', src: '/components/Header.vue', component: Header, type: 'header', layouts: ['index']},
  { name: 'knightlabTimeline', src: '/components/KnightlabTimeline.vue', component: KnightlabTimeline, selectors: ['tag:knightlab-timeline'], icon: 'fa-history', label: 'Knightlab Timeline'},
  { name: 'mapViewer', src: '/components/LeafletTimeDimension.vue', component: LeafletTimeDimension, selectors: ['tag:map'], icon: 'fa-map-marker-alt', label: 'Map'},
  { name: 'plantSpecimenViewer', src: '/components/PlantSpecimenViewer.vue', component: PlantSpecimenViewer, selectors: ['tag:plant-specimen'], icon: 'fa-seedling', label: 'Plant Specimens'},
  { name: 'plantsIndexHeader', src: '/components/PlantsIndexHeaderWithSearch.vue', component: PlantsIndexHeaderWithSearch, layouts: ['plants-index'], type: 'header', header: ['plants-index']},
  { name: 'siteFooter', src: '/components/Footer.vue', component: SiteFooter},
  { name: 'storiiiesViewer', src: '/components/StoriiiesViewer.vue', component: StoriiiesViewer, selectors: ['tag:storiiies'], icon: 'fa-book', label: 'Storiiies Viewer'},
  { name: 'tabulator', src: '/components/Tabulator.vue', component: Tabulator, selectors: ['tag:tabulator'], icon: 'fa-table', label: 'Tabulator'},
  { name: 'videoPlayer', src: '/components/VideoPlayer.vue', component: VideoPlayer, selectors: ['tag:video'], icon: 'fa-video', label: 'Videos'},
  { name: 'viewer', src: '/components/Viewer.vue', component: Viewer },
  { name: 'visNetwork', src: '/components/VisNetwork.vue', component: VisNetwork, selectors: ['tag:vis-network'], icon: 'fa-chart-network', label: 'Networks'},
  { name: 'graphicViewer', src: '/components/GraphicViewer.vue', component: GraphicViewer, selectors: ['tag:graphic'], icon: 'fa-table', label: 'Graphic Viewer'},  
  { name: 'citation', src: '/components/Citation.vue', component: Citation },

]

const loc = window.location
console.log(loc)

//let service = loc.host.indexOf('dev.') === 0 ? `https://dev.juncture-digital.org` : 'https://juncture-digital.org'
let service = loc.origin
let site = loc.href
let mode = 'prod'

if (loc.hostname.indexOf('.github.io') > 0) {
  service = 'https://juncture-digital.org'
  site = `${loc.origin}/${loc.pathname.split('/')[1]}`
} else if (loc.hostname.indexOf('localhost') >= 0) {
  service = 'http://localhost:8080'
  site = `${service}${loc.pathname}${loc.search ? loc.search : ''}`
  mode = 'dev'
} else if (loc.hostname.indexOf('.gitpod.io') > 0) {
  service = `https://8080-${loc.host.slice(5)}`
  site = `${service}${loc.pathname}${loc.search ? loc.search : ''}`
  mode = 'dev'
} else if (loc.hostname.indexOf('192.168') === 0) {
  service = `http://${loc.hostname}:8080`
}

console.log(`service=${service} site=${site} mode=${mode}`)

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
    //const ghRoot = referrerPath.length > 3 ? referrerPath[4] === 'docs' ? referrerPath[4] : null : null
    //const pathStart = ghRoot ? 5 : 4
    const pathStart = 4
    const pathEnd = referrerPath[referrerPath.length-1] === 'README.md' || referrerPath[referrerPath.length-1] === 'index.md' ? referrerPath.length-1 : referrerPath.length
    const ghPath = referrerPath.slice(pathStart, pathEnd).join('/').replace(/\.md$/, '')
    const redirect = (ghAcct === 'JSTOR-Labs' && ghRepo === 've-docs') 
      ? `https://docs.juncture-digital.org/${ghPath}`
      : `${loc.origin}/${ghAcct}/${ghRepo}/${ghPath}${ghBranch === 'master' || ghBranch === 'main' ? '' : '?ref=' + ghBranch}`
    console.log(`redirect=${redirect}`)
    window.location = redirect
  }
}

let jwt

let qargs = loc.href.indexOf('?') > 0 ? utils.parseQueryString(loc.href.split('?')[1]) : {}
if (qargs.token) {
  jwt = qargs.token
  window.localStorage.setItem('ghcreds', jwt)
} else {
  jwt = window.localStorage.getItem('ghcreds')
}

Vue.prototype.$tippy = tippy

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

let vm = new Vue({ // eslint-disable-line no-unused-vars
    template: '<App/>',
    store,
    render: h => h(App)
  })

async function getSiteInfo() {
  const resp = await fetch(`${service}/site-info?href=${encodeURIComponent(site)}`)
  return await resp.json()
}

const checkJWTExpiration = async(jwt) => {
  let response = await fetch(`${service}/jwt-expiration/${jwt}`)
  const expiration = parseInt(await response.text())
  const isExpired =  Date.now()/1000 >= expiration
  if (isExpired) window.localStorage.removeItem('ghcreds')
  return isExpired
}

const doRemoteRequests = async () => {
  const remoteRequests = [
    getSiteInfo(),
    Promise.resolve(baseComponentIndex)
  ]
  if (jwt !== null) remoteRequests.push(checkJWTExpiration(jwt))
  let responses = await Promise.all(remoteRequests)
  let siteInfo = responses[0]
  let componentsIndex = responses[1]
  if (jwt !== null) {
    const jwtIsExpired = responses[responses.length-1]
    if (jwtIsExpired) jwt = null
  }

  siteInfo.service = service
  siteInfo.mode = mode
  if (!siteInfo.components) siteInfo.components = []

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

  //Vue.use(VueAnalytics, {id: siteInfo.gaTrackingID || 'UA-125778965-8'})
  let gaTrackingCodes = ['UA-125778965-6']
  if (siteInfo.gaTrackingID) {
    if (Array.isArray(siteInfo.gaTrackingID)) {
      gaTrackingCodes = [...gaTrackingCodes, ...siteInfo.gaTrackingID]
    } else {
      gaTrackingCodes.push(siteInfo.gaTrackingID)
    }
  }
  console.log(`gaTrackingCodes=${gaTrackingCodes}`)
  Vue.use(VueAnalytics, {id: gaTrackingCodes})

  if (siteInfo.favicon) {
    let e = document.createElement('link')
    e.href = siteInfo.favicon
    e.rel = 'icon'
    e.type='image/x-icon'
    document.getElementsByTagName('head')[0].appendChild(e)
  }
  if (siteInfo.title) {
    document.title = siteInfo.title
  }
  if (siteInfo.css) {
    let e = document.createElement('link')
    e.href = siteInfo.css
    e.rel = 'stylesheet'
    document.getElementsByTagName('head')[0].appendChild(e)
  }
  console.log('components', components)
  console.log('siteInfo', siteInfo)
  store.dispatch('setSiteInfo', siteInfo)
  store.dispatch('setComponents', components)
  store.dispatch('setJWT', jwt)
  document.querySelectorAll('script[data-ve-meta]').forEach(scr => eval(scr.text))
  store.dispatch('setAppVersion', window.veMeta ? window.veMeta.version : undefined)
  store.dispatch('setServiceBase', service)
}

doRemoteRequests().then(_ => vm.$mount('#app')) // eslint-disable-line no-unused-vars
