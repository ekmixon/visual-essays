<template>
  <div :style="containerStyle">
    <iframe 
      :src="`https://cdn.knightlab.com/libs/timeline3/latest/embed/index.html?source=${item.source}&font=Default&lang=en&timenav_position=${item['timenav-position'] || 'bottom'}&hash_bookmark=${item['hash_bookmark'] || 'false'}&initial_zoom=${item['initial-zoom'] || '2'}&height=${item.height || '650'}`"
      :width="width" 
      :height="height"
      webkitallowfullscreen mozallowfullscreen allowfullscreen 
      frameborder="0">
    </iframe>    
</template>
<script>

module.exports = {
  name: 'TimelineViewer',
  props: { 
    items: Array,
    width: Number,
    height: Number
  },
  computed: {
    containerStyle() { return { position: 'relative', width: `${this.width}px`, height: `${this.height}px`, overflowY: 'auto !important' } },
    item() { return this.items[0] },
    source() { return this.items[0].source }
  },
  mounted() {
    console.log(`${this.$options.name}.mounted: height=${this.height} width=${this.width}`, this.mapDef)
  },
  methods: {}
}
</script>

<style>
</style>