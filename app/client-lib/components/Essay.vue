<template>
  <div ref="essay" id="essay" :class="styleClass" v-html="html"/>
</template>

<script>

module.exports = {
  name: 'essay',
  props: {
    html: String,
    layout: String,
    height: Number,
    width: Number,
    anchor: String,
    styleClass: String,
    debug: Boolean,
    viewerIsOpen: Boolean,
    hoverItem: String,
    selectedItem: String,
    allItems: { type: Array, default: () => ([]) },
    activeElements: { type: Array, default: () => ([]) }
  },
  data: () => ({
    paragraphs: {},
    scenes: [],
    activeElement: undefined,
    spacer: undefined,
    triggerOffset: 500,
    triggerHook: 0.4
  }),
  computed: {},
  mounted() {
    // console.log(`${this.$options.name}.mounted`)
    this.$nextTick(() => this.init())
  },
  methods: {
    init() {
      this.linkTaggedItems()
      // this.addFootnotesHover()
      this.addSpacer()
      // Setup ScrollMagic (https://scrollmagic.io/)
      let first
      let prior
      Array.from(document.body.querySelectorAll('p')).filter(elem => elem.id).forEach((para) => {
        if (!first) first = para.id
        
        const items = this.itemsInElements(this.elemIdPath(para.id), this.allItems)
        this.paragraphs[para.id] = { prior, items }

        if (items.length > 0) {
          para.classList.add('has-items')
          para.addEventListener('click', this.paragraphClickHandler)
        }

        const scene = this.$scrollmagic.scene({
          triggerElement: `#${para.id}`,
          triggerHook: this.triggerHook,
        })
        .on('enter', () => this.setActiveElements(para.id) )
        .on('leave', () => this.setActiveElements(this.paragraphs[para.id].prior) )
        
        // if (this.debug) 
        // scene.addIndicators({indent: this.layout === 'vertical' ? this.width/2 : 0})
        
        this.$scrollmagic.addScene(scene)
        this.scenes.push(scene)        
        prior = para.id

      })
      this.findContent()
      this.setActiveElements(first)
    },
    addSpacer() {
      // Adds a spacer element that expands and contracts to match the size of the visualizer so
      // that content at the end of the article is still reachable by scrolling
      let essayWrapper = document.getElementById('scrollableContent')
      if (essayWrapper) {
        console.log(`addSpacer=${essayWrapper.clientHeight - 150}px`)
        this.spacer = document.createElement('div')
        this.spacer.id = 'essay-spacer'
        this.spacer.style.height = `${essayWrapper.clientHeight - 150}px`
      document.getElementById('essay').appendChild(this.spacer)
      }
    },
    setActiveElements(elemId) {
      if (elemId) {
        const newActiveElements = this.elemIdPath(elemId)
        if (newActiveElements.length > 0 && !this.eqSet(new Set(this.activeElements), new Set(newActiveElements))) {
          this.$emit('set-active-elements', newActiveElements)
          // const contentParaIDs = Object.keys(this.paragraphs).filter(pid => pid.indexOf('section-') === 0)
          // const idx = contentParaIDs.indexOf(newActiveElements[0])
        }
      }
    },
    getParagraphs(elem, headerSize) {
      headerSize = headerSize || 0
      const paragraphs = []
      if (elem) {
        Array.prototype.slice.call(elem.getElementsByTagName('p')).forEach((para) => {
          if (para.id) {
            const paraTop = para.offsetTop - headerSize
            this.paragraphs[para.id].top = paraTop
            this.paragraphs[para.id].height = para.offsetHeight
            para.title = `${para.id} (${paraTop})`
            paragraphs.push({
              type: 'paragraph',
              id: para.id,
              top: paraTop,
              bottom: para.offsetTop + para.offsetHeight,
              items: this.itemsPartOf(para.id),
            })
          }
        })
      }
      return paragraphs
    },

    findContent() {
      const header = document.getElementById('header')
      const headerSize = header ? header.clientHeight : 0
      // const content = this.getParagraphs(document.getElementById('essay', headerSize))
      const content = []
      for (let i = 1; i < 9; i++) {
        document.body.querySelectorAll(`#essay h${i}`).forEach((heading) => {
          const sectionElem = heading.parentElement
          const sectionId = sectionElem.attributes.id.value
          //sectionElem.title = `${sectionId} (${sectionElem.offsetTop})`
          const section = {
            id: sectionId,
            level: i,
            title: heading.innerHTML,
            top: sectionElem.offsetTop,
            bottom: sectionElem.offsetTop + sectionElem.offsetHeight,
            items: this.itemsPartOf(sectionId),
            paragraphs: this.getParagraphs(sectionElem, headerSize)
          }
          content.push(section)
        })
      }
      // this.$store.dispatch('setContent', content)
    },

    itemsPartOf(elemId) {
      const items = []
      this.allItems.forEach((item) => {
        if (item.found_in.has(elemId) || item.tagged_in.has(elemId) ||
            (item.tag !== 'entity' && item.tagged_in.has('essay'))) {
          items.push(item)
        }
      })
      return items
    },
    scrollTo(elemid) {
      const elem = document.getElementById(elemid)
      if (elem) {
        this.$emit('collapse-header')
        let scrollTo = elem.offsetTop - 115
        let scrollable = document.getElementById('scrollableContent')
        if (!scrollable) scrollable = window
        console.log(scrollable, `scrollTo=${scrollTo}`)
        scrollable.scrollTo(0, scrollTo)
        // window.scrollTo(0, elem.offsetTop)
      }
    },
    /*
    addFootnotesHover() {
      document.querySelectorAll('.footnote-ref').forEach((fn) => {
        fn.addEventListener('mouseover', (e) => {
          const fnId = e.toElement.hash.slice(1)
          const fnHTML = document.getElementById(fnId).innerHTML
          // console.log(`footnote: id=${fnId} html="${fnHTML}"`)
        })
      })
    },
    */
    linkTaggedItems() {
      document.querySelectorAll('.tagged').forEach((item) => {
        item.addEventListener('click', this.itemClickHandler)
      })
    },
    paragraphClickHandler(e) {
      this.$emit('collapse-header')
      this.$emit('set-viewer-is-open', true)
      const paraId = e.target.tagName === 'P'
        ? e.target.id
        : e.target.parentElement.id
      //this.$store.dispatch('setSelectedParagraphID', paraId)
      console.log(`paragraphClickHandler: paraId=${paraId}`)
      if (this.paragraphs[paraId]) {
        let scrollTo
        const para = this.paragraphs[paraId]
        /*
        if (this.layout !== 'vertical') {
          // position active paragraph just above viewer pane, if possible
          const paraBottom = para.top + para.height
          this.triggerOffset = this.height/2 + 50
          if (this.height/2 > paraBottom) this.triggerOffset -= this.height/2 - paraBottom
          scrollTo = para.top + para.height - this.height/2 + 100
        } else {
          scrollTo = para.top - 56
        }
        */
        console.log(`paragraphClickHandler layout=${this.layout} para=${paraId} top=${para.top} height=${para.height} scrollTo=${scrollTo}`)
        let scrollable = document.getElementById('scrollableContent')
        if (!scrollable) scrollable = window
        scrollable.scrollTo(0, scrollTo)
      }

    },
    setHoverItem(e) {
      this.$emit('set-hover-item', e.type === 'mouseover' ? e.target.dataset.eid : null)
    },
    itemClickHandler(e) {
      e.stopPropagation()
      this.$emit('set-selected-item', e.target.attributes['data-eid'].value)
    },
    addItemEventHandlers(elemId) {
      const elem = document.getElementById(elemId)
      // console.log(`addItemEventHandlers: elemId=${elemId}`, elem)
      if (elem) {
        document.getElementById(elemId).querySelectorAll('.inferred, .tagged').forEach((entity) => {
          entity.addEventListener('click', this.itemClickHandler)
          entity.addEventListener('mouseover', this.setHoverItem)
          entity.addEventListener('mouseout', this.setHoverItem)
        })
      }
    },
    removeItemEventHandlers(elemId) {
      // console.log(`removeItemEventHandlers: elemId=${elemId}`)
      const elem = document.getElementById(elemId)
      if (elem) {
        document.getElementById(elemId).querySelectorAll('.active-elem .inferred, .active-elem .tagged').forEach((entity) => {
          entity.removeEventListener('click', this.itemClickHandler)
          entity.removeEventListener('mouseover', this.setHoverItem)
          entity.removeEventListener('mouseout', this.setHoverItem)
        })
      }
    }
  },
  watch: {
    anchor(anchor) {
      if (anchor) this.scrollTo(anchor)
    },
    layout: {
      handler () {
        // console.log(`layout=${this.layout}`)
        const containerElem = document.getElementById('scrollableContent')
        if (containerElem) containerElem.scrollTo(0, 0)
        // this.findContent()
      },
      immediate: true
    },
    height: {
      handler () {
        if (this.height) {
          this.triggerHook = (this.triggerOffset - 100) / (this.height * (this.viewerIsOpen ? 2 : 1))
        }
      },
      immediate: true
    },
    viewerIsOpen: {
      handler (isOpen) {
        if (!isOpen) this.triggerOffset = 500
      },
      immediate: true
    },
    activeElements: {
      handler (active) {
        this.activeElement = active[0]
      },
      immediate: true
    },
    activeElement: {
      handler (active, prior) {
        console.log('Essay.activeElement', active)
        if (prior) this.removeItemEventHandlers(prior)
        if (active) this.addItemEventHandlers(active)
      },
      immediate: true
    },
    hoverItem: {
      handler: function (itemID, prior) {
        // if (itemID) console.log(`${this.$options.name}.watch.hoverItem=${itemID}`)
        if (itemID) document.querySelectorAll(`.active-elem [data-eid="${itemID}"]`).forEach(elem => elem.classList.add('entity-highlight'))
        if (prior) document.querySelectorAll(`.active-elem [data-eid="${prior}"]`).forEach(elem => elem.classList.remove('entity-highlight'))
      },
      immediate: true
    },
    triggerHook: {
      handler: function () {
        // console.log(`triggerHook=${this.triggerHook}`)
        this.scenes.forEach(scene => {
          scene.triggerHook(this.triggerHook)
        })
      },
      immediate: true
    }
  }
}
</script>

<style>

.essay {
  padding: 0 6px !important;
}

.vertical .essay {
  background-color: #dadada;
  padding: 0 0 0 0 !important;
  /* box-shadow: 5px 5px 10px 0px rgba(0,0,0,0.3); */
}

.vertical p.active-elem {
  background-color: #ffffff;
  /* padding-top: 16px;
  padding-bottom: 16px; */
  border-left: none;
  box-shadow:  0 1px 3px 1px rgba(0,0,0,0.25);
  position: relative;
  cursor: default;
}

p.has-items:hover {
  cursor: pointer !important;
  background-color: #f7f7f7;;
}
  
.vertical p {
  padding: 8px 28px 8px 24px;
  line-height: 1.6;
}

.vertical h1,
.vertical h2,
.vertical h3, 
.vertical h4, 
.vertical h5,
.vertical h6,
.footnote {
  margin-left: 24px;
}

.footnote p{
  padding: 0;
  font-size: 1rem;
}

.tagged.location,
p.active-elem .inferred.location,
.tagged.building,
p.active-elem .inferred.building,
.tagged.place,
p.active-elem .inferred.place,
.tagged.person,
p.active-elem .inferred.person,
.tagged.fictional_character,
p.active-elem .inferred.fictional_character,
.tagged.written_work,
p.active-elem .inferred.written_work,
.tagged.plant,
p.active-elem .inferred.plant,
.tagged.entity,
p.active-elem .inferred.entity,
.tagged.event,
p.active-elem .inferred.event {
  border-bottom: 2px solid #219653;
  cursor: pointer;
  z-index: 10;
  /* white-space: nowrap; */
}

.entity-highlight,
.tagged.location:hover,
p.active-elem .inferred.location:hover,
.tagged.building:hover,
p.active-elem .inferred.building:hover,
.tagged.place:hover,
p.active-elem .inferred.place:hover,
.tagged.person:hover,
p.active-elem .inferred.person:hover,
.tagged.fictional_character:hover,
p.active-elem .inferred.fictional_character:hover,
.tagged.written_work:hover,
p.active-elem .inferred.written_work:hover,
.tagged.plant:hover,
p.active-elem .inferred.plant:hover,
.tagged.entity:hover,
p.active-elem .inferred.entity:hover,
.tagged.event:hover,
p.active-elem .inferred.event:hover {
  background: #a8e2bb !important;
  transition: all 0.2s ease-in;
}

</style>