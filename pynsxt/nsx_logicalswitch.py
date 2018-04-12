#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import is_uuid
import nsx_tz
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)


OBJECT = 'LogicalSwitch'
MODULE = 'Logical Switching'


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
    This function returns all LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical switch
    """
    request = client.__getattr__(MODULE).ListLogicalSwitches()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + OBJECT)
        return []
    return response['results']


def _create_ls(client, data):
    """
    This function returns alled LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    if not is_uuid(data['transport_zone_id']):
        tzs = nsx_tz.get_list(client)
        tz = [t for t in tzs if t['display_name']
              == data['transport_zone_id']][0]
        data['transport_zone_id'] = tz['id']

    if tz['transport_type'] == 'VLAN':
        if not data['vlan']:
            logger.error("You need vlan id to create an vlan logical switch")
            return

    elif tz['transport_type'] == 'OVERLAY':
        data['replication_mode'] = 'MTEP'

    data['admin_state'] = 'UP'
    param = {'LogicalSwitch': data}
    request = client.__getattr__(MODULE).CreateLogicalSwitch(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _delete_ls(client, data):
    """
    This function returns deleted LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a list containing deleted logical switch
    """
    param = {'lswitch-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalSwitch(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_ls(client, data)
    elif action == 'update':
        logger.error('Not implemented')
        return None
    elif action == 'delete':
        return _delete_ls(client, data)
