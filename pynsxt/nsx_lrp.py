from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Logical Router Port'
MODULE = 'Logical Routing And Services'


def get_list(client, logical_router_id=None, resource_type=None):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    param = {}
    if logical_router_id:
        param['logical_router_id'] = logical_router_id
    if resource_type:
        param['resource_type'] = resource_type
    request = client.__getattr__(MODULE).ListLogicalRouterPorts(**param)
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
    param = {'LogicalRouterPort': data}
    request = client.__getattr__(MODULE).CreateLogicalRouterPort(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    param = {'logical-router-port-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalRouterPort(**param)
    response, _ = request.result()
    return response
