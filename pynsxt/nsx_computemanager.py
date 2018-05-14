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
