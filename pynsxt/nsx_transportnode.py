from logging import basicConfig, getLogger, DEBUG
from pynsxt_utils import get_thumbprint
import nsx_uplinkprofile
import nsx_ippool
import nsx_tz
import nsx_hostnode
from pprint import pprint
logger = getLogger(__name__)

OBJECT = 'Transport Node'
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
    This function returns all fabric host nodes in NSX
    :param client: bravado client for NSX
    :return: returns a tuple, the first item is a list of tuples with item 0 containing the IPset Name as string
             and item 1 containing the IPset id as string. The second item contains a list of dictionaries containing
             all ipset details
    """

    request = client.__getattr__(MODULE).ListTransportNodes()
    response, _ = request.result()
    return response['results']


def get(client, data):
    param = {'transportnode-id': get_id(client, data)}
    request = client.__getattr__(MODULE).ReadNode(**param)
    response, _ = request.result()
    return response


def create(client, data):
    """
    """
    transportNode = {}
    transportNode["resource_type"] = "TransportNode"
    transportNode["display_name"] = data['display_name']
    transportNode['node_id'] = nsx_hostnode.get_id(
        client, {'display_name': data['node']})
    transportNode["transport_zone_endpoints"] = []
    transportNode["host_switch_spec"] = {"resource_type": "StandardHostSwitchSpec",
                                         "host_switches": []}
    transportNode["host_switch_spec"]["host_switches"] = []

    for nvds in data['nvds']:
        tz = nsx_tz.get(client, {'display_name': nvds['tz']})
        transportNode["transport_zone_endpoints"].append(
            {'transport_zone_id': tz['id']})

        uplinkprofile_id = nsx_uplinkprofile.get_id(
            client, {'display_name': nvds['uplink_profile']})
        hostswitch = {"host_switch_profile_ids": [
            {"value": uplinkprofile_id,
             "key": "UplinkHostSwitchProfile"}]}
        hostswitch["host_switch_name"] = tz['host_switch_name']
        hostswitch["pnics"] = []
        for uplink_name, device_name in nvds['uplink_mapping'].items():
            hostswitch["pnics"].append(
                {"device_name": device_name, "uplink_name": uplink_name})

        if nvds.has_key('ip_assignment'):
            hostswitch["ip_assignment_spec"] = {}
            if nvds['ip_assignment'].has_key('ippool'):
                hostswitch["ip_assignment_spec"]["resource_type"] = "StaticIpPoolSpec"
                ippool_id = nsx_ippool.get_id(
                    client, {'display_name': nvds['ip_assignment']['ippool']})
                hostswitch["ip_assignment_spec"]["ip_pool_id"] = ippool_id
        transportNode["host_switch_spec"]["host_switches"].append(hostswitch)

    param = {'TransportNode': transportNode}
    request = client.__getattr__(
        'Network Transport').CreateTransportNode(**param)
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
    param = {'transportnode-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteTransportZone(**param)
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
