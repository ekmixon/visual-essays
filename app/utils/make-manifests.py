#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s :  %(name)s : %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

import os, sys, getopt, traceback, time
from datetime import datetime

import json
import requests
import traceback
logging.getLogger('requests').setLevel(logging.WARNING)

sys.path.append('/opt/lib')

import os
import sys
import getopt
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

iiif_service_endpoint = 'https://iiif-v2.visual-essays.app/manifest/'

ignore_fields = {'ready', 'essay', 'thumbnail', 'manifest', 'iiif-url', 'width', 'height', 'format'}

def get_workbook(workbook=default_workbook, **kwargs):
    logger.info(f'get_workbook: {workbook}')
    creds = ServiceAccountCredentials.from_json_keyfile_name(f'{BASEDIR}/app/creds/labs-gs-creds.json', scope)
    client = gspread.authorize(creds)
    return client.open(workbook)

def create_manifest(iiif_service=iiif_service_endpoint, **kwargs):
    logger.info(f'create_manifest: service_endpoint={iiif_service} kwargs={kwargs}')
    data = {**dict([(f,kwargs[f]) for f in kwargs if f not in ignore_fields and kwargs[f]]), **{'iiif': True,}}
    resp = requests.post(iiif_service, headers={'Content-type': 'application/json'}, json=data)
    if resp.status_code == 200:
        return resp.json()
    else:
        logger.warning(f'{resp.status_code} {resp.content}')

def as_hyperlink(qid, label=None):
    return '=HYPERLINK("{}", "{}")'.format('https://kg.jstor.org/entity/{}'.format(qid), label if label else qid)

def as_image(url):
    return f'=IMAGE("{url}")'

def is_ready(rec):
    return rec.get('ready').lower() in ('x', 't', 'true', 'y', 'yes')

def usage():
    print(('%s [hl:w:s:i:rn]' % sys.argv[0]))
    print('   -h --help            Print help message')
    print('   -l --loglevel        Logging level (default=warning)')
    print('   -w --workbook        Workbook name (default="%s")' % default_workbook)
    print('   -s --worksheet       Worksheet name (default="%s")' % default_worksheet)
    print('   -i --iiif-service    IIIF service endpoint (default="%s")' % iiif_service_endpoint)
    print('   -r --refresh         Force refresh')
    print('   -n --dryrun          Run script without updating worksheet')

if __name__ == '__main__':
    logger.setLevel(logging.WARNING)
    kwargs = {}
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 'hl:w:s:i:rn', ['help', 'loglevel', 'workbook', 'worksheet', 'iiif-service', 'refresh', 'dryrun'])
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
        elif o in ('-i', '--iiif-service'):
            kwargs['iiif-service'] = a
        elif o in ('-r', '--refresh'):
            kwargs['refresh'] = True
        elif o in ('-n', '--dryrun'):
            kwargs['dryrun'] = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"


    dryrun = kwargs.pop('dryrun', False)
    force_refresh = kwargs.pop('refresh', False)
    iiif_service = kwargs.pop('iiif-service', iiif_service_endpoint)

    logger.info(f'iiif-service={iiif_service}')

    worksheets = {}
    ws_data = {}
    wb = get_workbook(**kwargs)
    logger.debug(kwargs.get('worksheet', default_worksheet))
    ws = wb.worksheet(kwargs.get('worksheet', default_worksheet))
    rows = ws.get_all_values()
    fields = rows[0]
    field_idx = dict([(fields[i], i) for i in range(len(fields))])
    recs = [dict([(fields[col], row[col]) for col in range(len(row))]) for row in rows[1:]]

    updates = []
    for i, rec in enumerate(recs):
        row = i + 2
        logger.debug(f'{is_ready(rec)} {not rec.get("manifest")} {force_refresh}')
        if is_ready(rec) and (not rec.get('manifest') or force_refresh):
            try:
                logger.info(f'processing row {row}')
                manifest = create_manifest(iiif_service, **rec)
                if manifest:
                    logger.debug(json.dumps(manifest, indent=2))
                    img = manifest['sequences'][0]['canvases'][0]['images'][0]['resource']
                    row_updates = {
                        'manifest': manifest['@id'],
                        'thumbnail': as_image(manifest['thumbnail']),
                        'iiif-url': img['service']['@id'],
                        'height': img['height'],
                        'width': img['width'],
                        'format': img['format'].split('/')[-1],
                        'ready': 'processed'
                    }
                    updates += [Cell(row, field_idx[fld] + 1, val) for fld, val in row_updates.items() if fld in field_idx]
            except:
                logger.warning(traceback.format_exc())
                logger.info(manifest)
    updates.sort(key=lambda cell: cell.col, reverse=False)
    if dryrun:
        print(updates)
    else:
        if updates:
            ws.update_cells(updates, value_input_option='USER_ENTERED')
