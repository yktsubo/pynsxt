#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
import nsx_t0lr
from pynsxt_utils import is_uuid
from nsx_edge import list_edge_cluster
import nsx_logicalswitch
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)

OBJECT = 'T1 Logical Router'
MODULE = 'Logical Routing And Services'


def get_list(client):
    """
    This function returns all T1 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(
        MODULE).ListLogicalRouters(router_type='TIER1')
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


def _create_t1lr(client, data):
    """
    """
    if data.has_key('edge_cluster_id'):
        if not is_uuid(data['edge_cluster_id']):
            edgeclusters = list_edge_cluster(client)
            data['edge_cluster_id'] = [e['id']
                                       for e in edgeclusters if e['display_name'] == data['edge_cluster_id']][0]
    param = {'LogicalRouter': data}
    request = client.__getattr__(MODULE).CreateLogicalRouter(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _connect_to_t0lr(client, data):
    res = []
    t0_id = nsx_t0lr._get_id(client, {'display_name': data['connect_to_T0']})
    t1_id = _get_id(client, data)

    param = {
        'LogicalRouterPort':
        {
            'display_name': "Link_to_%s" % data['display_name'],
            'resource_type': 'LogicalRouterLinkPortOnTIER0',
            'logical_router_id': t0_id,
            'tags': []
        }
    }
    request = client.__getattr__(MODULE).CreateLogicalRouterPort(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    res.append(response)

    param = {
        'LogicalRouterPort':
        {
            'display_name': "Link_to_%s" % data['connect_to_T0'],
            'resource_type': 'LogicalRouterLinkPortOnTIER1',
            'logical_router_id': t1_id,
            'tags': [],
            'linked_logical_router_port_id': {
                'target_id': response['id']
            }
        }
    }
    request = client.__getattr__(MODULE).CreateLogicalRouterPort(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    res.append(response)
    return res


def _connect_to_ls(client, data):
    res = []
    t1_id = _get_id(client, data)
    ls_id = nsx_logicalswitch._get_id(
        client, {'display_name': data['connect_to_LS']['ls']})

    param = {
        'LogicalPort': {
            'logical_switch_id': ls_id,
            'display_name': 'To_%s' % data['display_name'],
            'admin_state': 'UP'
        }
    }
    request = client.__getattr__(
        'Logical Switching').CreateLogicalPort(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + 'Logical Port')
        return []
    res.append(response)

    param = {
        'LogicalRouterPort': {
            'display_name': "Link_to_%s" % data['connect_to_LS']['ls'],
            'resource_type': 'LogicalRouterDownLinkPort',
            'logical_router_id': t1_id,
            'tags': [],
            'linked_logical_switch_port_id': {
                'target_id': response['id']
            },
            'subnets': [{
                'ip_addresses': [data['connect_to_LS']['ip_address']],
                'prefix_length': data['connect_to_LS']['prefix_length']
            }]
        }
    }

    request = client.__getattr__(MODULE).CreateLogicalRouterPort(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    res.append(response)
    return res


def _advertise(client, data):
    t1_id = _get_id(client, data)
    param = {'logical-router-id': t1_id}
    request = client.__getattr__(MODULE).ReadAdvertisementConfig(**param)
    response, _ = request.result()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not config advertisement")
        return []

    param = {
        'logical-router-id': t1_id,
        'AdvertisementConfig': response
    }

    for key in data['advertisement'].keys():
        param['AdvertisementConfig'][key] = data['advertisement'][key]

    request = client.__getattr__(MODULE).UpdateAdvertisementConfig(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not config advertisement")
        return []
    return response


def _get_lrp(client, data):
    t1_id = _get_id(client, data)
    request = client.__getattr__(
        MODULE).ListLogicalRouterPorts(logical_router_id=t1_id)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + 'Logical Port')
        return []
    return response['results']


def _delete_t1lr(client, data):
    """
    """
    t1_lrp = _get_lrp(client, data)
    lp_rm = []
    lrp_rm = []

    for lrp in t1_lrp:
        if lrp.has_key('linked_logical_switch_port_id'):
            lp_rm.append(lrp['linked_logical_switch_port_id']['target_id'])
        elif lrp.has_key('linked_logical_router_port_id'):
            lrp_rm.append(lrp['linked_logical_router_port_id']['target_id'])
        lrp_rm.append(lrp['id'])

    for lp in lp_rm:
        param = {'lport-id': lp}
        request = client.__getattr__(
            'Logical Switching').DeleteLogicalPort(**param)
        try:
            response, _ = request.result()
        except:
            logger.error("Could not create " + 'Logical Port')
            return []

    for lrp in lrp_rm:
        param = {'logical-router-port-id': lp}
        request = client.__getattr__(
            'Logical Switching').DeleteLogicalRouterPort(**param)
        try:
            response, _ = request.result()
        except:
            logger.error("Could not create " + 'Logical Port')
            return []

    param = {'logical-router-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalRouter(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_t1lr(client, data)
    elif action == 'update':
        if data.has_key('connect_to_T0'):
            return _connect_to_t0lr(client, data)
        elif data.has_key('connect_to_LS'):
            return _connect_to_ls(client, data)
        elif data.has_key('advertisement'):
            return _advertise(client, data)
        else:
            logger.error('Not implemented')
            return None
    elif action == 'delete':
        return _delete_t1lr(client, data)
