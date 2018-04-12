#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import is_uuid
from nsx_edge import list_edge_cluster
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)

OBJECT = 'DFW section'
MODULE = 'Services'


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListSections()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + OBJECT)
        return []
    return response['results']


def _get_id(client, data):
    if data.has_key('id'):
        return param['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def _create_dfw_section(client, data):
    """
    """
    param = {'FirewallSection': data}
    request = client.__getattr__(MODULE).AddSection(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _delete_dfw_section(client, data):
    """
    """
    param = {'section-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteSection(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_dfw_section(client, data)
    elif action == 'delete':
        return _delete_dfw_section(client, data)
