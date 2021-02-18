<template>
  <modal 
    class="modal"
    name="entity-infobox-modal" 
    height="auto" 
    :maxHeight="modalStyle"
    :scrollable="true"
    width="500px"
    :draggable="true"
    @closed="clearSelectedItem"
  >
    <button class="close-button" @click="close">
      <i class="fal fa-times"></i>
    </button>
    <entity-infobox :eid="selectedItem"></entity-infobox>
  </modal>
</template>

<script>
// Uses vue-js-modal:  https://github.com/euvl/vue-js-modal/blob/master/README.md

module.exports = {
  name: 'EntityInfoboxModal',
  props: {
    hoverItem: String,
    selectedItem: String
  },
  data: () => ({}),
  computed: {
    modalStyle() {
      var h = window.innerHeight - 100;
      return h;
    },
  },
  methods: {
    clearSelectedItem() {
      this.$emit('set-selected-item', null)
    },
    close() {
      this.$modal.hide('entity-infobox-modal')
      this.clearSelectedItem()
    },
  },
  watch: {
    selectedItem(selectedItem) {
      if (selectedItem) this.$modal.show('entity-infobox-modal')
    }
  }
}
</script>

<style scoped>
  .modal {
    z-index:1001;
  }

  .close-button {
    position: absolute;
    top: 8px;
    right: 8px;
    background-color: black;
    border-radius: 40px;
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
