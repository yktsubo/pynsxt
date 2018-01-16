#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import json
from pprint import pprint
from pynsxt_utils import load_configfile, load_spec, api_request, get_api_client, convert_to_dict
from nsx_poolmanagement import list_ippool
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate
from pprint import pprint

logger = getLogger(__name__)


def list_uplink_profile(client):
    request = client.__getattr__('Network Transport').ListHostSwitchProfiles()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get uplink profiles")
        return []
    return response['results']


def _list_uplink_profile(client, **kwargs):
    uplink_profile_list = list_uplink_profile(client)
    _print_uplink_profile_tabulate(uplink_profile_list)
    pass


def _print_uplink_profile_tabulate(uplink_profile_list):
    print_list = []
    for uplink_profile in uplink_profile_list:
        print_list.append([uplink_profile['display_name'],
                           uplink_profile['id'],
                           uplink_profile['mtu'],
                           uplink_profile['transport_vlan'],
                           uplink_profile['teaming']['policy'],
                           ",".join(
                               [uplink['uplink_name'] for uplink in uplink_profile['teaming']['active_list']]),
                           ",".join([uplink['uplink_type'] for uplink in uplink_profile['teaming']['active_list']])])
    print tabulate(print_list, headers=["Uplink profile name", "ID", "MTU", "VLAN", "Policy", "Uplink Name", "Uplink Type"], tablefmt="psql")


def list_tz(client):
    """
    This function returns all TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    request = client.__getattr__('Network Transport').ListTransportZones()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get transport zones")
        return []
    return response['results']


def _list_tz(client, **kwargs):
    tz_list = list_tz(client)
    _print_tz_tabulate(tz_list)
    pass


def _print_tz_tabulate(tz_list):
    print_list = []
    for tz in tz_list:
        print_list.append((tz['display_name'],
                           tz['id'],
                           tz['host_switch_name'],
                           tz['transport_type'],
                           tz['host_switch_mode']))
    print tabulate(print_list, headers=["TZ name", "TZ ID", "Host Switch", "TZ type", "Host Switch mode"], tablefmt="psql")
    pass


def add_tz(client, tz):
    """
    This function returns alled TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'TransportZone': convert_to_dict(tz)}
    request = client.__getattr__(
        'Network Transport').CreateTransportZone(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not add compute manager with %s" %
                     tz.display_name)
        return []
    return [response]


def _add_tz(client, **kwargs):
    TransportZone = client.get_model('TransportZone')
    transport_type = kwargs['transport_type']
    host_switch_mode = kwargs['host_switch_mode']

    if not host_switch_mode:
        host_switch_mode = 'STANDARD'

    if transport_type == 'OVERLAY' and host_switch_mode == 'ENS':
        logger.error('Cannot create overlay host switch with ens mode')
        return

    tz = TransportZone(display_name=kwargs['display_name'],
                       host_switch_name=kwargs['host_switch_name'],
                       host_switch_mode=host_switch_mode,
                       transport_type=transport_type)

    tz_list = add_tz(client, tz)
    _print_tz_tabulate(tz_list)
    pass


def get_tz(client, oid):
    """
    This function returns TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'zone-id': oid}
    request = client.__getattr__('Network Transport').GetTransportZone(**param)
    response, responseAdapter = request.result()
    return [response]


def _get_tz(client, **kwargs):
    oid = kwargs['oid']
    tz_list = get_tz(client, oid)
    _print_tz_tabulate(tz_list)
    pass


def delete_tz(client, oid):
    """
    This function returns deleted TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    try:
        tzs = get_tz(client,  oid)
        tz = tzs[0]
    except:
        logger.error("No such a TZ with id: %s" % cmid)
        return []

    param = {'zone-id': oid}
    request = client.__getattr__(
        'Network Transport').DeleteTransportZone(**param)
    try:
        request.result()
    except:
        logger.error("Could not delete transport zone with %s" %
                     oid)
        return []
    return [tz]


def _delete_tz(client, **kwargs):
    oid = kwargs['oid']
    tz_list = delete_tz(client, oid)
    _print_tz_tabulate(tz_list)
    pass


def configure_cluster(client, cluster_name, tz_name, uplink_profile_name, ippool_name, pnic_name):
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

    tzs = list_tz(client)
    TransportZoneEndPoint = client.get_model('TransportZoneEndPoint')
    specificied_tz = None
    for tz in tzs:
        if tz['display_name'] == tz_name:
            specificied_tz = tz
            break

    if specificied_tz is None:
        logger.error("No such a transport zone with %s" % tz_name)
        return []
    tzep = TransportZoneEndPoint(transport_zone_id=specificied_tz['id'])
    # TODO should get uplink profile here
    HostSwitchProfileTypeIdEntry = client.get_model(
        'HostSwitchProfileTypeIdEntry')
    uplink_profiles = list_uplink_profile(client)
    specified_uplink_profile = None
    for uplink_profile in uplink_profiles:
        if uplink_profile['display_name'] == uplink_profile_name:
            specified_uplink_profile = uplink_profile
            break

    if specified_uplink_profile is None:
        logger.error("No such a uplink profile with %s" % uplink_profile_name)
        return []
    host_switch_profile_id = HostSwitchProfileTypeIdEntry(key='UplinkHostSwitchProfile',
                                                          value=specified_uplink_profile['id'])

    ippools = list_ippool(client)
    StaticIpPoolSpec = client.get_model('StaticIpPoolSpec')
    ip_pool_spec = None

    for ippool in ippools:
        if ippool['display_name'] == ippool_name:
            ip_pool_spec = StaticIpPoolSpec(ip_pool_id=ippool['id'],
                                            resource_type=u'StaticIpPoolSpec')
            break
    if ip_pool_spec is None:
        logger.error("No such Ip pool with %s" % ippool_name)
        return []

    pnic_list = []
    Pnic = client.get_model('Pnic')
    for i, pnic in enumerate(pnic_name):
        pnic_list.append(Pnic(device_name=pnic,
                              uplink_name=specified_uplink_profile['teaming']['active_list'][i]['uplink_name']))

    StandardHostSwitch = client.get_model('StandardHostSwitch')
    host_switch = StandardHostSwitch(host_switch_name=specificied_tz['host_switch_name'],
                                     cpu_config=[],
                                     host_switch_profile_ids=[
                                         host_switch_profile_id],
                                     ip_assignment_spec=ip_pool_spec,
                                     pnics=pnic_list)
    StandardHostSwitchSpec = client.get_model('StandardHostSwitchSpec')
    shss = StandardHostSwitchSpec(host_switches=[host_switch],
                                  resource_type='StandardHostSwitchSpec')

    ComputeCollectionTransportNodeTemplate = client.get_model(
        'ComputeCollectionTransportNodeTemplate')
    cctnt = ComputeCollectionTransportNodeTemplate(compute_collection_ids=[cc['external_id']],
                                                   host_switch_spec=shss,
                                                   resource_type='ComputeCollectionTransportNodeTemplate',
                                                   transport_zone_endpoints=[tzep])
    param = {'ComputeCollectionTransportNodeTemplate': convert_to_dict(cctnt)}
    request = client.__getattr__(
        'Network Transport').CreateComputeCollectionTransportNodeTemplate(**param)

    try:
        request.result()
    except:
        logger.error("Could not create compute collection transport template for %s" %
                     cluster_name)
        return []
    return [cc]
    pass


def _configure_cluster(client, **kwargs):
    cluster_name = kwargs['cluster_name']
    tz_name = kwargs['tz_name'][0]
    uplink_profile = kwargs['uplink_profile'][0]
    ippool_name = kwargs['ippool_name']
    pnic_name = kwargs['pnic_name']
    cc_list = configure_cluster(client,
                                cluster_name,
                                tz_name,
                                uplink_profile,
                                ippool_name,
                                pnic_name)
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


def configure_edge(client, edge_name, tz_name, uplink_profile, ippool_name):
    # TODO
    return []
    pass


def _configure_edge(client, **kwargs):
    # TODO
    edge_name = kwargs['edge_name']
    tzs = kwargs['tz_name']
    uplink_profiles = kwargs['uplink_profile']
    ippool_name = kwargs['ippool_name']
    cc_list = configure_edge(client,
                             edge_name,
                             tzs,
                             uplink_profiles,
                             ippool_name)
    pass


def construct_parser(subparsers):
    parser = subparsers.add_parser('transport', description="Functions for transport",
                                   help="Functions for transport",
                                   formatter_class=RawTextHelpFormatter)
    parser.add_argument("command", help="""
    get_tz:              Get transport zone
    list_tz:             List transport zone
    add_tz:              Add transport zone
    delete_tz:           Delete transport zone
    list_uplink_profile: List Uplink profiles
    configure_cluster:   Configure cluster
    configure_edge:      configure edge node as transport node
    """)

    parser.add_argument("-n",
                        "--display_name",
                        help="name for object")
    parser.add_argument("-i",
                        "--oid",
                        help="id for an object")
    parser.add_argument("--host-switch-name",
                        help="hostswitch name")
    parser.add_argument("--transport-type",
                        help="transport type for TZ",
                        choices=['OVERLAY', 'VLAN'])
    parser.add_argument("--host-switch-mode",
                        help="host switch mode for TZ",
                        choices=['STANDARD', 'ENS'])
    parser.add_argument("--cluster-name",
                        help="cluster name for auto configuration")
    parser.add_argument("--tz-name",
                        nargs='*',
                        help="TZ name for auto configuration")
    parser.add_argument("--uplink-profile",
                        nargs='*',
                        help="uplink profile name for auto configuration")
    parser.add_argument("--ippool-name",
                        help="ip pool name for auto configuration")
    parser.add_argument("--pnic-name",
                        nargs='*',
                        help="pnic name for auto configuration")
    parser.add_argument("--edge-name",
                        help="edge name to add as a transport node")
    parser.set_defaults(func=_transport_main)


def _transport_main(args):
    if args.debug:
        debug = True
    else:
        debug = False
    config = load_configfile(args)
    client = get_api_client(config, validation=args.spec_validation)

    try:
        command_selector = {
            'get_tz': _get_tz,
            'list_tz': _list_tz,
            'add_tz': _add_tz,
            'delete_tz': _delete_tz,
            'list_uplink_profile': _list_uplink_profile,
            'configure_cluster': _configure_cluster,
            'configure_edge': _configure_edge,
        }
        command_selector[args.command](client,
                                       display_name=args.display_name,
                                       host_switch_name=args.host_switch_name,
                                       transport_type=args.transport_type,
                                       host_switch_mode=args.host_switch_mode,
                                       cluster_name=args.cluster_name,
                                       tz_name=args.tz_name,
                                       uplink_profile=args.uplink_profile,
                                       ippool_name=args.ippool_name,
                                       pnic_name=args.pnic_name,
                                       edge_name=args.edge_name,
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
