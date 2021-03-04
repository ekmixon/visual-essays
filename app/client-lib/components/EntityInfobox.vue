<template>
  <div class="entity-infobox">
    <!--
      <div class="entity-image-holder" v-if="imageSrc" :style="{backgroundSize: imageFit, backgroundImage: 'url(' + imageSrc + ')'}"></div>
    -->
    <img v-if="imageSrc" :src="imageSrc">
    <h3 class="entity-title" primary-title v-html="title"></h3>
    <div class="subtitle">{{ description }}</div>
    <div class="entity-description" v-html="html"></div>
    <a v-if="entity.wikipedia_page.en" class="entity-link" :href="entity.wikipedia_page.en.value" target="_blank">View Source</a>
  </div>
</template>

<script>

module.exports = {
  name: 'entity-infobox',
  props: {
    eid: { type: String, default: undefined },
    imageFit: { type: String, default: 'contain' }
    /* imageFit:
       fill = stretched to fit box
       contain = maintain its aspect ratio, scaled fit within the element’s box, letterboxed if needed
       cover = fills entire box, maintains aspect ration, clipped to fit
       none = content not resized
       scale-down = same as none or contain, whichever is smaller
    */
  },
  data: () => ({
    requested: new Set(),
    entityInfo: undefined
  }),
  computed: {
    entity () { return this.$store.getters.items.find(entity => this.eid === entity.eid || this.eid === entity.id) || {} },
    // entityInfo () { return this.entity['summary info'] },
    title () { return this.entityInfo && this.entityInfo.displaytitle || this.entity.label || this.entity.title },
    description () { return this.entityInfo ? this.entityInfo.description : this.entity.description },
    thumbnail () { return this.entityInfo && this.entityInfo.thumbnail ? this.entityInfo.thumbnail.source : null },
    imageSrc () { return this.thumbnail ?  this.thumbnail : this.entity.images ? this.entity.images[0] : null },
    html () { return this.entityInfo ?  this.entityInfo.extract_html : null },
    context() { return this.$store.getters.context },
    apiBaseURL() { return this.$store.getters.serviceBase }
  },
  mounted() {
    this.getSummaryInfo()
  },
  methods: {
    toQueryString(args) {
      const parts = []
      Object.keys(args).forEach((key) => {
        parts.push(`${key}=${encodeURIComponent(args[key])}`)
      })
      return parts.join('&')
    },
    getEntity() {
      let url = `${this.apiBaseURL}/entity/${encodeURIComponent(this.eid)}`
      const args = {}
      if (this.context) args.context = this.context
      if (this.entity.article) args.article = this.entity.article
      if (Object.keys(args).length > 0) {
        url += `?${this.toQueryString(args)}`
      }
      console.log(`getEntity=${url}`)
      return fetch(url).then(resp => resp.json())
    },
    getSummaryInfo() {
      console.log('getSummaryInfo', this.eid, this.entity)
      if (this.entity['summary info']) {
        this.entityInfo = this.entity['summary info']
      } else if (!this.requested.has(this.entity.id)) {
        this.requested.add(this.entity.id)
        this.getEntity()
          .then((updated) => {
            if (!updated['summary info']) {
              updated['summary info'] = null
            }
            this.entityInfo = updated['summary info']
            updated.id = this.eid
            this.$store.dispatch('updateItem', updated)
          })
      }
    }
  },
  watch: {
    entity() {
      this.getSummaryInfo()
    }
  }
}
</script>

<style>

  .entity-description p {
    margin: 0;
    padding: 0 !important;
    line-height: 1.2 !important;
  }
</style>

<style scoped>

  .entity-infobox {
    display: grid;
    height: 100%;
    overflow-y: scroll;
    grid-template-columns: auto;
    grid-template-rows: auto auto auto 1fr auto;
    grid-template-areas:
      "image"
      "title"
      "subtitle "
      "description"
      "link";
    align-items: left;
  }

  .entity-infobox .v-card__text {
    height: 100%;
    min-height: 165px;
    padding-bottom: 0 !important;
  }

  h3.entity-title {
    grid-area: title;
    font-size: 1.3em;
    margin: 0.5rem;
  }

  .entity-infobox img {
    grid-area: image;
    justify-self: center;
    object-fit: contain;
    max-height: 200px;
    margin-top: 6px;
  }

  .entity-image-holder {
    grid-area: image;
    width: 100%;
    height: 300px;
    background-color: #7F828B;
  }

  .subtitle {
    grid-area: subtitle;
    font-size: 1.1rem;
    margin: 0.5rem;
  }

  .entity-description {
    grid-area: description;
    margin: 16px 0;
    line-height: 1.4;
    font-size: 1rem;
    margin: 0.5rem;
  }

  .entity-link {
    grid-area: link;
    font-size: 1.1rem;
    color: black !important;
    text-decoration: underline !important;
    margin: 0.5rem;
  }

</style>
