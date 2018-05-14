#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import nsx_edgecluster
from pynsxt_utils import load_configfile, connect_cli, exec_command
from nsx_manager import get_thumbprint
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Edge'
MODULE = 'Fabric'


def join_manager(client, data, config):
    thumbprint = get_thumbprint(config)
    logger.info('Join edge with manager')
    for edge in config['nsxEdge']:
        connect_cli(edge)
        _get_manager_status(edge)
        if not edge['join_manager']:
            stdin, stdout, stderr = edge['cli'].exec_command(
                "join management-plane %s username %s password %s thumbprint %s" % (config['nsxManager']['ip'], config['nsxManager']['username'],  config['nsxManager']['password'], thumbprint))
            for line in stdout:
                if len(line.strip()) == 0:
                    continue
                else:
                    if 'Node successfully registered' in line:
                        logger.info(line)
                        break
    return


def get_status(args):
    config = load_configfile(args)
    for edge in config['nsxEdge']:
        cli = connect_cli(edge)
        exec_command(cli, 'get interface eth0', display=True)
        exec_command(cli, 'get managers', display=True)
    return


def _get_manager_status(edge):
    connect_cli(edge)
    ret = exec_command(edge['cli'], 'get managers')
    if 'Connected' in ret:
        logger.info('%s is connected to manager', edge['ip'])
        edge['join_manager'] = True
    else:
        logger.warning('%s is not connected to manager', edge['ip'])
        edge['join_manager'] = False


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListNodes(resource_type='EdgeNode')
    response, _ = request.result()
    return response['results']


def get_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def get_memberid(client, data, edgecluster=None):
    if edgecluster:
        for edge in edge_cluster['members']:
            if edge['transport_node_id'] == get_id(client, data):
                return edge['member_index']
    else:
        for edge_cluster in nsx_edgecluster.get_list(client):
            for edge in edge_cluster['members']:
                if edge['transport_node_id'] == get_id(client, data):
                    return edge['member_index']


def run(client, action, data, config=None):
    if action == 'join_manager':
        return join_manager(client, data, config)
