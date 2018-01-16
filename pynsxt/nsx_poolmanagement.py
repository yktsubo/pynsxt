#!/usr/bin/env python

import argparse
from pprint import pprint
from pynsxt_utils import load_configfile, get_api_client, convert_to_dict
from logging import basicConfig, getLogger, DEBUG
from argparse import RawTextHelpFormatter
from tabulate import tabulate

logger = getLogger(__name__)


def delete_ippool(client, ippool_id):
    """
    This function returns deleted ip pool found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all pool details
    """
    try:
        ipPools = get_ippool(client,  ippool_id)
        ipPool = ipPools[0]
    except:
        logger.error("No such a ip pool with id: %s" % ippool_id)
        return ([], [])

    param = {'pool-id': ippool_id}
    request = client.__getattr__('Pool Management').DeleteIpPool(**param)
    request.also_return_response = True
    try:
        request.result()
    except:
        logger.error("Could not delete ip pool with id: %s" % ippool_id)
        return ([], [])
    return [ipPool]


def _delete_ippool(client, **kwargs):
    ippool_id = kwargs['ippool_id']
    ippool_list = delete_ippool(client, ippool_id)
    _print_tabulate(ippool_list)
    pass


def get_ippool(client, ippool_id):
    """
    This function returns ip pool having specified ID in NSX
    :param client: bravado client for NSX
    :param ippool_id: IP pool id
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all ip pool detail
    """
    param = {'pool-id': ippool_id}
    request = client.__getattr__('Pool Management').ReadIpPool(**param)
    request.also_return_response = True
    ipPool, responseAdapter = request.result()
    return [ipPool]


def _get_ippool(client, **kwargs):
    ippool_id = kwargs['ippool_id']
    ippool_list = get_ippool(client, ippool_id)
    _print_tabulate(ippool_list)
    pass


def list_ippool(client):
    """
    This function returns all ip pools found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    request = client.__getattr__(
        'Pool Management').ListIpPools()
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not get ip pools")
        return ([], [])

    return response['results']


def _list_ippool(client, **kwargs):
    ippool_list = list_ippool(client)
    _print_tabulate(ippool_list)


def _test_ippool(client, **kwargs):
    # Test to add ip pool
    logger.info("Test for adding")
    _add_ippool(client,
                start='192.168.10.1',
                end='192.168.10.100',
                cidr='192.168.10.0/24',
                display_name='UNITTEST',
                dns_nameserver='192.168.10.254',
                dns_suffix='ytsuboi.local',
                gateway='192.168.10.254')

    # List ip Pools
    logger.info("Test for list ippool")
    _list_ippool(client)

    ipPools = list_ippool(client)
    for ippoolId4Test in [ippool['id'] for ippool in ipPools if ippool['display_name'] == 'UNITTEST']:
        # Get ip Pools
        logger.info("Test for Get ippool")
        _get_ippool(client, ippool_id=ippoolId4Test)

        # Delete ip Pools
        logger.info("Test for Delete ippool")
        _delete_ippool(client, ippool_id=ippoolId4Test)

        # List ip Pools
        logger.info("Test for list ippool")
        _list_ippool(client)

    pass


def add_ippool(client, ippool):
    """
    This function returns deleted ip pool found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all pool details
    """
    ippool
    param = {'IpPool': convert_to_dict(ippool)}
    request = client.__getattr__('Pool Management').CreateIpPool(**param)
    try:
        response, responseAdpter = request.result()
    except:
        logger.error("Could not create ip pool with id: %s" %
                     ippool.display_name)
        return ([], [])
    return [response]


def _add_ippool(client, **kwargs):
    IpPool = client.get_model('IpPool')
    IpPoolSubnet = client.get_model('IpPoolSubnet')
    IpPoolRange = client.get_model('IpPoolRange')
    newIpPoolRange = IpPoolRange(start=kwargs['start'], end=kwargs['end'])
    newIpPoolSubnet = IpPoolSubnet(allocation_ranges=[newIpPoolRange],
                                   cidr=kwargs['cidr'])
    if kwargs['dns_nameserver']:
        newIpPoolSubnet.dns_nameservers = [kwargs['dns_nameserver']]
    if kwargs['gateway']:
        newIpPoolSubnet.gateway_ip = kwargs['gateway']
    if kwargs['dns_suffix']:
        newIpPoolSubnet.dns_suffix = kwargs['dns_suffix']

    newIpPool = IpPool(
        display_name=kwargs['display_name'], resource_type='IpPool', subnets=[newIpPoolSubnet])

    ippool_list = add_ippool(client, newIpPool)
    _print_tabulate(ippool_list)
    pass


def _print_tabulate(ippool_list):
    print_list = []
    for ippool in ippool_list:
        pool = ["", "", "", ""]
        pool[0] = ippool['display_name']
        pool[1] = ippool['id']
        if ippool['subnets']:
            for subnet in ippool['subnets']:
                pool[2] += subnet['cidr'] + ","
                if subnet['gateway_ip']:
                    pool[3] += subnet['gateway_ip'] + ","
                else:
                    pool[3] += ","
        print_list.append(pool)
    print tabulate(print_list, headers=["IP pool name", "IP pool ID", "CIDR", "Gateway"], tablefmt="psql")


def _pool_main(args):
    if args.debug:
        debug = True
    else:
        debug = False

    config = load_configfile(args)
    client = get_api_client(config)

    try:
        command_selector = {
            'add_ippool': _add_ippool,
            'get_ippool': _get_ippool,
            'list_ippool': _list_ippool,
            'delete_ippool': _delete_ippool,
            'test_ippool': _test_ippool
        }
        command_selector[args.command](client,
                                       ippool_id=args.ippool_id,
                                       start=args.start,
                                       end=args.end,
                                       cidr=args.cidr,
                                       display_name=args.display_name,
                                       gateway=args.gateway,
                                       dns_nameserver=args.dns_nameserver,
                                       dns_suffix=args.dns_suffix,)

    except KeyError as e:
        print('Unknown command {}'.format(e))


def construct_parser(subparsers):
    parser = subparsers.add_parser('pool', description="Functions for pool",
                                   help="Functions for pool",
                                   formatter_class=RawTextHelpFormatter)

    parser.add_argument("command", help="""
    add_ippool:       return an added IP pool
    get_ippool:       return a IP pool    
    list_ippool:      return a list of IP pool
    delete_ippool:    return deleted ip pool
    test_ippool: test
    """)
    parser.add_argument("-i", "--ippool_id",
                        help="IP pool id needed for delete")
    parser.add_argument("-s", "--start",
                        help="start of IP pool")
    parser.add_argument("-e", "--end",
                        help="end of IP pool")
    parser.add_argument("-c", "--cidr",
                        help="cidr of IP pool")
    parser.add_argument("-n", "--display_name",
                        help="display name of IP pool")
    parser.add_argument("-g", "--gateway",
                        help="gateway of IP pool")
    parser.add_argument("--dns_nameserver",
                        help="dns server of IP pool")
    parser.add_argument("--dns_suffix",
                        help="dns suffix of IP pool")

    parser.set_defaults(func=_pool_main)


def main():
    pass


if __name__ == "__main__":
    main()
