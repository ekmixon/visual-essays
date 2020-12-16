<template>
    <div id="graphic" :style="containerStyle">

        <div v-if="this.svg">
            <div v-html="this.svg"></div>
        </div>
        <div v-if="this.image">
            <img :src="this.image">
        </div>

    </div>
</template>

<script>

module.exports = {
    name: 'graphicViewer',
    props: {
      items: Array,
      width: Number,
      height: Number,
    },
    
    data: () => ({
        svg: undefined,
        image: undefined,
    }),
    
    computed: {
        containerStyle() { return { width: `${this.width}px`, height: `${this.height}px`} },
        input() { return this.items[0].img || this.items[0].url || this.items[0].file }
        
    },
    mounted() {
        this.init();
    },
    methods: {
        init() {
            console.log('this.input', this.input)
            console.log('this.items[0].img', this.items[0].img)

            //check if svg
            if (this.input.split('.').pop() == 'svg'){
                fetch(this.input).then((resp) => resp.text())
                    .then((dataString) => {
                        this.svg = dataString;
                    })
            }
            else {
                this.image = this.input
            }
           
        },
    }
  }
</script>

<style scoped>
</style>