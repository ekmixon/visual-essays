<template>
  <div id="essay">
    <div class="section" v-for="(sect, sidx) in sections" :key="`section-${sidx}`">
        <h1 v-if="sect.title" v-html="sect.title"></h1>
        <div v-if="sect.paragraphs" class="overview">
            <p v-html="para" v-for="(para, pidx) in sect.paragraphs" :key="`para-${sidx}-${pidx}`"></p>
        </div>
        <div v-if="sect.essays" class="essay-index">
            <template v-for="(essay, eidx) in sect.essays">
                <div :key="`essay-${eidx}`" class="card-wrapper">
                <template v-if="essay.link">
                    <div v-if="essay.items" v-html="essay.title" class="essay-title"></div>
                    <a class="essay-card" :class="{group: essay.items}" :href="essay.link">
                        <div class="essay-image">
                            <img :src="essay.image" alt="" />
                        </div>
                        <div v-if="!essay.items" class="essay-cite">
                            <div class="essay-title" v-html="essay.title"></div>
                            <div class="essay-author" v-html="essay.author || essay.authors"></div>
                        </div>
                        <div v-if="showAbstracts" class="essay-abstract" v-html="essay.abstract"></div>
                    </a>
                </template>
                <template v-else>
                    <div v-if="essay.items" v-html="essay.title" class="essay-title"></div>
                    <div class="essay-card" :class="{group: essay.items}">
                        <div class="essay-image">
                            <img :src="essay.image" alt="" />
                        </div>
                        <div v-if="!essay.items" class="essay-cite">
                            
                            <div class="essay-title" v-html="essay.title"></div>
                            <div class="essay-author" v-html="essay.author || essay.authors"></div>
                            <div v-if="essay.authortitle" class="essay-author-title" v-html="essay.authortitle"></div>
                            
                        </div>
                        <div v-if="showAbstracts" class="essay-abstract" v-html="essay.abstract"></div>
                        
                        <!--
                        <div v-if="essay.authortitle"><input type="checkbox" id="expanded"></div>
                        -->

                        <input type="checkbox" id="expanded">
                        <div v-if="showAbstracts" class="essay-abstract" v-html="essay.abstract"></div>
                        <label for="expanded" role="button">read more</label>
                    </div>
                </template>
                <ul class="social-media">
                    <li v-if="essay.twitter"><i class="fab fa-twitter"></i>{{essay.twitter}}</li>
                    <li v-if="essay.facebook"><i class="fab fa-facebook"></i>{{essay.facebook}}</li>
                    <li v-if="essay.linkedin"><i class="fab fa-linkedin"></i>{{essay.linkedin}}</li>
                    <li v-if="essay.email"><i class="far fa-envelope"></i>{{essay.email}}</li>
                </ul>
                <div v-if="essay.items">
                    <ul>
                        <li v-for="(item, iidx) in essay.items" :key="`item-${eidx}-${iidx}`">
                            <a :href="item.link" v-html="item.title"></a>
                        </li>
                    </ul>
                </div>
                </div>
            </template>
        </div>
    </div>
  </div>
</template>

<script>

module.exports = {
  name: 'EssayIndex',
  props: {
    html: String,
    essayConfig: { type: Object, default: function(){ return {}} }
  },
  data: () => ({
      sections: []
  }),
  computed: {
      showAbstracts() { return !this.essayConfig || this.essayConfig['show-abstracts'] !== 'false' }
  },
  mounted() {
    console.log(`${this.$options.name}.mounted`)

    const ps = document.querySelectorAll(".essay-abstract");
    const observer = new ResizeObserver(entries => {
    for (let entry of entries) {
        entry.target.classList[entry.target.scrollHeight > entry.contentRect.height ? 'add' : 'remove']('truncated');
    }
    });

    ps.forEach(p => {
    observer.observe(p);
    });

  },
  methods: {
      parsePageHTML() {
        const sections = []
        const content = document.createElement('div')
        content.innerHTML = this.html
        Array.from(content.children).forEach(topSection => {
            const section = {}
            sections.push(section)
            const children = Array.from(topSection.children)
            section.title = children[0].innerHTML
            const sectionIsEssayIndex = children[1].children.item(1)
            if (sectionIsEssayIndex) {
                section.essays = []
                children.slice(1).forEach(c => {
                    const essay = {}
                    section.essays.push(essay)
                    const essayElems = Array.from(c.children)
                    let idx = 1
                    // the second essayElems item includes the title
                    const linkedTitle = essayElems[idx].querySelector('a')
                    if (linkedTitle) {
                        essay.title = linkedTitle.innerHTML
                        essay.link = linkedTitle.href
                    } else {
                        essay.title = essayElems[1].innerHTML
                    }
                    // the third essayElems item includes an optional list of metadata in a UL
                    ++idx
                    if (essayElems[idx] && essayElems[idx].tagName === 'UL') {
                        Array.from(essayElems[idx].children)
                        .map(c => c.innerText)
                        .forEach(li => {
                            const separatorPos = li.indexOf(':')
                            essay[li.slice(0, separatorPos).trim().toLowerCase()] = li.slice(separatorPos+1).trim()
                        })
                        ++idx
                    }
                    // the remaining essayElems are optional and can include:
                    //   - paragraphs that are merged in the essay abstract
                    //   - a UL list with linked essays
                    essayElems.slice(idx).forEach(e => {
                        if (e.tagName === 'P' || e.tagName === 'FIGURE') {
                            if (e.children.length === 1 && e.children.item(0).tagName === 'IMG') {
                                essay.image = e.children.item(0).src
                            } else {
                                essay.abstract = essay.abstract ? `${essay.abstract}<br/>${e.innerHTML}` : e.innerHTML
                            }
                        } else if (e.tagName === 'UL') {
                            essay.items = []
                            Array.from(e.children).forEach(li => {
                                Array.from(li.children).forEach(lic => {
                                    if (lic.tagName === 'A') essay.items.push({title: lic.innerHTML, link: lic.href})
                                })
                            })
                        }
                    })

                })
            } else {
                section.paragraphs = children.slice(1).map(c => c.innerHTML)
            }
        })
        return sections
      },
      parseUrl(href) {
        const match = href.match(/^(https?):\/\/(([^:/?#]*)(?::([0-9]+))?)(\/[^?#]*)(\?[^#]*|)(#.*|)$/)
        return (
            match && {
            protocol: match[1],
            host: match[2],
            hostname: match[3],
            origin: `${match[1]}://${match[2]}`,
            port: match[4],
            pathname: match[5],
            search: match[6],
            hash: match[7]
            }
        )
    }
  },
  watch: {
      html: {
        handler: function () {
            this.sections = this.parsePageHTML()
        },
        immediate: true
      }
  }
}

</script>

<style>

    h1 {
        margin: 1rem 0;
        font-size: 2.5rem;
        font-family: 'Playfair Display', Serif;
        font-weight: normal;
    }

    a {
        color: #000 !important;
        text-decoration: none !important;
    }

    .section {
        padding: 1rem;
    }

    .essay-index {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr) );
        /* grid-template-columns: repeat(4, minmax(100px, 400px)) */
        grid-auto-rows: 1fr;
        grid-gap: 1.8rem;
    }

    .card-wrapper:hover .essay-title {
        /* color: #444A1E; */
    }

    a:hover {
        color: #444;
    }

    .essay-card {
        display: grid;
        grid-template-columns: 1fr;
        grid-template-rows: auto 1fr;
        grid-template-areas:
            "image"
            "cite"
            "abstract";
        border-radius: 4px;
        padding: .5rem;
    }

    ul {
        margin: 0.5rem 0 0 0.5rem;
        padding: 0 0 0 1rem;
        /* list-style-type: none; */
    }

    .essay-cite {
        grid-area: cite;
        /* min-height: 120px; */
    }

    .essay-title {
        grid-area: title;
        font-weight: bold;
        font-size: 1.5rem;
        line-height:1.3;
        margin-top: 1.3rem;
        margin-bottom: 0.8rem;
        text-decoration: underline;
    }

    .essay-image {
        grid-area: image;
        max-height: 250px;
        overflow: hidden;
    }

    .essay-author {
        grid-area: author;
        font-size: .9rem;
        font-weight: 400;
    }

    .essay-author-title {
        grid-area: author;
        font-size: 1.1rem;
        font-style: italic;
        font-weight: 400;
    }

    .essay-abstract {
        grid-area: abstract;
        font-size: 0.8em;
        /*font-style: italic;*/
        /* height: 200px;*/
        margin: 1.0rem 0.2rem 0.5rem 0.3rem;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 6;
        -webkit-box-orient: vertical;  
    }

    .overview p {
        margin: 1rem 0 0 0;
    }

    ul.social-media {
        list-style: none;
        font-size: 0.8em;
        margin: 0;
    }

    ul.social-media svg {
        margin-right: 12px;
    }

    input {
        opacity: 0;
        position: absolute;
        pointer-events: none;
    }
    input:focus ~ label {
        outline: -webkit-focus-ring-color auto 5px;
    }
  
    input:checked + .essay-abstract{
        -webkit-line-clamp: unset;
    }
    
    input:checked ~ label,
    .essay-abstract:not(.truncated) ~ label{
        display: none;
    }

    label {
    border-radius: 4px;
    padding: 0.2em 0.6em;
    border: 1px solid #605C2A;
    background-color: #605C2A;
    color: #fff;
    font-size: 0.8em;
  }

</style>
