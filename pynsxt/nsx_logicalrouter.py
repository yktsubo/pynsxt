#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import load_configfile, load_spec, api_request, get_api_client, convert_to_dict
from nsx_transport import list_tz
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)


def list_t0_logicalrouter(client):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(
        'Logical Routing And Services').ListLogicalRouters(router_type='TIER0')
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get logical routers")
        return []
    return response['results']


def _list_t0_logicalrouter(client, **kwargs):
    t0logicalrouter_list = list_t0_logicalrouter(client)
    _print_logicalrouter_tabulate(t0logicalrouter_list)
    pass


def get_logicalrouter(client, oid):
    """
    This function returns logical router in NSX
    :param client: bravado client for NSX
    :return: returns a list includes found Logical router
    """
    param = {'logical-router-id': oid}
    request = client.__getattr__(
        'Logical Routing And Services').ReadLogicalRouter(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get logical router")
        return []
    return [response]


def _get_logicalrouter(client, **kwargs):
    oid = kwargs['oid']
    logicalrouter_list = get_logicalrouter(client, oid)
    _print_logicalrouter_tabulate(logicalrouter_list)
    pass


def _print_logicalrouter_tabulate(logicalrouter_list):
    print_list = []
    for logicalrouter in logicalrouter_list:
        print_list.append((logicalrouter['display_name'],
                           logicalrouter['id'],
                           logicalrouter['router_type'],
                           logicalrouter['edge_cluster_id'],
                           logicalrouter['failover_mode'],
                           logicalrouter['high_availability_mode']))
    print tabulate(print_list, headers=["LR name", "ID", "Type", "Failover mode", "High availability mode"], tablefmt="psql")
    pass


def add_t0_logicalrouter(client, logicalrouter):
    """
    This function returns added logical router in NSX
    :param client: bravado client for NSX
    :return: returns a list includes added logical router
    """
    param = {'Logicalrouter': convert_to_dict(logicalrouter)}
    request = client.__getattr__(
        'Logical Routing And Services').CreateLogicalRouter(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not add create logicalrouter with %s" %
                     logicalrouter['display_name'])
        return []
    return [response]


def _add_t0_logicalrouter(client, **kwargs):

    tz_list = list_tz(client)
    transport_zone_id = None
    for tz in tz_list:
        if tz['display_name'] == kwargs['transport_zone_name']:
            transport_zone_id = tz['id']
            transport_type = tz['transport_type']
            break

    if transport_zone_id == None:
        logger.error("No such a transport zone with %s" %
                     kwargs['transport_zone_name'])
        return

    LogicalRouter = client.get_model('LogicalRouter')
    lr = Logicalrouter(display_name=kwargs['display_name'],
                       resource_type='LogicalRouter',
                       router_type='TIER0',
                       high_availability_mode='ACTIVE_ACTIVE',
                       edge_cluster_id='')
    logicalrouter_list = add_t0_logicalrouter(client, lr)
    _print_logicalrouter_tabulate(logicalrouter_list, tz_list)
    pass


def delete_logicalrouter(client, oid):
    """
    This function returns deleted LOGICALROUTER in NSX
    :param client: bravado client for NSX
    :return: returns a list containing deleted logical switch
    """

    try:
        logicalrouters = get_logicalrouter(client,  oid)
        logicalrouter = logicalrouters[0]
    except:
        logger.error("No such a Logical switch with id: %s" % oid)
        return []

    param = {'lswitch-id': oid}
    request = client.__getattr__(
        'Logical Switching').DeleteLogicalrouter(**param)
    try:
        request.result()
    except:
        logger.error("Could not delete logical switch with %s" %
                     oid)
        return []
    return [logicalrouter]


def _delete_logicalrouter(client, **kwargs):
    oid = kwargs['oid']
    logicalrouter_list = delete_logicalrouter(client, oid)
    tz_list = list_tz(client)
    _print_logicalrouter_tabulate(logicalrouter_list, tz_list)
    pass


def construct_parser(subparsers):
    parser = subparsers.add_parser('logicalrouter', description="Functions for logicalrouter",
                                   help="Functions for logicalrouter",
                                   formatter_class=RawTextHelpFormatter)
    parser.add_argument("command", help="""
    get_t0:              Get T0 logicalrouter
    list_t0:             List T0 logicalrouter
    add_t0:              Add T0 logicalrouter
    delete_t0:           Delete T0 logicalrouter
    get_t1:              Get T1 logicalrouter
    list_t1:             List T1 logicalrouter
    add_t1:              Add T1 logicalrouter
    delete_t1:           Delete T1 logicalrouter    
    """)

    parser.add_argument("-n",
                        "--display_name",
                        help="name for object")
    parser.add_argument("-i",
                        "--oid",
                        help="id for an object")
    # parser.add_argument("--vlan",
    #                     help="vlan for creating logical switch")
    # parser.add_argument("--transport-zone-name",
    #                     help="transport zone name for creating logical switch")
    # parser.add_argument("--replication-mode",
    #                     help="replication mode for logical switch",
    #                     default='MTEP',
    #                     choices=['MTEP', 'SOURCE'])

    parser.set_defaults(func=_logicalrouter_main)


def _logicalrouter_main(args):
    if args.debug:
        debug = True
    else:
        debug = False
    config = load_configfile(args)
    client = get_api_client(config, validation=args.spec_validation)

    try:
        command_selector = {
            'get_t0': _get_t0_logicalrouter,
            'list_t0': _list_t0_logicalrouter,
            'add_t0': _add_t0_logicalrouter,
            # 'delete_t0': _delete_t0_logicalrouter,
            # 'get_t1': _get_t1_logicalrouter,
            # 'list_t1': _list_t1_logicalrouter,
            # 'add_t1': _add_t1_logicalrouter,
            # 'delete_t1': _delete_t1_logicalrouter
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
