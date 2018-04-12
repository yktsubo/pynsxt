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

OBJECT = 'IP pool'
MODULE = 'Pool Management'


def get_list(client):
    """
    This function returns all ip pools found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    request = client.__getattr__(MODULE).ListIpPools()
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


def _create_ippool(client, data):
    """
    This function returns deleted ip pool found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all pool details
    """
    param = {'IpPool': data}
    request = client.__getattr__(MODULE).CreateIpPool(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _delete_ippool(client, data):
    """
    """
    param = {'pool-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpPool(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_ippool(client, data)
    elif action == 'delete':
        return _delete_ippool(client, data)
