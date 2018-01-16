#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import load_configfile, load_spec, api_request, get_api_client, get_thumbprint, convert_to_dict
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate

from pprint import pprint

logger = getLogger(__name__)


def list_hostnode(client):
    request = client.__getattr__('Fabric').ListNodes(resource_type='HostNode')
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get nodes")
        return []
    return response['results']


def _list_hostnode(client, **kwargs):
    node_list = list_hostnode(client)
    _print_hostnode_tabulate(node_list)
    pass


def _print_hostnode_tabulate(node_list):
    print_list = []
    for node in node_list:
        print_list.append([node['display_name'],
                           node['id'],
                           node['fqdn'],
                           node['os_type'],
                           ",".join(node['ip_addresses'])])
    print tabulate(print_list, headers=["Hostnode name", "ID", "FQDN", "OS Type", "IP"], tablefmt="psql")
    pass


def list_edgenode(client):
    request = client.__getattr__('Fabric').ListNodes(resource_type='EdgeNode')
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get nodes")
        return []
    return response['results']


def _list_edgenode(client, **kwargs):
    node_list = list_edgenode(client)
    _print_edgenode_tabulate(node_list)
    pass


def _print_edgenode_tabulate(node_list):
    print_list = []
    for node in node_list:
        print_list.append([node['display_name'],
                           node['id'],
                           node['deployment_type'],
                           ",".join(node['ip_addresses'])])
    print tabulate(print_list, headers=["Edgenode name", "ID", "Deployment type", "IP"], tablefmt="psql")
    pass


def list_cm(client):
    """
    This function returns all compute managers in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    request = client.__getattr__('Fabric').ListComputeManagers()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get compute managers")
        return []
    return response['results']


def _list_cm(client, **kwargs):
    cm_list = list_cm(client)
    _print_cm_tabulate(cm_list)
    pass


def add_cm(client, cm):
    """
    This function returns added compute manager in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'ComputeManager': convert_to_dict(cm)}
    request = client.__getattr__('Fabric').AddComputeManager(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not add compute manager with %s" %
                     cm.display_name)
        return []
    return [response]


def _add_cm(client, **kwargs):

    ComputeManager = client.get_model('ComputeManager')
    UsernamePasswordLoginCredential = client.get_model(
        'UsernamePasswordLoginCredential')
    auth = UsernamePasswordLoginCredential(
        username=kwargs['vc_user'],
        password=kwargs['vc_pass'],
        credential_type='UsernamePasswordLoginCredential',
        thumbprint=get_thumbprint(kwargs['vc_address']))
    cm = ComputeManager(
        origin_type='vCenter',
        display_name=kwargs['display_name'],
        server=kwargs['vc_address'],
        credential=auth)

    cm_list = add_cm(client, cm)
    _print_cm_tabulate(cm_list)
    pass


def get_cm(client, cmid):
    """
    This function returns Compute Manager having specified ID in NSX
    :param client: bravado client for NSX
    :param cmid: Compute Manager id
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all ip pool detail
    """
    param = {'compute-manager-id': cmid}
    request = client.__getattr__('Fabric').ReadComputeManager(**param)
    response, responseAdapter = request.result()
    return [response]


def _get_cm(client, **kwargs):
    cmid = kwargs['cmid']
    cm_list = get_cm(client, cmid)
    _print_cm_tabulate(cm_list)
    pass


def delete_cm(client, cmid):
    """
    This function returns deleted compute manager in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    try:
        cms = get_cm(client,  cmid)
        cm = cms[0]
    except:
        logger.error("No such a cm with id: %s" % cmid)
        return []

    param = {'compute-manager-id': cmid}
    request = client.__getattr__('Fabric').DeleteComputeManager(**param)
    try:
        request.result()
    except:
        logger.error("Could not delete compute manager with %s" %
                     cmid)
        return []
    return [cm]


def _delete_cm(client, **kwargs):
    cmid = kwargs['cmid']
    cm_list = delete_cm(client, cmid)
    _print_cm_tabulate(cm_list)
    pass


def _print_cm_tabulate(cm_list):
    print_list = []
    for cm in cm_list:
        print_list.append([cm['display_name'],
                           cm['id'],
                           cm['origin_type'],
                           cm['server']])
    print tabulate(print_list, headers=["CM name", "CM ID", "CM type", "CM IP"], tablefmt="psql")
    pass


def configure_cluster(client, cluster_name):
    param = {'display_name': cluster_name}
    request = client.__getattr__('Fabric').ListComputeCollections(**param)
    response, responseAdapter = request.result()
    if len(response['results']) == 0:
        logger.error("No such a Compute collection with %s" % cluster_name)
        return []
    elif len(response['results']) > 1:
        logger.error("More than one Compute collections with %s" %
                     cluster_name)
        return []
    cc = response['results'][0]
    ComputeCollectionFabricTemplate = client.get_model(
        'ComputeCollectionFabricTemplate')
    ccft = ComputeCollectionFabricTemplate(auto_install_nsx=True,
                                           compute_collection_id=cc['external_id'])
    param = {'ComputeCollectionFabricTemplate': convert_to_dict(ccft)}
    request = client.__getattr__(
        'Fabric').CreateComputeCollectionFabricTemplate(**param)
    try:
        request.result()
    except:
        logger.error("Could not create compute collection fabric template for %s" %
                     cluster_name)
        return []
    return [cc]


def _configure_cluster(client, **kwargs):
    cluster_name = kwargs['cluster_name']
    cc_list = configure_cluster(client, cluster_name)
    _print_cc_tabulate(cc_list)
    pass


def _print_cc_tabulate(cc_list):

    print_list = []
    for cc in cc_list:
        print_list.append([cc['display_name'],
                           cc['external_id'],
                           cc['origin_type']])
    print tabulate(print_list, headers=["Compute Collection name", "ID", "Origin type"], tablefmt="psql")
    pass


def construct_parser(subparsers):
    parser = subparsers.add_parser('fabric', description="Functions for fabric",
                                   help="Functions for fabric",
                                   formatter_class=RawTextHelpFormatter)
    parser.add_argument("command", help="""
    list_hostnode:  List Host nodes
    list_edgetnode: List Edge nodes
    add_cm:     Add new compute manager
    delete_cm:  Delete specified compute manager
    list_cm:    List compute manager
    configure_cluster: Configure cluster
    """)

    parser.add_argument("--vc_address",
                        help="vcenter address")
    parser.add_argument("--vc_user",
                        help="vcenter username")
    parser.add_argument("--vc_pass",
                        help="vcenter password")
    parser.add_argument("-n",
                        "--display_name",
                        help="name for object")
    parser.add_argument("-i",
                        "--oid",
                        help="id for an object")
    parser.add_argument("--cluster-name",
                        help="cluster name for auto configuration")

    parser.set_defaults(func=_fabric_main)


def _fabric_main(args):
    if args.debug:
        debug = True
    else:
        debug = False
    config = load_configfile(args)
    client = get_api_client(config, validation=args.spec_validation)

    try:
        command_selector = {
            'list_hostnode': _list_hostnode,
            'list_edgenode': _list_edgenode,
            'get_cm': _get_cm,
            'add_cm':  _add_cm,
            'list_cm': _list_cm,
            'delete_cm': _delete_cm,
            'configure_cluster': _configure_cluster,
        }
        command_selector[args.command](client,
                                       display_name=args.display_name,
                                       vc_address=args.vc_address,
                                       vc_user=args.vc_user,
                                       vc_pass=args.vc_pass,
                                       cluster_name=args.cluster_name,
                                       cmid=args.oid)

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
