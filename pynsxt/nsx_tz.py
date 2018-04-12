from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Transport Zone'
MODULE = 'Network Transport'


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
    This function returns all TZ in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    request = client.__getattr__(MODULE).ListTransportZones()
    response, _ = request.result()
    return response['results']


def get(client, data):
    param = {'zone-id': get_id(client, data)}
    request = client.__getattr__(MODULE).GetTransportZone(**param)
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
    param = {'TransportZone': data}
    request = client.__getattr__(MODULE).CreateTransportZone(**param)
    response, _ = request.result()
    return response


def update(client, data):
    """
    """
    param = {'zone-id': get_id(client, data)}
    request = client.__getattr__(MODULE).GetTransportZone(**param)
    tz, _ = request.result()

    for key in data.keys():
        if key == 'display_name' or key == 'id':
            continue
        tz[key] = data[key]

    param = {'zone-id': tz['id'], 'TransportZone': tz}
    request = client.__getattr__(MODULE).UpdateTransportZone(**param)
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
    param = {'zone-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteTransportZone(**param)
    response = request.result()
    return response


def exist(client, data):
    if get_id(client, data):
        return True
    else:
        return False


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        if exist(client, data):
            logger.error('Already exist')
        else:
            return create(client, data)
    elif action == 'update':
        return update(client, data)
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
