#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import base64

import requests
logging.getLogger('requests').setLevel(logging.INFO)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

_gh_token = os.environ.get('gh_token')
if not _gh_token and os.path.exists(f'{SCRIPT_DIR}/gh-token'):
    with open(f'{SCRIPT_DIR}/gh-token', 'r') as fp:
        _gh_token = fp.read().strip()
logger.info(f'_gh_token={_gh_token} {SCRIPT_DIR}')
def gh_token():
    return _gh_token

def get_gh_file(url, token=None):
    content = sha = None
    resp = requests.get(url, headers={
        'Authorization': f'Token {token or gh_token()}',
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'JSTOR Labs visual essays client'
    })
    logger.info(f'{url} {resp.status_code}')
    if resp.status_code == 200:
        resp = resp.json()
        content = base64.b64decode(resp['content']).decode('utf-8')
        sha = resp['sha']
    return content, url, sha

def query_gh_file(acct, repo, branch, path, token=None):
    logger.info(f'query_gh_file: acct={acct} repo={repo} branch={branch} path={path}')
    url = f'https://api.github.com/repos/{acct}/{repo}/contents{path}?ref={branch}'
    return get_gh_file(url, token)

def gh_repo_info(acct, repo):
    url = f'https://api.github.com/repos/{acct}/{repo}'
    resp = requests.get(url, headers={
        'Authorization': f'Token {gh_token()}',
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'JSTOR Labs visual essays client'
    })
    logger.info(f'{url} {resp.status_code}')
    return resp.json() if resp.status_code == 200 else None

_checked_prefixes = {}
def has_gh_repo_prefix(path):
    elems = path[1:].split('/')
    prefix = '/'.join(elems[:2]) if len(elems) >= 2 else None
    if prefix is not None and prefix not in _checked_prefixes:
        _checked_prefixes[prefix] = gh_repo_info(elems[0], elems[1]) is not None
    _is_repo_prefix = _checked_prefixes.get(prefix, False)
    logger.info(f'has_gh_repo_prefix: prefix={prefix} _is_repo_prefix={_is_repo_prefix}')
    return _is_repo_prefix

def get_gh_markdown(acct, repo, branch, path, token):
    logger.info(path)
    if has_gh_repo_prefix(path):
        path = f'/{"/".join(path.split("/")[3:])}'    
    logger.info(f'get_gh_markdown: path={path}')
    markdown = md_path = url = sha = None
    if path.endswith('.md'):
        paths = [path]
    else:
        if path == '/':
            paths = ['/README.md', '/index.md']
        else:
            if path[-1] == '/':
                paths = [f'{path}{file}' for file in ('README.md', 'index.md')]
            else:
                paths = [f'{path}.md'] + [f'{path}/{file}' for file in ('README.md', 'index.md')]
    for _path in paths:
        markdown, url, sha = query_gh_file(acct, repo, branch, _path, token)
        if markdown:
            md_path = _path.replace('.md', '')
            break
    return markdown, md_path, url, sha