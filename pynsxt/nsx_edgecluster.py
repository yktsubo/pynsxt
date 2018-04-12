from logging import basicConfig, getLogger, DEBUG

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
