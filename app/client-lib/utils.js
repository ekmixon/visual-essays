export function parseUrl(href) {
  const match = href.match(
    /^(https?):\/\/(([^:/?#]*)(?::([0-9]+))?)(\/?[^?#]*)(\?[^#]*|)(#.*|)$/
  )
  // console.log('parseUrl', href, match)
  return (
    match && {
      protocol: match[1],
      host: match[2],
      hostname: match[3],
      origin: `${match[1]}://${match[2]}`,
      port: match[4],
      pathname: match[5] || '/',
      search: match[6],
      hash: match[7]
    }
  )
}

export function parseQueryString(queryString) {
  /* eslint-disable no-param-reassign */
  /* eslint-disable no-plusplus */
  queryString = queryString || window.location.search;
  const dictionary = {};
  try {
    if (queryString.indexOf("?") === 0) {
      queryString = queryString.substr(1);
    }
    const parts = queryString.split("&");
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i];
      const keyValuePair = p.split("=");
      if (keyValuePair[0] !== "") {
        const key = keyValuePair[0];
        if (keyValuePair.length === 2) {
          let value = keyValuePair[1];
          // decode URI encoded string
          value = decodeURIComponent(value);
          value = value.replace(/\+/g, " ");
          dictionary[key] = value;
        } else {
          dictionary[key] = "true";
        }
      }
    }
  } catch (err) {
    // console.log(err);
  }
  return dictionary;
}

export function prepItems(items) {
  items.forEach(item => {
    // ensure each item has both found_in and tagged_in props and
    // make them a Set for convenient inclusion tests
    item.tagged_in = new Set(item.tagged_in || []);
    item.found_in = new Set(item.found_in || []);
  });
  return items;
}

// Returns IDs for ancestor HTML elements for element with elemId
export function elemIdPath(elemId) {
  const elemIds = [];
  let elem = document.getElementById(elemId);
  while (elem) {
    elemIds.push(elem.id);
    if (elem.id === "essay") {
      break;
    }
    elem = elem.parentElement;
  }
  return elemIds;
}

export function itemsInElements(elemIds, items) {
  const selected = [];
  const selectedItemIds = new Set();
  for (let i = 0; i < elemIds.length; i++) {
    const elemId = elemIds[i];
    items.forEach(item => {
      // Get all items for most local (paragraph) element
      if (
        i === 0 &&
        item.found_in !== undefined &&
        item.tagged_in !== undefined &&
        (item.found_in.has(elemId) || item.tagged_in.has(elemId)) &&
        !selectedItemIds.has(item.id)
      ) {
        selected.push(item);
        selectedItemIds.add(item.id);
      }
      // Get items with specific tag for any element in element hierarchy
      if (
        ["map", "map-layer", "geojson", "location", "image", "video"].includes(
          item.tag
        ) &&
        item.tagged_in.has(elemId) &&
        !selectedItemIds.has(item.id)
      ) {
        selected.push(item);
        selectedItemIds.add(item.id);
      }
    });
  }
  return selected;
}

export function groupItems(items, componentSelectors) {
  // console.log('groupItems', items, componentSelectors)
  const exclude = ["essay"];
  const groups = {};

  if (
    componentSelectors &&
    componentSelectors.tag &&
    componentSelectors.tag.map
  ) {
    const maps = items.filter(item => item.tag === "map");
    let selectedMap =
      maps.length > 0 ? { ...maps[0], ...{ layers: [] } } : undefined;
    if (selectedMap) {
      groups.mapViewer = {
        ...componentSelectors.tag.map[0],
        ...{ items: [selectedMap] }
      };
      items
        .filter(item => item.tag === "map-layer")
        .forEach(layer => selectedMap.layers.push(layer));
    }
  }

  items
    .filter(item => !exclude.includes(item.tag))
    .forEach(item => {
      for (let [field, values] of Object.entries(componentSelectors)) {
        if (item[field] && values[item[field]]) {
          values[item[field]].forEach(component => {
            if (!groups[component.name]) {
              groups[component.name] = { ...component, ...{ items: [] } };
            }
            groups[component.name].items.push(item);
          });
        }
      }
    });
  // console.log("groups", groups);
  return groups;
}

export function eqSet(as, bs) {
  if (as.size !== bs.size) return false;
  for (var a of as) if (!bs.has(a)) return false;
  return true;
}

export function throttle(callback, interval) {
  let enableCall = true;
  return function(...args) {
    if (!enableCall) return;
    enableCall = false;
    callback.apply(this, args);
    setTimeout(() => (enableCall = true), interval);
  };
}

export function parseDate(ds) {
  let date;
  if (Number.isInteger(ds)) {
    date = new Date(`${ds}-01-01T00:00:00Z`);
  } else {
    const split = ds.split("-");
    if (split.length === 1) {
      const yr = split[0].toUpperCase().replace(/[. ]/, "");
      let yrAsInt;
      if (yr.indexOf("BC") > 0) {
        // covers both 'BC' and 'BCE' eras
        yrAsInt = -Math.abs(parseInt(yr.slice(0, yr.indexOf("BCE"))));
      } else if (yr.indexOf("CE") > 0 || yr.indexOf("AD") > 0) {
        yrAsInt = parseInt(yr.slice(0, yr.indexOf("CE")));
      } else {
        yrAsInt = parseInt(ds);
      }
      if (yrAsInt >= 1000) {
        date = new Date(`${yrAsInt}-01-01T00:00:00Z`);
      } else {
        date = new Date(yrAsInt, 0, 0);
        date.setUTCFullYear(yrAsInt);
      }
    } else if (split.length === 2) {
      date = new Date(`${split[0]}-${split[1]}-01T00:00:00Z`);
    } else if (split.length === 3) {
      date = new Date(`${ds}T00:00:00Z`);
    }
  }
  return date;
}

export function delimitedStringToObjArray(delimitedData, delimiter) {
  delimiter = delimiter || `\t`;
  const objArray = [];
  const lines = delimitedData.split("\n").filter(line => line.trim() !== "");
  if (lines.length > 1) {
    const keys = lines[0].split(delimiter).map(key => key.trim());
    lines.slice(1).forEach(line => {
      let obj = {};
      line
        .split(delimiter)
        .map(value => value.trim())
        .forEach((value, i) => {
          let rawKey = keys[i].split(".");
          let key = rawKey[0];
          let prop = rawKey.length === 2 ? rawKey[1] : "id";
          if (!obj[key]) obj[key] = {};
          if (value || prop === "id") {
            obj[key][prop] = value;
          }
        });
      objArray.push(obj);
    });
    let assignedId = 0;
    let labels = {};
    objArray.forEach(obj => {
      Object.values(obj).forEach(child => {
        if (child.id === "" && child.label) {
          if (!labels[child.label]) labels[child.label] = ++assignedId;
          child.id = labels[child.label];
        }
      });
    });
  }
  return objArray;
}

export function load(url, callback) {
  let e
  if (url.split('.').pop() === 'js') {
      e = document.createElement('script')
      e.src = url
      e.type='text/javascript'
  } else {
      e = document.createElement('link')
      e.href = url
      e.rel='stylesheet'
  }
  e.addEventListener('load', callback)
  document.getElementsByTagName('head')[0].appendChild(e)
}

export function loadDependencies(dependencies, i, callback) {
  if (dependencies.length > 0) {
    this.load(dependencies[i], () => {
        if (i < dependencies.length-1) {
            this.loadDependencies(dependencies, i+1, callback) 
        } else {
            callback()
        }
    })
  }
}
