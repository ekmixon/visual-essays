#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s')
logger = logging.getLogger()

import os
import sys
import json
import getopt
import pypandoc
from bs4 import BeautifulSoup

from urllib.parse import quote

import requests
logging.getLogger('requests').setLevel(logging.INFO)

GRAPHS = [
    {
        'ns': 'jstor',
        'prefix': 'http://kg.jstor.org/entity/',
        # 'sparql_endpoint': 'https://kg-query.jstor.org/proxy/wdqs/bigdata/namespace/wdq/sparql'
        'sparql_endpoint': 'https://cy9in0xsv5.execute-api.us-east-1.amazonaws.com/prod/sparql',
    },
    {
        'ns': 'wd',
        'prefix': 'http://www.wikidata.org/entity/',
        'sparql_endpoint': 'https://query.wikidata.org/sparql'
    }
]
PREFIXES = dict([(g['ns'],g['prefix']) for g in GRAPHS])
DEFAULT_NS = 'wd'

def _as_uri(s, acct=None, repo=None, **kwargs):
    uri = None
    if s.startswith('http'):
        uri = s
    else:
        prefix, entity_id = s.split(':') if ':' in s else (DEFAULT_NS, s)
        if prefix in PREFIXES and _is_entity_id(entity_id, False):
            uri = f'{PREFIXES[prefix]}{entity_id}'
    return uri

def _is_entity_id(s, ns_required=True):
    if not s or not isinstance(s, str): return False
    eid = s.split(':')
    if len(eid) == 1 and ns_required:
        return False
    if len(eid) == 2 and eid[0] not in PREFIXES:
        return False
    if len(eid) > 2:
        return False
    return len(eid[-1]) > 1 and eid[-1][0] in ('Q', 'P') and eid[-1][1:].isdecimal()

def _mw_url(eid):
    entity_uri = _as_uri(eid)
    graph = [g for g in GRAPHS if entity_uri.startswith(g['prefix'])][0]
    sparql = '''
        SELECT ?mwPage {
            ?mwPage schema:about <%s> .
            ?mwPage schema:isPartOf <https://en.wikipedia.org/> .
        }''' % (entity_uri)
    resp = requests.post(
        graph['sparql_endpoint'],
        headers={
            'Accept': 'application/sparql-results+json;charset=UTF-8',
            'Content-type': 'application/x-www-form-urlencoded',
            'User-agent': 'JSTOR Labs python client'},
        data='query=%s' % quote(sparql)
    )
    logger.debug(f'{graph["sparql_endpoint"]} {sparql} {resp.status_code}')
    if resp.status_code == 200:
        resp = resp.json()
        if resp['results']['bindings']:
            return resp['results']['bindings'][0]['mwPage']['value']

def mw_page(eid, format='mediawiki'):
    mw_url = _mw_url(eid)
    mw_title = mw_url.split('/')[-1] if mw_url else None
    logger.info(f'mw_page: eid={eid} title={mw_title}')
    if not mw_title: return
    resp = requests.get(f'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles={mw_title}&rvslots=main')
    if resp.status_code == 200:
        resp = resp.json()
        for pageid in resp['query']['pages']:
            wikitext = resp['query']['pages'][pageid]['revisions'][0]['slots']['main']['*']
            as_html = pypandoc.convert_text(wikitext, 'html', format='mediawiki')
            output = pypandoc.convert_text(as_html, format, format='html')
            '''
            if format == 'mediawiki':
                output = wikitext
            else:
                output = pypandoc.convert_text(wikitext, format, format='mediawiki')
            '''
            return output

def eids(titles):
    _eids = {}
    page_uris = ' '.join([f'<https://en.wikipedia.org/wiki/{title}>' for title in titles])
    sparql = 'SELECT ?mwPage ?entity WHERE { VALUES ?mwPage { %s } ?mwPage schema:about ?entity . }' % page_uris
    resp = requests.post(
        'https://query.wikidata.org/sparql',
        headers={
            'Accept': 'application/sparql-results+json;charset=UTF-8',
            'Content-type': 'application/x-www-form-urlencoded',
            'User-agent': 'JSTOR Labs python client'},
        data='query=%s' % quote(sparql)
    )
    if resp.status_code == 200:
        resp = resp.json()
        for item in resp['results']['bindings']:
            _eids[item['mwPage']['value'].split('/')[-1]] = item['entity']['value'].split('/')[-1]
    return _eids

def mentioned_entities(eid):
    mentions = {}
    html = mw_page(eid, 'html')
    titles = {}
    if not html: return
    soup = BeautifulSoup(html, 'html5lib')
    for link in soup.find_all('a'):
        if 'href' in link.attrs and not link.attrs['href'].startswith('#') and not link.attrs['href'].startswith('http') and not link.attrs['href'].startswith('Category'):
            title = link.attrs['href']
            titles[title] = titles.get(title, 0) + 1
    for title, eid in eids(titles.keys()).items():
        mentions[title] = {'eid': eid, 'count': titles[title]}
    return mentions

AVAILABLE_FORMATS = '''
    commonmark (CommonMark Markdown)
    commonmark_x (CommonMark Markdown with extensions)
    docbook (DocBook)
    dokuwiki (DokuWiki markup)
    gfm (GitHub-Flavored Markdown)
    haddock (Haddock markup)
    html (HTML)
    jats (JATS XML)
    json (JSON version of native AST)
    latex (LaTeX)
    markdown (Pandoc’s Markdown)
    markdown_mmd (MultiMarkdown)
    markdown_phpextra (PHP Markdown Extra)
    markdown_strict (original unextended Markdown)
    mediawiki (MediaWiki markup)
    man (roff man)
    muse (Muse)
    native (native Haskell)
    opml (OPML)
    org (Emacs Org mode)
    rst (reStructuredText)
    t2t (txt2tags)
    textile (Textile)
    tikiwiki (TikiWiki markup)
    twiki (TWiki markup)
    vimwiki (Vimwiki)
'''

def usage():
    print(f'{sys.argv[0]} [hl:f:e eid')
    print(f'   -h --help       Print help message')
    print(f'   -l --loglevel   Logging level (default=warning)')
    print(f'   -e --entities   Find mentioned entities')
    print(f'   -f --format     Output format (default=mediawiki)')
    print(f'Available formats: {AVAILABLE_FORMATS}')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    kwargs = {'format': 'mediawiki'}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:f:e', ['help', 'loglevel', 'format', 'entities'])
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
        elif o in ('-e', '--entities'):
            kwargs['entities'] = True
        elif o in ('-f', '--format'):
            kwargs['format'] = a
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    eid = args[0]
    if kwargs.get('entities'):
        print(json.dumps(mentioned_entities(eid)))
    else:
        print(mw_page(eid, **kwargs))
