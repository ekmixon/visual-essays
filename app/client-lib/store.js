import Vue from 'vue'
import Vuex from 'vuex'
import { itemsInElements } from './utils'

Vue.use(Vuex)

/*
acct
activeElements
branch
components
componentSelectors
content
contentStartPos
context
debug
essayConfig
essayHTML
hash
height
isMobile
items
itemsInActiveElements
jwt
layout
mdPath
progress
repo
selectedParagraphID
showBanner
triggerOffset
viewerIsOpen
width
*/

export default new Vuex.Store({
  state: {
    acct: undefined,
    repo: undefined,
    branch: undefined,
    mdPath: undefined,
    path: undefined,
    jwt: undefined,
    hash: undefined,
    components: {},
    componentSelectors: {},
    essayHTML: undefined,
    essayConfig: undefined,
    siteInfo: undefined,
    appVersion: undefined,
    siteTitle: undefined,
    isMobile: false,
    isTouchDevice: false,
    layout: 'horizontal',
    showBanner: true,
    headerSize: 96,
    headerHeight: 0,
    footerHeight: 0,
    contentStartPos: 0,
    triggerOffset: 500,
    debug: false,
    context: undefined,
    content: [],
    items: [],
    activeElements: [],
    itemsInActiveElements: [],
    hoverItemID: null,
    selectedParagraphID: null,
    selectedItemID: null,
    selectedImageID: null,
    viewerIsOpen: false,
    height: 0,
    width: 0,
    topMargin: 0,
    progress: 0,
    geoJsonCache: {}
  },
  mutations: {
    addComponent (state, payload) { 
      const components = { ...state.components }
      components[payload.name] = payload.component
      state.components = components
    },
    setComponents (state, components) {
      const componentSelectors = {}
      Object.values(components).forEach(component => {
        if (component.selectors) {
          component.selectors.forEach(selector => {
            const split = selector.split(':')
            if (split.length === 2) {
              const field = split[0]
              const value = split[1]
              if (!componentSelectors[field]) {
                componentSelectors[field] = {}
              }
              if (!componentSelectors[field][value]) {
                componentSelectors[field][value] = []
              }
              componentSelectors[field][value].push(component)
            }
          })
        }
      })
      state.components = components
      state.componentSelectors = componentSelectors
    },
    setAcct (state, acct) { 
      state.acct = acct
      console.log(`setAcct=${state.acct}`)
    },
    setRepo (state, repo) { state.repo = repo },
    setBranch (state, branch) { state.branch = branch },
    setMdPath (state, mdPath) { state.mdPath = mdPath },
    setJWT (state, jwt) { state.jwt = jwt },
    setHash (state, hash) { state.hash = hash },
    setEssayHTML (state, html) {
      state.essayHTML = html 
    },
    setEssayConfig (state, config) { state.essayConfig = config },
    setSiteInfo (state, siteInfo) { state.siteInfo = siteInfo },
    setAppVersion (state, appVersion) { state.appVersion = appVersion },
    setSiteTitle (state, siteTitle) { state.siteTitle = siteTitle },
    setIsMobile (state, isMobile) { state.isMobile = isMobile },
    setIsTouchDevice (state, isTouchDevice) { state.isTouchDevice = isTouchDevice },
    setLayout (state, layout) { state.layout = layout },
    setShowBanner (state, showBanner) { state.showBanner = showBanner},
    setHeaderSize (state, headerSize) { state.headerSize = headerSize},
    setHeaderHeight (state, headerHeight) { state.headerHeight = headerHeight},
    setFooterHeight (state, footerHeight) { state.footerHeight = footerHeight},
    setContentStartPos (state, pos) { state.contentStartPos = pos },
    setTriggerOffset (state, triggerOffset) { state.triggerOffset = triggerOffset },
    setContext (state, context) { state.context = context },
    setDebug (state, debug) { state.debug = debug },
    setContent (state, elems) { state.content = elems },
    setItems (state, items) { state.items = items },
    setActiveElements (state, elems) {
      state.activeElements = elems
      state.itemsInActiveElements = itemsInElements(state.activeElements, state.items)
    },
    setHoverItemID (state, id) { state.hoverItemID = id },
    setSelectedItemID (state, id) { state.selectedItemID = id },
    setSelectedImageID (state, id) { state.selectedImageID = id },
    setSelectedParagraphID (state, id) { state.selectedParagraphID = id },
    setViewerIsOpen (state, isOpen) { state.viewerIsOpen = isOpen },
    updateItem (state, item) {
      /*
      state.items = [ 
        ...state.items.filter(c => c.id !== item.id),
        { ...state.items.find(c => c.id === item.id), ...item }
      ]
      */
      const target = state.items.find(c => c.id === item.id)
      if (target) Object.assign(target, item)
      // console.log('updateItem', item, target)
    },
    setViewport(state, viewport) { 
      state.height = viewport.height
      state.width = viewport.width
    },
    setTopMargin (state, height) { state.topMargin = height },
    setProgress (state, progress) {
      state.progress = progress
      if (window.app) {
        window.app.progress = state.progress
      }
    },
    addToGeoJsonCache (state, geoJson) { state.geoJsonCache = { ...state.geoJsonCache, ...geoJson} }
  },
  actions: {
    addComponent: ({ commit }, payload) => commit('addComponent', payload),
    setAcct: ({ commit }, acct) => commit('setAcct', acct),
    setRepo: ({ commit }, repo) => commit('setRepo', repo),
    setBranch: ({ commit }, branch) => commit('setBranch', branch),
    setContentRoot: ({ commit }, contentRoot) => commit('setContentRoot', contentRoot),
    setMdPath: ({ commit }, mdPath) => commit('setMdPath', mdPath),
    setJWT: ({ commit }, jwt) => commit('setJWT', jwt),
    setHash: ({ commit }, hash) => commit('setHash', hash),
    setComponents: ({ commit }, components) => commit('setComponents', components),
    setEssayHTML: ({ commit }, html) => commit('setEssayHTML', html),
    setEssayConfig: ({ commit }, config) => commit('setEssayConfig', config),
    setSiteInfo: ({ commit }, siteInfo) => commit('setSiteInfo', siteInfo),
    setAppVersion: ({ commit }, appVersion) => commit('setAppVersion', appVersion),
    setSiteTitle: ({ commit }, siteTitle) => commit('setSiteTitle', siteTitle),
    setIsMobile: ({ commit }, isMobile) => commit('setIsMobile', isMobile),
    setIsTouchDevice: ({ commit }, isTouchDevice) => commit('setIsTouchDevice', isTouchDevice),
    setLayout: ({ commit }, layout) => commit('setLayout', layout),
    setShowBanner: ({ commit }, showBanner) => commit('setShowBanner', showBanner),
    setHeaderSize: ({ commit }, headerSize) => commit('setHeaderSize', headerSize),
    setHeaderHeight: ({ commit }, headerHeight) => commit('setHeaderHeight', headerHeight),
    setFooterHeight: ({ commit }, footerHeight) => commit('setFooterHeight', footerHeight),
    setContentStartPos: ({ commit }, pos) => commit('setContentStartPos', pos),
    setTriggerOffset: ({ commit }, triggerOffset) => commit('setTriggerOffset', triggerOffset),
    setContext: ({ commit }, context) => commit('setContext', context),
    setDebug: ({ commit }, debug) => commit('setDebug', debug),
    setContent: ({ commit }, content) => commit('setContent', content),
    setItems: ({ commit }, items) => commit('setItems', items),
    setActiveElements: ({ commit }, elems) => commit('setActiveElements', elems),
    setHoverItemID: ({ commit }, id) => commit('setHoverItemID', id),
    setSelectedItemID: ({ commit }, id) => commit('setSelectedItemID', id),
    setSelectedImageID: ({ commit }, id) => commit('setSelectedImageID', id),
    setSelectedParagraphID: ({ commit }, id) => commit('setSelectedParagraphID', id),
    setViewerIsOpen: ({ commit }, isOpen) => commit('setViewerIsOpen', isOpen),
    updateItem: ({ commit }, entity) => commit('updateItem', entity),
    setViewport: ({ commit }, viewport) => commit('setViewport', viewport),
    setTopMargin: ({ commit }, height) => commit('setTopMargin', height),
    setProgress: ({ commit }, progress) => commit('setProgress', progress),
    addToGeoJsonCache: ({ commit }, geoJson) => commit('addToGeoJsonCache', geoJson)
  },
  getters: {
    acct: state => state.acct,
    repo: state => state.repo,
    branch: state => state.branch,
    mdPath: state => state.mdPath,
    contentRoot: state => state.contentRoot,
    jwt: state => state.jwt,
    hash: state => state.hash,
    components: state => state.components,
    componentSelectors: state => state.componentSelectors,
    siteTitle: state => state.siteTitle,
    layout: state => state.layout,
    isMobile: state => state.isMobile,
    isTouchDevice: state => state.isTouchDevice,
    showBanner: state => state.showBanner,
    headerSize: state => state.headerSize,
    headerHeight: state => state.headerHeight,
    footerHeight: state => state.footerHeight,
    contentStartPos: state => state.contentStartPos,
    triggerOffset: state => state.triggerOffset,
    essayHTML: state => state.essayHTML,
    essayConfig: state => state.essayConfig,
    siteInfo: state => state.siteInfo,
    appVersion: state => state.appVersion,
    context: state => state.context,
    debug: state => state.debug,
    content: state => state.content,
    items: state => state.items,
    activeElements: state => state.activeElements,
    activeElement: (state) => state.activeElements.length > 0 ? state.activeElements[0] : undefined,
    itemsInActiveElements: state => state.itemsInActiveElements,
    hoverItemID: state => state.hoverItemID,
    selectedItemID: state => state.selectedItemID,
    selectedImageID: state => state.selectedImageID,
    selectedParagraphID: state => state.selectedParagraphID,
    viewerIsOpen: state => state.viewerIsOpen,
    height: state => state.height,
    width: state => state.width,
    topMargin: state => state.topMargin,
    progress: state => state.progress,
    geoJsonCache: state => state.geoJsonCache
  },
  modules: {
  }
})
