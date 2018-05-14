import nsx_tz
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)


OBJECT = 'LogicalSwitch'
MODULE = 'Logical Switching'


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
    This function returns all LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical switch
    """
    request = client.__getattr__(MODULE).ListLogicalSwitches()
    response, _ = request.result()
    return response['results']


def create(client, data):
    """
    This function returns alled LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    tz = nsx_tz.get(client, {'display_name': data['transport_zone_id']})
    data['transport_zone_id'] = tz['id']

    if tz['transport_type'] == 'VLAN':
        if not data['vlan']:
            logger.error("You need vlan id to create an vlan logical switch")
            return

    elif tz['transport_type'] == 'OVERLAY':
        data['replication_mode'] = 'MTEP'

    data['admin_state'] = 'UP'
    param = {'LogicalSwitch': data}
    request = client.__getattr__(MODULE).CreateLogicalSwitch(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    This function returns deleted LOGICALSWITCH in NSX
    :param client: bravado client for NSX
    :return: returns a list containing deleted logical switch
    """
    param = {'lswitch-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalSwitch(**param)
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
