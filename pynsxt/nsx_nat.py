
import nsx_t0lr
import nsx_t1lr
from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)

OBJECT = 'NAT rule'
MODULE = 'Logical Routing And Services'


def get_list(client, logical_router_id):
    """
    This function returns all T0 logical routers in NSX
    :param client: bravado client for NSX
    :return: returns the list of logical routers
    """
    param = {}
    if logical_router_id:
        param['logical_router_id'] = logical_router_id
    else:
        return None
        
    request = client.__getattr__(MODULE).ListNatRules(**param)
    response, _ = request.result()
    return response['results']


def get_id(client, data, logical_router_id):
    if data.has_key('id'):
        return data['id']
    elif data.has_key('display_name'):
        objects = get_list(client, logical_router_id)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def create(client, data, logical_router_id):
    """
    """
    param = {'NatRule': {}}
    if logical_router_id:
        param['logical_router_id'] = logical_router_id
    else:
        return None

    param['NatRule']['action'] = data['action']
    param['NatRule']['display_name'] = data['display_name']    
    param['NatRule']["match_source_network"] = data["match_source_network"]
    param['NatRule']["match_destination_network"] = data["match_destination_network"]
    param['NatRule']["translated_network"] = data["translated_network"]
    param['NatRule']["enabled"] = True
    param['NatRule']['resource_type'] = 'NatRule'


    if data.has_key('match_service'):
        param['NatRule']['match_service'] = data['match_service']
    
    if data.has_key('rule_priority'):
        param['NatRule']['rule_priority'] = int(data['rule_priority'])
          
    if data.has_key('nat_pass'):
        param['NatRule']['nat_pass'] = data['nat_pass']
    
    if data.has_key('logging'):
        param['NatRule']["logging"] = data['logging']
    request = client.__getattr__(MODULE).AddNatRule(**param)
    response, _ = request.result()
    return response


def delete(client, data, logical_router_id):
    """
    """
    param = {'logical-router-id': logical_router_id, 'rule-id': get_id(client, data, logical_router_id)}
    request = client.__getattr__(MODULE).DeleteNatRule(**param)
    response, _ = request.result()
    return response


def exist(client, data, logical_router_id):
    if get_id(client, data, logical_router_id):
        return True
    else:
        return False


def run(client, action, data, config=None):
    t0lr = nsx_t0lr.get_id(client,{'display_name': data['LR']})
    t1lr = nsx_t1lr.get_id(client,{'display_name': data['LR']})
    logical_router_id = None
    if t0lr:
        logical_router_id = t0lr
    if t1lr:
        logical_router_id = t1lr
    if logical_router_id is None:
        logger.error("Logical Rotuer %s does not exist" % data['LR'])
        
    if action == 'create':
        if exist(client, data, logical_router_id):
            logger.error('Already exist')
        else:
            return create(client, data, logical_router_id)
    elif action == 'delete':
        if exist(client, data,logical_router_id):
            return delete(client, data, logical_router_id)
        else:
            logger.error('Not exist')
