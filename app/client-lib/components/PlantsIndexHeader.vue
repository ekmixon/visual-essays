<template>
  <div>
  <div id="do-labs"> A collaboration between <i>JSTOR Labs</i> & <i>Dumbarton Oaks</i></div>

  <div :class="`header ${essayConfig.layout === 'index' ? 'index' : 'essay'}`" :style="`height:${height}; background-image: url(${banner})`" id="header" ref="header">
    <div class="homepage-header">
      <div id="logo" ref="logo">
        <img
                src="https://jstor-labs.github.io/plant-humanities/images/phl-website-png-logo.png"
                xlink:href="https://jstor-labs.github.io/plant-humanities/images/phl-website-svg-logo.svg" />
      </div>
      <div id="brand" ref="brand">
        <span class="brand-name">Plant Humanities Lab</span> <br/>
        <p class="tagline" ref="tagline">Explore the cultural histories of plants and their influence on human societies. </p>
      </div>
        <div id="menuToggle" ref="menuToggle">
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
            <li @click="openDocsSite" v-if="siteConfig.repo !== 've-docs'">
              <i :class="`fas fa-question`"></i>Documentation
            </li>
            <li @click="$modal.show('contact-modal')">
              <i class="fas fa-envelope"></i> Contact Us
            </li>
            <li>
              <a @click="logout" v-if="isAuthenticated">
                <i :class="`fas fa-user`"></i>Logout
              </a>
              <a :href="`https://visual-essays.app/login?redirect=${loginRedirect}`" v-else>
                <i :class="`fas fa-user`"></i>Login
              </a>
            </li>
            <hr>
            <li @click="viewMarkdown" style="margin-top:10px;">
              <i class="fas fa-file-code"></i>View page markdown
            </li>
            <li @click="editMarkdown('default')" v-if="isAuthenticated">
              <i class="fas fa-edit"></i>Edit page
            </li>
            <!--
            <li v-if="isAuthenticated" @click="editMarkdown('custom')">
              <i class="fas fa-edit"></i>Edit page (Custom)
            </li>
            -->
            <li @click="gotoGithub" v-if="isAuthenticated">
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

    </div>

      <modal
              :draggable="true"
              class="modal"
              height="auto"
              name="contact-modal"
              width="600px"

      >
        <div class="contact-us-container">
         <h1>Contact us</h1>
          <hr>
          <form class="form-wrapper" ref="feedback-form" v-on:submit.prevent="onSubmit">
            <input v-model="name" name="name" placeholder="Name" class="form-name" type="text" required> <br/>
            <input v-model="email" placeholder="Email" class="form-email" type="email" required> <br/>
            <input v-model="university" placeholder="University Affiliation (optional)" class="form-uni" type="text"> <br/>
            <select v-model="role" class="form-role">
              <option disabled value="">Please select one</option>
              <option value="Undergraduate Student">Undergraduate</option>
              <option value="Graduate Student">Graduate Student</option>
              <option value="Faculty">College/University Faculty</option>
              <option value="Scholar">Independent Scholar</option>
              <option value="Plant Enthusiast">Plant Enthusiast</option>
            </select> <br/>
            <textarea v-model="message" placeholder="Your message here" class="form-message" type="text" required></textarea>

            <button class="form-submit">Submit form</button>
          </form>
        </div>
      </modal>

    <div class="title-bar">
      <div class="title" v-html="title"></div>
      <div class="author" v-html="author"></div>
    </div>
  </div>
  </div>
</template>

<script>
  import { sendEmail } from '../api/EmailService'
  import TokenHelpers from '../mixins/token'

  export default {
    name: 'PlantsIndexHeader',
    mixins: [TokenHelpers],
    props: {
      essayConfig: { type: Object, default: function(){ return {}} },
      siteConfig: { type: Object, default: function(){ return {}} },
      progress: { type: Number, default: 0 },
      height: Number,
      appVersion: { type: String },
      contentRef: { type: String },
      isAuthenticated: { type: Boolean, default: false },
      href: String
    },
    data: () => ({
      headerWidth: null,
      headerHeight: null,
      observer: null,
      name: '',
      email: '',
      university: '',
      role: '',
      message: ''
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
      }
    },
    mounted() {
      console.log(`${this.$options.name}.mounted: height=${this.height}`, this.siteConfig, this.essayConfig)
      console.log(`isAuthenticated=${this.isAuthenticated}`)

      // set initial height
      this.$refs.header.style.height = `${this.height}px`

      // initialize a header size observer
      this.initObserver()
    },
    methods: {
      initObserver() {
        const header = this.$refs.header,
              vm = this,
              config = { attributes: true }

        // create the observer
        const observer = new MutationObserver(function (mutations) {
          mutations.forEach(function (mutation) {
            // check if the mutation is attributes and update the width and height data if it is.
            if (mutation.type === 'attributes') {
              let { width, height } = header.style
              vm.headerWidth = parseInt(width.replace(/px/, ''))
              vm.headerHeight = parseInt(height.replace(/px/, ''))
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
        console.log(`menuItemClicked=${item}`)
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
      onSubmit() {
        const options = {
          name: this.name,
          email: this.email,
          university: this.university,
          role: this.role,
          message: this.message,
        };

        this.getApiToken().then((token) => {
          return sendEmail(options, token, "labs@ithaka.org")
        })

        this.getApiToken().then((token) => {
          return sendEmail(options, token, "jessica.smith@ithaka.org")
        }).then((resp) => {
          if (resp.status === 200) {
            this.$modal.hide('contact-modal')
            alert("Thank you for contacting us.")
            //success
          } else {
            alert("failed to send " + resp.status)
          }
        }).catch((err) => {
          alert(err);
        })

      }
    },
    beforeDestroy() {
      if (this.observer) this.observer.disconnect()
    },
    watch: {
      href() {
        console.log('header.href', this.href)
      }
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
    /* min-height: 100px; */
    background-repeat: no-repeat;
    background-position: center center;
    background-size: cover;
    position: relative;
    margin: 0;
    color: rgba(0, 0, 0, 0.99);
  }

  .title-bar {
    display: grid;
    align-items: stretch;
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    grid-template-areas:
      "title"
      "author";
    color: white;
    background-color: rgba(0, 0, 0, .6);
    /*padding: 24px 0 0 70px;*/
    position: absolute;
    top: calc(100% - 100px);
    height: 100px;
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

  .header .title-bar {
    display: none;
  }

  #do-labs {
      background-color: black;
      font-size: .8rem;
      padding: 14px;
      color: white;
      text-align: center;
  }

  .homepage-header {
    padding: 0 1rem;
    background-color: #219653;
    height: 100px !important;
    z-index: 100;
    display: grid;
    grid-template-columns: 80px auto 100px;
  }

  #logo {
    padding: 8px;
    grid-column-start: 1;
  }

  #logo img {
    vertical-align: unset;
  }

  #brand {
    grid-column-start: 2;
    margin-left: 0.5rem;
  }

  .brand-name {
    font-family: 'Playfair Display', Serif;
    font-size: 3rem;
    color: white;
    line-height: 1.3;
  }

  .tagline {
      font-size: 1.3rem;
      color: white;
      font-family: Roboto, Sans-serif;
      font-weight: 300;
      margin: 0;
    line-height: 1;
  }

  .app-version {
    font-size: 0.9rem;
  }

  #menuToggle {
    grid-column-start: 3;
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

  .contact-us-container {
    padding: 8px 16px 16px;
  }

  .form-wrapper {
    margin-top:16px;
  }

  .form-name, .form-email, .form-uni, .form-message {
    width: calc(100% - 24px);
    height: 40px;
    margin: 10px 0;
    padding: 8px;
  }

  .form-role {
    width: calc(100% - 4px);
    height: 60px;
    margin: 10px 0;
    padding: 6px;
  }

  .form-message {
    height: 160px;
  }

  .form-submit {
    height: 40px;
    border: 0;
    color: white;
    border-radius: 4px;
    background-color:green;
  }

  input:focus:invalid {
    border: 2px solid red;
  }

  input:required:valid {
    border: 2px solid green;
  }

  @media (max-width: 920px) {
    .homepage-header {
      grid-template-columns: 8vw auto 8vw;
      height: 9vw !important;
    }

    #brand {
      margin-top: 6px;
    }

    .brand-name {
      font-size: 3.5vw;
      line-height: 5vw;
    }

    .tagline {
      font-size: 2vw;
      line-height: 2vw;
    }
  }

  @media (max-width: 740px) {
    #do-labs{
      padding: 2vw;
    }

    .homepage-header {
      padding: 1vw;
    }

    .brand-name {
      font-size: 4vw;
      line-height: 5vw;
    }

    .tagline {
      font-size: 2.2vw;
      line-height: 3vw;
    }

    #logo {
      padding:4px;
    }

    #brand {
      margin-top: 4px;
      margin-left: 8px;
      margin-right: 8px;
    }

    #menuToggle {
      top: 20px;
      right: 20px;
    }
  }

  @media (max-width: 600px) {
    .homepage-header {
      grid-template-columns: 8vw auto 8vw;
    }

    .brand-name {
      font-size: 5vw;
      line-height: 5vw;
    }

    .tagline {
      font-size: 2.2vw;
    }

    #brand {
      margin-top: 2px;
      margin-left: 6px;
    }

    #menuToggle {
      top: 10px;
      right: 10px;
    }

  }

</style>
