<template>
  <div>
    <!-- https://nightcatsama.github.io/vue-slider-component -->
    <vue-slider
      v-if="max"
      v-model="timeRange"
      :min="min" 
      :max="max"
      :marks="mark"
      :tooltip-formatter="label"
      @change="rangeChange"
    />
  </div>
</template>

<script>

/* global _ */

const dependencies = []

module.exports = {
  name: 'TimeSelector',
  props: {
    initialTimeRange: Array,
    data: Array
  },
  data: () => ({
    timeRange: [],
    min: undefined,
    max: undefined,
  }),
  mounted() {
    this.loadDependencies(dependencies, 0, this.init)
  },
  methods: {
    init() {
        this.timeRange = this.initialTimeRange || this.timeRange
        console.log(`${this.$options.name}.mounted: timeRange=${this.timeRange}`)
    },
    rangeChange: _.debounce(function (e) {
      this.$emit('range-change', e)
    }, 500),
    label(val) {
      return `${Math.abs(val)}${val < 0 ? ' BCE' : ''}`
    },
    mark(val) {
      if (val % 1000 === 0) {
        return {label: this.label(val)}
      }
      return false
    }
  },
  watch: {
    data: {
      handler: function () {
        const min = Math.min(...this.data.map(f => f.value))
        this.min = Math.floor(min/100)*100
        const max = Math.max(...this.data.map(f => f.value))
        this.max = Math.ceil(max/100)*100
        console.log(`TimeSelector.watch.data: data=${this.data.length} min=${this.min} max=${max} start=${this.timeRange.length > 0 ? this.timeRange[0] : undefined} end=${this.timeRange.length > 1 ? this.timeRange[1] : undefined}`)
      },
      immediate: false
    },
    initialTimeRange: {
      handler: function () {
        this.timeRange = this.initialTimeRange
        console.log(`TimeSelector.watch.timeRange: data=${this.data.length} start=${this.timeRange.length > 0 ? this.timeRange[0] : undefined} end=${this.timeRange.length > 1 ? this.timeRange[1] : undefined}`)
      },
      immediate: false
    }
  }

}

</script>