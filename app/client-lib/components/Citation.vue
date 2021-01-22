<template>

<modal 
            class="modal"
            name="citation-modal" 
            height="auto" 
            width="500px"
            :draggable="true"
            @closed="clearSelectedItem"
          >
            <button class="close-button" @click="close">
              <i class="fal fa-times"></i>
            </button>

            <div>
               <div class="citation-infobox">
                  Citations!
               </div>
            </div>
            
</modal>

</template>

<script>

module.exports = {
  name: 'citation-modal',
  props: {
    eid: { type: String, default: undefined },
    //imageFit: { type: String, default: 'cover' }
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
    apiBaseURL() { return window.location.origin }
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

<style scoped>

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

  .entity-image-holder {
    width: 100%;
    height: 300px;
    background-color: #7F828B;
  }

  .subtitle {
    font-size: 1.1rem;
  }

  .entity-description {
    margin: 16px 0;
    line-height: 1.3;
    max-height: 380px;
    overflow: scroll;
    font-size: 1.1rem;
  }

  .entity-description p {
    margin: 0;
  }

  .entity-link {
    font-size: 1.1rem;
    color: black !important;
    text-decoration: underline !important;
  }
</style>
