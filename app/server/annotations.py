#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s')
logger = logging.getLogger()

import os
import uuid
import json
import getopt
import sys
import base64
from datetime import datetime

import requests
logging.getLogger('requests').setLevel(logging.INFO)

class NotFoundException(Exception):
    pass

# Helper methods
def _target(acct, repo, essay, image_hash, **kwargs):
    '''Returns a target constructed from the acct, repo, essay, and image_hash values'''
    return f'https://visual-essays.app/{acct}/{repo}/{essay}/{image_hash}'

def _github_api_urls(target):
    '''Returns GitHub urls for content and last modified date'''
    # target = {acct}/{repo}/{branch}/{mdroot}/{essay-path}/{image-hash}
    #  essay-path can be variable length
    logger.info(f'target={target}')
    path = target.split('/')
    acct, repo, branch = path[:3]
    image_hash = path[-1]
    essay_elems = path[3:-1]
    essay_root = '/' if len(essay_elems) == 0 else f'/{"/".join(essay_elems)}/'
    logger.info(f'acct={acct} repo={repo} branch={branch} essay_root={essay_root} image_hash={image_hash}')
    content_url = f'https://api.github.com/repos/{acct}/{repo}/contents{essay_root}{image_hash}.json?ref={branch}'
    logger.info(content_url)
    last_modified_url = f'https://api.github.com/repos/{acct}/{repo}/commits?path={essay_root}/{image_hash}.json&page=1&per_page=1&ref={branch}'
    return content_url, last_modified_url

def _get_last_modified__github(api_url, auth_token, **kwargs):
    last_modified_date = None
    committer = {}
    resp = requests.get(api_url, headers={
        'Authorization': f'Token {auth_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'JSTOR Labs visual essays client'
    })
    if resp.status_code == 200:
        resp = resp.json()
        if len(resp) > 0:
            last_modified_date = resp[0]['commit']['committer']['date']
            committer = resp[0]['commit']['author']

    return last_modified_date, committer

# Annotation methods for interacting with a GitHub based annotations store

def _get_annos(target, auth_token):
    anno_page = {}
    sha = None
    gh_content_url, _ = _github_api_urls(target)
    resp = requests.get(gh_content_url, headers={
        'Authorization': f'Token {auth_token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-agent': 'JSTOR Labs visual essays client'
    })
    logger.info(f'_get_annos: url={gh_content_url} token={auth_token} status_code={resp.status_code}')
    if resp.status_code == 200:
        resp = resp.json()
        anno_page = json.loads(base64.b64decode(resp['content']).decode('utf-8'))
        logger.info(anno_page)
        sha = resp['sha']
    return anno_page, sha

def _put_annos(target, annos, sha, **kwargs):
    rel_target = '/'.join(target.split('/')[3:])
    branch = target.split('/')[2]
    gh_content_url, _ = _github_api_urls(target)
    annos_page = {
        '@context': 'http://www.w3.org/ns/anno.jsonld',
        'id': f'http://visual-essays.app/annotations/?include=description&target={rel_target}',
        'type': 'AnnotationPage',
        'partOf': {
            'id': f'http://visual-essays.app/annotations/?include=description&target={rel_target}',
            'total': len(annos),
            'modified': datetime.utcnow().isoformat(),
        },
        'startIndex': 0,
        'items': annos
    }
    payload = {
        'message': 'Annotation file update',
        'content': str(base64.b64encode(bytes(json.dumps(annos_page, indent=2), 'utf-8')), 'utf-8'),
        'branch': branch if branch in ('main', 'master', 'develop', 'annotations') else 'develop'
    }
    if sha:
        payload['sha'] = sha
    resp = requests.put(
        gh_content_url,
        headers={'Authorization': f'Token {kwargs.get("auth_token")}'},
        json=payload
    )
    if resp.status_code >= 200 and resp.status_code < 300:
        return 'success'
    else:
        logger.warning(f'_put_annos: {resp.status_code} {resp.content} {gh_content_url} {branch} {kwargs.get("auth_token")}')
        logger.info(json.dumps(annos_page, indent=2))
        return 'failed'

def get_annotation(annoid, **kwargs):
    # get github account and repo and path to annotation file (annotations_root)
    target = '/'.join(annoid.split('/')[:-1])
    rel_annoid = '/'.join(annoid.split('/')[3:])
    anno_page, _ = _get_annos(target, kwargs['auth_token'])
    for _anno in anno_page.get('items', []):
        if _anno['id'] == rel_annoid:
            return _anno

def query_annotations(**kwargs):
    kwargs['reader']('some file')
    anno_page, _ = _get_annos(kwargs['target'], kwargs['auth_token'])
    return anno_page

def create_annotation(anno, **kwargs):
    target = anno['target']['id']
    rel_target = '/'.join(target.split('/')[3:])
    anno['target']['id'] = rel_target
    anno['id'] = f'{rel_target}/{uuid.uuid4().hex[:8]}'
    anno_page, sha = _get_annos(target, kwargs['auth_token'])
    annos = anno_page.get('items', []) + [anno]
    if _put_annos(target, annos, sha, **kwargs) == 'success':
        return anno

def update_annotation(anno, annoid, **kwargs):
    target = '/'.join(annoid.split('/')[:-1])
    anno_page, sha = _get_annos(target, kwargs['auth_token'])
    annos = anno_page['items']
    updated = None
    for idx, _existing in enumerate(annos):
        if _existing['id'] == anno['id']:
            annos[idx] = anno
            updated = anno
            break
    if _put_annos(target, annos, sha, **kwargs) == 'success':
        return updated

def delete_annotation(annoid, **kwargs):
    target = '/'.join(annoid.split('/')[:-1])
    rel_annoid = '/'.join(annoid.split('/')[3:])
    anno_page, sha = _get_annos(target, kwargs['auth_token'])
    annos = [anno for anno in anno_page['items'] if anno['id'] != rel_annoid]
    if _put_annos(target, annos, sha, **kwargs) == 'success':
        return 'OK'

def usage():
    print(f'{sys.argv[0]} [hl:a:r:b:e:t:dqu] arg')
    print(f'   -h --help       Print help message')
    print(f'   -l --loglevel   Logging level (default=warning)')
    print(f'   -a --acct       GitHub account')
    print(f'   -r --repo       GitHub repository')
    print(f'   -b --branch     GitHub branch, default="develop"')
    print(f'   -e --essay      Essay path')
    print(f'   -t --token      Auth token')
    print(f'   -d --delete     Delete annotation')
    print(f'   -q --query      Query annotations')
    print(f'   -u --update     Update annotation')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    kwargs = {'branch': 'develop', 'store': 'server'}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:a:r:b:e:t:dqu', ['help', 'loglevel', 'acct', 'repo', 'branch', 'essay', 'token', 'delete', 'query', 'update'])
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
            kwargs['acct'] = a
        elif o in ('-r', '--repo'):
            kwargs['repo'] = a
        elif o in ('-b', '--branch'):
            kwargs['branch'] = a
        elif o in ('-e', '--essay'):
            kwargs['essay'] = a
        elif o in ('-t', '--token'):
            kwargs['auth_token'] = a
        elif o in ('-d', '--delete'):
            kwargs['delete'] = True
        elif o in ('-q', '--query'):
            kwargs['query'] = True
        elif o in ('-u', '--update'):
            kwargs['update'] = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    if sys.stdin.isatty():
        if len(args) == 1:
            if kwargs.pop('delete', False):
                annoid = args[0]
                print(json.dumps(delete_annotation(annoid, **kwargs)))
            elif kwargs.pop('query', False):
                kwargs['image_hash'] = args[0]
                print(json.dumps(query_annotations(**kwargs)))
            else:
                annoid = args[0]
                print(json.dumps(get_annotation(annoid, **kwargs)))
        else:
            usage()
            sys.exit()
    else:
        update = kwargs.pop('update', False)
        for line in sys.stdin:
            annos = json.loads(line)
            if isinstance(annos, dict):
                annos = [annos]
            for anno in annos:
                if update:
                    annoid = args[0]
                    print(json.dumps(update_annotation(anno, annoid, **kwargs)))
                else: # create
                    print(json.dumps(create_annotation(anno, **kwargs)))
