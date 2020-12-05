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
from urllib.parse import urlparse, unquote, urlencode

import requests
logging.getLogger('requests').setLevel(logging.INFO)

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

from flask import Flask, request, send_from_directory, redirect, Response, jsonify, g

app = Flask(__name__)

from essay import get_essay

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Credentials': True,
    'Access-Control-Allow-Methods': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD',
    'Access-Control-Allow-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Access-Control-Expose-Headers': 'ETag, Vary, Accept, Authorization, Prefer, Content-type, Link, Allow, Content-location, Location',
    'Allow': 'PUT, PATCH, GET, POST, DELETE, OPTIONS, HEAD'
}

_site_configs = {}
def _site_config(site, scheme='https'):
    global _site_configs
    if not site in _site_configs:
        resp = requests.get(f'{scheme}://{site}/config.json')
        if resp.status_code == 200:
            _site_configs[site] = resp.json()
        pass
    return _site_configs.get(site, {})

@app.route('/config.json', methods=['GET'])
def config():
    logger.info(f'config')
    _config = json.load(open(os.path.join(BASEDIR, 'config.json'), 'r'))
    return _config, 200

@app.route('/essay/<path:path>', methods=['GET'])
@app.route('/essay/', methods=['GET'])
def essay(path=None):
    parsed_base_url = urlparse(request.base_url)
    site = parsed_base_url.hostname
    logger.info(f'essay: site={site} path={path}')
    return get_essay(path, BASEDIR, site, _site_config(site, parsed_base_url.scheme)), 200

@app.route('/<path:path>', methods=['GET'])
@app.route('/', methods=['GET'])
def main(path=None):
    parsed_base_url = urlparse(request.base_url)
    site = parsed_base_url.hostname
    logger.info(f'main: site={site} path={path}')
    with open(os.path.join(BASEDIR, 'index.html'), 'r') as fp:
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