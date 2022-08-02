#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(filename)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger()

import sys
import getopt
import json

import requests
logging.getLogger('requests').setLevel(logging.INFO)

iiif_service_endpoint = 'https://iiif-v2.visual-essays.app/manifest/'

def get_manifest(url, **metadata):
    metadata['iiif'] = True
    logger.info(f'get_manifest: service_endpoint={iiif_service_endpoint} image_url={url} metadata={metadata}')
    data = {**metadata, **{'iiif': True, 'url': url}}
    resp = requests.post(iiif_service_endpoint, headers={'Content-type': 'application/json'}, json=data)
    if resp.status_code == 200:
        return resp.json()
    else:
        logger.warning(f'{resp.status_code} {resp.content}')

def usage():
    print(f'{sys.argv[0]} [hl:t:d:a:r:p:] url')
    print('   -h --help       Print help message')
    print('   -l --loglevel    Logging level (default=warning)')
    print('   -t --label       Image label')
    print('   -d --description Image description')
    print('   -a --attribution Image attribution')
    print('   -r --license     Image license')
    print('   -n --navDate     Image navDate')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    metadata = {}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:t:d:a:r:', ['help', 'loglevel'])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-l', '--loglevel'):
            loglevel = a.lower()
            if loglevel in ('error',): logger.setLevel(logging.ERROR)
            elif loglevel in ('warn', 'warning', 'info'): logger.setLevel(logging.INFO)
            elif loglevel in ('debug',): logger.setLevel(logging.DEBUG)
        elif o in ('-t', '--label'):
            metadata['label'] = a
        elif o in ('-d', '--description'):
            metadata['description'] = a
        elif o in ('-a', '--attribution'):
            metadata['attribution'] = a
        elif o in ('-r', '--license'):
            metadata['license'] = a
        elif o in ('-p', '--date'):
            metadata['date'] = a
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    if len(args) == 1:
        print(json.dumps(get_manifest(args[0], **metadata)))
    else:
        usage()