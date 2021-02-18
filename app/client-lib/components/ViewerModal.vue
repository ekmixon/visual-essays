<template>
  <modal 
    class="viewer-modal"
    name="viewer-modal" 
      :min-width="600"
      :min-height="250"
      width="100%"
      height="50%"
      :click-to-close="modalProperties.click2close"
      :shiftX="modalProperties.shiftX"
      :shiftY="modalProperties.shiftY"
      :draggable="modalProperties.draggable"
      :resizable="modalProperties.resizeable"
      transition="nice-modal-fade"
  >
    <button class="close-button" @click="close">
      <i class="fal fa-times"></i>
    </button>
    <div class="modal-content">
      Modal text
    </div>
  </modal>
</template>

<script>
// Uses vue-js-modal:  https://github.com/euvl/vue-js-modal/blob/master/README.md

  const MODAL_PROPERTIES = {
    float: { //middle modal
      pivotX: 0.5,
      pivotY: 0.5,
      draggable: true,
      resizeable: true,
      click2close: true,
      reset: true,
    },
    fixed: { //bottom up (mobile)
      shiftX: 0.0,
      shiftY: 1.0,
      draggable: false,
      resizeable: false,
      click2close: false,
      reset: true,
    },
    right: { //right to left
      pivotX: 1.0,
      pivotY: 0.0,
      draggable: false,
      resizeable: false,
      click2close: true,
      reset: true,
    }
  }
  
module.exports = {
  name: 'ViewerModal',
  props: {
  },
  data: () => ({}),
  computed: {
    modalProperties() { return MODAL_PROPERTIES['fixed'] },
    modalStyle() {
      var h = window.innerHeight - 100;
      return h;
    },
  },
  methods: {
    close() {
      this.$modal.hide('viewer-modal')
    },
  },
  watch: {}
}
</script>

<style>
  .vm--overlay {
    background: rgba(0, 0, 0, 0);
    width: 100vw;
    transition: background 4s ease-out;
  }
</style>

<style scoped>

  .modal {
    z-index:1001;
  }

  .modal-content {
    padding: 40px 12px 12px 12px;
  }

  .close-button {
    position: absolute;
    top: 0;
    left: 0px;
    background-color: black;
    border-radius: 0px;
    display: block;
    width: 30px;
    text-align: center;
    height: 30px;
    font-weight: bold;
    color: white;
    border: 0;
  }

  .close-button:hover {
    background-color: #219653;
  }
</style>
