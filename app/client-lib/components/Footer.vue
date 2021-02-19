<template>
  <div id="footer">
    <img v-if="logo" :src="logo">
  </div>
</template>

<script>

  module.exports = {  
    name: 'Footer',
    props: {
      siteConfig: { type: Object, default: function(){ return {}} }
    },
    data: () => ({}),
    computed: {
      logo() { return this.siteConfig ? this.siteConfig.logo : null }
    },
    mounted() {},
    methods: {},
    watch: {}
  }

</script>

<style>
  
  [v-cloak] { display: none; }

  #footer {
    display: flex;
    align-items: center;
    height: 50px;
    background-color: lightgrey;
  } 
  #footer img {
    height: 30px;
    margin: 0 12px;
  }

</style>