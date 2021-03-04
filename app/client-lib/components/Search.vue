<template>
    <div class="main-container"
         style="background-image: url(https://raw.githubusercontent.com/jstor-labs/plant-humanities/main/images/header.jpg)">

        <div class="heading">
            <div class="title">Plant Search</div>
            <div class="subtitle">Select language, enter search term and begin your plant research</div>
        </div>

        <div class="search-container">

            <div class="language-selector">
                <select v-model="selectedLanguage" class="selector">
                    <option :key="lang.code" :value="lang.code"
                            v-for="lang in languages"
                            v-html="lang.label" :title="lang.tooltip"
                    ></option>
                </select>
            </div>

            <form class="search-input">
                <div
                        aria-labelledby="autocomplete-label"
                        class="autocomplete__container"
                        role="combobox"
                >
                    <input
                            @keyup="inputHandler"
                            aria-controls="autocomplete-results"
                            aria-expanded="false"
                            autocomplete="off"
                            class="autocomplete__input"
                            id="autocomplete-input"
                            role="textbox"
                            v-model="searchFor"
                            label="Enter a plant name"
                    />
                    <button
                            :style="`visibility: ${wdResults.length > 0 ? 'visible' : 'hidden'};`"
                            @click="toggleDropdown"
                            aria-label="toggle dropdown"
                            class="autocomplete__dropdown-arrow"
                    >
                        <svg fill-rule="evenodd" height="5" viewBox="0 0 10 5" width="10">
                            <title>Open drop down</title>
                            <path d="M10 0L5 5 0 0z"></path>
                        </svg>
                    </button>
                    <ul
                            class="autocomplete__results"
                            id="autocomplete-results"
                            role="listbox"
                    >
                        <li :key="item.id" @click="itemSelected(item)" v-for="item in wdResults">
                            <ul>
                                <li>
                                    <span class="label" v-html="item.label"></span>
                                    <span class="aliases" v-if="item.aliases">({{item.aliases.join(', ')}})</span>
                                </li>
                                <li class="description" v-html="item.description"></li>
                            </ul>
                        </li>
                        <li @click="doSearch" class="continue" v-if="searchContinue">More...</li>
                    </ul>
                </div>
            </form>

            <div class="controls" >
                <span @click="reset" v-if="searchFor"><i
                    class="far fa-times-circle"></i></span>
            </div>
        </div>

        <div class="examples">
            <span class="examples-label">Example searches:</span>
            <span class="examples-links">
                <a href="https://search.plant-humanities.org/?eid=Q171497" target="_blank">Sunflower</a> |
                <a href="https://search.plant-humanities.org/?eid=Q1043" target="_blank">Carl Linnauus</a> |
                <a href="https://search.plant-humanities.org/?eid=Q1055" target="_blank">Hamburg, Germany</a>
            </span>
        </div>

    </div>
</template>

<script>

    /* global _ */

    const languages = [
        {code: 'ar', label: 'العربية', tooltip: 'Arabic'},
        {code: 'de', label: 'Deutsch', tooltip: 'German'},
        {code: 'en', label: 'English', tooltip: 'English'},
        {code: 'es', label: 'español', tooltip: 'Spanish'},
        {code: 'fr', label: 'français', tooltip: 'French'},
        {code: 'he', label: 'עברית', tooltip: 'Hebrew'},
        {code: 'it', label: 'italiano', tooltip: 'Italian'},
        {code: 'ja', label: '日本語', tooltip: 'Japanese'},
        {code: 'ko', label: '한국어', tooltip: 'Korean'},
        {code: 'nl', label: 'Nederlands', tooltip: 'Dutch'},
        {code: 'pl', label: 'polski', tooltip: 'Polish'},
        {code: 'pt', label: 'português', tooltip: 'Portuguese'},
        {code: 'ru', label: 'русский', tooltip: 'Russian'},
        {code: 'zh', label: '中文', tooltip: 'Chinese'},
        {code: 'hi', label: 'हिन्दी', tooltip: 'Hindi'},
        {code: 'bn', label: 'বাংলা', tooltip: 'Bengali'},
        {code: 'id', label: 'Bahasa Indonesia', tooltip: 'Indonesian'}
    ]

    module.exports = {
        name: 'Search',
        data: () => ({
            languages,
            selectedLanguage: null,
            searchFor: null,
            isSearching: false,
            page: 1,
            wdResults: [],
            searchContinue: 0,
            currentListItemFocused: -1,
            isDropDownOpen: false
        }),
        computed: {},
        mounted() {
            console.log('Search.mounted')
            this.selectedLanguage = 'en'
            this.input = document.getElementById('autocomplete-input')
            this.dropdownArrow = document.querySelector('.autocomplete__dropdown-arrow')
            this.resultsList = document.getElementById('autocomplete-results')
            this.comboBox = document.querySelector('.autocomplete__container')
        },

        methods: {

            inputHandler: _.throttle(function () {
                if (this.searchFor) {
                    if (!this.isDropDownOpen) this.openDropdown()
                    this.searchContinue = 0
                    this.doSearch()
                } else {
                    this.wdResults = []
                    if (this.isDropDownOpen) this.closeDropdown()
                }
            }, 500),

            setResults(results) {
                if (Array.isArray(results) && results.length > 0) {
                    this.resultsList.innerHTML = results
                        .map((item, index) =>
                            `<li class="autocomplete-item" id="autocomplete-item-${index}" role="listitem" tabindex="0">${item.label}</li>`
                        ).join('')
                    this.currentListItemFocused = -1
                }
            },

            openDropdown() {
                this.isDropDownOpen = true
                this.resultsList.classList.add('visible')
                this.dropdownArrow.classList.add('expanded')
                this.comboBox.setAttribute('aria-expanded', 'true')
            },
            closeDropdown() {
                this.isDropDownOpen = false;
                this.resultsList.classList.remove('visible')
                this.dropdownArrow.classList.remove('expanded')
                this.comboBox.setAttribute('aria-expanded', 'false')
                this.input.setAttribute('aria-activedescendant', '')
            },
            toggleDropdown(event) {
                event.preventDefault()
                if (!this.isDropDownOpen) {
                    this.openDropdown()
                } else {
                    this.closeDropdown()
                }
            },
            itemSelected(item) {
                // event.preventDefault()
                this.closeDropdown()
                this.searchFor = item.label
                console.log(`item-selected`, item)
                this.openSearchTool(item.id)
            },
            reset() {
                this.searchFor = ''
                this.wdResults = []
                this.searchContinue = 0
                this.closeDropdown()
                this.$emit('reset')
            },

            doSearch() {
                // console.log(`doSearch: searchFor="${this.searchFor}" searchContinue=${this.searchContinue} isSearching=${this.isSearching}`)
                if (!this.searchFor || this.isSearching) return
                this.isSearching = true
                let url = `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=${this.searchFor}&uselang=${this.selectedLanguage}&language=${this.selectedLanguage}&format=json&origin=*&continue=${this.searchContinue}`
                fetch(url)
                    .then(res => res.json())
                    .then(res => {
                        this.searchContinue = res['search-continue']
                        this.wdResults = this.searchContinue > 7 ? [...this.wdResults, ...res.search] : res.search
                    })
                    .catch(err => {
                        console.log(err)
                    })
                    .finally(() => (this.isSearching = false))
            },
            openSearchTool(eid) {
                this.openWindow(`https://search.plant-humanities.org${eid ? '?eid='+eid : ''}`, `toolbar=yes,location=yes,menubar=yes,scrollbars=yes,status=yes,titlebar=yes,left=0,top=0,width=1001,height=1200`)
            },
            openWindow(url, options) {
                console.log('openWindow', url)
                if (this.externalWindow) { this.externalWindow.close() }
                if (options === undefined) options = 'toolbar=yes,location=yes,scrollbars=yes,status=yes,left=0,top=0,width=1000,height=1200'
                this.externalWindow = window.open(url, '_blank', options)
            }
        },
        watch: {}
    }
</script>

<style scoped>

    .main-container {
        display: grid;
        grid-template-columns: 200px auto;
        grid-template-rows: auto auto auto;
        grid-template-areas: 
            ". heading"
            ". search-container"
            ". examples";
        grid-gap: 4px;
        align-items: center;
        width: 100%;
        height: 100%;
        padding: 30px 0;
    }

    .heading {
        grid-area: heading;
    }

    .examples {
        grid-area: examples;
    }

    .search-container {
        grid-area: search-container;
        display: flex;
        height: 50px;
        margin: 12px 0;
    }

    .language-selector {
        height: 100%;
    }

    .selector {
        height: 100%;
        border: none;
        background-color: #F8F8F8;
        padding: 4px;
        border-radius: 3px 0 0 3px ;
        border-right: 1px solid #9e9e9e;
        font-size: 1em;
    }

    .search-input {
        display: inline-block;
        height: 100%;
        width: 100%;
        justify-self: left;
    }

    .controls {
        font-size: 1.6em;
        width: 35px;
        height: 36px;
    }

    .controls span {
        cursor: pointer;
        margin-left: 6px;
    }

    .title,
    .subtitle,
    .examples-label,
    .examples-links,
    .examples-links a {
        font-family: Roboto, sans-serif !important;
        color: white !important;
    }

    .title {
        font-family: 'Playfair Display', Serif !important;
        font-size: 2em;
    }

    .subtitle {
        padding-top: 6px;
    }

    .examples-label {
        font-weight: bold;
        padding-right: 12px;
    }

    * {
        box-sizing: border-box;
    }

    .autocomplete__container {
        grid-area: autocomplete-container;
        position: relative;
        width: 100%;
        max-width: 500px;
        height: 100%;
    }

    .autocomplete__results.visible {
        visibility: visible;
    }

    .autocomplete__input {
        display: block;
        width: 100%;
        height: 100%;
        border: none;
        padding-left: 0.5rem;
        border-radius: 0 3px 3px 0;
        font-size: 1.4rem;
        opacity: 1 !important;
        pointer-events: unset !important;
    }

    .autocomplete__input:focus {
        border-color: hsl(221, 61%, 40%);
    }

    .autocomplete__dropdown-arrow {
        position: absolute;
        right: 0;
        top: 0;
        background: transparent;
        border: none;
        cursor: pointer;
        height: 100%;
        transition: transform 0.2s linear;
    }

    .autocomplete__dropdown-arrow.expanded {
        transform: rotate(-180deg);
    }

    .autocomplete__results {
        visibility: hidden;
        position: absolute;
        top: 100%;
        margin: 0;
        width: 100%;
        overflow-y: auto;
        border: 1px solid #999;
        padding: 0;
        max-height: 400px;
        background: white;
        z-index: 10;
    }

    .autocomplete__results li {
        list-style: none;
        padding: 0.3rem 0.3rem;
        cursor: pointer;
        color: black;
        line-height: 1em !important;
        font-size: 1em;
    }

    .autocomplete__results ul {
        list-style-type: none;
        padding-left: 0;
    }

    .autocomplete__results > li:hover {
        background: hsl(212, 10%, 60%);
    }

    .autocomplete__results > li:focus {
        background: hsl(212, 10%, 70%);
    }

    .label {
        font-weight: bold;
    }

    .aliases {
        font-style: italic;
    }

    .description {
        font-size: 1em;
    }

    .continue {
        font-weight: bold;
        background-color: #ddd;
    }

</style>