from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'DFW section'
MODULE = 'Services'


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListSections()
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
    param = {'FirewallSection': data}
    request = client.__getattr__(MODULE).AddSection(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    param = {'section-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteSection(**param)
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
