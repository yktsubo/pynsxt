#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import re

from pynsxt_utils import load_configfile, connect_cli, exec_command
from nsx_manager import get_thumbprint
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)


def join_manager(client, data, config):
    thumbprint = get_thumbprint(config)
    logger.info('Join controller with manager')
    for controller in config['nsxController']:
        connect_cli(controller)
        _get_manager_status(controller)
        if not controller['join_manager']:
            stdin, stdout, stderr = controller['cli'].exec_command(
                "join management-plane %s username %s password %s thumbprint %s" % (config['nsxManager']['ip'], config['nsxManager']['username'], config['nsxManager']['password'], thumbprint))
            for line in stdout:
                if len(line.strip()) == 0:
                    continue
                else:
                    if 'Node successfully registered' in line:
                        print(line)
                        break
    return


def initialize(client, data, config):
    for controller in config['nsxController']:
        connect_cli(controller)
        _get_cluster_status(controller)
        if controller['master'] == False and controller['majority'] == False:
            exec_command(controller['cli'], "set control-cluster security-model shared-secret secret %s" %
                         controller['secret'], display=True)
            exec_command(controller['cli'],
                         'initialize control-cluster', display=True)
            return


def get_status(args):
    config = load_configfile(args)
    for controller in config['nsxController']:
        cli = connect_cli(controller)
        exec_command(cli, 'get interface eth0', display=True)
        exec_command(cli, 'get managers', display=True)
        exec_command(cli, 'get control-cluster status', display=True)
        _get_manager_status(controller)
        _get_cluster_status(controller)
    return


def _update_controller_status(controller):
    _get_manager_status(controller)
    _get_cluster_status(controller)
    return


def join_cluster(args):
    config = load_configfile(args)
    # Check master exists
    master = _get_master(config)
    logger.info("Master: %s" % master['ip'])
    if master is None:
        logger.error('No master node exists')
        return
    connect_cli(master)

    slaves = _get_slaves(config)
    logger.info("Slaves: %s" % ",".join([slave['ip'] for slave in slaves]))
    for controller in slaves:
        connect_cli(controller)
        controller['master'], controller['majority'] = _get_cluster_status(
            controller['cli'])

    for controller in slaves:
        if controller['majority']:
            continue
        controller['thumbprint'] = _get_thumbprint(controller['cli'])
        if controller['thumbprint'] is None:
            exec_command(controller['cli'], "set control-cluster security-model shared-secret secret %s" %
                         controller['secret'], display=True)
            controller['thumbprint'] = _get_thumbprint(controller['cli'])

    for controller in slaves:
        if controller['majority']:
            continue
        exec_command(master['cli'], "join control-cluster %s thumbprint %s" %
                     (controller['ip'], controller['thumbprint']), display=True)
        exec_command(controller['cli'],
                     "activate control-cluster", display=True)


def _get_thumbprint(cli):
    stdin, stdout, stderr = cli.exec_command(
        'get control-cluster certificate thumbprint')
    for line in stdout:
        if len(line.strip()) == 0:
            continue
        elif 'Failure response' in line:
            logger.error('Could not get thumbprint')
            return None
        else:
            thumbprint = line.strip()
            print("Thumbprint: %s" % thumbprint)
            return thumbprint
    return None


def _get_manager_status(controller):
    connect_cli(controller)
    ret = exec_command(controller['cli'], 'get managers')
    if 'Connected' in ret:
        logger.info('%s is connected to manager', controller['ip'])
        controller['join_manager'] = True
    else:
        logger.warning('%s is not connected to manager', controller['ip'])
        controller['join_manager'] = False


def _get_cluster_status(controller):
    connect_cli(controller)
    ret = exec_command(controller['cli'], 'get control-cluster status')
    for line in ret.split("\n"):
        if 'master:' in line:
            if 'true' in line:
                logger.info('%s is master', controller['ip'])
                controller['master'] = True
            else:
                logger.info('%s is not master', controller['ip'])
                controller['master'] = False
        if 'majority:' in line:
            if 'true' in line:
                logger.info('%s is majority', controller['ip'])
                controller['majority'] = True
            else:
                logger.info('%s is not majority', controller['ip'])
                controller['majority'] = False
        if 'This node has not yet joined the cluster' in line:
            return
    ret = exec_command(controller['cli'], 'get control-cluster status verbose')
    numOfJoinedNode = 0
    for line in ret.split("\n"):
        if 'Zookeeper Server IP:' in line:
            numOfJoinedNode += 1

    logger.info("%s controllers shown in %s" %
                (numOfJoinedNode, controller['ip']))
    if numOfJoinedNode > 1:
        controller['activate'] = True
    else:
        controller['activate'] = False
    return


def _get_master(config):
    for controller in config['nsxController']:
        _get_cluster_status(controller)
        if controller['master']:
            return controller
    return None


def _get_slaves(config):
    slaves = []
    for controller in config['nsxController']:
        _get_cluster_status(controller)
        if not controller['master']:
            slaves.append(controller)
    return slaves


def run(client, action, data, config=None):
    if action == 'join_manager':
        return join_manager(client, data, config)
    elif action == 'initialize':
        return initialize(client, data, config)
