<template>
  <div ref="app" id="visual-essay" :class="`visual-essay ${layout}`">
    <div v-if="headerEnabled" ref="header" class="header">
      <component v-bind:is="headerComponent"
        :height="headerHeight"
        :essay-config="essayConfig"
        :site-config="siteInfo"
        :is-authenticated="isAuthenticated"
        :read-only="readOnly"
        :href="href"
        :appVersion="appVersion"
        @collapse-header="collapseHeader"
        @menu-item-clicked="menuItemClicked"
        @logout="logout"
        @view-markdown="viewMarkdown"
        @edit-markdown="editMarkdown"
        @goto-github="gotoGithub"
        @open-docs-site="openDocsSite"
      ></component>
    </div>
    <div ref="essay" class="essay hidden">
      <component v-if="html" v-bind:is="contentComponent"
        :html="html"
        :layout="layout"
        :width="essayWidth"
        :height="essayHeight"
        :essay-config="essayConfig"
        :style-class="styleClass"
        :hover-item="hoverItemID"
        :selected-item="selectedItemID"
        :viewer-is-open="viewerIsOpen"
        :active-elements="activeElements"
        :all-items="allItems"
        :items-in-active-elements="itemsInActiveElements"
        :debug="debug"
        @set-viewer-is-open="viewerIsOpen = $event"
        @set-active-elements="setActiveElements"
        @set-hover-item="setHoverItem"
        @set-selected-item="setSelectedItem"
        @collapse-header="collapseHeader"
      ></component>
    </div>
    <div ref="viewer" class="viewer hidden">
      <component v-if="html && viewerIsOpen" v-bind:is="viewerComponent"
        :width="viewerWidth"
        :height="viewerHeight"
        :hover-item="hoverItemID"
        :selected-item="selectedItemID"
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
        @set-viewer-is-open="viewerIsOpen = $event"
        @set-hover-item="setHoverItem"
        @set-selected-item="setSelectedItem"
        @toggle-viewer="toggleOption('viewerIsOpen')"
      ></component>
    </div>
    <div v-if="footerEnabled && siteInfo" ref="footer" id="siteFooter" class="footer">
      <component :is="footerComponent" :site-config="siteInfo"></component>
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
        footerEnabled: true,
        footerHeight: 0,
        viewerHeight: 0,
        viewerWidth: 0,
        essayHeight: 0,
        essayWidth: 0,
        headerHeight: 400,
        headerMinHeight: 104,
        headerMaxHeight: 400,
        header: null,
        footer: null,
        lastTouchY: undefined,
        hoverItemID: null,
        selectedItemID: null,
        viewerIsOpen: false,
        essayBase: undefined,
        essayPath: undefined,
        essayFname: undefined,
        qargs: {},
        href: undefined,
        appVersion: 'APP_VERSION',
        externalWindow: undefined
      }),
      computed: {
        acct() { return this.$store.getters.siteInfo.acct },
        repo() { return this.$store.getters.siteInfo.repo },
        branch() { return this.$store.getters.siteInfo.branch },
        // path() { return `${this.$store.getters.mdPath}` },
        hash() { return `${this.$store.getters.hash}` },
        jwt() { return this.$store.getters.jwt },
        isAuthenticated() { return this.jwt !== null && this.jwt !== undefined },
        readOnly() { return this.qargs.readonly},
        allItems() { return this.$store.getters.items },
        html() { return this.$store.getters.essayHTML },
        components() { return Object.values(this.$store.getters.components) },
        // viewerIsOpen() { return this.$store.getters.viewerIsOpen },
        layout() { return this.$store.getters.layout },
        essayConfig() { return this.$store.getters.essayConfig || {} },
        siteInfo() { return this.$store.getters.siteInfo || {} },
        debug() { return this.$store.getters.debug },
        styleClass() { 
          return this.essayConfig && this.essayConfig.style
            ? this.essayConfig.style
            : this.layout === this.layout === 'vertical'
              ? 'essay-default'
              : ''
        },
        contentComponents() { return this.components.filter(compConf => compConf.type === 'content') },
        contentComponent() { 
          const found = this.contentComponents.find(c => c.layouts && c.layouts.indexOf(this.layout) >= 0)
          return found ? found.component :null
        },
        headerComponents() { return this.components.filter(compConf => compConf.type === 'header') },
        headerComponent() {
          const found = this.headerComponents.find(c => c.layouts && c.layouts.indexOf(this.layout) >= 0)
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
        // window.onpopstate = (e) => { this.loadEssay(e.state.file, true) }
        this.href = window.location.href
        this.essayBase = this.siteInfo.baseurl
        this.essayPath = window.location.pathname.length > this.essayBase.length
          ? window.location.pathname.slice(this.essayBase.length)
          : ''
        /*
        if (this.essayPath[this.essayPath.length-1] !== '/') {
          this.essayPath += '/'
          history.replaceState({file: `${this.essayBase}${this.essayPath}`}, '', `${this.essayBase}${this.essayPath}`)
        }
        */
        this.qargs = this.parseQueryString()
        console.log(`refQueryArg=${this.refQueryArg}`)
        console.log(`App: base=${this.essayBase} path=${this.essayPath}`, this.qargs, this.siteInfo, this.essayConfig)
        window.onpopstate = (e) => { this.setEssay(e.state.file, true) }
        this.setEssay(this.essayPath)
        this.init()
      },
      methods: {
        init() {
          this.viewerIsOpen = this.layout[0] === 'v'
          // console.log(`init: layout=${this.layout} touchDevice=${'ontouchstart' in window}`)
          this.waitForHeaderFooter() // header and footer are dynamically loaded external components        
        },
        setActiveElements(activeElements) {
          this.activeElements = activeElements
          this.itemsInActiveElements = itemsInElements(activeElements, this.allItems)
        },
        resizeHeader(e) {
          // console.log('resizeHeader')
          let delta
          if (e.touches) {
            delta = (e.touches[0].screenY - this.lastTouchY) / 5
          } else {
            delta = e.wheelDeltaY ? e.wheelDeltaY : -e.deltaY
          }
          const scrollDir = delta > 0 ? 'expand' : 'shrink'
          if ((scrollDir === 'shrink' && this.header.clientHeight > this.headerMinHeight) ||
              (scrollDir === 'expand' && this.header.clientHeight < this.headerMaxHeight && this.$refs.essay.scrollTop === 0)) {
            let newHeaderHeight = this.header.clientHeight + delta
            if (scrollDir === 'shrink' && newHeaderHeight < this.headerMinHeight) newHeaderHeight = this.headerMinHeight
            if (scrollDir === 'expand' && newHeaderHeight > this.headerMaxHeight) newHeaderHeight = this.headerMaxHeight
            this.header.style.height = `${newHeaderHeight}px`
            this.headerHeight = newHeaderHeight
            //e.preventDefault()
            e.stopPropagation()
          }
        },
        waitForHeaderFooter() {
          if (!this.header) {
            // this.header = document.querySelector(`#header.${this.layout === 'index' ? 'index' : 'essay'}`)
            this.header = document.querySelector(`#header`)
            if (this.header && this.$refs.essay) {
              if ('ontouchstart' in window) {
                this.header.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.$refs.essay.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.header.addEventListener('touchmove', this.resizeHeader )
                this.$refs.essay.addEventListener('touchmove', this.resizeHeader)
              } else {
                this.header.addEventListener('wheel', this.resizeHeader, {passive: true})
                this.$refs.essay.addEventListener('wheel', this.resizeHeader, {passive: true})
              }
            }
          }
          if (!this.footer) {
            this.footer = document.getElementById('footer')
            if (this.footer) {
              this.footerHeight = this.footer.clientHeight
            }
          }
          if (!this.header || !this.footer) setTimeout(this.waitForHeaderFooter, 250)
        },
        setHoverItem(itemID) {
          this.hoverItemID = itemID
        },
        setSelectedItem(itemID) {
          this.selectedItemID = itemID
        },
        toggleOption(option) {
          if (option === 'layout') this.setLayout(this.layout === 'vertical' ? 'horizontal' : 'vertical')
          if (option === 'viewerIsOpen') this.setViewerIsOpen(!this.viewerIsOpen)
          if (option === 'header') this.headerEnabled = !this.headerEnabled
          if (option === 'footer') this.footerEnabled = !this.footerEnabled
        },
        setLayout(layout) {
          this.$store.dispatch('setLayout', layout)
          this.setViewerIsOpen(layout === 'vertical')
        },
        setViewerIsOpen(isOpen) {
          this.$store.dispatch('setViewerIsOpen', isOpen)
        },
        collapseHeader() {
          this.header.style.height = `${this.headerMinHeight}px`
          this.headerHeight = this.headerMinHeight
        },
        async loadEssay(path, replace) {
          console.log(`loadEssay=${path} ${replace}`)
          const resp = await fetch(`https://exp.visual-essays.app/essay${this.essayBase}${path}${this.refQueryArg}`)
          let html = await resp.text()
          let browserPath = `${this.essayBase}${path}${this.refQueryArg}`
          if (replace) {
            history.replaceState({file: path || ''}, '', browserPath)
          } else {
            history.pushState({file: path || ''}, '', browserPath)
          }
          this.href = window.location.href
          const tmp = document.createElement('div')
          tmp.innerHTML = html
          window.data = []
          tmp.querySelectorAll('script[data-ve-tags]').forEach(scr => eval(scr.text))
          const essayElem = tmp.querySelector('#essay')
          this.essayFname = `${essayElem.dataset.name}.md`
          const leaf = essayElem.dataset.name.split('/').pop().replace('.md', '').toLowerCase()
          const isFolder = leaf === 'index' || leaf === 'readme'
          console.log(`name=${essayElem.dataset.name} isFolder=${isFolder}`)
          if (isFolder) {
            if (path[path.length-1] !== '/') {
              this.essayPath += '/'
              history.replaceState({file: `${this.essayBase}${this.essayPath}${this.refQueryArg}`}, '', `${this.essayBase}${this.essayPath}${this.refQueryArg}`)
            }
          } else {
            if (path[path.length-1] === '/') {
              this.essayPath = path.slice(0, path.length-1)
              history.replaceState({file: `${this.essayBase}${this.essayPath}${this.refQueryArg}`}, '', `${this.essayBase}${this.essayPath}${this.refQueryArg}`)
            }
          }

          const items = this.prepItems(window.data.filter(item => item.tag !== 'component'))
          
          const essayConfig = items.find(item => item.tag === 'config') || {}
          this.$store.dispatch('setEssayHTML', essayElem.innerHTML)
          this.$store.dispatch('setItems', items)
          this.$store.dispatch('setEssayConfig', essayConfig)
          const layout = essayConfig.layout
            ? essayConfig.layout[0] === 'v'
              ? 'vertical'
              : essayConfig.layout
            : 'horizontal'
          this.$store.dispatch('setLayout', layout)
          this.$nextTick(() => {this.convertLinks()})
        },
        reset() {
          this.$store.dispatch('setEssayHTML', null)
          this.$store.dispatch('setItems', [])
          this.$store.dispatch('setEssayConfig', null)
          this.setActiveElements([])
        },
        convertLinks() {
          this.$refs.essay.querySelectorAll('a').forEach(link => {
            console.log(link.href)
            if (!link.href || link.href.indexOf(window.location.host) > 0) {
              let target = link.dataset.target
              if (!target) { 
                const parsedUrl = this.parseUrl(link.href)
                console.log(parsedUrl)
                target = parsedUrl.pathname.slice(this.essayBase.length)
              }
              link.addEventListener('click', (e) => {
                let target = e.target
                while(!target.dataset.target && target.parentElement) {
                  target = target.parentElement
                }
                console.log('click', target.dataset.target)
                // this.essayPath = target.dataset.target
                this.setEssay(target.dataset.target)
              })
              link.removeAttribute('href')
              link.setAttribute('data-target', target)
            } else {
              link.innerHTML += '<sup><i class="fal fa-external-link-alt" style="margin-left:4px;font-size:0.8em;color:blue;"></i></sup>'
              link.setAttribute('target', '_blank')
            }
          })
        },
        menuItemClicked(path) {
          console.log('menuItemClicked', path)
          this.setEssay(path)
        },
        logout() {
          console.log('logout')
        },
        viewMarkdown() {
          
          this.openWindow(`/markdown-viewer/${this.siteInfo.acct}/${this.siteInfo.repo}/${this.ref}${this.essayBase}${this.essayFname}`)
        },
        editMarkdown(editor) {
          this.openWindow(editor == 'custom'
            ? `https://editor.visual-essays.app/${this.siteInfo.acct}/${this.siteInfo.repo}${this.essayBase}${this.essayFname}`
            : `https://github.com/${this.siteInfo.acct}/${this.siteInfo.repo}/edit/${this.siteInfo.editBranch}${this.essayBase}${this.essayFname}`
          ) 
        },
        gotoGithub() {
          this.openWindow(`https://github.com/${this.siteInfo.acct}/${this.siteInfo.repo}/tree/${this.ref}`, null)
        },
        openDocsSite() {
          this.openWindow(`https://docs.visual-essays.app?readonly`, `toolbar=yes,location=yes,left=0,top=0,width=1000,height=1200,scrollbars=yes,status=yes`)
        },
        openWindow(url, options) {
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
          this.essayPath = path
          this.fadeOut(this.$refs.essay)
          this.fadeOut(this.$refs.viewer)
          this.reset()
          this.$nextTick(() => {
            this.loadEssay(path, replace)
            this.fadeIn(this.$refs.essay)
            this.fadeIn(this.$refs.viewer)
          })
        }
      },
      updated() {
        this.viewerHeight = this.$refs.app.clientHeight - this.$refs.header.clientHeight - this.$refs.footer.clientHeight
        if (this.$refs.essay) this.viewerWidth = this.$refs.essay.clientWidth
      },
      watch: {
        /*
        essayPath: {
          handler: function (path) {
            // console.log(`essayPath=${path}`)
            // if (path) this.setEssay(path)
          },
          immediate: true
        },
        */
        essayConfig: {
          handler: function (essayConfig) {
            console.log('essayConfig', essayConfig)
          },
          immediate: true
        },
        layout: {
          handler: function (layout) {
            this.viewerIsOpen = layout[0] === 'v'
          },
          immediate: true
        }
      }
}
</script>

<style scoped>

  #visual-essay {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto auto;
    grid-template-areas: 
      "header"
      "essay"
      "viewer"
      "footer";
    height: 100vh;
    width: 100vw;
  }
  #visual-essay.vertical {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr auto;
    grid-template-areas: 
      "header header"
      "essay  viewer"
      "footer footer";
    position: absolute;
  }
  .header {
    grid-area: header;
  }
  .essay {
    grid-area: essay;
    overflow-y: auto;
  }
  .viewer {
    grid-area: viewer;
    justify-self: stretch;
  }
  .footer {
    grid-area: footer;
  }

  #visual-essay.index .essay,
  #visual-essay.horizontal .essay {
    padding: 2em;
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
</style>
