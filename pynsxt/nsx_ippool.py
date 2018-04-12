from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'IP pool'
MODULE = 'Pool Management'


def get_list(client):
    """
    This function returns all ip pools found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    request = client.__getattr__(MODULE).ListIpPools()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + OBJECT)
        return []
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
    This function returns deleted ip pool found in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with IP pool summary.
             The second item contains a list of dictionaries containing all pool details
    """
    param = {'IpPool': data}
    request = client.__getattr__(MODULE).CreateIpPool(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    param = {'pool-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpPool(**param)
    response = request.result()
    return response


def exist(client, data):
    if get_id(client, data):
        return True
    else:
        return False


def run(client, action, data):
    if action == 'create':
        if exist(client, data):
            logger.error('Already exist')
        else:
            return create(client, data)
    elif action == 'update':
        logger.error('Not implemented')
        return None
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
