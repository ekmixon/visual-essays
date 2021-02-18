<template>
  <div>
    <div v-if="layout === 'vertical'" id="tabs-bar">
      <span v-for="tab in tabs" :key="`tab-${tab}`"
        :class="{'active-tab': activeTab === tab}"
        :data-tab="tab"
        @click="activeTabSelected"
      >
        <i :class="groups[tab].icon" class="fal"></i>
      </span>
    </div>
    <div v-if="layout != 'vertical'" ref="tabs" class="tab">
      <button @click="closeViewer"><i class="fal fa-times"></i></button>
      <button v-for="tab in tabs" :key="`tab-${tab}`"
        :data-viewer-name="tab"
        :class="{active: activeTab === tab}"
        @click="activeTab = tab"
      >
        <i :class="groups[tab].icon" class="fal"></i>
      </button>
      <!-- <button>{{viewerLabel}}</button> -->
    </div>
    <component ref="viewer"
      v-if="viewerIsOpen && activeTab && actions[activeTab]"
      v-bind:is="groups[activeTab].component"
      :siteInfo="siteInfo"
      :acct="acct"
      :repo="repo"
      :branch="branch"
      :path="path"
      :items="groups[activeTab].items"
      :actions="actions[activeTab].actions"
      :action-sources="actions[activeTab].sources"
      :items-in-active-elements="itemsInActiveElements"
      :active-element="activeElement"
      :selected="activeTab"
      :width="width"
      :height="height"
      :hover-item="hoverItem"
      :selected-item="selectedItem"
      :jwt="jwt"
      :service-base="serviceBase"
      @set-hover-item="setHoverItem"
      @set-selected-item="setSelectedItem"
    />
  </div>
</template>

<script>
  const tabOrder = ['imageViewer', 'mapViewer', 'videoViewer']

  module.exports = {
    name: 'Viewer',
    props: {
      width: Number,
      height: Number,
      viewerIsOpen: Boolean,
      hoverItem: String,
      selectedItem: String,
      layout: String,
      siteInfo: { type: Object, default: () => ({}) },
      acct: String,
      repo: String,
      branch: String,
      path: String,
      jwt: String,
      activeElements: { type: Array, default: () => ([]) },
      itemsInActiveElements: { type: Array, default: () => ([]) },
      groups: { type: Object, default: () => ({}) },
      serviceBase: String
    },
    data: () => ({
      selectedTab: undefined,
      paragraphs: {},
      spacer: undefined,
      tabs: [],
      activeTab: undefined,
      header: undefined,
      contentContainer: 0,
      position: 'relative',
      activeElement: undefined,
      actions: {},
      viewerHeight: 0,
      viewerWidth: 0
      // viewerIsOpen: false
    }),
    computed: {
      primary() {return this.itemsInActiveElements.find(item => item.primary === 'true' || item.tag === 'primary') },
      primaryTab() {
        let primary = this.primary ? `${this.primary.tag}` : undefined
        if (primary === 'map' || primary === 'image') {
          primary = `${primary}Viewer`
        }
        return primary
      },
      viewerLabel() {
        const items = this.groups[this.activeTab] ? this.groups[this.activeTab].items : []
        return items.length > 0 ? items[0].label || items[0].title || '' : ''
      }
    },
    mounted() {
      console.log(`viewer: viewerIsOpen=${this.viewerIsOpen} activeTab=${this.activeTab} actions=${this.actions[this.activeTab]} width=${this.width} viewerWidth=${this.viewerWidth} height=${this.height} viewerHeight=${this.viewerHeight}`)
      this.activeElementChange()
    },
    methods: {
      activeTabSelected(e) {
        e.stopPropagation()
        let target = e.target
        while (target.tagName !== 'SPAN') {
          target = target.parentElement
        }
        if (target.dataset.tab) this.activeTab = target.dataset.tab
      },
      closeViewer() {
        this.$emit('set-viewer-is-open', false)
      },
      setHoverItem(itemID) {
        this.$emit('set-hover-item', itemID)
      },
      setSelectedItem(itemID) {
        this.$emit('set-selected-item', itemID)
      },
      createTabsBar() {
        this.tabsBar = document.createElement('div')
        this.tabsBar.setAttribute('id', 'tabs-bar')
      },
      getActionSources(elemId) {
          const sources = {}
          Array.from (document.querySelectorAll(`#${elemId} span`))
          .forEach(elem => {
              for (let i = 0; i < elem.attributes.length; i++) {
                  const attr = elem.attributes.item(i)
                  if (attr.name.indexOf('data-') === 0 && attr.name.split('-').length === 4) {

                    const [event, target, action] = attr.name.split('-').slice(1) // eslint-disable-line no-unused-vars
                    if (!sources[target]) sources[target] = []
                    if (sources[target].indexOf(elem) === -1) sources[target].push(elem)
                  }
              }
          })
          return sources
      },
      getInteractionAttrs(elemId) {
          const eventAttrs = []
          Array.from (document.querySelectorAll(`#${elemId} span`))
          .forEach(elem => {
              for (let i = 0; i < elem.attributes.length; i++) {
                  const attr = elem.attributes.item(i)
                  if (attr.name.indexOf('data-') === 0 && attr.name.split('-').length === 4) {
                      const [event, target, action] = attr.name.split('-').slice(1) // eslint-disable-line no-unused-vars
                      // console.log(event, target, action)
                      eventAttrs.push({ elem, event })
                  }
              }
          })
          return eventAttrs
      },
      addInteractionHandlers(elemId) {
        this.getInteractionAttrs(elemId)
        .forEach(eventAttr => {
          eventAttr.elem.addEventListener(eventAttr.event, this.interactionHander)
          eventAttr.elem.classList.add('essay-interaction')
        })
      },
      removeInteractionHandlers(elemId, target) {
        this.getInteractionAttrs(elemId, target)
        .forEach(eventAttr => {
          eventAttr.elem.removeEventListener(eventAttr.event, this.interactionHander)
          eventAttr.elem.classList.remove('essay-interaction')
        })
      },
      interactionHander(e) {
        e.stopPropagation()
        const eventActions = {}
        Array.from(e.target.attributes)
        .filter(attr => attr.name.indexOf(`data-`) === 0 && attr.name.split('-').length === 4)
        .map(attr => {
          const [event, target, action] = attr.name.split('-').slice(1)
           return { elem: e.target, event, target, action, value: attr.value } 
        })
        .filter(action => action.event === e.type)
        .forEach(action => {
          const group = Object.values(this.groups).find(group => group.selectors.indexOf(`tag:${action.target}`) === 0)
          if (!eventActions[group.name]) eventActions[group.name] = []
          if (group) eventActions[group.name].push(action)
        })
        const actions = { ...this.actions }
        Object.keys(eventActions).forEach(groupName => actions[groupName].actions = eventActions[groupName])
        this.actions = actions
      },
      activeElementChange(current, prior) {
        // console.log(`activeElementChange: ${current} ${this.activeElement}`)
        current = current || this.activeElement
        const tabsBar = document.querySelector('#tabs-bar')
        // (`activeElementChange: current=${current} prior=${prior} tabsBar=${tabsBar !== null}`)
        document.querySelectorAll('.active-elem').forEach(elem => elem.classList.remove('active-elem'))
        // document.querySelectorAll('#tabs-bar').forEach(tb => tb.parentElement.removeChild(tb))
        if (prior) this.removeInteractionHandlers(prior)
        if (current) {
          const currentElem = document.getElementById(current)
          // console.dir(currentElem)
          if (currentElem) {
            currentElem.classList.add('active-elem')
            this.addInteractionHandlers(current)
            if (this.layout === 'vertical' && tabsBar) currentElem.appendChild(tabsBar)
          }
        }
      }
    },
    updated() {
      this.activeElementChange()
    },
    watch: {
      activeElements: {
        handler: function (activeElements) {
          // console.log('activeElements')
          this.activeElement = activeElements[0]
        },
        immediate: true
      },
      activeElement: {
        handler: function (current, prior) {
          // console.log(`Viewer.activeElement=${current}`)
          this.$nextTick(() => this.activeElementChange(current, prior))
            this.activeElementChange(current, prior)
      },
        immediate: true
      },
      height() {
        this.viewerHeight = this.height - (this.$refs.tabs ? this.$refs.tabs.clientHeight : 0)
        console.log(`Viewer.height=${this.viewerHeight}`)
        // this.viewerHeight = this.height
      },
      width() { this.viewerWidth = this.width },
      groups: {
        handler: function () {
          const availableGroups = []
          tabOrder.forEach(group => { if (this.groups[group]) availableGroups.push(group) })
          Object.keys(this.groups).forEach(group => {
            if (availableGroups.indexOf(group) === -1 && this.groups[group].icon) {
              availableGroups.push(group)
            }
          })
          this.tabs = availableGroups
          // this.activeTab = (this.tabs.indexOf(this.activeTab) >= 0 ? this.activeTab : undefined) || this.primaryTab || availableGroups[0] 
          this.activeTab = this.primaryTab || availableGroups[0] 
          // console.log(`groups: availableGroups=${availableGroups} activeTab=${this.activeTab}`)

          const actionSources = this.getActionSources(this.activeElement)
          const actions = {}
          for (let [groupName, group] of Object.entries(this.groups)) {
            const tag = group.selectors.find(selector => selector.indexOf('tag:') === 0).split(':')[1]
            actions[groupName] = {
              sources: actionSources[tag] ? actionSources[tag] : [],
              actions: []
            }
            this.actions = actions
          }  
        },
        immediate: true
      },
      primaryTab: {
        handler: function () {
          // console.log(`primaryTab=${this.primaryTab}`)
          this.activeTab = this.primaryTab || this.activeTab
        },
        immediate: true
      },
      viewerIsOpen: {
        handler: function (isOpen) {
          if (this.layout !== 'vtl') {
            if (this.$refs.viewer) {
              this.$refs.viewer.$el.style.display = isOpen ? 'block' : 'none'
            }
            if (!isOpen) {
              //this.spacer.style.height = 0
              document.querySelectorAll('.active-elem').forEach(elem => elem.classList.remove('active-elem'))
            } else if (this.activeElement) {
              //this.spacer.style.height = `${this.viewportHeight*0.7}px`
              document.getElementById(this.activeElement).classList.add('active-elem')
            }
          }
        },
        immediate: false
      },
      /*
      selectedParagraphID: {
        handler: function () {
          if (this.selectedParagraphID) {
            this.$store.dispatch('setViewerIsOpen', true)
            this.$store.dispatch('setSelectedParagraphID')
          }
        },
        immediate: false
      },
      */
      activeTab: {
        handler: function () {
          this.$nextTick(() => {
            //console.log(`activeTab=${this.activeTab}`)
            this.activeElementChange()
            //console.log(this.groups[this.activeTab])
            //this.viewerHeight = this.height - (this.$refs.tabs ? this.$refs.tabs.clientHeight : 0)
            //this.viewerWidth = this.width
            //console.log(this.viewerWidth, this.height, this.viewerHeight, this.$refs.tabs)
          })
        },
        immediate: false
      }
    }
  }
</script>

<style>

  #tabs-bar {
    display: flex;
    flex-direction: column;
    background-color: white;
    padding: 0;
    gap: 3px;
    position: absolute;
    top: 0;
    right: 0;
    font-size: 24px;
    text-align: center;
    margin: 0;
  }

  #tabs-bar span {
    margin: 0;
    padding: 3px;
    background-color: white;
    line-height: 1em;
  }

  #tabs-bar span svg {
    margin: 0;
    background-color: white !important;
    color: #219653 !important;
  }

  #tabs-bar span.active-tab svg {
    margin: 0;
    background-color: #219653 !important;
    color: white !important;
  }

  #tabs-bar span.active-tab:hover {
    margin: 0;
    background-color: #166337 !important;
    color: white !important;
  }
  #tabs-bar span.active-tab:hover svg {
    margin: 0;
    background-color: #219653 !important;
    color: white !important;
  }

  #tabs-bar span:hover, span.active-tab {
    color: white !important;
    background-color: #219653 !important;
  }
  #tabs-bar span:hover svg {
    color: white !important;
    background-color: #219653 !important;
  }

  .essay-interaction {
    z-index: 10;
  }

</style>

<style scoped>

  /* Style the tab */
  .tab {
    overflow: hidden;
    border: 1px solid #ccc;
    background-color: #f1f1f1;
  }

  /* Style the buttons inside the tab */
  .tab button {
    background-color: inherit;
    float: left;
    border: none;
    outline: none;
    cursor: pointer;
    /* padding: 14px 16px; */
    padding: 4px;
    margin: 0 6px;
    transition: 0.3s;
    font-size: 24px;
  }

  /* Change background color of buttons on hover */
  .tab button:hover {
    background-color: #ddd;
  }

  /* Create an active/current tablink class */
  .tab button.active {
    background-color: #ccc;
  }

  /* Style the tab content */
  .tabcontent {
    display: none;
    padding: 6px 12px;
    border: 1px solid #ccc;
    border-top: none;
  }

</style>
