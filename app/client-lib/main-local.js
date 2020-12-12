import Vue from 'vue'
import App from './App.vue'
import store from './store.js'
import 'lodash'
import httpVueLoader from 'http-vue-loader'
import * as utils from './utils.js'
import VueScrollmagic from 'vue-scrollmagic'

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

Vue.config.productionTip = false

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

const components = {}
baseComponentIndex.forEach(component => {
  if (!components[component.name]) {
    if (!component.component) {
      component.component = httpVueLoader(component.src)
    }
    Vue.component(component.name, component.component)
    components[component.name] = component
  }
})

console.log(components)

Vue.use(VueScrollmagic, {
  vertical: true,
  globalSceneOptions: {},
  loglevel: 2,
  refreshInterval: 100
})

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

async function getEssay() {
  const resp = await fetch(`https://dev.visual-essays.app/essay/jstor-labs/ve-docs`)
  console.log(resp)
  return await resp.text()
}

getEssay().then(html => {
  console.log(html)
  store.dispatch('setEssayHTML', html)
})

const essayConfig = {
  title: 'Testing',
  banner: 'images/banner.jpg'
}
store.dispatch('setEssayConfig', essayConfig)

vm.$mount('#app')