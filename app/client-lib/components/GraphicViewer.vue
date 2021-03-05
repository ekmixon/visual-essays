<template>
    <div class="grid-container" :style="containerStyle">
        <div id="graphic-container" v-if="this.svg" :style="graphicStyle">
            <div id="graphic" v-html="this.svg"></div>
        </div>
        <div id="graphic-container" v-if="this.image" :style="graphicStyle">
            <img id="graphic" :src="this.image">
        </div>
        <div class="citation">
            <span class="title">{{this.items[0].title}}</span>
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
        input() { return this.items[0].img || this.items[0].url || this.items[0].file },
        graphicStyle() {
            return {
                //width: `${this.width}px`,
                //height: `${this.height}px`,
                overflowY: 'auto !important',
                marginLeft: '0',   
            }
        }      
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

    .grid-container {
        display: grid;
        grid-template-rows: 95% 5%;
        grid-template-areas:
        "main"
        "footer";
        justify-items: center;
        align-items: center;
    }

    #graphic-container {
        grid-area: main;
        width:100%;
    }

    #graphic {
        width:100%;
    }

    .citation {
      /* row-start / column-start / row-end / column-end */
      grid-area: footer;
      z-index: 2;
      justify-self: stretch;
      align-self: stretch;
      /* background-color: rgba(255, 255, 255, 0.8); */
      background-color: #ccc;
      padding: 3px 6px;
        text-align: center;
        line-height: 1;
    }

    .title {
      font-size: 0.9rem;
      font-weight: bold;
    }
</style>