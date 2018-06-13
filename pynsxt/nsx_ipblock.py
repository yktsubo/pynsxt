from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'IP block'
MODULE = 'Pool Management'


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListIpBlocks()
    response, _ = request.result()
    return response['results']


def get_subnet_list(client, data):
    param = {'block_id': get_id(client, data)}
    request = client.__getattr__(MODULE).ListIpBlockSubnets(**param)
    response, _ = request.result()
    return response['results']


def get(client, data):
    param = {'block-id': get_id(client, data)}
    request = client.__getattr__(MODULE).ReadIpBlock(**param)
    response, _ = request.result()
    return response


def update(client, data):
    param = {
        'block-id': get_id(client, data),
        'IpBlock': data
    }
    request = client.__getattr__(MODULE).UpdateIpBlock(**param)
    response, _ = request.result()
    return response


def get_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def get_subnet_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_subnet_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def create(client, data):
    """
    """
    param = {'IpBlock': data}
    request = client.__getattr__(MODULE).CreateIpBlock(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    param = {'block-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpBlock(**param)
    response = request.result()
    return response


def delete_subnet(client, data):
    """
    """
    param = {'subnet-id': get_subnet_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpBlockSubnet(**param)
    response = request.result()
    return response


def exist(client, data):
    if get_id(client, data):
        return True
    else:
        return False


def run(client, action, data, config=None):
    if action == 'create':
        if exist(client, data):
            logger.error('Already exist')
        else:
            return create(client, data)
    elif action == 'update':
        if exist(client, data):
            return update(client, data)
        else:
            logger.error('Not exist')
            return None
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
