<template>
    <svg :width="width" :height="height" :style="containerStyle"></svg>
</template>

<script>

/* global d3, simulation */

// https://bl.ocks.org/heybignick/3faf257bbbbc7743bb72310d03b86ee8

const dependencies = ['https://d3js.org/d3.v4.min.js']

module.exports = {
    name: 'D3ForceGraph',
    props: {
      items: Array,
      width: Number,
      height: Number
    },
    computed: {
      containerStyle() { return { width: `${this.width}px`, height: `${this.height}px`, overflowY: 'auto !important', marginLeft: '24px' } },
    },
    mounted() {
        console.log(this.$options.name, this.items)
        /*
        if (typeof d3 === 'object') {
            this.init()
        } else {
            this.loadDependencies(dependencies, 0, this.init)
        }
        */
        this.loadDependencies(dependencies, 0, this.init)
    },
    methods: {
        init() {
            var svg = d3.select("svg"),
                width = +svg.attr("width"),
                height = +svg.attr("height")

            var color = d3.scaleOrdinal(d3.schemeCategory20)

            var simulation = d3.forceSimulation()
                .force("link", d3.forceLink().id(function(d) { return d.id; }))
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(width / 2, height / 2))

            fetch(this.items[0].url).then(resp => resp.text())
            .then(delimitedDataString => {
                const data = this.transformData(this.delimitedStringToObjArray(delimitedDataString))
                console.log(data)

                
                d3.forceSimulation()
                    .nodes(data.nodes)
                    .links(data.edges)
                    //.size([width, height])

                d3.json(data, function(error, graph) {
                    if (error) throw error

                    var link = svg.append("g")
                        .attr("class", "links")
                        .selectAll("line")
                        .data(graph.links)
                        .enter().append("line")
                        .attr("stroke-width", function(d) { return Math.sqrt(d.value); })

                    var node = svg.append("g")
                        .attr("class", "nodes")
                        .selectAll("g")
                        .data(graph.nodes)
                        .enter().append("g")
                        
                    var circles = node.append("circle") // eslint-disable-line no-unused-vars
                        .attr("r", 5)
                        .attr("fill", function(d) { return color(d.group); })
                        .call(d3.drag()
                            .on("start", this.dragstarted)
                            .on("drag", this.dragged)
                            .on("end", this.dragended))

                    var lables = node.append("text") // eslint-disable-line no-unused-vars
                        .text(function(d) {
                            return d.id;
                        })
                        .attr('x', 6)
                        .attr('y', 3)

                    node.append("title")
                        .text(function(d) { return d.id; })

                    simulation
                        .nodes(graph.nodes)
                        .on("tick", ticked)

                    simulation.force("link")
                        .links(graph.links)

                    function ticked() {
                        link
                            .attr("x1", function(d) { return d.source.x; })
                            .attr("y1", function(d) { return d.source.y; })
                            .attr("x2", function(d) { return d.target.x; })
                            .attr("y2", function(d) { return d.target.y; })

                        node
                            .attr("transform", function(d) {
                            return "translate(" + d.x + "," + d.y + ")"
                            })
                    }
                })
            })
        },
        transformData(objArray) {
            const nodes = {}
            const transformed = { nodes: [], edges: [] }
            objArray.forEach((obj) => {
                ['source', 'target'].forEach((nodeType) => {
                let nodeId = obj[nodeType].id || obj[nodeType].label
                if (nodes[nodeId] === undefined) {
                    let id = transformed.nodes.length
                    // let qid = obj[nodeType].id[0] === 'Q' ? obj[nodeType].id : undefined
                    let label = obj[nodeType].label || obj[nodeType].id
                    nodes[nodeId] = id
                    transformed.nodes.push({ id: label })
                }
                });
            });
            objArray.forEach((obj) => {
                transformed.edges.push({
                    source: nodes[obj.source.id || obj.source.label],
                    target: nodes[obj.target.id || obj.target.label]
                })
            })
            return transformed;
        },
        dragstarted(d) {
            if (!d3.event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
        },
        dragged(d) {
            d.fx = d3.event.x
            d.fy = d3.event.y
        },
        dragended(d) {
            if (!d3.event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
        }
    }
  }
</script>

<style scoped>
    .links line {
        stroke: #999;
        stroke-opacity: 0.6;
    }

    .nodes circle {
        stroke: #fff;
        stroke-width: 1.5px;
    }

    text {
        font-family: sans-serif;
        font-size: 10px;
    }

</style>