from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'IP block'
MODULE = 'Pool Management'


def get_list(client):
    """
    """
    request = client.__getattr__(MODULE).ListIpBlocks()
    try:
        response, _ = request.result()
    except:
        logger.error("Could not list " + OBJECT)
        return []
    return response['results']


def _get_id(client, data):
    if data.has_key('id'):
        return param['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def _create_ipblock(client, data):
    """
    """
    param = {'IpBlock': data}
    request = client.__getattr__(MODULE).CreateIpBlock(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _delete_ipblock(client, data):
    """
    """
    param = {'block-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpBlock(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_ipblock(client, data)
    elif action == 'delete':
        return _delete_ipblock(client, data)
