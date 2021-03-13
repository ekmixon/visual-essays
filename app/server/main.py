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
import hashlib
import base64
import gzip
import jwt
import traceback
import math

from functools import wraps
from PIL import Image
from io import StringIO, BytesIO
import shutil

from urllib.parse import urlparse, parse_qs, quote, unquote, urlencode

import requests
logging.getLogger('requests').setLevel(logging.INFO)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.dirname(SCRIPT_DIR)
while BASEDIR != '/' and not os.path.exists(os.path.join(BASEDIR, 'index.html')):
    BASEDIR = os.path.dirname(BASEDIR)
logger.info(f'SCRIPT_DIR={SCRIPT_DIR} BASEDIR={BASEDIR}')

from flask import Flask, request, send_from_directory, redirect, Response, jsonify, g
from flask_cors import CORS

app = Flask(__name__, static_url_path='/static', static_folder=BASEDIR)
cors = CORS(app, resources={r"/static/*": {"origins": "*"}})

from gh import query_gh_file, get_gh_file, has_gh_repo_prefix, get_site_config
from essay import get_essay
from annotations import query_annotations, get_annotation, create_annotation, update_annotation, delete_annotation, NotFoundException
from entity import KnowledgeGraph, as_uri
from fingerprints import get_fingerprints
from specimens import get_specimens

try:
    from gc_cache import Cache
    cache = Cache(creds_path=f'{BASEDIR}/creds/juncture-gcreds.json')
except:
    logger.warning(f'Cache init failed')
    logger.warning(traceback.format_exc())
    from expiringdict import ExpiringDict
    expiration = 60 * 60 * 24 # one day
    cache = ExpiringDict(max_len=200, max_age_seconds=expiration)

ENV = 'prod'
CONTENT_ROOT = None
OAUTH_ENDPOINT = 'https://labs-auth-atjcn6za6q-uc.a.run.app'

KNOWN_SITES = {
    'default': ['jstor-labs', 've-docs'],
    'plant-humanities.app': ['jstor-labs', 'plant-humanities'],
    'planthumanities.org': ['jstor-labs', 'plant-humanities'],
    'lab.planthumanities.org': ['jstor-labs', 'plant-humanities'],
    'plant-humanities.org': ['jstor-labs', 'plant-humanities'],
    'lab.plant-humanities.org': ['jstor-labs', 'plant-humanities'],
    'kent-maps.online': ['kent-map', 'kent'],
    've.rsnyder.info': ['rsnyder', 've'],
    'docs.juncture-digital.org': ['jstor-labs', 've-docs']
}

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Credentials': True,
    'Access-Control-Allow-Methods': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD',
    'Access-Control-Allow-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Access-Control-Expose-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Allow': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD'
}

# Fetch the public key from the auth service so we can validate tokens,
# we're assuming a locally running auth service here
# In production, the URL would be something like
# https://auth.labs.jstor.org/publickey or https://labs.jstor.org/auth/publickey
try:
    r = requests.get(f'{OAUTH_ENDPOINT}/publickey')
    public_key = r.text
except:
   public_key = None

default_gh_token = os.environ.get('gh_token')
if default_gh_token is None and os.path.exists(f'{BASEDIR}/creds/gh-token'):
    with open(f'{BASEDIR}/creds/gh-token', 'r') as fp:
        default_gh_token = fp.read().strip()

def gh_token():
    try:
        token = g.token
    except:
        token = default_gh_token
    logger.info(f'gh_token: token={token} default_gh_token={default_gh_token}')
    return token 

# Middleware decorator to enforce logins
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure an Authorization header is provided
        if request.headers.get('Authorization', '') == '':
            return jsonify({'msg': 'login required'}), 401
        # Bearer tokens are always prefixed with 'Bearer '
        token_type, token_value = request.headers.get('Authorization').split()
        if token_type == 'GHToken':
            g.token = token_value
            return f(*args, **kwargs)
        elif token_type == 'Bearer':
            try:
                # Validate the JWT against the public key, must be RS256 since we're using RSA keys
                decoded = jwt.decode(token_value, public_key.encode('utf-8'), algorithms='RS256')
                # Store the ghtoken from decoded JWT on the application context for use in request handlers            
                g.token = decoded['token']
                return f(*args, **kwargs)
            except jwt.DecodeError:
                # JWT is not valid (may have expired, or fake token)
                return jsonify({'msg': 'not a valid token'}), 401
        else:
            return jsonify({'msg': 'must be a bearer or github token'})
    return decorated_function

def _is_local(site):
    return site.startswith('localhost') or site.startswith('192.168') or site.endswith('gitpod.io')

def _is_ve_site(site):
    _site = site.split(':')[0]
    _site = _site[4:] if _site[:4] in ('dev.', 'exp.') else _site
    return _site == 'juncture-digital.org' or _is_local(site)

def qargs():
    return dict([(k, request.args.get(k)) for k in request.args])

def _normalize_path(path):
    return f'/{path[:-1] if path[-1] == "/" else path}' if path else '/'

def _get_site_info(href):
    parsed = urlparse(href)
    hostname = parsed.hostname
    _qargs = dict([(k, v[0]) for k,v in parse_qs(parsed.query).items()])
    path_elems = [elem for elem in parsed.path.split('/') if elem]
    logger.info(f'hostname={hostname} path_elems={path_elems} qargs={_qargs}')
    repo_info = None
    site_info = {
        'ghpSite': False,
        'private': False,
        'baseurl': '',
        'acct': None,
        'repo': None,
        'ref': None,
        # 'ref': _qargs.get('ref'),
        'defaultBranch': None,
        'editBranch': None
    }
    siteConfigUrl = None
    if hostname.endswith('.github.io'):
        acct = hostname[:-10]
        repo = path_elems[0]
        site_info.update({
            'ghpSite': True,
            'acct':    acct,
            'repo':    repo,
            'baseurl': f'/{acct}/{repo}'
        })
    elif hostname != 'docs.juncture-digital.org' and (hostname.startswith('localhost') or hostname.startswith('192.168') or hostname.endswith('juncture-digital.org') or hostname.endswith('gitpod.io')):
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
            site_info.update({'acct': KNOWN_SITES['default'][0], 'repo': KNOWN_SITES['default'][1]})
    else:
        _site = hostname[4:] if hostname[:4] in ('dev.', 'exp.') else hostname
        logger.info(f'{_site} {_site in KNOWN_SITES}')
        if _site in KNOWN_SITES:
            acct, repo = KNOWN_SITES[_site]
            site_info['acct'] = acct
            site_info['repo'] = repo
        else:
            site_info.update({'acct': KNOWN_SITES['default'][0], 'repo': KNOWN_SITES['default'][1]})
            siteConfigUrl = f'{parsed.scheme}://{parsed.netloc}/config.json'
    logger.info(f'ref={site_info["ref"]}')
    if repo_info is None:
        url = f'https://api.github.com/repos/{site_info["acct"]}/{site_info["repo"]}'
        resp = requests.get(url)
        logger.info(f'{url} {resp.status_code}')
        if resp.status_code == 200:
            repo_info = resp.json()
            if site_info['ref'] is None:
                site_info['ref'] = repo_info['default_branch']
            site_info['defaultBranch'] = repo_info['default_branch']
        elif resp.status_code == 404:
            site_info['private'] = True
    logger.info(f'ref={site_info["ref"]}')
    if not siteConfigUrl:
        if repo_info is None: # Probably a private GH site 
            siteConfigUrl = f'https://{site_info["acct"]}.github.io/{site_info["repo"]}/config.json'
        else:
            siteConfigUrl = f'https://raw.githubusercontent.com/{site_info["acct"]}/{site_info["repo"]}/{site_info["ref"]}/config.json'
    resp = requests.get(siteConfigUrl)
    logger.info(f'siteConfigUrl={siteConfigUrl} {resp.status_code}')
    if resp.status_code == 200:
        site_config = resp.json()
        site_info['ref'] = site_info['ref'] if site_info['ref'] else site_config.get('ref')        
        if CONTENT_ROOT:
            resource_baseurl = f'{parsed.scheme}://{parsed.netloc}/static'
        else:
            if site_info['private']:
                resource_baseurl = f'https://{site_info["acct"]}.github.io/{site_info["repo"]}'
            else:
                resource_baseurl = f'https://raw.githubusercontent.com/{site_info["acct"]}/{site_info["repo"]}/{site_info["ref"]}'
        for key, value in site_config.items():
            #if key in site_info: continue
            if key == 'components':
                site_info['components'] = []
                for comp in value:
                    if not comp['src'].startswith('http'):
                        comp['src'] = f'{resource_baseurl}{"" if comp["src"][0] == "/" else "/"}{comp["src"]}'
                    site_info['components'].append(comp)
            elif key in ('banner', 'favicon', 'logo', 'css') and not value.startswith('http'):
                if site_info['ghpSite'] and site_info['private']:
                    value = f'https://{site_info["acct"]}.github.io/{site_info["repo"]}{"" if value[0] == "/" else "/"}{value}'
                else:
                    value = f'{resource_baseurl}{"" if value[0] == "/" else "/"}{value}'
            # elif key in ('ref',): continue
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
        site_info['editBranch'] = _qargs.get('ref', site_info['ref'])
    logger.info(f'ref={site_info["ref"]}')
    return site_info

def _context(path=None):
    path = _normalize_path(path)
    parsed = urlparse(request.base_url)
    site = parsed.netloc
    hostname = urlparse(request.base_url).hostname
    logger.info(f'_context: _is_ve_site={_is_ve_site(site)} gh_repo_prefix={has_gh_repo_prefix(path)}')
    if _is_ve_site(site) and has_gh_repo_prefix(path):
        acct, repo = path[1:].split('/')[:2]
    else:
        acct, repo = KNOWN_SITES.get(hostname[4:] if hostname[:4] in ('dev.', 'exp.') else hostname, KNOWN_SITES['default'])
    query_args = qargs()
    ref = query_args.pop('ref', None)
    refresh = query_args.get('refresh', 'false') in ('', 'true')
    if ref is None:
        ref = get_site_config(acct, repo, refresh=refresh).get('ref')
    return site, acct, repo, ref, path, query_args

@app.route('/essay/<path:path>', methods=['GET'])
@app.route('/essay/', methods=['GET'])
def essay(path=None):
    global cache
    markdown = content = None
    site, acct, repo, ref, path, qargs = _context(path)
    logger.info(f'essay: site={site} acct={acct} repo={repo} ref={ref} path={path}')
    raw = qargs.get('raw', 'false') in ('', 'true')
    refresh = qargs.get('refresh', 'false') in ('', 'true')
    cache_key = f'{site}|{acct}|{repo}|{ref}|{path}'
    logger.info(f'cache key={cache_key} ENV={ENV} CONTENT_ROOT={CONTENT_ROOT} refresh={refresh} cache={cache}')
    cached_essay = cache.get(cache_key) if not refresh and not ENV == 'dev' and not CONTENT_ROOT else None
    if cached_essay and cached_essay['url']:
        markdown, _ , md_sha = get_gh_file(cached_essay['url'])
        path = cached_essay.get('md_path', path)
        if cached_essay['sha'] == md_sha:
            content = markdown if raw else cached_essay['html']

    logger.info(f'essay: site={site} acct={acct} repo={repo} ref={ref} path={path} refresh={refresh} raw={raw} cached={cached_essay is not None} content={content is not None}')
    
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
        content, md_url, md_sha, md_path = get_essay(**essay_args)
        if content and not raw:
            cache[cache_key] = {'html': content, 'url': md_url, 'sha': md_sha, 'md_path': md_path}

    if content:
        return content, 200, cors_headers
    return 'Not found', 404

@app.route('/components/<path:path>', methods=['GET'])
def components(path):
    full_path = f'{BASEDIR}/app/client-lib/components/{path}'
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
    site_info = {}
    site = urlparse(request.base_url).netloc
    args = qargs()
    href = args.get('href')
    refresh = args.get('refresh', 'false') in ('', 'true')
    if refresh or href not in _site_info_cache:
        if (site.startswith('localhost') or site.startswith('192.168')) and CONTENT_ROOT:
            local_config_path = os.path.join(CONTENT_ROOT, 'config.json')
            if os.path.exists(local_config_path):
                site_info = json.load(open(local_config_path, 'r'))
                for key in ('banner', 'logo', 'favicon', 'css'):
                    if key in site_info and not site_info[key].startswith('http'):
                        site_info[key] = f'http://{site}/static{"" if site_info[key][0] == "/" else "/"}{site_info[key]}'
                if 'components' in site_info:
                    for comp in site_info['components']:
                        if not comp['src'].startswith('http'):
                            comp['src'] = f'http://{site}{"" if comp["src"][0] == "/" else "/"}{comp["src"]}' 
        else:
            site_info = _get_site_info(href)
        _site_info_cache[href] = site_info
    logger.info(f'site-info: href={href} site_info={_site_info_cache[href]}')
    return _site_info_cache[href], 200, cors_headers

# Redirect the user to the auth server, the redirect callback URL must be added to the auth service whitelist
# For the following request to be valid, the config.yaml for the auth service will need to look something like:
# general:
#   allowed_redirect_urls:
#   - "http://localhost:8080/callback"
@app.route('/login')
def login():
    site, acct, repo, ref, path, qargs = _context()
    redirect_url = qargs.get('redirect', site)
    url = f'{OAUTH_ENDPOINT}/auth/login/github?redirect={quote(redirect_url)}'
    logger.info(f'login: OAUTH_ENDPOINT={OAUTH_ENDPOINT} url={url}')
    return redirect(url)

@app.route('/jwt-expiration/<token>')
def expires(token):
    try:
        decoded = jwt.decode(token, public_key.encode('utf-8'), algorithms='RS256')
    except:
        logger.debug(traceback.format_exc())
        decoded = {'exp': 0}
    return str(decoded['exp']), 200, cors_headers

def file_reader(arg):
    logger.info(f'file_reader {arg}')

def file_writer(arg):
    logger.info(f'file_writer {arg}')


@app.route('/annotator/<path:path>', methods=['GET']) 
@app.route('/annotator/', methods=['GET']) 
@app.route('/annotator', methods=['GET']) 
def annotator(path=None):
    logger.info(f'annotator: path={path}')
    return (open(os.path.join(SCRIPT_DIR, 'image-annotator.html'), 'r').read(), 200, cors_headers)

@app.route('/annotations/<path:annoid>', methods=['GET', 'OPTIONS'])
@app.route('/annotations', methods=['GET', 'OPTIONS'])
@app.route('/annotations/', methods=['GET', 'OPTIONS'])
def annotations(annoid=None):
    site, acct, repo, ref, path, qargs = _context()
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers)
    kwargs = {'auth_token': gh_token(), 'reader': file_reader}
    for arg in ('target',):
        if arg in qargs:
            kwargs[arg] = qargs.pop(arg)
    logger.info(kwargs)
    try:
        if 'target' in kwargs:
            return (query_annotations(**kwargs), 200, cors_headers)
        else:
            return (get_annotation(annoid, **kwargs), 200, cors_headers)
    except NotFoundException:
        return 'Not found', 404
    except:
        logger.error(traceback.format_exc())
        return ('Server error', 500, cors_headers)

@app.route('/annotations/', methods=['POST'])
@app.route('/annotations/<path:annoid>', methods=['DELETE', 'PUT'])
@login_required
def annotations_protected(annoid=None):
    site, acct, repo, ref, path, qargs = _context()
    kwargs = {'auth_token': gh_token()}
    for arg in ('target',):
        if arg in qargs:
            kwargs[arg] = qargs.pop(arg)
    try:
        if request.method == 'POST':
            return (create_annotation(request.json, **kwargs), 201, cors_headers)
        if request.method == 'PUT':
            return (update_annotation(request.json, annoid, **kwargs), 200, cors_headers)
        elif request.method == 'DELETE': 
            return (delete_annotation(annoid, **kwargs), 204, cors_headers)
    except NotFoundException:
        return 'Not found', 404

@app.route('/fingerprints', methods=['GET'])  
def fingerprints():
    site, acct, repo, ref, path, qargs = _context()
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers)
    else:
        logger.info(f'fingerprints: qargs={qargs}')
        if 'qids' in qargs:
            qids = set()
            for qid in qargs['qids'].split(','):
                # ensure qids are namespaced
                ns, qid = qid.split(':') if ':' in qid else ('wd', qid)
                qids.add(f'{ns.strip()}:{qid.strip()}')
        fingerprints = get_fingerprints(qids, qargs.get('language', 'en'))
        return fingerprints, 200, cors_headers

@app.route('/entity/<path:eid>', methods=['GET'])  
@app.route('/entity', methods=['GET'])  
def entity(eid=None):
    site, acct, repo, ref, path, qargs = _context()
    qargs['refresh'] = qargs.get('refresh', 'false') in ('true', '') or 'article' in qargs
    logger.info(f'entity: eid={eid} site={site} acct={acct} repo={repo} ref={ref} qargs={qargs}')
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers)
    else:
        if eid:
            qargs['uri'] = as_uri(eid, **qargs)
        entity = KnowledgeGraph(cache=cache, acct=acct, ref=ref, repo=repo, **qargs).entity(**qargs)
        return entity, 200, cors_headers

@app.route('/specimens/<path:path>', methods=['GET'])
@app.route('/specimen/<path:path>', methods=['GET'])
def specimens(path):
    site, acct, repo, ref, path, qargs = _context(path)
    accept = request.headers.get('Accept', 'application/json').split(',')
    content_type = ([ct for ct in accept if ct in ('text/html', 'application/json', 'text/csv', 'text/tsv')] + ['application/json'])[0]
    logger.info(f'specimens: path={path} qargs={qargs}')
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers)
    else:
        taxon_name = gpid = wdid = None
        path_elems = path.split('/')[1:]
        if len(path_elems) == 1:
            if _is_entity_id(path_elems[0], False):
                wdid = path_elems[0] if path_elems[0].startswith('wd:') else f'wd:{path_elems[0]}'
            else:
                taxon_name = path_elems[0].replace('_', ' ')
        else:
            gpid = '/'.join(path_elems)
        qargs['preload'] = qargs.pop('preload', 'false').lower() in ('true', '')
        refresh = qargs.pop('refresh', 'false').lower() in ('true', '')
        _specimens = cache.get(path) if not refresh else {}
        if not _specimens:
            _specimens = get_specimens(taxon_name=taxon_name, gpid=gpid, wdid=wdid, **qargs)
            if _specimens['specimens']:
                cache[path] = _specimens
        else:
            _specimens['from_cache'] = True
        if content_type == 'text/html':
            return (open(os.path.join(BASEDIR, 'app', 'server', 'json-viewer.html'), 'r').read().replace("'{{DATA}}'", json.dumps(_specimens)), 200, cors_headers)
        else:
            return (_specimens, 200, cors_headers)

@app.route('/send-email/', methods=['POST', 'OPTIONS'])
def send_email():
    if request.method == 'OPTIONS':
        return ('', 204, cors_headers)
    data = request.json
    token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImpzdG9ybGFicyIsInVzZXJfY2xhaW1zIjp7InN1cGVydXNlciI6dHJ1ZX0sImV4cCI6MTczNjE4ODA2N30.WFuob_hAYUi1DWvplUwHMLqMYv8JMt2i8sCqzXrVpbs'
    logger.info(f'send-email: {data}')
    resp = requests.post(
        'https://www.jstor.org/api/labs-email-service/',
        headers = {
            'Authorization': f'JWT {token}',
            'User-agent': 'Labs python client'
        },
        json = request.json
    )
    logger.info(resp.status_code)
    return {'status': 'OK'}, 200, cors_headers

@app.route('/<path:path>', methods=['GET'])
@app.route('/', methods=['GET'])
def main(path=None):
    site, acct, repo, ref, path, qargs = _context(path)
    if site in ('lab.planthumanities.org', 'plant-humanities.app'):
        return redirect(f'https://lab.plant-humanities.org{path}', code=302)
    with open(os.path.join(BASEDIR, 'index.html'), 'r') as fp:
        html = fp.read()
        if site.startswith('localhost') or site.startswith('192.168') or site.endswith('gitpod.io'):
            html = re.sub(r'"/juncture/js/juncture', f'"/static/js/juncture', html)
            html = re.sub(r'"/juncture/app/client-lib/public/css/', f'"/static/app/client-lib/public/css/', html)
        if ENV == 'dev':
            if site.endswith('gitpod.io'):
                html = re.sub(r'"/static/js/juncture.+"', f'"https://8088-{os.environ.get("GITPOD_WORKSPACE_URL").replace("https://","")}/js/juncture.js"', html)
            else:
                html = re.sub(r'"/static/js/juncture.+"', f'"http://{site}:8088/js/juncture.js"', html)
        return html, 200

    return 'Not found', 404

@app.route('/thumbnail')
def thumbnail():
    qargs = dict([(k, request.args.get(k)) for k in request.args])
    logger.info(json.dumps(qargs, indent=2))
    if 'url' in qargs:
        url = qargs.pop('url')
        width, height = [int(v) for v in qargs.pop('size', '400x260').lower().replace('x', ' ').replace(',', ' ').split()]
        quality = int(qargs.pop('quality', 50))
        rotate = int(qargs.pop('rotate')) if 'rotate' in qargs else None
        offset = int(qargs.pop('offset')) if 'offset' in qargs else None
        refresh = qargs.pop('refresh', 'false') in ('true', '')
        if qargs:
            url = f'{url}{"?" if "?" not in url else "&"}{urlencode(qargs)}'
        logger.info(f'thumbnail: url={url} width={width} height={height} quality={quality} refresh={refresh}')

        key = hashlib.sha256(f'{url}-{width}x{height}-{quality}'.encode()).hexdigest()
        img = cache.get(key) if not refresh else None
        logger.info(f'cached={img is not None}')
        if img is None:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                r.raw.decode_content = True
                im = Image.open(r.raw)
                im_format = im.format
                if rotate:
                    im = im.rotate(rotate, expand=True)

                aspect = im.width / im.height
                logger.info(f'url={url} format={im_format} width={im.width} height={im.height} rotate={rotate} aspect={aspect}')


                if width > height:
                    if im.width > im.height:
                        im.thumbnail([width, width])
                        offset = offset if offset is not None else math.ceil((im.height-height)/2)
                        im = im.crop((0, offset, width, offset+height))
                    else:
                        im.thumbnail([math.ceil(width/aspect), math.ceil(width/aspect)])
                        offset = offset if offset is not None else math.ceil((im.height-height)/2)
                        im = im.crop((0, offset, width, offset+height))
                else:
                    if im.width > im.height:
                        im.thumbnail([math.ceil(height*aspect), math.ceil(height*aspect)])
                        offset = offset if offset is not None else math.ceil((im.width-width)/2)
                        im = im.crop((offset, 0, offset+width, height))
                    else:
                        im.thumbnail([math.ceil(height), math.ceil(height)])
                        offset = offset if offset is not None else math.ceil((im.width-width)/2)
                        im = im.crop((offset, 0, offset+width, height))

                imgByteArr = BytesIO()
                logger.info(f'format={im_format}')
                im.save(imgByteArr, format=im_format, quality=quality)
                img_b64 = base64.b64encode(imgByteArr.getvalue())
                img = {'b64': str(img_b64, 'utf-8'), 'content_type': Image.MIME[im_format]}
                # cache.set(key, img)
        decoded = base64.b64decode(bytes(img['b64'], 'utf-8'))
        accept_encoding = request.headers.get('Accept-Encoding', '')
        response = Response(status=200)
        response.headers['Content-Type'] = img['content_type']
        response.headers['Content-Length'] = len(decoded)
        if 'gzip' in accept_encoding.lower():
            gzip_buffer = BytesIO()
            gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
            gzip_file.write(decoded)
            gzip_file.close()
            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
        else:
            response.data = decoded
        logger.info(f'size={len(decoded)}')
        return response

def _is_entity_id(s, ns_required=True):
    if not s or not isinstance(s, str): return False
    eid = s.split(':')
    if len(eid) == 1 and ns_required:
        return False
    if len(eid) > 2:
        return False
    return len(eid[-1]) > 1 and eid[-1][0] in ('Q', 'P') and eid[-1][1:].isdecimal()

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
            CONTENT_ROOT = os.path.abspath(a)
            app.static_folder = CONTENT_ROOT
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, 'unhandled option'

    logger.info(f'ENV={ENV} CONTENT_ROOT={CONTENT_ROOT}')
    app.run(debug=True, host='0.0.0.0', port=8080)