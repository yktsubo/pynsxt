import nsx_lrp
import nsx_lp
import nsx_edgecluster
import nsx_logicalswitch
import nsx_edge
import nsx_edgecluster
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'T0 Logical Router'
MODULE = 'Logical Routing And Services'


def get_list(client):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    request = client.__getattr__(
        MODULE).ListLogicalRouters(router_type='TIER0')
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


def get(client, data):
    param = {'logical-router-id': get_id(client, data)}
    request = client.__getattr__(MODULE).ReadLogicalRouter(**param)
    response, _ = request.result()
    return response


def create(client, data):
    """
    """
    data['edge_cluster_id'] = nsx_edgecluster.get_id(client,
                                                     {'display_name': data['edge_cluster_id']})
    param = {'LogicalRouter': data}
    request = client.__getattr__(MODULE).CreateLogicalRouter(**param)
    response, _ = request.result()
    return response


def delete(client, data):
    """
    """
    if is_ha_vip_config(client, data):
        _delete_ha_vip_config(client, data)

    t0_id = get_id(client, data)
    t0_lrp = nsx_lrp.get_list(client, logical_router_id=t0_id)
    lp_rm = []
    lrp_rm = []

    for lrp in t0_lrp:
        if lrp.has_key('linked_logical_switch_port_id'):
            lp_rm.append(lrp['linked_logical_switch_port_id']['target_id'])
        elif lrp.has_key('linked_logical_router_port_id'):
            lrp_rm.append(lrp['linked_logical_router_port_id'])
        lrp_rm.append(lrp['id'])

    for lrp in lrp_rm:
        nsx_lrp.delete(client, {'id': lrp})
    for lp in lp_rm:
        nsx_lp.delete(client, {'id': lp})

    param = {'logical-router-id': get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteLogicalRouter(**param)
    response = request.result()
    return response


def update(client, data):
    param = {
        'logical-router-id': data['id'],
        'LogicalRouter': data
    }
    request = client.__getattr__(MODULE).UpdateLogicalRouter(**param)
    response, _ = request.result()
    return response


def is_ha_vip_config(client, data):
    t0lr = get(client, data)
    if t0lr['advanced_config']['ha_vip_configs'] is None:
        return False
    else:
        return True


def _delete_ha_vip_config(client, data):
    t0_routerconfig = get(client, data)
    t0_routerconfig['advanced_config']['ha_vip_configs'] = None
    update(client, t0_routerconfig)


def _create_uplink(client, data):
    res = []
    t0_id = get_id(client, data)
    ls_id = nsx_logicalswitch.get_id(
        client, {'display_name': data['create_uplink']['ls']})

    param = {
        'logical_switch_id': ls_id,
        'display_name': "Uplink_on_%s" % data['create_uplink']['edge_node'],
        'admin_state': 'UP'
    }
    t0_lp = nsx_lp.create(client, param)

    edge_memberid = nsx_edge.get_memberid(
        client, {'display_name': data['create_uplink']['edge_node']})

    param = {
        'display_name': data['create_uplink']['display_name'],
        'resource_type': 'LogicalRouterUpLinkPort',
        'logical_router_id': t0_id,
        'tags': [],
        'linked_logical_switch_port_id': {
            'target_id': t0_lp['id']
        },
        'edge_cluster_member_index': [edge_memberid],
        'subnets': [{
            'ip_addresses': [data['create_uplink']['ip_address']],
            'prefix_length': data['create_uplink']['prefix_length']
        }]
    }
    nsx_lrp.create(client, param)


def _add_static_route(client, data):
    t0_id = get_id(client, data)

    param = {
        'logical-router-id': t0_id,
        'StaticRoute': data['add_static_route']
    }
    request = client.__getattr__(MODULE).AddStaticRoute(**param)
    response, _ = request.result()
    return response


def _update_ha_vip_config(client, data):
    t0_id = get_id(client, data)
    uplink_lrps = nsx_lrp.get_list(
        client, logical_router_id=t0_id, resource_type='LogicalRouterUpLinkPort')
    redundant_uplink_port_ids = []
    for uplink in data['ha_vip_config']['uplinks']:
        for uplink_lrp in uplink_lrps:
            if uplink_lrp['display_name'] == uplink:
                redundant_uplink_port_ids.append(uplink_lrp['id'])

    t0_routerconfig = get(client, data)
    t0_routerconfig['advanced_config']['ha_vip_configs'] = [
        {
            'enabled': True,
            'ha_vip_subnets': [
                {
                    'active_vip_addresses': [data['ha_vip_config']['vip']],
                    'prefix_length': data['ha_vip_config']['prefix_length']
                }
            ],
            'redundant_uplink_port_ids': redundant_uplink_port_ids
        }
    ]
    update(client, t0_routerconfig)


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
        if data.has_key('create_uplink'):
            return _create_uplink(client, data)
        elif data.has_key('add_static_route'):
            return _add_static_route(client, data)
        elif data.has_key('ha_vip_config'):
            return _update_ha_vip_config(client, data)
        else:
            logger.error('Not implemented')
            return None
    elif action == 'delete':
        if exist(client, data):
            return delete(client, data)
        else:
            logger.error('Not exist')
