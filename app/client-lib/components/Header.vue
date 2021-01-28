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
      <div class="title" v-html="title"></div>
      <div class="author" v-html="author"></div>
      <div class="citation" @click="$modal.show('citation-modal')">Cite this essay</div>
    </div>

    <modal 
      class="modal"
      name="citation-modal" 
      height="auto" 
      width="600px"
      :draggable="true"
    >
      <button class="close-button" @click="$modal.hide('citation-modal')">
        <i class="fal fa-times"></i>
      </button>
      <div>
        <div class="entity-infobox">
          <h3 class="entity-title" primary-title>Cite this essay</h3>
          <br>

          <div class="subtitle">MLA</div>
          <div class="citation-wrapper">
            <div class="citation-text" @click="copyTextToClipboard" v-html="mlaCitation"></div>
            <div class="copy-citation" @click="copyCitationToClipboard(`${mlaCitation}`)" title="Copy to clipboard">Copy</div>
              <span class="tooltiptext">Copy to clipboard</span>
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
      chicago: undefined
    }),
    computed: {
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
      console.log(`${this.$options.name}.mounted: height=${this.height}`, this.siteConfig, this.essayConfig)
      console.log(`href=${this.href} appVersion=${this.appVersion} ref=${this.contentRef} isAuthenticated=${this.isAuthenticated}`)
      
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
      toQueryString(args) {
        const parts = []
        Object.keys(args).forEach((key) => {
          parts.push(`${key}=${encodeURIComponent(args[key])}`)
        })
        return parts.join('&')
      },
      getEntity() {
        let url = `${this.apiBaseURL}/entity/${encodeURIComponent(this.essayConfig.qid)}`
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
        console.log('getSummaryInfo', this.essayConfig.qid)
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
          alert("Copied to clipboard!");
        }
      },
    },

    beforeDestroy() {
      if (this.observer) this.observer.disconnect()
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
    min-height: 104px;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: cover;
    position: relative;
    margin: 0;
    color: #444;
  }

  .title-bar {
    display: grid;
    align-items: stretch;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    grid-template-areas: 
      "title title"
      "author citation";
    color: white;
    background-color: rgba(0, 0, 0, .6);
    /*padding: 24px 0 0 70px;*/
    position: absolute;
    top: calc(100% - 104px);
    height: 104px;
    width: 100%;
    font-weight: bold;    
  }

  .title {
    grid: title;
    font-size: 2em;
    margin: 0 0 0 70px;
    padding: 22px 0 0 0;
  }
  .author {
    grid: author;
    font-size: 1.3em;
    margin: 0 0 0 70px;
    padding: 0 0 6px 0;
  }

  .citation {
    grid: citation;
    margin-left: auto;
    margin-right: 1vw;
    font-size: 1em;
    color: white;
    background-color: green;
    border: 1px solid green;
    padding: 6px;
    padding-bottom: 7px !important;
    height: 2vh;
    cursor: pointer;
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
    background: #cdcdcd;
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
  * at the top left of the screen
  */
  #menu {
    position: absolute;
    width: 230px;
    margin: -100px 0 0 -50px;
    padding: 120px 50px 10px 45px;
    background: #ededed;
    list-style-type: none;
    -webkit-font-smoothing: antialiased;
    /* to stop flickering of text in safari */
    transform-origin: 0% 0%;
    transform: translate(-100%, 0);
    transition: transform 0.5s cubic-bezier(0.77,0.2,0.05,1.0);
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
  }

  #menu li {
    display: flex;
    padding: 0.5em 0;
    font-size: 1.2em;
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
    transform: none;
  }

  #menuToggle {
    display: block;
    position: relative;
    top: 30px;
    /*left: 30px;*/
    margin-left: 30px;
    z-index: 1;
    -webkit-user-select: none;
    user-select: none;
  }

  .app-version {
    font-size: 0.9rem;
  }

  .subtitle {
    font-size: 1.1rem;
    font-weight: bold;
  }

  .citation-wrapper {
    margin: 16px 0;
    line-height: 1.3;
    max-height: 380px;
    display: flex;
    font-size: 1.1rem;
    overflow:auto
  }

  .citation-text {
    float: left;
    padding: 10px;
    border: 1px solid black;
    margin: 10px;
    cursor: pointer;
  }

  .copy-citation {
    float: left;
    border: 2px solid green;
    color: white;
    background-color: green;
    padding: 6px;
    padding-bottom: 7px !important;
    height: 2vh;
    margin: 10px;
    cursor: pointer;
  }

  .entity-infobox {
    align-items: left;
    margin: 1rem;
  }

  .entity-infobox .v-card__text {
    height: 100%;
    min-height: 165px;
    padding-bottom: 0 !important;
  }

  h3.entity-title {
    font-size: 1.5em;
    margin: 0 0 0.5rem 0;
  }

  .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: black;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  
  /* Position the tooltip */
  position: absolute;
  z-index: 1;
  bottom: 100%;
  left: 50%;
  margin-left: -60px;
}
.tooltip .tooltiptext::after {
  content: " ";
  position: absolute;
  top: 100%; /* At the bottom of the tooltip */
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: black transparent transparent transparent;
}
.tooltip:hover .tooltiptext {
  visibility: visible;
}

.close-button {
  margin-left: auto;
  float:left;
  margin: 10px;
}

</style>