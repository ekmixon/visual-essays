<template>
  <div id="app">
      Hello
  </div>
</template>

<script>
  export default {
    name: 'App',
    components: {},
    data: () => ({}),
    computed: {},
    mounted() {
        console.log(`${this.$options.name}.mounted`)
    },
    methods: {},
    watch: {}
  }
</script>

<style scoped>
</style>
