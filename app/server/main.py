#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import sys
import re
import json
import getopt
import base64
from urllib.parse import urlparse, parse_qs, unquote, urlencode

import requests
logging.getLogger('requests').setLevel(logging.INFO)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.dirname(SCRIPT_DIR)
while BASEDIR != '/' and not os.path.exists(os.path.join(BASEDIR, 'index.html')):
    BASEDIR = os.path.dirname(BASEDIR)
logger.info(f'SCRIPT_DIR={SCRIPT_DIR} BASEDIR={BASEDIR}')

from flask import Flask, request, send_from_directory, redirect, Response, jsonify, g
app = Flask(__name__, static_url_path='/static', static_folder=os.path.join(BASEDIR, 'static'))

from essay import get_essay
from gh import gh_token, query_gh_file, get_gh_file, has_gh_repo_prefix, get_site_config

from expiringdict import ExpiringDict
expiration = 60 * 60 * 24 # one day
cache = ExpiringDict(max_len=200, max_age_seconds=expiration)

ENV = 'prod'
CONTENT_ROOT = None
DEFAULT_GH_ACCT = 'jstor-labs'
DEFAULT_GH_REPO = 've-docs'

KNOWN_SITES = {
    'default': ['jstor-labs', 've-docs'],
    'plant-humanities.app': ['jstor-labs', 'plant-humanities'],
    'kent-maps.online': ['kent-map', 'kent']
}

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Credentials': True,
    'Access-Control-Allow-Methods': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD',
    'Access-Control-Allow-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Access-Control-Expose-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Allow': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD'
}

def _is_local(site):
    return site.startswith('localhost') or site.endswith('gitpod.io')

def _is_ve_site(site):
    _site = site[4:] if site[:4] in ('dev.', 'exp.') else site
    return _site == 'visual-essays.app' or _is_local(site)

def qargs():
    return dict([(k, request.args.get(k)) for k in request.args])

def _normalize_path(path):
    return f'/{path[:-1] if path[-1] == "/" else path}' if path else '/'

def _get_site_info(href):
    parsed = urlparse(href)
    hostname = parsed.hostname
    path_elems = [elem for elem in parsed.path.split('/') if elem]
    logger.info(f'hostname={hostname} path_elems={path_elems}')
    repo_info = None
    site_info = {
        'ghpSite': False,
        'private': False,
        'baseurl': '',
        'acct': DEFAULT_GH_ACCT,
        'repo': DEFAULT_GH_REPO,
        'ref': None,
        'defaultBranch': None,
        'editBranch': None
    }
    siteConfigUrl = None
    if hostname.endswith('.github.io'):
        site_info.update({
            'ghpSite': True,
            'acct':    hostname[:-10],
            'repo':    path_elems[0],
            'baseurl': f'/{path_elems[0]}'
        })
    elif hostname == 'localhost' or hostname.endswith('visual-essays.app') or hostname.endswith('gitpod.io'):
        if len(path_elems) >= 2:
            resp = requests.get(f'https://api.github.com/repos/{path_elems[0]}/{path_elems[1]}')
            if resp.status_code == 200:
                repo_info = resp.json()
                site_info.update({
                    'acct': path_elems[0],
                    'repo': path_elems[1], 
                    'defaultBranch': repo_info['default_branch'],
                    'ref': site_info['ref'] if site_info['ref'] else repo_info['default_branch'],
                    'baseurl': f'/{path_elems[0]}/{path_elems[1]}'
                })
    else:
        siteConfigUrl = f'{parsed.scheme}://{parsed.netloc}/config.json'

    if repo_info is None:
        url = f'https://api.github.com/repos/{site_info["acct"]}/{site_info["repo"]}'
        resp = requests.get(url)
        logger.info(f'repos: {url} {resp.status_code}')
        if resp.status_code == 200:
            repo_info = resp.json()
            if site_info['ref'] is None:
                site_info['ref'] = repo_info['default_branch']
            site_info['defaultBranch'] = repo_info['default_branch']

    if not siteConfigUrl:
        if repo_info is None and site_info['ghpSite'] == True: # Probably a private GH site 
            siteConfigUrl = f'https://{hostname}{site_info["baseurl"]}/config.json'
        else:
            siteConfigUrl = f'https://raw.githubusercontent.com/{site_info["acct"]}/{site_info["repo"]}/{site_info["ref"]}/config.json'
    resp = requests.get(siteConfigUrl)
    logger.info(f'siteConfig: {siteConfigUrl} {resp.status_code}')
    if resp.status_code == 200:
        site_config = resp.json()
        site_info.update({
            'acct': site_config.get('acct', site_info['acct']),
            'repo': site_config.get('repo', site_info['repo']),
            'ref':  site_info['ref'] if site_info['ref'] else site_config.get('ref'),
            'private': repo_info is None and site_info['ghpSite'] == True
        })
        
        if CONTENT_ROOT:
            resource_baseurl = f'{parsed.scheme}://{parsed.netloc}/static'
        else:
            resource_baseurl = f'https://raw.githubusercontent.com/{site_info["acct"]}/{site_info["repo"]}/{site_info["ref"]}'
        for key, value in site_config.items():
            if key == 'components':
                site_info['components'] = []
                for comp in value:
                    if not comp['src'].startswith('http'):
                        comp['src'] = f'{resource_baseurl}{"" if comp["src"][0] == "/" else "/"}{comp["src"]}'
                    site_info['components'].append(comp)
            elif key in ('banner', 'favicon', 'logo') and not value.startswith('http'):
                value = f'{resource_baseurl}{"" if value[0] == "/" else "/"}{value}'
            site_info[key] = value

    if site_info['ref'] and len(site_info['ref']) == 7 and re.match(r'^[0-9a-f]+$', site_info['ref']):
        resp = requests.get(
            f'https://api.github.com/repos/{site_info["acct"]}/{site_info["repo"]}/commits/{site_info["ref"]}/branches-where-head',
            headers = {'Accept': 'application/vnd.github.groot-preview+json'}
        )
        if resp.status_code == 200:
            commit_info = resp.json()
            site_info['editBranch'] = commit_info[0]['name']
    else:
        site_info['editBranch'] = site_info['ref']
    return site_info

def _context(path=None):
    path = _normalize_path(path)
    site = urlparse(request.base_url).hostname
    logger.info(f'_context: _is_ve_site={_is_ve_site(site)} gh_repo_prefix={has_gh_repo_prefix(path)}')
    if _is_ve_site(site) and has_gh_repo_prefix(path):
        acct, repo = path[1:].split('/')[:2]
    else:
        acct, repo = KNOWN_SITES.get(site, KNOWN_SITES['default'])
    ref = qargs().pop('ref', None)
    if ref is None:
        ref = get_site_config(acct, repo)['ref']
    return site, acct, repo, ref, path, qargs()

@app.route('/config.json', methods=['GET'])
def local_config():
    logger.info(f'local_config: ENV={ENV} CONTENT_ROOT={CONTENT_ROOT}')
    if ENV == 'dev' and CONTENT_ROOT:
        config_path = os.path.join(CONTENT_ROOT, 'config.json')
        if os.path.exists(config_path):
            return json.load(open(config_path, 'r')), 200
    return 'Not found', 404

@app.route('/config/<path:path>', methods=['GET'])
@app.route('/config/', methods=['GET'])
@app.route('/config', methods=['GET'])
def config(path=None):
    site, acct, repo, ref, path, qargs = _context(path)
    logger.info(f'config: site={site} acct={acct} repo={repo} ref={ref} path={path}')
    raw, _, _ = query_gh_file( acct, repo, ref, '/config.json')
    _config = json.loads(raw) if raw is not None else {} 
    _config.update({'acct': acct, 'repo': repo, 'ref': ref})
    return _config, 200, cors_headers

@app.route('/essay/<path:path>', methods=['GET'])
@app.route('/essay/', methods=['GET'])
def essay(path=None):
    global cache
    markdown = content = None
    site, acct, repo, ref, path, qargs = _context(path)
    raw = qargs.get('raw', 'false') in ('', 'true')
    cache_key = f'{site}|{acct}|{repo}|{ref}|{path}'
    cached_essay = cache.get(cache_key) if not ENV == 'dev' else None
    if cached_essay:
        markdown, _ , md_sha = get_gh_file(cached_essay['url'])
        if cached_essay['sha'] == md_sha:
            content = markdown if raw else cached_essay['html']
    
    logger.info(f'essay: site={site} acct={acct} repo={repo} ref={ref} path={path} raw={raw} cached={cached_essay is not None and content is not None}')
    
    if content is None:
        essay_args = {
            'markdown': markdown,
            'site': site,
            'acct': acct,
            'repo': repo,
            'ref': ref,
            'path': path,
            'root': CONTENT_ROOT,
            'raw': raw,
            'token': gh_token()}
        content, md_url, md_sha = get_essay(**essay_args)
        if content and not raw:
            cache[cache_key] = {'html': content, 'url': md_url, 'sha': md_sha}

    if content:
        return content, 200, cors_headers
    return 'Not found', 404

@app.route('/components/<path:path>', methods=['GET'])
def components(path):
    full_path = f'{BASEDIR}/components/{path}'
    logger.info(f'components: path={path} full_path={full_path} exists={os.path.exists(full_path)}')
    if os.path.exists(full_path):
        path_elems = full_path.split('/')
        return send_from_directory(f'/{"/".join(path_elems[:-1])}', path_elems[-1], as_attachment=False), 200, cors_headers
    else:
        return 'Not found', 404

@app.route('/markdown-viewer/<path:path>', methods=['GET']) 
def markdown_viewer(path=None):
    logger.info(f'markdown-viewer: path={path}')
    return (open(os.path.join(SCRIPT_DIR, 'markdown-viewer.html'), 'r').read(), 200, cors_headers)

_site_info_cache = {}
@app.route('/site-info/', methods=['GET'])
@app.route('/site-info', methods=['GET'])
def siteinfo(path=None):
    site, acct, repo, ref, path, qargs = _context()
    href = qargs.get('href')
    if href not in _site_info_cache:
        site_info = _get_site_info(href)
        _site_info_cache[href] = site_info
    logger.info(f'site-info: href={href} site_info={_site_info_cache[href]}')
    return _site_info_cache[href], 200, cors_headers

@app.route('/<path:path>', methods=['GET'])
@app.route('/', methods=['GET'])
def main(path=None):
    site, acct, repo, ref, path, qargs = _context(path)
    logger.info(f'main: site={site} acct={acct} repo={repo} ref={ref} path={path}')
    with open(os.path.join(BASEDIR, 'index.html'), 'r') as fp:
        html = fp.read()
        if site == 'localhost':
            html = re.sub(r'"/visual-essays/static/', f'"/static/', html)
        if ENV == 'dev':
            if site.endswith('gitpod.io'):
                html = re.sub(r'"/static/js/visual-essays.+"', f'"{os.environ.get("core_js_host")}/lib/visual-essays.js"', html)
            else:
                html = re.sub(r'"/static/js/visual-essays.+"', f'"http://{site}:8088/js/visual-essays.js"', html)
        return html, 200

    return 'Not found', 404

def usage():
    print('%s [hl:da:r:c:]' % sys.argv[0])
    print('   -h --help             Print help message')
    print('   -l --loglevel         Logging level (default=warning)')
    print('   -d --dev              Use local Visual Essay JS Lib')
    print('   -a --acct             Default Github account (jstor-labs)')
    print('   -r --repo             Default Github repository (ve-docs)')
    print('   -c --root             Content root')

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hl:da:r:c:', ['help', 'loglevel', 'dev', 'acct', 'repo', 'root'])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-l', '--loglevel'):
            loglevel = a.lower()
            if loglevel in ('error',): logger.setLevel(logging.ERROR)
            elif loglevel in ('warn','warning'): logger.setLevel(logging.INFO)
            elif loglevel in ('info',): logger.setLevel(logging.INFO)
            elif loglevel in ('debug',): logger.setLevel(logging.DEBUG)
        elif o in ('-d', '--dev'):
            ENV = 'dev'
        elif o in ('-a', '--acct'):
            KNOWN_SITES['default'][0] = a
        elif o in ('-r', '--repo'):
            KNOWN_SITES['default'][1] = a
        elif o in ('-c', '--root'):
            CONTENT_ROOT = d
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, 'unhandled option'

    logger.info(f'ENV={ENV}')
    app.run(debug=True, host='0.0.0.0', port=8080)