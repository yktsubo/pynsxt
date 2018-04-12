#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import is_uuid
import nsx_edge
import nsx_logicalswitch
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)

OBJECT = 'T0 Logical Router'
MODULE = 'Logical Routing And Services'


def get_list(client):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(
        MODULE).ListLogicalRouters(router_type='TIER0')
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


def _get_t0lr(client, data):
    param = {'logical-router-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).ReadLogicalRouter(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not read " + OBJECT)
        return []
    return response


def _create_t0lr(client, data):
    """
    """
    if not is_uuid(data['edge_cluster_id']):
        edgeclusters = nsx_edge.list_edge_cluster(client)
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


def _delete_t0lr(client, data):
    """
    """
    param = {'logical-router-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalRouter(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def _create_uplink(client, data):
    res = []
    t0_id = _get_id(client, data)
    ls_id = nsx_logicalswitch._get_id(
        client, {'display_name': data['create_uplink']['ls']})

    param = {
        'LogicalPort': {
            'logical_switch_id': ls_id,
            'display_name': "Uplink_on_%s" % data['create_uplink']['edge_node'],
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

    t0lr = _get_t0lr(client, data)

    target_edge_id = None
    edges = nsx_edge.list_edgenode(client)
    for e in edges:
        if e['display_name'] == data['create_uplink']['edge_node']:
            target_edge_id = e['id']

    target_edge_memberid = None
    edge_clusters = nsx_edge.list_edge_cluster(client)
    for ecl in edge_clusters:
        if ecl['id'] == t0lr['edge_cluster_id']:
            for edge in ecl['members']:
                if edge['transport_node_id'] == target_edge_id:
                    target_edge_memberid = edge['member_index']
                    break
            break

    param = {
        'LogicalRouterPort': {
            'display_name': data['create_uplink']['display_name'],
            'resource_type': 'LogicalRouterUpLinkPort',
            'logical_router_id': t0_id,
            'tags': [],
            'linked_logical_switch_port_id': {
                'target_id': response['id']
            },
            'edge_cluster_member_index': [target_edge_memberid],
            'subnets': [{
                'ip_addresses': [data['create_uplink']['ip_address']],
                'prefix_length': data['create_uplink']['prefix_length']
            }]
        }
    }

    request = client.__getattr__(MODULE).CreateLogicalRouterPort(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create uplink")
        return []
    res.append(response)
    return res


def _add_static_route(client, data):
    res = []
    t0_id = _get_id(client, data)

    param = {
        'logical-router-id': t0_id,
        'StaticRoute': data['add_static_route']
    }
    request = client.__getattr__(MODULE).AddStaticRoute(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create static route")
        return []
    return response


def _update_ha_vip_config(client, data):
    t0_id = _get_id(client, data)

    request = client.__getattr__(MODULE).ListLogicalRouterPorts(
        logical_router_id=t0_id,
        resource_type='LogicalRouterUpLinkPort')
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + 'Logical Port')
        return []

    uplinks = response['results']
    redundant_uplink_port_ids = []
    for u in data['ha_vip_config']['uplinks']:
        for uplink in uplinks:
            if uplink['display_name'] == u:
                redundant_uplink_port_ids.append(uplink['id'])

    param = {'logical-router-id': t0_id}
    request = client.__getattr__(MODULE).ReadLogicalRouter(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not read logicalrouter")
        return []

    t0_routerconfig = response
    t0_routerconfig['advanced_config']['ha_vip_configs'] = [
        {
            'enabled': True,
            'ha_vip_subnets': [
                {
                    'active_vip_addresses': [data['ha_vip_config']['vip']],
                    'prefix_length': data['ha_vip_config']['prefix_length']
                }
            ],
            'redundant_uplink_port_ids': redundant_uplink_port_ids
        }
    ]

    param = {
        'logical-router-id': t0_id,
        'LogicalRouter': t0_routerconfig
    }
    pprint(param)
    request = client.__getattr__(MODULE).UpdateLogicalRouter(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create uplink")
        return []

    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_t0lr(client, data)
    elif action == 'update':
        if data.has_key('create_uplink'):
            return _create_uplink(client, data)
        elif data.has_key('add_static_route'):
            return _add_static_route(client, data)
        elif data.has_key('ha_vip_config'):
            return _update_ha_vip_config(client, data)
        else:
            logger.error('Not implemented')
            return None
    elif action == 'delete':
        return _delete_t0lr(client, data)
