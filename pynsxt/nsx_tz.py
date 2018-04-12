#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)

OBJECT = 'Transport Zone'
MODULE = 'Network Transport'


def _get_id(client, data):
    if data.has_key('id'):
        return param['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def get_list(client):
    """
    This function returns all TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    request = client.__getattr__(MODULE).ListTransportZones()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + OBJECT)
        return []
    return response['results']


def _create_tz(client, data):
    """
    This function returns alled TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'TransportZone': data}
    request = client.__getattr__(
        'Network Transport').CreateTransportZone(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not add transport zone")
        return []
    return response


def _update_tz(client, data):
    """
    """
    param = {'zone-id': _get_tzid(client, data)}
    request = client.__getattr__('Network Transport').GetTransportZone(**param)
    try:
        tz, responseAdapter = request.result()
    except:
        logger.error("Could not get Transport zone with")

    for key in data.keys():
        if key == 'display_name' or key == 'id':
            continue
        tz[key] = data[key]

    param = {'zone-id': tz['id'], 'TransportZone': tz}
    request = client.__getattr__(
        'Network Transport').UpdateTransportZone(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not update transport zone")
        return []
    return response


def _get_tzid(client, param):
    if param.has_key('id'):
        return param['id']
    elif param.has_key('display_name'):
        tzs = get_list(client)
        for tz in tzs:
            if tz['display_name'] == param['display_name']:
                return tz['id']
    return None


def _delete_tz(client, data):
    """
    This function returns deleted TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'zone-id': _get_tzid(client, data)}
    request = client.__getattr__(
        'Network Transport').DeleteTransportZone(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete transport zone with %s" %
                     oid)
        return []
    return response


def run(client, action, data):
    logger.info('TransportZone ' + action)
    if action == 'create':
        return _create_tz(client, data)
    elif action == 'update':
        return _update_tz(client, data)
    elif action == 'delete':
        return _delete_tz(client, data)
