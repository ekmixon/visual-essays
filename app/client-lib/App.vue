<template>
  <div ref="app" id="visual-essay" :class="`visual-essay ${layout} ${isEmbedded ? 'embedded' : ''}`">
    <div v-if="headerEnabled" ref="header" class="header">
      <component v-bind:is="headerComponent"
        :height="headerHeight"
        :essay-config="essayConfig"
        @toggle-option="toggleOption"
        @collapse-header="collapseHeader"
      ></component>
    </div>
    <div ref="essay" id="scrollableContent" class="essay">
      <component v-bind:is="contentComponent"
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
    <div ref="viewer" class="viewer">
      <component v-bind:is="viewerComponent"
        :width="viewerWidth"
        :height="viewerHeight"
        :hover-item="hoverItemID"
        :selected-item="selectedItemID"
        :acct="acct"
        :repo="repo"
        :branch="branch"
        :path="path"
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
        headerEnabled: false,
        footerEnabled: false,
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
        viewerIsOpen: true
      }),
      computed: {
        acct() { return this.$store.getters.acct },
        repo() { return this.$store.getters.repo },
        branch() { return this.$store.getters.branch },
        path() { return `${this.$store.getters.mdPath}` },
        hash() { return `${this.$store.getters.hash}` },
        jwt() { return this.$store.getters.jwt },
        allItems() { return this.$store.getters.items },
        html() { return this.$store.getters.essayHTML },
        components() { return Object.values(this.$store.getters.components) },
        // viewerIsOpen() { return this.$store.getters.viewerIsOpen },
        isEmbedded() { return !this.$store.getters.showBanner },
        layout() { return this.$store.getters.layout },
        essayConfig() { return this.$store.getters.essayConfig || {} },
        siteInfo() { return this.$store.getters.siteInfo || {} },
        debug() { return this.$store.getters.debug },
        pageTitle() { return this.essayConfig.title || this.$store.getters.siteTitle },
        styleClass() { 
          return this.essayConfig && this.essayConfig.style
            ? this.essayConfig.style
            : this.layout === 'horizontal' || this.layout === 'vertical'
              ? 'essay-default'
              : ''
        },

        contentComponents() { return this.components.filter(compConf => compConf.type === 'content') },
        contentComponent() { 
          const found = this.contentComponents.find(c => c.layouts && c.layouts.indexOf(this.layout) >= 0)
          return found ? found.component : 'essay'
        },
        headerComponents() { return this.components.filter(compConf => compConf.type === 'header') },
        headerComponent() {
          const found = this.headerComponents.find(c => c.layouts && c.layouts.indexOf(this.layout) >= 0)
          return found ? found.component : 'essayHeader'
        },
        footerComponent() {
          const found = this.components.find(c => c.name === 'siteFooter')
          return found ? found.component : 'siteFooter'
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
        groups() { return groupItems(itemsInElements(elemIdPath(this.activeElement), this.allItems), this.$store.getters.componentSelectors) },
      },
      mounted() {
        // this.headerEnabled = this.footerEnabled = !this.isEmbedded
        this.headerEnabled = this.footerEnabled = true
        this.init()
      },
      methods: {
        init() {
          // this.viewerIsOpen = this.layout[0] === 'v'
          this.viewerIsOpen = false
          console.log(`App: ${this.acct}/${this.repo}/${this.branch}${this.path} layout=${this.layout} viewerIsOpen=${this.viewerIsOpen}`)
          console.log(`init: layout=${this.layout} touchDevice=${'ontouchstart' in window}`)
          window.addEventListener('resize', this.doLayout)
          this.waitForHeaderFooter() // header and footer are dynamically loaded external components
          this.doLayout(true)
        
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
            this.doLayout()
            //e.preventDefault()
            e.stopPropagation()
          }
        },
        waitForHeaderFooter() {
          if (!this.header) {
            // this.header = document.querySelector(`#header.${this.layout === 'index' ? 'index' : 'essay'}`)
            this.header = document.querySelector(`#header`)
            if (this.header) {
              if ('ontouchstart' in window) {
                this.header.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.$refs.essay.addEventListener('touchstart', (e) => { this.lastTouchY = e.touches[0].screenY })
                this.header.addEventListener('touchmove', this.resizeHeader )
                this.$refs.essay.addEventListener('touchmove', this.resizeHeader)
              } else {
                this.header.addEventListener('wheel', this.resizeHeader, {passive: true})
                this.$refs.essay.addEventListener('wheel', this.resizeHeader, {passive: true})
              }
              this.doLayout()
            }
          }
          if (!this.footer) {
            this.footer = document.getElementById('footer')
            if (this.footer) {
              this.footerHeight = this.footer.clientHeight
              this.doLayout()
            }
          }
          if (!this.header || !this.footer) setTimeout(this.waitForHeaderFooter, 250)
        },
        doLayout(init) { // eslint-disable-line no-unused-vars
          /*
          const container = document.getElementById('content')
          // const viewer = this.$refs.viewer
          const viewer = null
          const essay = this.$refs.essay
          if (this.header && (init || this.header.clientHeight === 0)) {
            this.header.style.height = this.header.maxHeight
            this.header.style.display = null
          }
          const headerHeight = this.header ? this.header.clientHeight : 0
          const footerHeight = this.footer ? this.footer.clientHeight : 0
          const contentHeight = this.isEmbedded
            ? container ? container.clientHeight : 100
            // ? this.$refs.app.clientHeight
            : this.$refs.app.clientHeight - headerHeight - footerHeight
          if (viewer) {
            if (this.layout === 'vertical') {
              if (!this.viewerIsOpen) this.setViewerIsOpen(true)
              essay.style.height = `${contentHeight}px`
              viewer.style.height = `${contentHeight}px`
              viewer.style.width = `${this.$refs.app.clientWidth/2}px`
            } else {
              essay.style.height = this.viewerIsOpen ? `${(contentHeight)/2}px` : `${contentHeight}px`
              viewer.style.width = `${this.$refs.app.clientWidth}px`
            }
            viewer.style.display = this.viewerIsOpen ? null : 'none'
            this.$nextTick(() => {
              this.viewerHeight = viewer.clientHeight
              this.viewerWidth = viewer.clientWidth
              this.essayHeight = essay.clientHeight
              this.essayWidth = essay.clientWidth
              // console.log(`doLayout: layout=${this.layout} container=${container ? container.clientHeight : 100} header=${[this.headerEnabled,headerHeight]} footer=${[this.footerEnabled,footerHeight]} content=${contentHeight} viewerIsOpen=${this.viewerIsOpen} viewer=${[viewer.clientWidth,viewer.clientHeight]} essay=${[essay.clientWidth,essay.clientHeight]}`)
            })
          }
          */
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
          this.doLayout()
        }
      },
      watch: {
        // viewerHeight() { console.log(`App: height=${this.viewerHeight} width=${this.viewerWidth}`) },
        // viewerWidth() { console.log(`App: height=${this.viewerHeight} width=${this.viewerWidth}`) },
        layout() { this.doLayout() },
        viewerIsOpen() { this.doLayout() },
        headerEnabled() { this.doLayout() },
        footerEnabled() { this.doLayout() },
        pageTitle: {
          handler: function (title) {
            console.log(`Setting title="${title}"`)
            if (title) {
              document.title = title
            }
          },
          immediate: true
        }
      }
}
</script>

<style scoped>

  [v-cloak] { display: none; }

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
    display: none;
  }
  .footer {
    grid-area: footer;
  }

  .default, .essay {
    padding: 2em;
  }

</style>

<style>

  html {
    -webkit-text-size-adjust: 100%;
        -ms-text-size-adjust: 100%;
  }

  body {
    margin: 0;
    background-color: white;
    color: #444;
  }

  #visual-essay {
    margin: 0;
    font-family: Roboto, sans-serif;
    font-size: 1.3rem;
    scroll-behavior: smooth;
    color: #000;
  }

  #visual-essay.default {
    /* margin: 0 3rem; */
  }

  article,
  aside,
  details,
  figcaption,
  figure,
  footer,
  header,
  hgroup,
  nav,
  section,
  summary {
    display: block;
  }

  h1, h2, h3, h4, h5, h6, figure { content: ""; display: table; clear: both; }
  br { clear: both; }

  ::-moz-selection {
    background-color: hsla(0,0%,0%,.5);
    color: #fff;
    text-shadow: none;
  }
  ::selection {
    background-color: hsla(0,0%,0%,.5);
    color: #fff;
    text-shadow: none;
  }
  a {
    color: #2156d2;
  }
  a:focus {
    outline: thin dotted;
  }
  a:active,
  a:hover {
    outline: 0;
    cursor: pointer;
    color: #193d85;
  }
  strong {
    font-weight: bold;
  }
  mark {
    background: #ff6;
    color: #444;
  }
  code,
  pre {
    font-family: monospace, serif;
    font-size: 1em;
  }
  pre {
    white-space: pre;
  }
  img {
    border: 0;
    max-width: 100%;
    vertical-align: top;
  }

  button,
  input,
  select,
  textarea {
    font-family: inherit;
    font-size: 100%;
    margin: 0;
  }
  button,
  input {
    line-height: normal;
  }
  button,
  html input[type="button"],
  input[type="reset"],
  input[type="submit"] {
    cursor: pointer;
    -webkit-appearance: button;
  }
  input[type="checkbox"],
  input[type="radio"] {
    box-sizing: border-box;
    padding: 0;
  }
  button::-moz-focus-inner,
  input::-moz-focus-inner {
    border: 0;
    padding: 0;
  }
  textarea {
    overflow: auto;
    vertical-align: top;
  }
  table {
    border-collapse: collapse;
    border-spacing: 0;
  }

  p {
    margin: 1rem 0;
    line-height: 1.5;
    -webkit-hyphens: none;
       -moz-hyphens: none;
        -ms-hyphens: none;
            hyphens: none;
  }

  h1,
  h2,
  h3,
  h4,
  h5
  h6 {
    font-weight: bold;
    line-height: 1;
    margin: 0.6em 2rem 0.6em 0;
    display: inline-block;
  }

  h1 {
    font-size: 2.5rem;
  }
  h2 {
    font-size: 2rem;
  }
  h3 {
    font-size: 1.5rem;
  }
  h4 {
    font-size: 1.25rem;
  }
  h5 {
    font-size: 1.25rem;
  }
  h6 {
    font-size: 1.25rem;
  }

  blockquote {
    margin: 0 4em 0 2em;
    border-left: 6px solid #ddd;
    text-align: justify;
    -webkit-hyphens: none;
        -moz-hyphens: none;
        -ms-hyphens: none;
            hyphens: none;
  }
  blockquote p {
    margin-left: 16px;
    line-height: 1.4em !important;
    font-size: 1em;
    font-style: italic;
  }
  p a:link,
  p a:visited {
    /*
    border-bottom: 2px solid #6af;
    color: #444;
    padding-bottom: 1px;
    */
    text-decoration: none;
    -webkit-transition: .25s;
        -moz-transition: .25s;
        -ms-transition: .25s;
          -o-transition: .25s;
            transition: .25s;
  }
  p a:hover,
  p a:focus {
    color: #193d85;
  }
  p a:active {
    position: relative;
    top: 1px;
    -webkit-transition: none;
        -moz-transition: none;
        -ms-transition: none;
          -o-transition: none;
            transition: none;
  }
  dl,
  ol,
  ul {
    font-size: 1em;
    margin: 0 2rem 0 0;
    padding-left: 1.5rem;
  }
  dd,
  dt,
  li {
    line-height: 2em;
    padding-left: 0.2em;
    margin: 0;
  }

  section:after {
    content: "";
    display: table;
    clear: both;
  }

  .dropshadow {
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
  }
  
  .border {
    border:1px solid #aaa;
  }
  
  .thumbimage, .thumbnail {
    border: 1px solid #ccc;
    /*
    width: 150px;
    height: 150px;
    object-fit: cover;
    */
  }

  .thumbcaption {
    margin-top: 6px;
    margin-bottom: 18px;
    font-weight: bold;
    text-align: center;
  }

  figure {
    max-width: 40%;
    font-weight: bold;
    font-size: 1.0rem;
    text-align: center;
    margin: 0 12px 12px 0;
  }
        
  figcaption {
    padding: 6px;
    line-height: 1.1rem;
    font-size: 1.2em;
  }

  .left { 
    float: left !important;
    margin: 8px 18px 0 0 !important;
  }

  .right {
    float: right !important;
    margin: 8px 0 0 18px !important;
  }

  .border {
    border: 1px solid #aaa;
  }

.highlight .hll { background-color: #ffffcc }
.highlight  { background: #f8f8f8; }
.highlight .c { color: #408080; font-style: italic } /* Comment */
.highlight .err { border: 1px solid #FF0000 } /* Error */
.highlight .k { color: #008000; font-weight: bold } /* Keyword */
.highlight .o { color: #666666 } /* Operator */
.highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
.highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
.highlight .cp { color: #BC7A00 } /* Comment.Preproc */
.highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
.highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
.highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
.highlight .gd { color: #A00000 } /* Generic.Deleted */
.highlight .ge { font-style: italic } /* Generic.Emph */
.highlight .gr { color: #FF0000 } /* Generic.Error */
.highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.highlight .gi { color: #00A000 } /* Generic.Inserted */
.highlight .go { color: #888888 } /* Generic.Output */
.highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.highlight .gs { font-weight: bold } /* Generic.Strong */
.highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.highlight .gt { color: #0044DD } /* Generic.Traceback */
.highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.highlight .kp { color: #008000 } /* Keyword.Pseudo */
.highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.highlight .kt { color: #B00040 } /* Keyword.Type */
.highlight .m { color: #666666 } /* Literal.Number */
.highlight .s { color: #BA2121 } /* Literal.String */
.highlight .na { color: #7D9029 } /* Name.Attribute */
.highlight .nb { color: #008000 } /* Name.Builtin */
.highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
.highlight .no { color: #880000 } /* Name.Constant */
.highlight .nd { color: #AA22FF } /* Name.Decorator */
.highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
.highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
.highlight .nf { color: #0000FF } /* Name.Function */
.highlight .nl { color: #A0A000 } /* Name.Label */
.highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
.highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
.highlight .nv { color: #19177C } /* Name.Variable */
.highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
.highlight .w { color: #bbbbbb } /* Text.Whitespace */
.highlight .mb { color: #666666 } /* Literal.Number.Bin */
.highlight .mf { color: #666666 } /* Literal.Number.Float */
.highlight .mh { color: #666666 } /* Literal.Number.Hex */
.highlight .mi { color: #666666 } /* Literal.Number.Integer */
.highlight .mo { color: #666666 } /* Literal.Number.Oct */
.highlight .sa { color: #BA2121 } /* Literal.String.Affix */
.highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
.highlight .sc { color: #BA2121 } /* Literal.String.Char */
.highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
.highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.highlight .s2 { color: #BA2121 } /* Literal.String.Double */
.highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
.highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
.highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
.highlight .sx { color: #008000 } /* Literal.String.Other */
.highlight .sr { color: #BB6688 } /* Literal.String.Regex */
.highlight .s1 { color: #BA2121 } /* Literal.String.Single */
.highlight .ss { color: #19177C } /* Literal.String.Symbol */
.highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
.highlight .fm { color: #0000FF } /* Name.Function.Magic */
.highlight .vc { color: #19177C } /* Name.Variable.Class */
.highlight .vg { color: #19177C } /* Name.Variable.Global */
.highlight .vi { color: #19177C } /* Name.Variable.Instance */
.highlight .vm { color: #19177C } /* Name.Variable.Magic */
.highlight .il { color: #666666 } /* Literal.Number.Integer.Long */
</style>