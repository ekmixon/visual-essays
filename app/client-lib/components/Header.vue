<template>
  <div ref="header" id="header" class="header" :style="`height:${height}; background-image: url(${banner})`">
    <nav>
      <div id="menuToggle">
        <input type="checkbox" />
        <span></span>
        <span></span>
        <span></span>
        <ul id="menu">
          <li @click="nav('/')">
            <i :class="`fas fa-home`"></i>Home
          </li>
          <template v-for="item in siteConfig.nav">
            <li :key="item.path" @click="nav(item.path)">
              <i :class="`fas fa-${item.icon}`"></i>{{item.label}}
            </li>
          </template>
          <li v-if="siteConfig.repo !== 've-docs'" @click="openDocsSite">
            <i :class="`fas fa-question`"></i>Documentation
          </li>
          <li v-if="!readOnly">
            <a v-if="isAuthenticated" @click="logout">
              <i :class="`fas fa-user`"></i>Logout
            </a>
            <a v-else :href="`https://visual-essays.app/login?redirect=${loginRedirect}`">
              <i :class="`fas fa-user`"></i>Login
            </a>
          </li>
          <hr>
          <li style="margin-top:10px;" @click="viewMarkdown">
            <i class="fas fa-file-code"></i>View page markdown
          </li>
          <li v-if="isAuthenticated && !readOnly" @click="editMarkdown('default')">
            <i class="fas fa-edit"></i>Edit page
          </li>
          <!--
          <li v-if="isAuthenticated && !readOnly" @click="editMarkdown('custom')">
            <i class="fas fa-edit"></i>Edit page (Custom)
          </li>
          -->
          <li v-if="isAuthenticated && !readOnly" @click="gotoGithub">
            <i class="fab fa-github"></i>Github repository
          </li>
          <li style="margin-top:10px; padding:0;">
            <div class="app-version">App: {{appVersion}}</div>
          </li>
          <li style="padding:0;">
            <div class="app-version">Content: {{contentRef}}</div>
          </li>
        </ul>
      </div>
    </nav>

    <div class="title-bar">
      <div class="metadata-group">
        <div class="title" v-html="title"></div>
        <div class="author" v-html="author"></div>
      </div>
      <div class="essay-action-group">
        <div v-if="essayQid" class="citation" @click="$modal.show('citation-modal')">
          <i class="fas fa-sm fa-quote-left"></i> Cite this essay</div>
        <div v-if="aboutQid" class="search" @click="openSearchTool">
          <i class="fas fa-sm fa-search"></i> More resources</div>
      </div>
    </div>

    <modal 
      class="modal"
      name="citation-modal" 
      height="auto" 
      width="600px"
      :draggable="true"
      @opened="initTippy"
    >

      <div>
        <div class="entity-infobox" id="cite-modal" title="Citation saved to clipboard">
          <div class="dialog-header">
            <button class="close-button" @click="$modal.hide('citation-modal')">
              <i class="fal fa-times"></i>
            </button>
            <h3 class="entity-title">Cite this essay</h3>
          </div>


          <div class="subtitle">MLA</div>
          <div class="citation-wrapper">
            <div class="citation-text" @click="copyTextToClipboard" v-html="mlaCitation"></div>
            <div class="copy-citation" @click="copyCitationToClipboard(`${mlaCitation}`)" title="Copy to clipboard">Copy</div>
          </div>
          
          <div class="subtitle">APA</div>
          <div class="citation-wrapper">
            <div class="citation-text" @click="copyTextToClipboard" v-html="apaCitation"></div>
            <div class="copy-citation" @click="copyCitationToClipboard(`${apaCitation}`)" title="Copy to clipboard">Copy</div>
          </div>

          <div class="subtitle">Chicago</div>
          <div class="citation-wrapper">
            <div class="citation-text" @click="copyTextToClipboard" v-html="chicagoCitation"></div>
            <div class="copy-citation" @click="copyCitationToClipboard(`${chicagoCitation}`)" title="Copy to clipboard">Copy</div>
          </div>

        </div>
      </div>
  </modal>

  </div>
</template>

<script>

  module.exports = {
    name: 'Header',
    props: {
      //eid: { type: String, default: undefined },
      essayConfig: { type: Object, default: function(){ return {}} },
      siteConfig: { type: Object, default: function(){ return {}} },
      progress: { type: Number, default: 0 },
      height: Number, // initial height
      appVersion: { type: String },
      contentRef: { type: String },
      isAuthenticated: { type: Boolean, default: false },
      readOnly: { type: Boolean, default: false },
      href: { type: String, default: '' }
    },    
    data: () => ({
      headerWidth: null,
      headerHeight: null,
      observer: null,
      requested: new Set(),
      entityInfo: undefined,
      mla: undefined,
      apa: undefined,
      chicago: undefined,
      tippy: null
    }),
    computed: {
      essayQid() { return this.essayConfigLoaded ? this.essayConfig.qid || this.essayConfig.eid : null },
      aboutQid() { return this.essayConfig.loaded ? this.essayConfig.about : null },
      essayConfigLoaded() { return this.essayConfig !== null },
      banner() { return this.essayConfigLoaded ? (this.essayConfig.banner || this.siteConfig.banner) : null },
      bannerHeight() { return this.essayConfig && this.essayConfig.bannerHeight || this.siteConfig.bannerHeight || 400 },
      title() { return this.essayConfigLoaded ? (this.essayConfig.title || this.siteConfig.title) : null },
      author() { return (this.essayConfigLoaded && this.essayConfig.author) || '&nbsp;' },
      numMaps() { return (this.essayConfigLoaded && this.essayConfig['num-maps']) },
      numImages() { return (this.essayConfigLoaded && this.essayConfig['num-images']) },
      numSpecimens() { return (this.essayConfigLoaded && this.essayConfig['num-specimens']) },
      numPrimarySources() { return (this.essayConfigLoaded && this.essayConfig['num-primary-sources']) },
      hasStats() { return this.numMaps || this.numImages || this.numSpecimens || this.numPrimarySources },
      loginRedirect() { return encodeURIComponent(this.href.split('/').length === 3
        ? `${this.href}/`
        : this.href.split('/').length > 4 && this.href.split('/').pop() === ''
          ? this.href.slice(0,this.href.length-1)
          : this.href)
      },
      entity () { return this.$store.getters.items.find(entity => this.essayConfig.qid === entity.eid || this.essayConfig.qid === entity.id) || {} },
      //apiBaseURL() { return window.location.origin }
      apiBaseURL() { return 'https://visual-essays.app'},

      mlaCitation() { return this.mla },
      apaCitation() { return this.apa },
      chicagoCitation() { return this.chicago },

    },
    mounted() {
      // console.log(`${this.$options.name}.mounted: height=${this.height}`, this.siteConfig, this.essayConfig)
      // console.log(`href=${this.href} appVersion=${this.appVersion} ref=${this.contentRef} isAuthenticated=${this.isAuthenticated}`)
      
      this.getClaimsInfo()

      // set initial height
      this.$refs.header.style.height = `${this.height}px`
      const header = this.$refs.header,
            headerSize = header.getBoundingClientRect()
      this.headerWidth = `${Math.trunc(headerSize.width)}px`
      this.headerHeight = `${Math.trunc(headerSize.height)}px`

      // initialize a header size observer
      this.initObserver()

    },
    methods: {
      initObserver() {
        const header = this.$refs.header, vm = this, config = { attributes: true }

        // create the observer
        const observer = new MutationObserver(function (mutations) {
          mutations.forEach(function (mutation) {
            // check if the mutation is attributes and update the width and height data if it is.
            if (mutation.type === 'attributes') {
              let { width, height } = header.style
              vm.headerWidth = width
              vm.headerHeight = height
            }
          })
        })

        // observe element's specified mutations
        observer.observe(header, config)

        // add the observer to data so we can disconnect it later
        this.observer = observer
      },
      closeDrawer() {
        document.querySelector('#menuToggle input').checked = false
      },
      nav(item) {
        this.closeDrawer()
        // console.log(`menuItemClicked=${item}`)
        this.$emit('menu-item-clicked', item)
      },
      logout(e) {
        e.preventDefault()
        this.closeDrawer()
        this.$emit('logout')
      },
      toggleOption(option) {
        this.closeDrawer()
        this.$emit('toggle-option', option)
      },
      collapseHeader() {
        this.closeDrawer()
        this.$emit('collapse-header')
      },
      viewMarkdown() {
        this.closeDrawer()
        this.$emit('view-markdown')
      },
      editMarkdown(editor) {
        this.closeDrawer()
        this.$emit('edit-markdown', editor)
      },
      gotoGithub() {
        this.closeDrawer()
        this.$emit('goto-github')
      },
      openDocsSite() {
        this.closeDrawer()
        this.$emit('open-docs-site')
      },
      openInfoboxModal() {
        this.closeDrawer()
        this.$emit('open-infobox-modal')
      },
      openSearchTool() {
        console.log('open search tool', this.aboutQid);
        this.$emit('open-search-tool', this.aboutQid)
      },
      toQueryString(args) {
        const parts = []
        Object.keys(args).forEach((key) => {
          parts.push(`${key}=${encodeURIComponent(args[key])}`)
        })
        return parts.join('&')
      },
      initTippy() {
        if (!this.tippy) {
          new this.$tippy(document.querySelectorAll('.copy-citation'), {
            animation:'scale',
            trigger:'click',
            // theme: 'light-border',
            content: 'Citation saved to clipboard',
            onShow: (instance) => {
              setTimeout(() => { instance.hide() }, 2000) 
            }
          })
        }
      },
      getEntity() {
        let url = `${this.apiBaseURL}/entity/${encodeURIComponent(this.essayQid)}`
        const args = {}
        if (this.context) args.context = this.context
        if (this.entity.article) args.article = this.entity.article
        if (Object.keys(args).length > 0) {
          url += `?${this.toQueryString(args)}`
        }
        console.log(`getEntity=${url}`)
        return fetch(url).then(resp => resp.json())
        //console.log('resp', resp)
      },
      getClaimsInfo() {
        // console.log('getSummaryInfo', this.essayConfig.qid)
        this.getEntity()
          .then((data) => {
            if (data['claims']){
              console.log('claims info', data['claims'])
              this.claimsInfo = data['claims']
              this.formatCitations()
            }
          })
      },
      formatCitations(){
        let author = this.claimsInfo['author name string'][0]['value']
        let title = this.claimsInfo['title'][0]['value']['text']
        let sponsor = this.claimsInfo['sponsor'][0]['value']['value']
        let publish_date = '2021'
        let access_date = new Date()
        let url = this.claimsInfo['full work available at'][0]['value']
        //mla        
        this.mla = author.split(' ').pop() + ', ' + author.split(' ')[0] + '. <i>'+title+'</i>. ' + sponsor + ', ' + publish_date + '. '
        this.mla += url + '. Accessed ' + access_date.getDate() + ' ' + access_date.toLocaleString('default', { month: 'short' }) + '. ' + access_date.getFullYear()+ '.' 

        //apa
        this.apa = author.split(' ').pop() + ', ' + author.split(' ')[0].charAt(0) + '. ('+ publish_date + '). ' + '<i>'+title+'</i>. ' + sponsor + '.'

        //chicago
        this.chicago = author.split(' ').pop() + ', ' + author.split(' ')[0] + '. <i>'+title+'</i>. ' + sponsor + ', '
        this.chicago += publish_date + '. Accessed ' + access_date.toLocaleString('default', { month: 'long' }) + ' ' + access_date.getDate() + ', ' + access_date.getFullYear()+ '.'
      },
      copyTextToClipboard(e) {
        console.log('clicked!', e.target.textContent)
        if (navigator.clipboard) navigator.clipboard.writeText(e.target.textContent)
      },
      copyCitationToClipboard(citation) {
        console.log('clicked!', 'citation', citation)
        if (navigator.clipboard){
          navigator.clipboard.writeText(citation)
          // alert("Copied to clipboard!");
        }
      },
    },

    beforeDestroy() {
      if (this.observer) this.observer.disconnect()
    },
    watch: {
      essayConfigLoaded: {
        handler: function () {
          console.log('essayConfigLoaded')
        },
        immediate: true
      },
    }
  }
</script>

<style scoped>

  [v-cloak] { display: none; }

  body {
    margin: 0;
    padding: 0;
    background-color: white;
    color: #444;
  }

  .header {
    font-family: Roboto, sans-serif;
    font-size: 1rem;
    min-height: 100px;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: cover;
    position: relative;
    margin: 0;
    color: rgba(0, 0, 0, 0.97);
  }

  .title-bar {
    display: grid;
    grid-template-columns: auto 200px 100px;
    color: white;
    background-color: rgba(0, 0, 0, .6);
    /*padding: 24px 0 0 70px;*/
    position: absolute;
    top: calc(100% - 100px);
    height:100px;
    width: 100%;
    font-weight: bold;    
  }

  .metadata-group {
    grid-column-start: 1;
  }

  .essay-action-group {
    grid-column-start: 2;
    padding: 10px 0;
  }

  .title {
    font-size: min(3vw, 2.2em);
    margin-left: 24px;
    padding-top: 16px;
  }
  .author {
    font-size: min(3vw, 1.3em);
    margin-left: 24px;
    font-weight: normal;
  }
  .citation {
    margin-left: auto;
    margin-right: 1.3vw;
    font-size: 14px;
    color: white;
    background-color: #219653;
    border-radius: 4px;
    padding: 8px 24px 4px;
    font-weight: normal;
    height: 21px;
    cursor: pointer;
  }
  .search {
    margin-left: auto;
    margin-right: 1.3vw;
    margin-top: 0.6vh;
    font-size: 14px;
    color: white;
    background-color: #219653;
    border-radius: 4px;
    padding: 8px 20px 4px;
    font-weight: normal;
    height: 21px;
    cursor: pointer;
  }

  .citation .fa-sm {
    margin-bottom: 1px;
  }

  #menuToggle {
    display: block;
    position: absolute;
    top: 30px;
    right: 30px;
    margin-left: 30px;
    z-index: 1;
    -webkit-user-select: none;
    user-select: none;
  }

  #menuToggle a {
    text-decoration: none;
    color: #232323;
    transition: color 0.3s ease;
  }

  #menuToggle a:hover {
    color: tomato;
  }

  #menuToggle input {
    display: block;
    width: 40px;
    height: 32px;
    position: absolute;
    top: -7px;
    left: -5px;
    cursor: pointer;
    opacity: 0; /* hide this */
    z-index: 2; /* and place it over the hamburger */
    -webkit-touch-callout: none;
  }

  /*
  * Just a quick hamburger
  */
  #menuToggle span {
    display: block;
    width: 30px;
    height: 4px;
    margin-bottom: 4px;
    position: relative;
    background: #ffffff;
    border-radius: 3px;
    z-index: 1;
    transform-origin: 4px 0px;
    transition: transform 0.5s cubic-bezier(0.77,0.2,0.05,1.0),
                background 0.5s cubic-bezier(0.77,0.2,0.05,1.0),
                opacity 0.55s ease;
  }

  #menuToggle span:first-child {
    transform-origin: 0% 0%;
  }

  #menuToggle span:nth-last-child(2) {
    transform-origin: 0% 100%;
  }

  /* 
  * Transform all the slices of hamburger
  * into a crossmark.
  */
  #menuToggle input:checked ~ span {
    opacity: 1;
    transform: rotate(45deg) translate(-2px, -1px);
    background: #232323;
  }

  /*
  * But let's hide the middle one.
  */
  #menuToggle input:checked ~ span:nth-last-child(3) {
    opacity: 0;
    transform: rotate(0deg) scale(0.2, 0.2);
  }

  /*
  * Ohyeah and the last one should go the other direction
  */
  #menuToggle input:checked ~ span:nth-last-child(2) {
    transform: rotate(-45deg) translate(0, -1px);
  }

  /*
  * Make this absolute positioned
  * at the top right of the screen
  */
  #menu {
    display: none;
    position: absolute;
    width: 200px;
    margin: -118px 0 0 -160px;
    padding: 120px 10px 10px 10px;
    background: #ededed;
    list-style-type: none;
    -webkit-font-smoothing: antialiased;
    /* to stop flickering of text in safari */
    transform-origin: 0% 0%;
    transform: translate(100%, 0);
    transition: transform 0.5s cubic-bezier(0.77,0.2,0.05,1.0);
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
  }

  #menu li {
    display: flex;
    /* padding: 0.5em 0; */
    font-size: 1em;
  }

  #menu li:hover {
    cursor: pointer;
    color: #1976d2;
  }

  #menu li svg {
    min-width: 1.5em;
    margin-right: 10px;
    margin-top: 6px;
    /* font-weight: bold; */
    font-size: 1em;
  }

  /*
  * And let's slide it in from the left
  */
  #menuToggle input:checked ~ ul {
    display: block;
    transform: none;
  }

  .app-version {
    font-size: 0.9rem;
  }

  .subtitle {
    font-size: 1.1rem;
    font-weight: bold;
  }

  .citation-wrapper {
    margin-top: 16px;
    margin-bottom: 32px;
    line-height: 1.3;
    max-height: 380px;
    display: flex;
    font-size: 1.1rem;
    overflow:auto
  }

  .citation-text {
    float: left;
    padding: 10px;
    border: 1px solid #626262;
    cursor: pointer;
  }

  .copy-citation {
    float: left;
    color: white;
    background-color: #219653;
    border-radius: 4px;
    padding: 12px;
    height: 20px;
    margin-left: 10px;
    cursor: pointer;
  }

  .entity-infobox {
    color: black;
    align-items: left;
    margin: 1.5rem;
  }

  .entity-infobox .v-card__text {
    height: 100%;
    min-height: 165px;
    padding-bottom: 0 !important;
  }

  .dialog-header {
    margin-bottom: 2rem;
  }

  .close-button {
    float: right;
  }

  .entity-title {
    display: inline !important;
    margin: unset;
    font-size: 1.5em;
    font-weight: normal;
    font-family: 'Playfair Display', Serif;
  }

  .tippy-content {
    font-family: Roboto !important;
  }

  @media (max-width: 1000px){
    .citation, .search {
      display: none ;
    }
    .title-bar {
      grid-template-columns: auto 100px;
    }
    .title {
      margin-left: 16px;
      margin-bottom: 8px;
    }
    .author {
      margin-left: 16px;
    }
  }

</style>