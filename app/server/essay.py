#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s')
logger = logging.getLogger()

import os
import re

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
SPARQL_DIR = os.path.join(SCRIPT_DIR, 'sparql')
BASEDIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

import json
import getopt
import sys
import base64
import hashlib
import traceback
from urllib.parse import quote, urlparse
from time import time as now

from bs4 import BeautifulSoup
from bs4.element import Comment, Tag

import requests
logging.getLogger('requests').setLevel(logging.INFO)

from slugify import slugify

import markdown as markdown_parser

from bs4 import BeautifulSoup
from bs4.element import Tag

from rdflib import ConjunctiveGraph as Graph
from pyld import jsonld

import concurrent.futures

from gh import get_gh_markdown

DEFAULT_REPO = 've-docs'

cache = {}

def get_local_markdown(path, root):
    abs_path = f'{root}{path[:-1] if path.endswith("/") else path}'
    logger.info(f'get_local_markdown: path={path} root={root} abs={abs_path} exists={os.path.exists(abs_path)}')
    markdown = md_path = None
    to_check = []
    if os.path.exists(abs_path):
        if abs_path.endswith('.md'):
            markdown = open(abs_path, 'r').read()
            md_path = path
        else:
            to_check = [f'{abs_path}/{file}' for file in ('README.md', 'index.md')]
    else:
        to_check = [f'{abs_path}.md'] + [f'{abs_path}{file}' for file in ('README.md', 'index.md')]
    if not markdown:
        for _path in to_check:
            logger.info(f'path={_path} exists={os.path.exists(_path)}')
            if os.path.exists(_path):
                markdown = open(_path, 'r').read()
                md_path = _path[len(root)+1:]
                break
    return markdown, md_path

def _img_to_figure(soup):
    for elem in soup.find_all('img'):
        if elem.parent.name == 'a' and 've-button' in elem.attrs.get('src'):
            elem.parent.extract()
            continue
        figure = soup.new_tag('figure')
        if 'class' in elem.attrs:
            figure.attrs['class'] = elem.attrs['class']
        img = soup.new_tag('img')
        img.attrs['src'] = elem.attrs['src']
        figure.append(img)
        if 'alt' in elem.attrs and elem.attrs['alt'] != '':
            figcaption = soup.new_tag('figcaption')
            figcaption.string = elem.attrs['alt']
            figure.append(figcaption)       
        elem.replace_with(figure)
    return soup

def convert_relative_links(soup, site, acct, repo, ref, path, root=None):
    path_elems = path[1:].split('/')
    if site.startswith('localhost') and root is not None:
        abs_baseurl = f'http://{site}/static'
    else:
        abs_baseurl = f'https://raw.githubusercontent.com/{acct}/{repo}/{ref}'
    rel_baseurl = f'{abs_baseurl}/{"/".join(path_elems[:-1])}' if len(path_elems) > 1 else abs_baseurl
    logger.debug(f'convert_relative_links: site={site} acct={acct} repo={repo} ref={ref} root={root} path={path} abs_baseurl={abs_baseurl} rel_baseurl={rel_baseurl}')

    for tag in ('img', 'var', 'span', 'param'):
        for elem in soup.find_all(tag):
            for attr in ('banner', 'data-banner', 'logo', 'src', 'url', 'file', 'manifest', 'data', 'geojson', 'logo'):
                if attr in elem.attrs and elem.attrs[attr] and not elem.attrs[attr].startswith('http'):
                    before = elem.attrs[attr]
                    if elem.attrs[attr][0] == '/':
                        elem.attrs[attr] = f'{abs_baseurl}{elem.attrs[attr]}'
                    else:
                        elem.attrs[attr] = f'{rel_baseurl}/{elem.attrs[attr]}'
                    logger.debug(f'{before} {elem.attrs[attr]}')

def markdown_to_html5(markdown, site, acct, repo, ref, path, root):
    '''Transforms markdown generated HTML to semantic HTML'''
    html = markdown_parser.markdown(
        markdown,
        output_format='html5', 
        extensions=['footnotes', 'tables', 'pymdownx.superfences', 'pymdownx.details', 'def_list', 'attr_list'],
        extension_configs = {
            'footnotes': {
                'SEPARATOR': '-'
            }
        })
    soup = BeautifulSoup(f'<div id="md-content">{html}</div>', 'html5lib')
    convert_relative_links(soup, site, acct, repo, ref, path, root)

    base_html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title></title></head><body></body></html>'
    html5 = BeautifulSoup(base_html, 'html5lib')

    article = html5.new_tag('article', id='essay')
    article.attrs['data-app'] = 'true'
    article.attrs['data-name'] = path
    html5.html.body.append(article)

    snum = 0 # section number
    pnum = 0 # paragraph number within section

    root = soup.find('div', {'id': 'md-content'})

    soup = _img_to_figure(soup)

    sections = []
    for elem in root.find_all(recursive=False):
        if isinstance(elem, Tag):
            if elem.name[0] == 'h' and elem.name[1:].isdigit():
                level = int(elem.name[1:])
                title = elem.string
                snum += 1
                section_id = f'section-{snum}'
                # logger.info(f'section: level={level} id={section_id} title="{title}')
                tag = html5.new_tag('section', id=section_id)
                head = html5.new_tag(f'h{level}')
                head.attrs = elem.attrs
                head.string = title if title else ''
                tag.append(head)
                section = {
                    'id': section_id,
                    'level': level,
                    'parent': None,
                    'tag': tag
                }
                pnum = 0
                for s in sections[::-1]:
                    if s['level'] < section['level']:
                        section['parent'] = s['id']
                        break
                sections.append(section)
            else:
                parent = sections[-1]['tag'] if sections else article
                if elem.name == 'p' and not _is_empty(elem):
                    pnum += 1
                    # ensure non-empty paragraphs have an ID
                    if 'id' not in elem.attrs:
                        elem.attrs['id'] = f'{parent.attrs["id"]}-{pnum}'
                parent.append(elem)

    sections = dict([(s['id'], s) for s in sections])

    for section in sections.values():
        parent = sections[section['parent']]['tag'] if section['parent'] else article
        parent.append(section['tag'])

    return str(html5)

def _is_empty(elem):
    child_images = [c for c in elem.children if c.name == 'img']
    if child_images:
        return False
    anchors = [c for c in elem.children if c.name == 'a' and 'name' in c.attrs and 'href' not in c.attrs]
    if anchors:
        if elem.previous_sibling.previous_sibling and elem.previous_sibling.previous_sibling.name[0].upper() == 'H':
            elem.previous_sibling.previous_sibling.attrs['id'] = anchors[0].attrs['name']
    elem_contents = [t for t in elem.contents if t and (isinstance(t, str) and t.strip()) or t.name not in ('br',) and t.string and t.string.strip()]
    return len(elem_contents) == 0

def _enclosing_section(elem):
    parent_section = None
    while elem.parent and parent_section is None:
        if elem.name == 'section' or elem.attrs.get('id') == 'essay':
            parent_section = elem
            break
        elem = elem.parent
    return parent_section

def _enclosing_section_id(elem, default=None):
    section = _enclosing_section(elem)
    return section.attrs['id'] if section and 'id' in section.attrs else default

def _get_entity_data(qids):
    sparql = open(os.path.join(SPARQL_DIR, 'entities.rq'), 'r').read()
    sparql = sparql.replace('VALUES (?item) {}', f'VALUES (?item) {{ ({") (".join(qids)}) }}')
    context = json.loads(open(os.path.join(SPARQL_DIR, 'entities_context.json'), 'r').read())
    for _ in range(3):
        resp = requests.post(
            'https://query.wikidata.org/sparql',
            headers={
                'Accept': 'text/plain',
                'Content-type': 'application/x-www-form-urlencoded',
                'User-agent': 'JSTOR Labs python client'},
            data='query=%s' % quote(sparql)
        )
        if resp.status_code == 200:
            # Convert N-Triples to json-ld using json-ld context
            graph = Graph()
            graph.parse(data=resp.text, format='nt')
            _jsonld = json.loads(str(graph.serialize(format='json-ld', context=context, indent=None), 'utf-8'))
            if '@graph' not in _jsonld:
                _context = _jsonld.pop('@context')
                _jsonld = {'@context': _context, '@graph': [_jsonld]}
            return _jsonld
        logger.debug(f'_get_entity_data: resp_code={resp.status_code} msg=${resp.text}')

def _update_entities_from_knowledgegraph(markup, refresh=False):
    by_eid = dict([(item['eid'], item) for item in markup.values() if 'eid' in item and is_qid(item['eid'])])
    if by_eid:
        cache_key = hashlib.sha256(str(sorted(by_eid.keys())).encode('utf-8')).hexdigest()
        kg_entities = cache.get(cache_key) if not refresh else None
        from_cache = kg_entities is not None
        if kg_entities is None:
            kg_entities = _get_entity_data([eid for eid in by_eid.keys() if eid.split(':')[0] in ('wd', 'jstor')])['@graph']
            cache[cache_key] = kg_entities
        # logger.info(json.dumps(kg_entities, indent=2))
        for entity in kg_entities:
            if 'whos_on_first_id' in entity:
                wof = entity.pop('whos_on_first_id')
                wof_parts = [wof[i:i+3] for i in range(0, len(wof), 3)]
                entity['geojson'] = f'https://data.whosonfirst.org/{"/".join(wof_parts)}/{wof}.geojson'
        for kg_props in kg_entities:
            if kg_props['id'] in by_eid:
                me = by_eid[kg_props['id']]
                me['fromCache'] = from_cache
                for k, v in kg_props.items():
                    if k in ('aliases',) and not isinstance(v, list):
                        v = [v]
                    elif k == 'qid' and ':' not in kg_props[k]:
                        v = f'wd:{kg_props[k]}'
                    elif k == 'coords':
                        coords = []
                        for coords_str in v:
                            coords.append([float(c.strip()) for c in coords_str.replace('Point(','').replace(')','').split()[::-1]])
                        v = coords
                    elif k == 'category':
                        if 'category' in me:
                            v = me['category']
                    if k in ('aliases',) and k in by_eid[kg_props['id']]:
                        # merge values
                        v = sorted(set(by_eid[kg_props['id']][k] + v))
                    me[k] = v
                    
def _find_ve_markup(soup):
    ve_markup = {}
    cur_image = {}
    # custom markup is defined in a var or span elements.  Custom properties are defined with element data-* attribute
    for vem_elem in [vem_elem for vem_tag in ('var', 'span', 'param') for vem_elem in soup.find_all(vem_tag)]:
        attrs = dict([k.replace('data-',''),v] for k,v in vem_elem.attrs.items() if k not in ['class']) if vem_elem.attrs else {}
        tags = [k[3:] for k in attrs if k[:3] == 've-']
        tag = tags[0] if len(tags) == 1 else None
        if tag is None:
            if vem_elem.name in ('param', 'span'):
                tag = 'entity'
            else:
                continue
        else:
            del attrs[f've-{tag}']

        attrs['tag'] = tag
        for attr in attrs:
            if attrs[attr] == '':
                attrs[attr] = 'true'

        if 'id' not in attrs:
            attrs['id'] = f'{tag}-{sum([1 for item in ve_markup.values() if item["tag"] == tag])+1}'

        if 'aliases' in attrs:
            attrs['aliases'] = [alias.strip() for alias in attrs['aliases'].split('|')]
        if 'qid' in attrs:
            attrs['eid'] = attrs.pop('qid')
        if 'eid' in attrs and ':' not in attrs['eid']:
            attrs['eid'] = f'wd:{attrs["eid"]}'

        elif tag == 'entity':
            if 'eid' in attrs:
                for cur_item in ve_markup.values():
                    if cur_item['tag'] == 'entity'and 'eid' in cur_item and cur_item['eid'] == attrs['eid']:
                        attrs = {**attrs, **cur_item}
                        break
            if 'coords' in attrs or 'geojson' in attrs:
                attrs['category'] = 'location'
            pass
            #if 'scope' not in attrs:
            #    attrs['scope'] = 'global'

        elif tag == 'map':
            if 'center' in attrs:
                if is_qid(attrs['center']):
                    attrs['center'] = _qid_coords(attrs['center'])
                else:
                    try:
                        attrs['center'] = [float(c.strip()) for c in attrs['center'].replace(',', ' ').split()]
                    except:
                        attrs['center'] = [25, 0]
            if 'zoom' in attrs:
                try:
                    attrs['zoom'] = round(float(attrs['zoom']), 1)
                except:
                    attrs['zoom'] = 2.5

            if 'title' in attrs:
                try:
                    formatted_val = markdown_parser.markdown(attrs['title'], output_format='html5').replace('<p>','').replace('</p>','')
                    logger.info(attrs['title'])
                    logger.info(formatted_val)
                    if formatted_val != attrs['title']:
                        attrs['title_formatted'] = formatted_val
                        attrs['title'] = attrs['title'].replace(' _', ' ').replace('_ ', ' ').replace(' *', ' ').replace('* ', ' ')
                except:
                    attrs['title'] = attrs['title']

        elif tag == 'map-layer':
            for layer_type in ('geojson', 'mapwarper'):
                if layer_type in attrs:
                    attrs['type'] = layer_type
                    del attrs[layer_type]

        elif tag == 'image':
            try:
                for attr in ('gallery', 'layers', 'curtain', 'compare'):
                    if attr in attrs and attrs[attr] == 'true':
                        attrs.pop(attr)
                        attrs['mode'] = attr

                for attr in ('title', 'label', 'description', 'attribution'):
                    if attr in attrs:
                        formatted_val = markdown_parser.markdown(attrs[attr], output_format='html5').replace('<p>','').replace('</p>','')
                        # logger.info(f'{attr} {attrs[attr]} {formatted_val}')
                        if formatted_val != attrs[attr]:
                            attrs[f'{attr}_formatted'] = formatted_val
                            attrs[attr] = attrs[attr].replace(' _', ' ').replace('_ ', ' ').replace(' *', ' ').replace('* ', ' ')

                cur_image = attrs
            except:
                pass # del attrs['region']

        elif tag == 'annotation' and cur_image:
            if 'annotations' not in cur_image:
                cur_image['annotations'] = []
            cur_image['annotations'].append(attrs)

        elif tag == 'audio':
            source = attrs.get('src', attrs.get('url'))
            if source:
                audio_type = source.split('.')[-1]
                if audio_type in ('mp3', 'ogg'):
                    audio_contol = soup.new_tag('audio', controls=None)
                    audio_contol.attrs['id'] = attrs['id']
                    audio_contol.append(soup.new_tag('source', src=source, type=f'audio/{"mpeg" if audio_type == "mp3" else "ogg"}'))
                    audio_contol['style'] = 'width:150px; height:30px; margin-bottom:-6px;'
                    vem_elem.replace_with(audio_contol)
                else:
                    vem_elem.decompose()
            else:
                vem_elem.decompose()

        attrs['tagged_in'] = attrs.get('tagged_in', [])

        # add id of enclosing element to entities 'tagged_in' attribute
        if vem_elem.parent and vem_elem.parent.name == 'p': # enclosing element is a paragraph
            if 'id' in vem_elem.parent.attrs and not _is_empty(vem_elem.parent):
                enclosing_element_id = vem_elem.parent.attrs['id']
            else:
                enclosing_element_id = _enclosing_section_id(vem_elem, soup.html.body.article.attrs['id'])
            if enclosing_element_id not in attrs['tagged_in'] and attrs.get('scope') != 'element':
                attrs['tagged_in'].append(enclosing_element_id)
            if tag in ('entity',) and vem_elem.text:
                data_attrs = [attr for attr in vem_elem.attrs if attr.startswith('data-')]
                if len(data_attrs) == 0:
                    vem_elem.attrs['data-eid'] = attrs.get('eid', attrs.get('id'))
                    vem_elem.attrs['class'] = [tag, 'tagged']
                #if _type == 'geojson':
                #    attrs['scope'] = 'element'
            else:
                vem_elem.decompose()
        # logger.info(f'{attrs["id"]} {attrs["tagged_in"]}')

        if attrs['id'] in ve_markup:
            for fld in attrs['id']:
                if fld in ('id',): continue
                elif fld in ('tagged_in', 'found_in', 'aliases'):
                    # merge multi-valued fields
                    if fld in attrs:
                        if fld not in ve_markup[attrs['id']]:
                            ve_markup[attrs['id']][fld] = []
                        for val in attrs[fld]:
                            if val not in ve_markup[attrs['id']][fld]:
                                ve_markup[attrs['id']][fld].append(val)
                else:
                    ve_markup[attrs['id']][fld] = attrs[fld]
        else:
            ve_markup[attrs['id']] = attrs

    # logger.info(json.dumps(ve_markup, indent=2))
    return ve_markup

def _ids_for_elem(elem):
    section_ids = []
    while elem:
        if elem.name in('p', 'section', 'article') and 'id' in elem.attrs:
            section_ids.append(elem.attrs['id'])
        elem = elem.parent
    return section_ids

def _find_and_tag_items(soup, markup):
    def tm_regex(s):
        return r'(^|\W)(%s)($|\W|[,:;])' % re.escape(s.lower())

    def tag_visible(element):
        '''Returns true if text element is visible and not a comment.'''
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True

    to_match = {}
    for item in [item for item in markup.values() if item['tag'] in ('entity', 'map-layer')]:
        if 'label' in item:
            to_match[tm_regex(item['label'])] = {'str': item['label'], 'item': item}
        if item.get('aliases'):
            for alias in item['aliases']:
                to_match[tm_regex(alias)] = {'str': alias, 'item': item}

    for e in [e for e in filter(tag_visible, soup.findAll(text=True)) if e.strip() != '']:
        context = _ids_for_elem(e)
        context_set = set(context)
        snorm = e.string.lower()
        matches = []
        for tm in sorted(to_match.keys(), key=len, reverse=True):
            item = to_match[tm]['item']
            try:
                for m in re.finditer(tm, snorm):
                    matched = m[2]
                    start = m.start(2)
                    end = start + len(matched)
                    logger.debug(f'{item.get("label")} "{tm}" "{e[start:end]}" {start}')
                    overlaps = False
                    for match in matches:
                        mstart = match['idx']
                        mend = mstart + len(match['matched'])
                        if (start >= mstart and start <= mend) or (end >= mstart and end <= mend):
                            logger.debug(f'{tm} overlaps with {match["matched"]} {match["idx"]}')
                            overlaps = True
                            break
                    if not overlaps:
                        _m = {'idx': start, 'matched': e.string[start:end], 'item': to_match[tm]['item']}
                        matches.append(_m)

            except:
                raise
        matches.sort(key=lambda x: x['idx'], reverse=False)
        logger.debug(json.dumps([{'idx': m['idx'], 'matched': m['matched']} for m in matches], indent=2))
        if matches:
            p = e.parent
            s = e.string
            for idx, child in enumerate(p.children):
                if child == e:
                    break

            cursor = None
            replaced = []
            for rec in matches:
                m = rec['idx']
                item = rec['item']
                if not cursor or m > cursor:
                    seg = s[cursor:m]
                    if replaced:
                        p.insert(idx+len(replaced), seg)
                    else:
                        e.replace_with(seg)
                    replaced.append(seg)
                    cursor = m

                logger.debug(f'{rec["matched"]} tagged_in={item["tagged_in"]} scope={item.get("scope")} context={context} in_scope={len(set(item["tagged_in"]).intersection(context_set)) > 0}')

                if context[0] not in item.get('found_in',[]) and (item.get('scope') == 'global' or (item.get('scope') not in ('element',) and set(item['tagged_in']).intersection(context_set))):
                    # make tag for matched item
                    seg = soup.new_tag('span')
                    seg.string = rec['matched']
                    seg.attrs['title'] = item.get('title', item.get('label'))
                    seg.attrs['class'] = ['entity', 'inferred']
                    if 'category' in item:
                        seg.attrs['class'].append(item['category'])
                    # if 'eid' in item:
                    seg.attrs['data-eid'] = item.get('eid', item.get('id'))
                    if 'found_in' not in item:
                        item['found_in'] = []
                    if context[0] not in item['found_in']:
                        item['found_in'].append(context[0])
                else:
                    seg = s[cursor:cursor+len(rec['matched'])]

                if replaced:
                    p.insert(idx+len(replaced), seg if p.name in ('p', 'em', 'strong') else rec['matched'])
                else:
                    e.parent.attrs['title'] = item.get('title', item.get('label'))
                replaced.append(rec['matched'])
                cursor += len(rec['matched'])

            if cursor < len(s):
                seg = s[cursor:]
                p.insert(idx+len(replaced), seg)
                replaced.append(seg)

def _qid_coords(qid):
    global cache
    cache_key = '%s-coords' % (qid)
    coords = cache.get(cache_key)
    if not coords:
        sparql = f'SELECT ?coords WHERE {{ wd:{qid.split(":")[-1]} wdt:P625 ?coords . }}'
        for _ in range(3):
            resp = requests.post(
                'https://query.wikidata.org/sparql',
                headers={
                    'Accept': 'application/sparql-results+json',
                    'Content-type': 'application/x-www-form-urlencoded',
                    'User-agent': 'JSTOR Labs python client'},
                data='query=%s' % quote(sparql)
            )
            if resp.status_code == 200:
                bindings = resp.json()['results']['bindings']
                if len(bindings) > 0:
                    coords_str = bindings[0]['coords']['value']
                    coords = [float(c.strip()) for c in coords_str.replace('Point(','').replace(')','').split()[::-1]]
                    cache[cache_key] = coords
    return coords

def _add_entity_classes(soup, markup):
    for entity in [vem_elem for vem_tag in ('var', 'span') for vem_elem in soup.find_all(vem_tag, {'class': 'entity'})]:
        if 'category' in markup.get(entity.attrs.get('data-eid'), {}):
            entity.attrs['class'] = sorted(set([cls for cls in entity.attrs['class'] if cls != 'entity'] + [markup[entity.attrs['data-eid']]['category']]))

def _remove_empty_paragraphs(soup):
    for para_elem in soup.findAll(lambda tag: tag.name in ('p',)):
        if _is_empty(para_elem):
            para_elem.extract()

def _add_heading_ids(soup):
    for lvl in range(1, 9):
        for heading in soup.findAll(lambda tag: tag.name in ('h%s' % lvl,)):
            if 'id' not in heading.attrs:
                heading.attrs['id'] = slugify(heading.text)

def _get_manifest(item, essay_path, acct, repo):
    logger.debug(f'_get_manifest_iiifhosting {item}')
    if 'manifest' not in item:
        label_map = {'title': 'label', 'date': 'navDate'}
        data = {**dict([(label_map.get(k,k),item[k]) for k in item if k not in ('id', 'region', 'fit', 'hires', 'iiif-url', 'static', 'iiif', 'tag', 'tagged_in')]),
                **{'acct': acct, 'repo': repo, 'essay': essay_path}}
        data['iiif'] = 'true'
        resp = requests.post('https://iiif-v2.visual-essays.app/manifest/', headers={'Content-type': 'application/json'}, json=data)
        if resp.status_code == 200:
            item['manifest'] = resp.json()['@id']
    return item

_manifests_cache = {}
def _get_manifests(markup, essay_path, acct, repo):
    global _manifests_cache
    logger.debug(f'_get_manifests: essay_path={essay_path} acct={acct} repo={repo}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for item in markup.values():
            if item['tag'] == 'image':
                if 'manifest' not in item and 'url' in item:
                    mid = hashlib.sha256(f'{acct.lower()}{repo}{essay_path}{item["url"]}'.encode()).hexdigest()
                    logger.debug(f'{item["id"]} {item["tag"]} {mid} {mid in _manifests_cache}')
                    if mid in _manifests_cache:
                        item['manifest'] = _manifests_cache[mid]
                        continue

                futures[executor.submit(_get_manifest, item, essay_path, acct, repo)] = item['id']

        for future in concurrent.futures.as_completed(futures):
            item = future.result()
            if 'manifest' in item:
                _manifests_cache[item['manifest'].split('/')[-1]] = item['manifest']
            logger.debug(f'id={item["id"]} manifest={item.get("manifest")}')

def _add_data(soup, markup):
    data = soup.new_tag('script')
    data.attrs['type'] = 'application/javascript'
    data.attrs['data-ve-tags'] = ''
    data.append('\nwindow.data = ' + json.dumps([markup[_id] for _id in sorted(markup)], indent=2) + '\n')
    soup.html.body.append(data)

def is_qid(s, ns_required=False):
    if not s or not isinstance(s, str): return False
    split = s.split(':')
    if ns_required and len(split) == 1:
        return False
    eid = split[-1]
    return len(eid) > 1 and eid[0] == 'Q' and eid[1:].isdecimal()

def parse(html, md_path, acct, repo):
    soup = BeautifulSoup(html, 'html5lib')
    for comment in soup(text=lambda text: isinstance(text, Comment)):
        comment.extract()
    markup = _find_ve_markup(soup)
    _update_entities_from_knowledgegraph(markup)
    _find_and_tag_items(soup, markup)
    _add_entity_classes(soup, markup)
    _remove_empty_paragraphs(soup)
    _add_heading_ids(soup)
    _get_manifests(markup, md_path, acct, repo)
    _add_data(soup, markup)
    return str(soup)

def _is_local(site):
    is_local = site.startswith('localhost') or site.endswith('gitpod.io')
    logger.debug(f'is_local={is_local}')
    return is_local

def get_essay(markdown, site, acct, repo, ref, path, root, raw, token, **kwargs):
    if not path:  path = '/'
    logger.debug(f'essay: has_markdown={markdown is not None} site={site} acct={acct} repo={repo} ref={ref} root={root} path={path}')
    md_path = path
    content = url = sha = None
    if root and _is_local(site):
        markdown, md_path = get_local_markdown(path=f'/{"/".join(path.split("/")[3:])}', root=root)
    if markdown is None:
        markdown, md_path, url, sha = get_gh_markdown(acct, repo, ref, f'/{"/".join(path.split("/")[3:])}', token)
    if markdown:
        if raw:
            content = markdown
        else:
            if md_path[0] != '/':
                md_path = f'/{md_path}'
            html = markdown_to_html5(markdown, site, acct, repo, ref, md_path, root)
            content = parse(html, md_path or path, acct, repo)
    return content, url, sha, md_path

def usage():
    print(f'{sys.argv[0]} [hl:a:r:b:s:t:] path')
    print(f'   -h --help          Print help message')
    print(f'   -l --loglevel      Logging level (default=warning)')
    print(f'   -a --acct          Github account (default="jstor-labs")')
    print(f'   -r --repo          Github repo (default="{DEFAULT_REPO}")')
    print(f'   -b --ref           Github ref (default="main")')
    print(f'   -s --site          Site (default="localhost")')
    print(f'   -t --token         Github token')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    site = 'localhost'
    token = None
    site_config = {'acct': 'jstor-labs', 'repo': DEFAULT_REPO, 'ref': 'main'}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:a:r:b:s:t:', ['help', 'loglevel', 'acct', 'repo', 'ref', 'site', 'tokeh'])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-l', '--loglevel'):
            loglevel = a.lower()
            if loglevel in ('error',): logger.setLevel(logging.ERROR)
            elif loglevel in ('warn','warning'): logger.setLevel(logging.INFO)
            elif loglevel in ('info',): logger.setLevel(logging.INFO)
            elif loglevel in ('debug',): logger.setLevel(logging.DEBUG)
        elif o in ('-a', '--acct'):
            site_config['acct'] = a
        elif o in ('-r', '--repo'):
            site_config['repo'] = a
        elif o in ('-b', '--ref'):
            site_config['ref'] = a
        elif o in ('-s', '--site'):
            site = a
        elif o in ('-t', '--token'):
            token = a
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    path = args[0] if len(args) == 1 else '/'
    # print(get_essay(path, BASEDIR, site, site_config, token))
