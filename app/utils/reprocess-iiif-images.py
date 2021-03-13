#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s :  %(name)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

import os, sys, getopt, traceback, time
from datetime import datetime

import json
import traceback

import requests
from requests.auth import HTTPBasicAuth
logging.getLogger('requests').setLevel(logging.WARNING)

sys.path.append('/opt/lib')

import os
import sys
import re
import getopt
from hashlib import sha256

from urllib.parse import quote, urlparse

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
BASEDIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

default_workbook = 'plant-humanities-image-inventory'
default_worksheet = 'metadata'

import gspread
from gspread.models import Cell
from oauth2client.service_account import ServiceAccountCredentials
logging.getLogger('oauth2client.client').setLevel(logging.WARNING)
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

default_iiif_service = 'https://iiif-server-atjcn6za6q-uc.a.run.app/api/v1/ingest'

def get_workbook(workbook=default_workbook, **kwargs):
    logger.info(f'get_workbook: {workbook}')
    creds = ServiceAccountCredentials.from_json_keyfile_name(f'{BASEDIR}/creds/labs-gs-creds.json', scope)
    client = gspread.authorize(creds)
    return client.open(workbook)

def process_image(url, endpoint=default_iiif_service):
    body = {
        'files': [{
            'id': sha256(url.encode('utf-8')).hexdigest(),
            'name': url.split('/')[-1],
            'url': url,
            'size': 0
        }]
    }
    logger.debug(json.dumps(body, indent=2))
    resp = requests.post(
        endpoint,
        auth=HTTPBasicAuth('admin', 'UXMtks54ryDfFYDa'),
        json = body
    )
    if resp.status_code == 200:
        resp = resp.json()
        logger.debug(json.dumps(resp, indent=2))
        return resp['data'][0]['url']
    else:
        logger.info(f'status={resp.status_code} msg={resp.content}')

def usage():
    print(('%s [hl:w:s:r:]' % sys.argv[0]))
    print('   -h --help            Print help message')
    print('   -l --loglevel        Logging level (default=warning)')
    print('   -w --workbook        Workbook name (default="%s")' % default_workbook)
    print('   -s --worksheet       Worksheet name (default="%s")' % default_worksheet)
    print('   -r --row             Row to process')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    kwargs = {}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:w:s:i:r:fn', ['help', 'loglevel', 'workbook', 'worksheet', 'row'])
    except getopt.GetoptError as err:
        # print help information and exit:
        logger.info(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-l', '--loglevel'):
            loglevel = a.lower()
            if loglevel in ('error',): logger.setLevel(logging.ERROR)
            elif loglevel in ('warn','warning'): logger.setLevel(logging.INFO)
            elif loglevel in ('info',): logger.setLevel(logging.INFO)
            elif loglevel in ('debug',): logger.setLevel(logging.DEBUG)
        elif o in ('-w', '--workbook'):
            kwargs['workbook'] = a
        elif o in ('-s', '--worksheet'):
            kwargs['worksheet'] = a
        elif o in ('-r', '--row'):
            kwargs['row'] = int(a)
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"


    dryrun = kwargs.pop('dryrun', False)
    force_refresh = kwargs.pop('force', False)
    row_to_process = kwargs.pop('row') if 'row' in kwargs else None

    worksheets = {}
    ws_data = {}
    wb = get_workbook(**kwargs)
    logger.debug(kwargs.get('worksheet', default_worksheet))
    ws = wb.worksheet(kwargs.get('worksheet', default_worksheet))
    rows = ws.get_all_values()
    fields = rows[0]
    field_idx = dict([(fields[i], i) for i in range(len(fields))])
    recs = [dict([(fields[col], row[col]) for col in range(len(row))]) for row in rows[1:]]

    processed = {}
    if os.path.exists('iiif-urls.tsv'):
        with open('iiif-urls.tsv', 'r') as fp:
            for line in fp:
                rec = line.strip().split('\t')
                processed[rec[0]] = rec[1]

    for i, rec in enumerate(recs):
        row = i + 2
        if rec.get('manifest') and 'iiif-v2.juncture-digital.org' in rec['manifest']:
            if row_to_process is None or row_to_process == row:
                # logger.info(f'{i} {rec["iiif-url"]} {rec["iiif-url"] in processed}')
                if rec['iiif-url'] not in processed or force_refresh:
                    try:
                        processed[rec['iiif-url']] = process_image(rec['url'])
                    except KeyboardInterrupt:
                        break
                    except:
                        logger.info('error')
    
    with open('iiif-urls.tsv', 'w') as fp:
        for orig, reprocessed in processed.items():
            fp.write('\t'.join([orig, reprocessed]) + '\n')
