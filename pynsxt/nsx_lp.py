#!/usr/bin/env python

from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Logical Port'
MODULE = 'Logical Switching'


def get_list(client):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(MODULE).ListLogicalPorts()
    response, _ = request.result()
    return response['results']


def get_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def create(client, data):
    """
    """
    param = {'LogicalPort': data}
    request = client.__getattr__(MODULE).CreateLogicalPort(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    param = {'lport-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalPort(**param)
    response, _ = request.result()
    return response
