from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Loadbalancer'
MODULE = 'Services'


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListLoadBalancerServices()
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
    pass
    # param = {'FirewallSection': data}
    # request = client.__getattr__(MODULE).AddSection(**param)
    # response, _ = request.result()
    # return response


def delete(client, data):
    """
    """
    param = {'service-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLoadBalancerService(**param)
    response = request.result()
    return response


def get_virtualserver_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListLoadBalancerVirtualServers()
    response, _ = request.result()
    return response['results']


def get_virualserver_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_virtualserver_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def delete_virtualserver(client, data):
    """
    """
    param = {'virtual-server-id': get_virualserver_id(client, data)}
    request = client.__getattr__(
        MODULE).DeleteLoadBalancerVirtualServer(**param)
    response = request.result()
    return response


def get_rule_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListLoadBalancerRules()
    response, _ = request.result()
    return response['results']


def get_rule_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_rule_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def delete_rule(client, data):
    """
    """
    param = {'rule-id': get_rule_id(client, data)}
    request = client.__getattr__(
        MODULE).DeleteLoadBalancerRule(**param)
    response = request.result()
    return response


def get_pool_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListLoadBalancerPools()
    response, _ = request.result()
    return response['results']


def get_pool_id(client, data):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_pool_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def delete_pool(client, data):
    """
    """
    param = {'pool-id': get_pool_id(client, data)}
    request = client.__getattr__(
        MODULE).DeleteLoadBalancerPool(**param)
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
        logger.error('Not implemented')
        return None
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
