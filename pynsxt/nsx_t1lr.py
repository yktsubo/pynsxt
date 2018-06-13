import nsx_t0lr
import nsx_lrp
import nsx_lp
import nsx_edgecluster
import nsx_logicalswitch
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'T1 Logical Router'
MODULE = 'Logical Routing And Services'


def get_list(client):
    """
    This function returns all T1 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(
        MODULE).ListLogicalRouters(router_type='TIER1')
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
    if data.has_key('edge_cluster_id'):
        data['edge_cluster_id'] = nsx_edgecluster.get_id(
            {'display_name': data['edge_cluster_id']})

    param = {'LogicalRouter': data}
    request = client.__getattr__(MODULE).CreateLogicalRouter(**param)
    response, _ = request.result()
    return response


def _connect_to_t0lr(client, data):
    t0_id = nsx_t0lr.get_id(client, {'display_name': data['connect_to_T0']})
    t1_id = get_id(client, data)

    t1_lrps = nsx_lrp.get_list(client, logical_router_id=t1_id)

    if "Link_to_%s" % data['connect_to_T0'] in [lrp['display_name'] for lrp in t1_lrps]:
        logger.error('T1 Already connected to T0')
        return None
    
    param = {
        'display_name': "Link_to_%s" % data['display_name'],
        'resource_type': 'LogicalRouterLinkPortOnTIER0',
        'logical_router_id': t0_id
    }
    t0_lrp = nsx_lrp.create(client, param)
    param = {
        'display_name': "Link_to_%s" % data['connect_to_T0'],
        'resource_type': 'LogicalRouterLinkPortOnTIER1',
        'logical_router_id': t1_id,
        'linked_logical_router_port_id': {
            'target_id': t0_lrp['id']
        }
    }
    nsx_lrp.create(client, param)


def _connect_to_ls(client, data):
    res = []
    t1_id = get_id(client, data)
    ls_id = nsx_logicalswitch.get_id(
        client, {'display_name': data['connect_to_LS']['ls']})

    t1_lrps = nsx_lrp.get_list(client, logical_router_id=t1_id)

    if "Link_to_%s" % data['connect_to_LS']['ls'] in [lrp['display_name'] for lrp in t1_lrps]:
        logger.error("T1 Already connected to %s" % data['connect_to_LS']['ls'])
        return None
    
    param = {
        'logical_switch_id': ls_id,
        'display_name': 'To_%s' % data['display_name'],
        'admin_state': 'UP'
    }

    t1_lp = nsx_lp.create(client, param)

    param = {
        'display_name': "Link_to_%s" % data['connect_to_LS']['ls'],
        'resource_type': 'LogicalRouterDownLinkPort',
        'logical_router_id': t1_id,
        'tags': [],
        'linked_logical_switch_port_id': {
            'target_id': t1_lp['id']
        },
        'subnets': [{
            'ip_addresses': [data['connect_to_LS']['ip_address']],
            'prefix_length': data['connect_to_LS']['prefix_length']
        }]
    }
    nsx_lrp.create(client, param)


def _advertise(client, data):
    t1_id = get_id(client, data)
    param = {'logical-router-id': t1_id}
    request = client.__getattr__(MODULE).ReadAdvertisementConfig(**param)
    response, _ = request.result()

    param = {
        'logical-router-id': t1_id,
        'AdvertisementConfig': response
    }

    for key in data['advertisement'].keys():
        param['AdvertisementConfig'][key] = data['advertisement'][key]

    request = client.__getattr__(MODULE).UpdateAdvertisementConfig(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    t1_id = get_id(client, data)
    t1_lrp = nsx_lrp.get_list(client, logical_router_id=t1_id)
    lp_rm = []
    lrp_rm = []

    for lrp in t1_lrp:
        if lrp.has_key('linked_logical_switch_port_id'):
            lp_rm.append(lrp['linked_logical_switch_port_id']['target_id'])
        elif lrp.has_key('linked_logical_router_port_id'):
            lrp_rm.append(lrp['linked_logical_router_port_id'])
        lrp_rm.append(lrp['id'])

    for lrp in lrp_rm:
        nsx_lrp.delete(client, {'id': lrp})

    param = {'logical-router-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalRouter(**param)
    response = request.result()

    for lp in lp_rm:
        nsx_lp.delete(client, {'id': lp})

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
        if data.has_key('connect_to_T0'):
            return _connect_to_t0lr(client, data)
        elif data.has_key('connect_to_LS'):
            return _connect_to_ls(client, data)
        elif data.has_key('advertisement'):
            return _advertise(client, data)
        else:
            logger.error('Not implemented')
            return None
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
