#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
from pynsxt_utils import load_configfile, connect_cli, exec_command
from nsx_manager import get_thumbprint
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
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
        cmd.append("vi://%s:%s@%s/%s/host/%s" % (config['vcenter']['user'], config['vcenter']
                                             ['password'], config['vcenter']['ip'],  edge['datacenter'], edge['cluster']))
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


def list_edge_cluster(client):
    """
    This function returns all edge cluster in NSX
    :param client: bravado client for NSX
    :return: returns the list of edge cluster
    """
    request = client.__getattr__('Network Transport').ListEdgeClusters()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get edge clusters")
        return []
    return response['results']


def _list_edge_cluster(client, **kwargs):
    edge_cluster_list = list_edge_cluster(client)
    _print_edge_cluster_tabulate(edge_cluster_list)


def _print_edge_cluster_tabulate(edge_cluster_list):
    print_list = []
    for edge_cluster in edge_cluster_list:
        print_list.append((logicalrouter['display_name'],
                           logicalrouter['id'],
                           logicalrouter['router_type'],
                           logicalrouter['edge_cluster_id'],
                           logicalrouter['failover_mode'],
                           logicalrouter['high_availability_mode']))
    print tabulate(print_list, headers=["LR name", "ID", "Type", "Failover mode", "High availability mode"], tablefmt="psql")
    pass


def construct_parser(subparsers):
    parser = subparsers.add_parser('edge', description="Functions for NSX edge",
                                   help="Functions for NSX edge",
                                        formatter_class=RawTextHelpFormatter)
    edge_subparsers = parser.add_subparsers()
    edge_deploy_parser = edge_subparsers.add_parser(
        'deploy', help='Deploy NSX-T')
    edge_deploy_parser.set_defaults(func=deploy_edge)

    edge_join_manager_parser = edge_subparsers.add_parser(
        'join_manager', help='Join with NSX manager')
    edge_join_manager_parser.set_defaults(func=join_manager)

    edge_status_parser = edge_subparsers.add_parser(
        'status', help='Status of NSX edge')
    edge_status_parser.set_defaults(func=get_status)

    # parser.add_argument("command", help="""
    # list_edge_cluster:   List Edge Cluster
    # """)

    # parser.add_argument("-n",
    #                     "--display_name",
    #                     help="name for object")
    # parser.add_argument("-i",
    #                     "--oid",
    #                     help="id for an object")

    # parser.set_defaults(func=_edge_main)


def _edge_main(args):
    if args.debug:
        debug = True
    else:
        debug = False
    config = load_configfile(args)
    client = get_api_client(config, validation=args.spec_validation)

    try:
        command_selector = {
            'list_edge_cluster': _list_edge_cluster
        }
        command_selector[args.command](client,
                                       display_name=args.display_name,
                                       oid=args.oid)

    except KeyError as e:
        print('Unknown command {}'.format(e))


def main():
    main_parser = argparse.ArgumentParser()
    subparsers = main_parser.add_subparsers()
    contruct_parser(subparsers)
    args = main_parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
