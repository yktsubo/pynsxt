#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
from pynsxt_utils import load_configfile, connect_cli, exec_command
from nsx_manager import get_thumbprint
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)


def deploy_edge(args):
    config = load_configfile(args)
    logger.info('Deploy NSX Edge')
    for edge in config['nsxEdge']:
        # Create deploy command
        cmd = ["ovftool"]
        cmd.append("--name=%s" % edge['name'])
        cmd.append("--deploymentOption=%s" % edge['deploymentOption'])
        cmd.append("--X:injectOvfEnv")
        cmd.append("--allowExtraConfig")
        cmd.append("--datastore=%s" % edge['datastore'])
        cmd.append("--net:\"Network 0=%s\"" % edge['network0'])
        cmd.append("--net:\"Network 1=%s\"" % edge['network1'])
        cmd.append("--net:\"Network 2=%s\"" % edge['network2'])
        cmd.append("--net:\"Network 3=%s\"" % edge['network3'])
        cmd.append("--acceptAllEulas")
        cmd.append("--noSSLVerify")
        cmd.append("--diskMode=thin")
        cmd.append("--powerOn")
        cmd.append("--prop:nsx_ip_0=%s" % edge['ip'])
        cmd.append("--prop:nsx_netmask_0=%s" % edge['netmask'])
        cmd.append("--prop:nsx_gateway_0=%s" % edge['gw'])
        cmd.append("--prop:nsx_dns1_0=%s" % config['dns'])
        cmd.append("--prop:nsx_domain_0=%s" % config['domain'])
        cmd.append("--prop:nsx_ntp_0=%s" % config['ntp'])
        cmd.append("--prop:nsx_isSSHEnabled=True")
        cmd.append("--prop:nsx_allowSSHRootLogin=True")
        cmd.append("--prop:nsx_passwd_0=%s" % edge['password'])
        cmd.append("--prop:nsx_cli_passwd_0=%s" %
                   edge['password'])
        cmd.append("--prop:nsx_hostname=%s" % edge['name'])
        cmd.append(edge['ova'])
        cmd.append("vi://%s:%s@%s/?ip=%s" % (config['vc_mng']['user'], config['vc_mng']
                                             ['password'], config['vc_mng']['ip'], edge['vmhost']))
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
    logger.info('Join edge with manager')
    for edge in config['nsxEdge']:
        connect_cli(edge)
        _get_manager_status(edge)
        if not edge['join_manager']:
            stdin, stdout, stderr = edge['cli'].exec_command(
                "join management-plane %s username %s password %s thumbprint %s" % (config['nsxManager']['ip'], config['nsxManager']['user'],  config['nsxManager']['password'], thumbprint))
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


def construct_parser(subparsers):
    edge_parser = subparsers.add_parser('edge', description="Functions for NSX edge",
                                        help="Functions for NSX edge")
    edge_subparsers = edge_parser.add_subparsers()
    edge_deploy_parser = edge_subparsers.add_parser(
        'deploy', help='Deploy NSX-T')
    edge_deploy_parser.set_defaults(func=deploy_edge)

    edge_join_manager_parser = edge_subparsers.add_parser(
        'join_manager', help='Join with NSX manager')
    edge_join_manager_parser.set_defaults(func=join_manager)

    edge_status_parser = edge_subparsers.add_parser(
        'status', help='Status of NSX edge')
    edge_status_parser.set_defaults(func=get_status)
