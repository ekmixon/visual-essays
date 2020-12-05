#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import sys
import re
import json
import traceback
import getopt
import base64
from urllib.parse import urlparse, unquote, urlencode

import requests
logging.getLogger('requests').setLevel(logging.INFO)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

from flask import Flask, request, send_from_directory, redirect, Response, jsonify, g

app = Flask(__name__)

from essay import get_essay

KNOWN_SITES = {
    'plant-humanities.app': {'acct': 'jstor-labs', 'repo': 'plant-humanities'},
    'kent-maps.online': {'acct': 'kent-map', 'repo': 'kent'}
}

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Credentials': True,
    'Access-Control-Allow-Methods': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD',
    'Access-Control-Allow-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Access-Control-Expose-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Allow': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD'
}

default_gh_token = os.environ.get('gh_token')
if default_gh_token is None and os.path.exists(f'{SCRIPT_DIR}/gh-token'):
    with open(f'{SCRIPT_DIR}/gh-token', 'r') as fp:
        default_gh_token = fp.read().strip()

def _get_gh_file(path, acct, repo, branch='main', gh_token=None):
    global default_gh_token
    gh_token = gh_token if gh_token else default_gh_token
    logger.info(f'get_gh_file: acct={acct} repo={repo} branch={branch} path={path} gh_token={gh_token}')
    content = sha = None
    url = f'https://api.github.com/repos/{acct}/{repo}/contents{path}?ref={branch}'
    resp = requests.get(url, headers={
        'Authorization': f'Token {gh_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'JSTOR Labs visual essays client'
    })
    logger.info(f'{url} {resp.status_code}')
    if resp.status_code == 200:
        resp = resp.json()
        content = base64.b64decode(resp['content']).decode('utf-8')
        sha = resp['sha']
    return content, sha

def _check_local(site):
    is_local = site.startswith('localhost') or site.endswith('gitpod.io')
    logger.info(f'is_local={is_local}')
    return is_local

def _get_acct_repo_branch(path):
    acct = repo = branch = None
    site = urlparse(request.base_url).hostname
    site = site[4:] if site[:4] in ('dev.', 'exp.') else site
    if site == 'visual-essays.app' or _check_local(site):
        path_elems = path[1:].split('/')
        if len(path_elems) > 1:
            acct, repo = path_elems[:2]
        else:
            acct, repo = ('jstor-labs', 've-docs')
    elif site in KNOWN_SITES:
        acct = KNOWN_SITES[site]['acct']
        repo = KNOWN_SITES[site]['repo']
    qargs = dict([(k, request.args.get(k)) for k in request.args])
    branch = qargs.get('ref', 'main')
    logger.info(f'site={site} acct={acct} repo={repo} branch={branch}')
    return site, acct, repo, branch

_site_configs = {}
def _site_config(path):
    global _site_configs
    site, acct, repo, branch = _get_acct_repo_branch(path)
    config_key = f'{acct}/{repo}/{branch}'
    if config_key not in _site_configs:
        if _check_local(site) and config_key.startswith('jstor-labs/ve-docs/'):
            _config = json.load(open(os.path.join(BASEDIR, 'config.json'), 'r'))
        else:
            content, sha = _get_gh_file('/config.json', acct, repo, branch)
            _config = json.loads(content)
        if _config:
            _site_configs[config_key] = _config
    return _site_configs.get(config_key, {})

@app.route('/config/<path:path>', methods=['GET'])
@app.route('/config/', methods=['GET'])
@app.route('/config.json', methods=['GET'])
@app.route('/config', methods=['GET'])
def config(path=None):
    path = f'/{path}' if path else '/'
    site = urlparse(request.base_url).hostname
    logger.info(f'config: site={site}')
    return _site_config(path), 200

@app.route('/essay/<path:path>', methods=['GET'])
@app.route('/essay/', methods=['GET'])
def essay(path=None):
    path = f'/{path}' if path else '/'
    site = urlparse(request.base_url).hostname
    logger.info(f'essay: site={site} path={path}')
    return get_essay(path, BASEDIR, site, _site_config(path), default_gh_token), 200

@app.route('/<path:path>', methods=['GET'])
@app.route('/', methods=['GET'])
def main(path=None):
    path = f'/{path}' if path else '/'
    qargs = dict([(k, request.args.get(k)) for k in request.args])
    parsed_base_url = urlparse(request.base_url)
    site = parsed_base_url.hostname
    logger.info(f'main: site={site} path={path}')
    for _dir in (SCRIPT_DIR, BASEDIR):
        abs_path = os.path.join(_dir, 'index.html')
        if os.path.exists(abs_path):
            with open(abs_path, 'r') as fp:
                html = fp.read()
                return html, 200

def usage():
    print('%s [hl:d]' % sys.argv[0])
    print('   -h --help             Print help message')
    print('   -l --loglevel         Logging level (default=warning)')
    print('   -d --dev              Use local Visual Essay JS Lib')

if __name__ == '__main__':
    kwargs = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hl:d', ['help', 'loglevel', 'dev'])
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
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, 'unhandled option'

    app.run(debug=True, host='0.0.0.0', port=8080)