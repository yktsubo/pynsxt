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


def get_allocations(client, data):
    param = {'pool-id': get_id(client, data)}
    request = client.__getattr__(MODULE).ListIpPoolAllocations(**param)
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
    obj_id = get_id(client, data)
    if not obj_id:
        return None
    param = {'pool-id': obj_id}
    request = client.__getattr__(MODULE).ReadIpPool(**param)
    response, _ = request.result()
    return response


def update(client, data):
    param = {
        'pool-id': get_id(client, data),
        'IpPool': data
    }
    request = client.__getattr__(MODULE).UpdateIpPool(**param)
    response, _ = request.result()
    return response


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


def delete(client, data, force=False):
    """
    """
    param = {'pool-id': get_id(client, data)}
    if force:
        param['force'] = True
    request = client.__getattr__(MODULE).DeleteIpPool(**param)
    response = request.result()
    return response


def delet_allocation(client, ippool, allocation):
    param = {'action': 'RELEASE', 'pool-id': ippool['id'], 'AllocationIpAddress': {
        'allocation_id': allocation['allocation_id']}}
    request = client.__getattr__(MODULE).AllocateOrReleaseFromIpPool(**param)
    response, _ = request.result()
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
