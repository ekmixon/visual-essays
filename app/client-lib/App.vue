<template>
  <div ref="app" id="visual-essay" :class="`visual-essay ${layout}`">
    <div v-if="headerEnabled && essayConfig !== undefined" ref="header" class="header">
      <component v-bind:is="headerComponent"
        :height="headerHeight"
        :essay-config="essayConfig"
        :site-config="siteInfo"
        :is-authenticated="isAuthenticated"
        :read-only="readOnly"
        :href="href"
        :app-version="appVersion"
        :content-ref="ref"
        @collapse-header="collapseHeader"
        @menu-item-clicked="menuItemClicked"
        @logout="logout"
        @view-markdown="viewMarkdown"
        @edit-markdown="editMarkdown"
        @goto-github="gotoGithub"
        @open-docs-site="openDocsSite"
        @open-search-tool="openSearchTool"
      ></component>
    </div>
    <div ref="essay" id="scrollableContent" class="essay" @scroll="resizeHeader">
      <component v-if="html" v-bind:is="contentComponent"
        :html="html"
        :layout="layout"
        :width="essayWidth"
        :height="essayHeight"
        :anchor="anchor"
        :essay-config="essayConfig"
        :hover-item="hoverItemID"
        :selected-item="selectedItemID"
        :viewer-is-open="viewerIsOpen"
        :active-elements="activeElements"
        :all-items="allItems"
        :items-in-active-elements="itemsInActiveElements"
        :service-base=serviceBase
        :debug="debug"
        @set-viewer-is-open="setViewerIsOpen"
        @set-active-elements="setActiveElements"
        @set-hover-item="setHoverItem"
        @set-selected-item="setSelectedItem"
        @collapse-header="collapseHeader"
      ></component>
    </div>
    <div v-if="layout === 'horizontal' || layout === 'vertical'" ref="viewer" class="viewer" :style="`top:${viewerIsOpen ? 46 : 96}%;`">
      <component v-bind:is="viewerComponent"
        :width="viewerWidth"
        :height="viewerHeight"
        :hover-item="hoverItemID"
        :selected-item="selectedItemID"
        :siteInfo="siteInfo"
        :acct="acct"
        :repo="repo"
        :branch="branch"
        :path="essayPath"
        :hash="hash"
        :jwt="jwt"
        :layout="layout"
        :viewer-is-open="viewerIsOpen"
        :active-elements="activeElements"
        :items-in-active-elements="itemsInActiveElements"
        :groups="groups"
        :service-base=serviceBase
        @set-viewer-is-open="setViewerIsOpen"
        @set-hover-item="setHoverItem"
        @set-selected-item="setSelectedItem"
        @toggle-viewer="toggleOption('viewerIsOpen')"
      ></component>
    </div>
    <div v-if="footerEnabled && siteInfo" class="footer">
      <component :is="footerComponent" :site-config="siteInfo"></component>
    </div>
    <!--
    <button v-if="isMobile && layout === 'horizontal'" class="floating-action-button" @click="setViewerIsOpen(true)">
      <i class="fal fa-image"></i>
    </button>
    -->
    <div v-if="layout === 'horizontal'" class="fab1" @click="setViewerIsOpen(true)" >
      <i class="far fa-images"></i> Open visualization
    </div>

    <component v-bind:is="entityInfoboxModalComponent"
      :selected-item="selectedItemID"
      @set-selected-item="setSelectedItem"
    ></component>
  </div>
</template>

<script>

import { itemsInElements, groupItems, elemIdPath } from './utils'

export default {
  name: 'app',
      data: () => ({
        activeElements: [],
        itemsInActiveElements: [],
        headerEnabled: true,
        footerEnabled: false,
        footerHeight: 0,
        viewerHeight: 500,
        viewerWidth: 500,
        essayHeight: 0,
        essayWidth: 0,
        headerHeight: 400,
        header: null,
        essay: null,
        footer: null,
        lastTouchY: undefined,
        lastScrollY: 0,
        hoverItemID: null,
        selectedItemID: null,
        essayBase: undefined,
        essayPath: undefined,
        essayFname: undefined,
        qargs: {},
        href: undefined,
        hash: undefined,
        anchor: undefined,
        externalWindow: undefined,
    
        isMobile: false,
        headerPrior: 0,
        heightPrior: 0,
        widthPrior: 0,
        fabActions: [
          {
              name: 'cache',
              icon: 'cached'
          },
          {
              name: 'alertMe',
              icon: 'add_alert'
          }
      ]
      }),
      computed: {
        headerMaxHeight() { return this.isMobile ? 200 : 400 },
        headerMinHeight() { return this.isMobile ? 50 : 100 },
        siteInfo() { return this.$store.getters.siteInfo || {} },
        viewerIsOpen() { return this.$store.getters.viewerIsOpen },
        acct() { return this.siteInfo.acct },
        repo() { return this.siteInfo.repo },
        branch() { return this.siteInfo.ref },
        // path() { return `${this.$store.getters.mdPath}` },
        // hash() { return `${this.$store.getters.hash}` },
        jwt() { return this.$store.getters.jwt },
        isAuthenticated() { return this.jwt !== null && this.jwt !== undefined },
        readOnly() { return this.qargs.readonly},
        allItems() { return this.$store.getters.items },
        html() { return this.$store.getters.essayHTML },
        components() { return Object.values(this.$store.getters.components) },
        layout() { return this.$store.getters.layout },
        essayConfig() { return this.$store.getters.essayConfig },
        baseurl() { return this.siteInfo.baseurl || '' },
        serviceBase() { return this.siteInfo.service || '/' },
        debug() { return this.$store.getters.debug },
        appVersion() { return this.$store.getters.appVersion },
        /*
        styleClass() { 
          return this.essayConfig && this.essayConfig.style
            ? this.essayConfig.style
            : this.layout === this.layout === 'vertical'
              ? 'essay-default'
              : ''
        },
        */
        contentComponents() { return this.components.filter(compConf => compConf.type === 'content') },
        contentComponent() { 
          const found = this.contentComponents.find(c => c.layouts && c.layouts.indexOf(this.layout) >= 0)
          return found ? found.component :null
        },
        headerComponents() { return this.components.filter(compConf => compConf.type === 'header') },
        headerComponent() {
          let found = this.headerComponents.find(c => {
            return this.essayConfig
              ? (this.essayConfig.header && c.header && c.header.indexOf(this.essayConfig.header) >= 0) ||
                (!this.essayConfig.header && c.layouts && c.layouts.indexOf(this.layout) >= 0)
              : null
          })
          return found ? found.component : null
        },
        footerComponent() {
          const found = this.components.find(c => c.name === 'siteFooter')
          return found ? found.component : null
        },
        entityInfoboxModalComponent() {
          const found = this.components.find(c => c.name === 'entityInfoboxModal')
          return found ? found.component : null
        },
        viewerModalComponent() {
          const found = this.components.find(c => c.name === 'viewerModal')
          return found ? found.component : null
        },
        viewerComponent() {
          const found = this.components.find(c => c.name === 'viewer')
          return found ? found.component : null
        },
        activeElement() { return this.activeElements.length > 0 ? this.activeElements[0] : undefined },
        groups() { 
          const groups = groupItems(itemsInElements(elemIdPath(this.activeElement), this.allItems), this.$store.getters.componentSelectors) 
          return groups
        },
        ref() { return this.qargs && this.qargs.ref ? this.qargs.ref : this.siteInfo.ref},
        refQueryArg() { return this.ref && this.ref !== this.siteInfo.ref ? `?ref=${this.ref}` : '' }
      },
      mounted() {
        console.log(window.location)
        // this.$modal.show('viewer-modal')
        if (window.location.href.indexOf('#') > 0) {
          this.hash = window.location.href.split('#').pop()
        }
        this.href = window.location.href
        this.qargs = this.parseQueryString()

        let path = window.location.pathname.length > this.baseurl.length
          ? window.location.pathname.slice(this.baseurl.length)
          : '/'
        console.log(`App: baseurl=${this.baseurl} path=${path}`, this.qargs, this.siteInfo, this.essayConfig)
        console.log(`ref=${this.ref} refQueryArg=${this.refQueryArg}`)
        window.onpopstate = (e) => { this.setEssay(e.state.file, true) }

        const resizeObserver = new ResizeObserver(entries => { // eslint-disable-line no-unused-vars
          // this.viewerHeight = this.$refs.app.clientHeight - (this.$refs.header ? this.$refs.header.clientHeight : 0) - this.$refs.footer.clientHeight
          let calculated = this.calcViewerHeight()
          if (calculated !== this.viewerHeight) this.viewerHeight = this.calcViewerHeight()
          this.viewerWidth = this.layout[0] === 'v' ? this.$refs.app.clientWidth / 2 : this.$refs.app.clientWidth
          let isMobile = window.matchMedia('only screen and (max-width: 1000px)').matches
          if (isMobile) {
            if (!this.isMobile) {
              if (this.$refs.essay && this.header) this.$refs.essay.style.paddingTop = `${this.header.clientHeight}px`
              this.isMobile = isMobile
            }
          } else {
            if (this.isMobile) {
              if (this.$refs.essay) this.$refs.essay.style.paddingTop = 0             
              this.isMobile = isMobile
            }
          }
          // console.log(`resizeObserver: isMobile=${this.isMobile} viewerHeight=${this.viewerHeight} height=${this.$refs.app.clientHeight} width=${this.$refs.app.clientWidth} header=${this.$refs.header ? this.$refs.header.clientHeight : null} footer=${this.$refs.footer ? this.$refs.footer.clientHeight : null}`)
        })
        resizeObserver.observe(this.$refs.app)
        
        this.waitForHeaderFooter() // header and footer are dynamically loaded external components        
        this.setEssay(path)

        // this.updateViewerSize()
      },
      methods: {
        addHeaderSizeObserver() {
          if (this.header && !this.headerResizeObserver) {
            this.headerResizeObserver = new ResizeObserver(entries => { // eslint-disable-line no-unused-vars
              // console.log(`headerResizeObserver: isMobile=${this.isMobile} headerHeight=${this.header.clientHeight} essayTopPadding=${this.$refs.essay ? this.$refs.essay.style.paddingTop : 0}`)
              this.$refs.essay.style.paddingTop = `${this.header.clientHeight}px`
            })
            this.headerResizeObserver.observe(this.header)
          }
        },
        async loadEssay(path, replace) {
          this.footerEnabled = false
          this.headerHeight = !this.isMobile && window.innerHeight < 1000 ? this.headerMinHeight : this.headerMaxHeight
          // Load essay HTML, use local cached version if available
          let essayUrl = `${this.serviceBase}/essay/${this.siteInfo.acct}/${this.siteInfo.repo}${path}?ref=${this.ref}`
          console.log(`loadEssay: path=${path} url=${essayUrl}`)
          let html = await this.cachedEssay(essayUrl)

          // Create element from HTML source
          const tmp = document.createElement('div')
          tmp.innerHTML = html
          const essayElem = tmp.querySelector('#essay')
          this.essayFname = essayElem.dataset.name

          // Update browser URL
          if (path[path.length-1] !== '/') path += '/'
          // console.log(`browser url: baseurl=${this.baseurl} path=${path} refArg=${this.refQueryArg}`)
          let browserPath = `${this.baseurl}${path}${this.refQueryArg}`
          if (replace) {
            history.replaceState({file: path || ''}, '', browserPath)
          } else {
            history.pushState({file: path || ''}, '', browserPath)
          }
          this.essayPath = path
          this.href = window.location.href
          this.$ga.page(path)

          // Parse item data from HTML
          window.data = []
          tmp.querySelectorAll('script[data-ve-tags]').forEach(scr => eval(scr.text))
          const items = this.prepItems(window.data.filter(item => item.tag !== 'component'))

          // Update store with new essay data
          const essayConfig = items.find(item => item.tag === 'config') || {}
          this.$store.dispatch('setEssayHTML', essayElem.innerHTML)
          this.$store.dispatch('setItems', items)
          this.$store.dispatch('setEssayConfig', essayConfig)
          let layout = 'default'
          if (essayConfig.layout === 'vertical' || essayConfig.layout === 'vtl') {
            layout = this.isMobile ? 'horizontal' : 'vertical' 
          } else if (essayConfig.layout && essayConfig.layout[0] !== 'h') {
            layout = essayConfig.layout
          }
          console.log(`essayConfig.layout=${essayConfig.layout} isMobile=${this.isMobile} layout=${layout}`)
          this.$store.dispatch('setLayout', layout)
          this.$nextTick(() => {this.convertLinks()})
        },

        cachedEssay(url) {
          if (!window.essayCache) {
            window.essayCache = {}
          }
          // console.log(`cached=${this.siteInfo.mode !== 'dev' && window.essayCache[url] !== undefined}`)
          if (this.siteInfo.mode === 'dev' || !window.essayCache[url]) {
            window.essayCache[url] = fetch(url).then(resp => resp.text())
          }
          return window.essayCache[url]
        },

        reset() {
          this.$store.dispatch('setEssayHTML', null)
          this.$store.dispatch('setItems', [])
          // this.$store.dispatch('setEssayConfig', null)
          this.setActiveElements([])
        },

        convertLinks() {
          this.$refs.essay.querySelectorAll('a').forEach(link => {

            if (!link.href || link.href.indexOf(window.location.host) > 0) {
              
              // If internal link
              let target = link.dataset.target
              if (!target) { 
                const parsedUrl = this.parseUrl(link.href)
                // console.log(parsedUrl)
                target = parsedUrl.hash === '' ? parsedUrl.pathname : parsedUrl.hash.split('?')[0]
              }
              // console.log(link.href, target)
              link.removeAttribute('href')
              link.setAttribute('data-target', target)

              // Add click handler for internal links
              link.addEventListener('click', (e) => {
                let target = e.target
                while(!target.dataset.target && target.parentElement) {
                  target = target.parentElement
                }
                let path = target.dataset.target
                console.log('click', path)
                if (path[0] === '#') {
                  document.querySelector(path).scrollIntoView({block:'start'})
                } else {
                  this.setEssay(path)
                }
              })
            } else {
              
              // If external link, add external link icon to text and force opening in new tab
              link.innerHTML += '<sup><i class="fa fa-external-link-square-alt" style="margin-left:3px;margin-right:2px;font-size:0.7em;color:#219653;"></i></sup>'
              link.setAttribute('target', '_blank')
            }
          })
        },

        setActiveElements(activeElements) {
          this.activeElements = activeElements
          this.itemsInActiveElements = itemsInElements(activeElements, this.allItems)
        },
        resizeHeader(e) {
          let delta
          if (e.touches) {
            delta = (e.touches[0].screenY - this.lastTouchY) / 10
          } else if (e.wheelDeltaY) {
            delta = (e.wheelDeltaY ? e.wheelDeltaY : -e.deltaY)
          } else if (e.type === 'scroll') {
            delta = this.lastScrollY < e.srcElement.scrollTop ? -5 : 0
            this.lastScrollY = e.srcElement.scrollTop
          }

          const scrollDir = delta > 0 ? 'expand' : 'shrink'
          // console.log(`resizeHeader: delta=${delta} dir=${scrollDir} pos=${window.scrollY} height=${this.header.clientHeight} min=${this.headerMinHeight}`)
          if (delta && scrollDir === 'shrink' || window.scrollY === 0) {
            if ((scrollDir === 'shrink' && this.header.clientHeight > this.headerMinHeight) ||
                (scrollDir === 'expand' && this.header.clientHeight < this.headerMaxHeight && this.$refs.essay.scrollTop === 0)) {
              let newHeaderHeight = this.header.clientHeight + delta
              if (scrollDir === 'shrink' && newHeaderHeight < this.headerMinHeight) newHeaderHeight = this.headerMinHeight
              if (scrollDir === 'expand' && newHeaderHeight > this.headerMaxHeight) newHeaderHeight = this.headerMaxHeight
              this.header.style.height = `${newHeaderHeight}px`
              this.headerHeight = newHeaderHeight
              e.preventDefault()
              e.stopPropagation()
            }
          }
        },
        waitForHeaderFooter() {
          console.log('waitForHeaderFooter')
          if (!this.header) {
            this.header = document.getElementById('header')
            if (this.header && this.$refs.essay) {
              if (this.isMobile) this.addHeaderSizeObserver()
              if ('ontouchstart' in window) {
                this.header.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.$refs.essay.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.header.addEventListener('touchmove', this.resizeHeader )
                this.$refs.essay.addEventListener('touchmove', this.resizeHeader)
              } else {
                this.header.addEventListener('wheel', this.resizeHeader, {passive: false})
                this.$refs.essay.addEventListener('wheel', this.resizeHeader, {passive: false})
              }
            }
          }
          if (!this.footer) {
            this.footer = document.getElementById('footer')
            if (this.footer) {
              this.footerHeight = this.footer.clientHeight
            }
          }
          this.viewerHeight = this.calcViewerHeight()
          if (!this.isMobile && this.header && window.innerHeight < 1000) this.collapseHeader()
          if ((this.headerEnabled && !this.header) || (this.footerEnabled && !this.footer)) setTimeout(this.waitForHeaderFooter, 250)
        },
        calcViewerHeight() {
          let height
          if (this.isMobile) {
            height = window.innerHeight / 2
          } else {
            height = this.$refs.app.clientHeight
            if (this.$refs.header) height -= this.$refs.header.clientHeight
            if (this.$refs.footer) height -= this.$refs.footer.clientHeight
            // console.log(`calculated=${height} isMobile=${this.isMobile} app=${this.$refs.app.clientHeight} header=${this.$refs.header ? this.$refs.header.clientHeight : 0} footer=${this.$refs.footer ? this.$refs.footer.clientHeight : 0}`)
            height = this.layout === 'horizontal' ? height/2 : height
          }
          return height
        },
        setHoverItem(itemID) {
          this.hoverItemID = itemID
        },
        setSelectedItem(itemID) {
          this.selectedItemID = itemID
        },
        toggleOption(option) {
          // if (option === 'layout') this.setLayout(this.layout === 'vertical' ? 'horizontal' : 'vertical')
          if (option === 'viewerIsOpen') this.setViewerIsOpen(!this.viewerIsOpen)
          if (option === 'header') this.headerEnabled = !this.headerEnabled
          if (option === 'footer') this.footerEnabled = !this.footerEnabled
        },
        setLayout(layout) {
          this.$store.dispatch('setLayout', layout)
          this.setViewerIsOpen(layout === 'vertical')
        },
        setViewerIsOpen(isOpen) {
          console.log('setViewerIsOpen', isOpen)
          this.$store.dispatch('setViewerIsOpen', isOpen)
        },
        collapseHeader() {
          if (this.header) {
            this.header.style.height = `${this.headerMinHeight}px`
            this.headerHeight = this.headerMinHeight
          }
        },
        menuItemClicked(path) {
          console.log('menuItemClicked', path)
          this.setEssay(path)
        },
        logout() {
          window.localStorage.removeItem('ghcreds')
          this.$store.dispatch('setJWT', null)
        },
        viewMarkdown() {
          this.openWindow(`/markdown-viewer/${this.siteInfo.acct}/${this.siteInfo.repo}/${this.ref}${this.essayFname}`)
        },
        editMarkdown(editor) {
          this.openWindow(editor == 'custom'
            ? `https://editor.visual-essays.app/${this.siteInfo.acct}/${this.siteInfo.repo}${this.baseurl}${this.essayFname}`
            : `https://github.com/${this.siteInfo.acct}/${this.siteInfo.repo}/edit/${this.siteInfo.editBranch}${this.essayFname}.md`
          ) 
        },
        gotoGithub() {
          this.openWindow(`https://github.com/${this.siteInfo.acct}/${this.siteInfo.repo}/tree/${this.ref}`, null)
        },
        openDocsSite() {
          this.openWindow(`https://docs.visual-essays.app?readonly`, `toolbar=yes,location=yes,left=0,top=0,width=1000,height=1200,scrollbars=yes,status=yes`)
        },
        openSearchTool(qid) {
          this.openWindow(`https://search.plant-humanities.app?eid=${qid}`, `toolbar=yes,location=yes,left=0,top=0,width=1001,height=1200,scrollbars=yes,status=yes`)
        },
        openWindow(url, options) {
          console.log('openWindow', url)
          if (this.externalWindow) { this.externalWindow.close() }
          if (options === undefined) options = 'toolbar=yes,location=yes,left=0,top=0,width=1000,height=1200,scrollbars=yes,status=yes'
          this.externalWindow = window.open(url, '_blank', options)
        },         
        fadeIn(elem) {
          if (elem) {
            elem.classList.add('visible')
            elem.classList.remove('hidden')
          }
        },
        fadeOut(elem) {
          if (elem) {
            elem.classList.add('hidden')
            elem.classList.remove('visible') 
          }
        },
        setEssay(path, replace) {
          console.log(`setEssay: path=${path}`)
          this.essayPath = path
          this.fadeOut(this.$refs.essay)
          this.fadeOut(this.$refs.viewer)
          this.reset()
          this.$nextTick(() => {
            this.loadEssay(path, replace)
            this.fadeIn(this.$refs.essay)
            this.fadeIn(this.$refs.viewer)
          })
        },
        updateViewerSize() {
          if (this.$refs.header) {
            let headerHeight = this.$refs.header ? this.$refs.header.clientHeight : null
            if (headerHeight && headerHeight !== this.headerPrior ||
                this.$refs.app.clientHeight !== this.heightPrior ||
                this.$refs.app.clientWidth !== this.widthPrior) {
            // console.log(`updateViewerSize: height=${this.$refs.app.clientHeight} width=${this.$refs.app.clientWidth} header=${headerHeight} footer=${this.$refs.footer ? this.$refs.footer.clientHeight : null}`)
            // this.viewerHeight = this.$refs.app.clientHeight - (this.$refs.header ? this.$refs.header.clientHeight : 0) - this.$refs.footer.clientHeight
              this.viewerHeight = this.calcViewerHeight()
              this.headerPrior = headerHeight
              this.heightPrior = this.$refs.app.clientHeight
            }
          }
          this.viewerWidth = this.layout[0] === 'v' ? window.innerWidth / 2 : window.innerWidth
          this.widthPrior = window.innerWidth
        }
      },
      updated() { this.updateViewerSize() },
      watch: {
        viewerWidth() {
          console.log(`App.viewerWidth: width=${this.viewerWidth} height=${this.viewerHeight}`)
        },
        viewerHeight() {
          // console.log(`App.viewerHeight: width=${this.viewerWidth} height=${this.viewerHeight}`)
        },
        layout: {
          handler: function (layout) {
            this.setViewerIsOpen(layout === 'vertical')
            this.updateViewerSize()
            this.footerEnabled = layout === 'default' || layout === 'index'
          },
          immediate: false
        },
        html() {
          if (this.html && this.hash && this.header) this.$nextTick(() => {this.anchor = this.hash; this.hash = undefined})
        },
        header() {
          if (this.html && this.hash && this.header) this.$nextTick(() => {this.anchor = this.hash; this.hash = undefined})
        },
        headerComponent() {
          console.log('headerComponent')
          this.header = null
          this.headerResizeObserver = null
          this.$nextTick(() => this.waitForHeaderFooter())
        },
        isMobile: {
          handler: function (isMobile) {
            console.log(`viewerIsOpen=${this.viewerIsOpen} isMobile=${isMobile} viewer=${this.$refs.viewer !== undefined}`)
            console.log(this.$refs.viewer)
            this.headerHeight = this.headerMaxHeight
            //if (isMobile && this.$refs.viewer) this.$refs.viewer.style.display = this.viewerIsOpen ? '' : 'none'
          },
          immediate: true
        },
        viewerIsOpen: {
          handler: function (isOpen) {
            console.log(`viewerIsOpen=${isOpen} isMobile=${this.isMobile} viewer=${this.$refs.viewer !== undefined}`)
            //if (this.isMobile && this.$refs.viewer) this.$refs.viewer.style.display = isOpen ? '' : 'none'
            console.log(this.$refs.viewer)
            this.updateViewerSize()

          },
          immediate: true
        }
      }
}
</script>

<style scoped>

body {
  padding: 0 !important;
  margin: 0 !important;
}

  /* desktop/laptop */
  @media only screen and (min-width: 1000px) {

    #visual-essay.default,
    #visual-essay.index {
      display: grid;
      height: 100vh;
      width: 100%;
      grid-template-columns: auto;
      grid-template-rows: auto 1fr auto;
      grid-template-areas: 
        "header"
        "essay "
        "footer";
      position: absolute;
    }

    #visual-essay.vertical {
      display: grid;
      height: 100vh;
      width: 100%;
      grid-template-columns: 50% 50%;
      grid-template-rows: auto 1fr;
      grid-template-areas: 
        "header header"
        "essay  viewer";
      position: absolute;
    }

  }

  /* smartphone */
  @media only screen and (max-width: 1000px) {

    #visual-essay {
      height: 100%;
    }

    .header {
      position: fixed !important;
      top: 0;
      width: 100%;
    }

    .viewer {
      position: fixed !important;
      width: 100%;
      height: 50%;
      z-index: 0;
      transition: top 0.5s;
    }
  }

  .header {
    grid-area: header;
    z-index: 3;
  }
  .essay {
    grid-area: essay;
    overflow-y: auto;
  }
  .viewer {
    grid-area: viewer;
    justify-self: stretch;
    background: #333;
    z-index: 2;
  }
  .footer {
    grid-area: footer;
  }

  #visual-essay.horizontal .essay {
    padding: 0.5em;
    font-size: 90%;
    line-height: 1.2em !important;
  }

  #visual-essay.default .essay,
  #visual-essay.index .essay {
    /*padding: 2em;*/
  }

  .visible {
    visibility: visible;
    opacity: 1;
    transition: opacity 1s linear;
  }
  .hidden {
    visibility: hidden;
    opacity: 0;
    /*
    transition: opacity 0.5s linear;
    transition: visibility 0s 1s, opacity 1s linear;
    */
  }
  
  .fab1 {
    width: 160px;
    height: 45px;
    background-color: #219653;
    border-radius: 8px 0 0 8px;
    box-shadow: 0 1px 10px 0 rgb(0, 0, 0, 0.7);
    font-size: 14px;
    line-height: 45px ;
    color: white;
    text-align: center;
    position: fixed;
    right: 0;
    bottom: 100px;
    z-index: 0;
    transition: all 0.1s ease-in-out;
  }

  .fab1 svg {
    font-size: 18px;
  }

  .fab1:hover {
    box-shadow: 0 6px 14px 0 #666;
    transform: scale(1.1);
  }

</style>