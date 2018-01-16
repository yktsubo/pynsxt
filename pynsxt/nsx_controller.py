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


def deploy_controller(args):
    config = load_configfile(args)
    logger.info('Deploy NSX Controller')
    for controller in config['nsxController']:
        # Create deploy command
        cmd = ["ovftool"]
        cmd.append("--name=%s" % controller['name'])
        cmd.append("--X:injectOvfEnv")
        cmd.append("--allowExtraConfig")
        cmd.append("--datastore=%s" % controller['datastore'])
        cmd.append("--network=%s" % controller['network'])
        cmd.append("--acceptAllEulas")
        cmd.append("--noSSLVerify")
        cmd.append("--diskMode=thin")
        cmd.append("--powerOn")
        cmd.append("--prop:nsx_ip_0=%s" % controller['ip'])
        cmd.append("--prop:nsx_netmask_0=%s" % controller['netmask'])
        cmd.append("--prop:nsx_gateway_0=%s" % controller['gw'])
        cmd.append("--prop:nsx_dns1_0=%s" % config['dns'])
        cmd.append("--prop:nsx_domain_0=%s" % config['domain'])
        cmd.append("--prop:nsx_ntp_0=%s" % config['ntp'])
        cmd.append("--prop:nsx_isSSHEnabled=True")
        cmd.append("--prop:nsx_allowSSHRootLogin=True")
        cmd.append("--prop:nsx_passwd_0=%s" % controller['password'])
        cmd.append("--prop:nsx_cli_passwd_0=%s" %
                   controller['password'])
        cmd.append("--prop:nsx_hostname=%s" % controller['name'])
        cmd.append(controller['ova'])
        cmd.append("vi://%s:%s@%s/?ip=%s" % (config['vc_mng']['user'], config['vc_mng']
                                             ['password'], config['vc_mng']['ip'], controller['vmhost']))
        logger.debug('Executing command: ' + " ".join(cmd))
        ret = subprocess.check_call(" ".join(cmd), shell=True)
        if ret != 0:
            logger.error('Failed to deploy')
            return
    logger.info('Deployed successfully')
    pass


def join_manager(args):
    config = load_configfile(args)
    thumbprint = get_thumbprint(args)
    logger.info('Join controller with manager')
    for controller in config['nsxController']:
        connect_cli(controller)
        _get_manager_status(controller)
        if not controller['join_manager']:
            stdin, stdout, stderr = controller['cli'].exec_command(
                "join management-plane %s username %s password %s thumbprint %s" % (config['nsxManager']['ip'], config['nsxManager']['user'], config['nsxManager']['password'], thumbprint))
            for line in stdout:
                if len(line.strip()) == 0:
                    continue
                else:
                    if 'Node successfully registered' in line:
                        print(line)
                        break
    return


def initialize(args):
    config = load_configfile(args)
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


def construct_parser(subparsers):
    controller_parser = subparsers.add_parser('controller', description="Functions for NSX controller",
                                              help="Functions for NSX controller")
    controller_subparsers = controller_parser.add_subparsers()
    controller_deploy_parser = controller_subparsers.add_parser(
        'deploy', help='Deploy NSX-T controller')
    controller_deploy_parser.set_defaults(func=deploy_controller)

    controller_join_manager_parser = controller_subparsers.add_parser(
        'join_manager', help='Join with NSX manager')
    controller_join_manager_parser.set_defaults(func=join_manager)

    controller_status_parser = controller_subparsers.add_parser(
        'status', help='Status of NSX controller')
    controller_status_parser.set_defaults(func=get_status)

    controller_initialize_parser = controller_subparsers.add_parser(
        'initialize', help='Initialize NSX controller')
    controller_initialize_parser.set_defaults(func=initialize)

    controller_join_cluster_parser = controller_subparsers.add_parser(
        'join_cluster', help='Join NSX controller to master node')
    controller_join_cluster_parser.set_defaults(func=join_cluster)
