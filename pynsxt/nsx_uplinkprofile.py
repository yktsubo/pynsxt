from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'Uplink Profile'
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
    This function returns all uplink profile in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    request = client.__getattr__(MODULE).ListHostSwitchProfiles()
    response, _ = request.result()
    return response['results']


def get(client, data):
    param = {'host-switch-profile-id': get_id(client, data)}
    request = client.__getattr__(MODULE).GetHostSwitchProfile(**param)
    response, _ = request.result()
    return response


def create(client, data):
    """
    This function returns uplink profile in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """
    hostswitchprofile = {}
    hostswitchprofile['display_name'] = data['display_name']
    hostswitchprofile['mtu'] = data['mtu']
    hostswitchprofile['transport_vlan'] = data['transport_vlan']
    hostswitchprofile['resource_type'] = 'UplinkHostSwitchProfile'
    hostswitchprofile['teaming'] = {'active_list': [],
                                    'standby_list': [], 'policy': data['teaming_policy']}
    for uplink in data['active_uplink']:
        hostswitchprofile['teaming']['active_list'].append({'uplink_name': uplink,
                                                            'uplink_type': 'PNIC'})
    if data.has_key('standby_uplink'):
        for uplink in data['standby_uplink']:
            hostswitchprofile['teaming']['standby_list'].append({'uplink_name': uplink,
                                                                 'uplink_type': 'PNIC'})

    param = {'BaseHostSwitchProfile': hostswitchprofile}
    request = client.__getattr__(MODULE).CreateHostSwitchProfile(**param)
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
    param = {'host-switch-profile-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteHostSwitchProfile(**param)
    response = request.result()
    return response


def exist(client, data):
    if get_id(client, data):
        return True
    else:
        return False


def run(client, action, data, config=None):
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        if exist(client, data):
            logger.error('Already exist')
        else:
            return create(client, data)
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
