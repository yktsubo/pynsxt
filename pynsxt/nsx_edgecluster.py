from logging import basicConfig, getLogger, DEBUG
import nsx_hostnode
from pprint import pprint
logger = getLogger(__name__)

OBJECT = 'Edge Cluster'
MODULE = 'Network Transport'


def get_list(client):
    """
    This function returns all edge cluster in NSX
    :param client: bravado client for NSX
    :return: returns the list of edge cluster
    """
    request = client.__getattr__(MODULE).ListEdgeClusters()
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


def get(client, data):
    param = {'edge-cluster-id': get_id(client, data)}
    request = client.__getattr__(MODULE).ReadNode(**param)
    response, _ = request.result()
    return response


def create(client, data):
    """
    This function returns alled TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    edgecluster = {"members": []}
    edgecluster['display_name'] = data['display_name']
    for member in data['members']:
        edgecluster['members'].append(
            {"transport_node_id": nsx_hostnode.get_id(client, {'display_name': member})})
    param = {'EdgeCluster': edgecluster}
    request = client.__getattr__(MODULE).CreateEdgeCluster(**param)

    response, _ = request.result()
    return response


def delete(client, data):
    """
    This function returns deleted TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    param = {'edge-cluster-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteTransportZone(**param)
    response = request.result()
    return response


def exist(client, data):
    if get_id(client, data):
        return True
    else:
        return False


def run(client, action, data, config=None):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        if exist(client, data):
            logger.error('Already exist')
        else:
            return create(client, data)
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
