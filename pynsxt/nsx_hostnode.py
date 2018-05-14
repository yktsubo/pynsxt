from logging import basicConfig, getLogger, DEBUG
from pynsxt_utils import get_thumbprint
from pprint import pprint
logger = getLogger(__name__)

OBJECT = 'Fabric Node'
MODULE = 'Fabric'


def get_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def get_list(client):
    """
    This function returns all fabric host nodes in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    request = client.__getattr__(MODULE).ListNodes()
    response, _ = request.result()
    return response['results']


def get(client, data):
    param = {'node-id': get_id(client, data)}
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
    param = {'Node': {}}
    param['Node']['display_name'] = data['display_name']
    param['Node']['ip_addresses'] = [data['ip']]
    param['Node']['os_type'] = data['os_type']
    param['Node']['resource_type'] = 'HostNode'
    param['Node']['host_credential'] = {
        'username': data['username'], 'password': data['password'], 'thumbprint': get_thumbprint(data['ip'])}
    request = client.__getattr__(MODULE).AddNode(**param)
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
    param = {'node-id': get_id(client, data)}
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
