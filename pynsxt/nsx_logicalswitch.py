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


def list_logicalswitch(client):
    """
    This function returns all LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical switch
    """
    request = client.__getattr__('Logical Switching').ListLogicalSwitches()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get logical switches")
        return []
    return response['results']


def _list_logicalswitch(client, **kwargs):
    logicalswitch_list = list_logicalswitch(client)
    tz_list = list_tz(client)
    _print_logicalswitch_tabulate(logicalswitch_list, tz_list)
    pass


def _print_logicalswitch_tabulate(logicalswitch_list, tz_list):
    tz_dict = {}
    for tz in tz_list:
        tz_dict[tz['id']] = tz['display_name']

    print_list = []
    for logicalswitch in logicalswitch_list:
        if logicalswitch['vlan'] != None:
            print_list.append((logicalswitch['display_name'],
                               logicalswitch['id'],
                               logicalswitch['admin_state'],
                               'VLAN',
                               logicalswitch['vlan'],
                               tz_dict[logicalswitch['transport_zone_id']]))
        else:
            print_list.append((logicalswitch['display_name'],
                               logicalswitch['id'],
                               logicalswitch['admin_state'],
                               'VXLAN',
                               logicalswitch['vni'],
                               tz_dict[logicalswitch['transport_zone_id']]))
    print tabulate(print_list, headers=["LS name", "ID", "State", "Type", "VLAN/VNI", "Transport zone"], tablefmt="psql")
    pass


def add_logicalswitch(client, logicalswitch):
    """
    This function returns alled LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'LogicalSwitch': convert_to_dict(logicalswitch)}
    request = client.__getattr__(
        'Logical Switching').CreateLogicalSwitch(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not add create logicalswitch with %s" %
                     logicalswitch.display_name)
        return []
    return [response]


def _add_logicalswitch(client, **kwargs):

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

    LogicalSwitch = client.get_model('LogicalSwitch')
    if transport_type == 'VLAN':
        if not kwargs['vlan']:
            logger.error("You need vlan id to create an vlan logical switch")
            return
        logicalswitch = LogicalSwitch(display_name=kwargs['display_name'],
                                      admin_state='UP',
                                      resource_type='LogicalSwitch',
                                      vlan=kwargs['vlan'],
                                      transport_zone_id=transport_zone_id)
    elif transport_type == 'OVERLAY':
        if not kwargs['vlan']:
            logger.error("You need vlan id to create an vlan logical switch")
            return
        logicalswitch = LogicalSwitch(display_name=kwargs['display_name'],
                                      admin_state='UP',
                                      replication_mode=kwargs['replication_mode'],
                                      resource_type='LogicalSwitch',
                                      transport_zone_id=transport_zone_id)

    logicalswitch_list = add_logicalswitch(client, logicalswitch)
    _print_logicalswitch_tabulate(logicalswitch_list, tz_list)
    pass


def get_logicalswitch(client, oid):
    """
    This function returns LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a list includes finding Logical switch 
    """
    param = {'lswitch-id': oid}
    request = client.__getattr__('Logical Switching').GetLogicalSwitch(**param)
    response, responseAdapter = request.result()
    return [response]


def _get_logicalswitch(client, **kwargs):
    oid = kwargs['oid']
    logicalswitch_list = get_logicalswitch(client, oid)
    tz_list = list_tz(client)
    _print_logicalswitch_tabulate(logicalswitch_list, tz_list)
    pass


def delete_logicalswitch(client, oid):
    """
    This function returns deleted LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a list containing deleted logical switch
    """

    try:
        logicalswitchs = get_logicalswitch(client,  oid)
        logicalswitch = logicalswitchs[0]
    except:
        logger.error("No such a Logical switch with id: %s" % oid)
        return []

    param = {'lswitch-id': oid}
    request = client.__getattr__(
        'Logical Switching').DeleteLogicalSwitch(**param)
    try:
        request.result()
    except:
        logger.error("Could not delete logical switch with %s" %
                     oid)
        return []
    return [logicalswitch]


def _delete_logicalswitch(client, **kwargs):
    oid = kwargs['oid']
    logicalswitch_list = delete_logicalswitch(client, oid)
    tz_list = list_tz(client)
    _print_logicalswitch_tabulate(logicalswitch_list, tz_list)
    pass


def construct_parser(subparsers):
    parser = subparsers.add_parser('logicalswitch', description="Functions for logicalswitch",
                                   help="Functions for logicalswitch",
                                   formatter_class=RawTextHelpFormatter)
    parser.add_argument("command", help="""
    get_ls:              Get logicalswitch
    list_ls:             List logicalswitch
    add_ls:              Add logicalswitch
    delete_ls:           Delete logicalswitch    
    """)

    parser.add_argument("-n",
                        "--display_name",
                        help="name for object")
    parser.add_argument("-i",
                        "--oid",
                        help="id for an object")
    parser.add_argument("--vlan",
                        help="vlan for creating logical switch")
    parser.add_argument("--transport-zone-name",
                        help="transport zone name for creating logical switch")
    parser.add_argument("--replication-mode",
                        help="replication mode for logical switch",
                        default='MTEP',
                        choices=['MTEP', 'SOURCE'])

    parser.set_defaults(func=_logicalswitch_main)


def _logicalswitch_main(args):
    if args.debug:
        debug = True
    else:
        debug = False
    config = load_configfile(args)
    client = get_api_client(config, validation=args.spec_validation)

    try:
        command_selector = {
            'get_ls': _get_logicalswitch,
            'list_ls': _list_logicalswitch,
            'add_ls': _add_logicalswitch,
            'delete_ls': _delete_logicalswitch
        }
        command_selector[args.command](client,
                                       display_name=args.display_name,
                                       oid=args.oid,
                                       vlan=args.vlan,
                                       transport_zone_name=args.transport_zone_name,
                                       replication_mode=args.replication_mode)
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
