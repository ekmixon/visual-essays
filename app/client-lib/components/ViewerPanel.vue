<template>
  <div>
    <button class="floating-action-button" @click="open">
      <i class="fal fa-times"></i>
    </button>
    <div class="floating-div" :style="style">
      <button class="close-button" @click="close">
        <i class="fal fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script>
  
module.exports = {
  name: 'ViewerPanel',
  props: {
    viewerIsOpen: Boolean
  },
  data: () => ({
  }),
  computed: {
    style() { return {
      display: this.viewerIsOpen ? 'unset' : 'none'
    }}
  },
  mounted() {
    console.log('mounted', this.$refs.fab)
  },
  methods: {
    open() {
      this.$emit('set-viewer-is-open', true)
    },
    close() {
      this.$emit('set-viewer-is-open', false)
    }
  },
  watch: {}
}
</script>

<style scoped>

.floating-action-button {
  position: absolute;
  bottom: 60px;
  right: 8px;
  background-color: black;
  border-radius: 40px;
  display: block;
  width: 40px;
  text-align: center;
  height: 40px;
  font-size: 28px;
  font-weight: bold;
  color: white;
  border: 0;
}

.floating-div {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40%;
  background-color: #eee;
  padding: 12px;
  min-height: 200px;
  min-width: 200px;
}


</style>
