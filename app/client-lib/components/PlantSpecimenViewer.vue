<template>
  <div>
    <div ref="tabs" class="tab">
      <button v-for="specimens in specimensByTaxon" :key="specimens.id"
        :class="{active: selected === specimens.taxonName}"
        @click="selected = specimens.taxonName"
      >{{specimens.taxonName}} ({{images.length}})
      </button>
    </div>
    <image-viewer 
      v-if="selected"
      :items="images"
      :width="width"
      :height="height - 46"
      default-fit="cover"
    ></image-viewer>
  </div>

</template>

<script>

const dependencies = []

module.exports = {
    name: "PlantSpecimenViewer",
    props: {
      items: Array,
      width: Number,
      height: Number,
      serviceBase: String
    },
    //components: {
    //    imageViewer: `url:http://localhost:8080/components/OpenSeadragonViewer.vue`
    //},
    data: () => ({
      selected: undefined,
      specimensByTaxon: [],
    }),
    computed: {
        images() {
          return this.selected ? this.specimensByTaxon.find(specimens => specimens.taxonName === this.selected).specimens : []
        },
        outerContainerStyle() {
            return {
                width: `${this.width}px`,
                height: `${this.height}px`,
                padding: 0,
            }
        },
        innerContainerStyle() {
            return {
                height: `${this.height - 48}px`,
                padding: 0,
                overflowY: "auto !important",
            }
        },
    },
    mounted() {
        this.loadDependencies(dependencies, 0, this.init)
    },
    methods: {
        init() {
            console.log(`${this.$options.name}.mounted: height=${this.height} width=${this.width}`)
        },
        getSpecimenMetadata(item) {
            const id = item.jpid || item.eid
            if (item.specimensMetadata) {
                this.specimensByTaxon = [...this.specimensByTaxon, item.specimensMetadata]
            } else {
                const args = Object.keys(item)
                .filter((arg) => ["max", "reverse"].includes(arg))
                .map((arg) => `${arg}=${item[arg]}`)
                const url = `${this.serviceBase}/specimens/${id}` + (args ? `?${args.join("&")}` : "")
                console.log(url)
                fetch(url).then((resp) => resp.json())
                .then((specimensMetadata) => {
                    if (specimensMetadata.specimens.length > 0) {
                        specimensMetadata.caption = item.label || item.title
                        specimensMetadata.specimens.forEach((specimen) => {
                            specimen.url = specimen.images.find((img) => img.type === 'best').url
                            specimen.title = specimen.description
                        })
                        this.specimensByTaxon = [...this.specimensByTaxon, specimensMetadata]
                        this.selected = this.specimensByTaxon[0].taxonName
                        console.log('specimensByTaxon', this.specimensByTaxon)
                    }
                })
            }
        }
    },
    watch: {
        items: {
            handler: function(current, prior) {
                const currentItemIds = new Set(current.map((item) => item.id))
                const priorItemIds = new Set((prior || []).map((item) => item.id))
                if (!this.eqSet(currentItemIds, priorItemIds)) {
                    this.specimensByTaxon = []
                    this.items.forEach((item) => this.getSpecimenMetadata(item))
                }
            },
            immediate: true
        },
        selected: {
            handler: function(selected) {
              console.log(`PlantSpecimensViewer.watch.selected=${selected}`)
            },
            immediate: true
        },
        images: {
            handler: function(images) {
              console.log('PlantSpecimensViewer.watch.images', images)
            },
            immediate: true
        }
    }
}
</script>

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
