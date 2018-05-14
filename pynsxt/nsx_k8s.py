import nsx_logicalswitch
import nsx_lp
import nsx_tz
import nsx_t0lr
import nsx_ippool
import nsx_ipblock
from pynsxt_utils import has_tag, add_or_update_tag
from logging import basicConfig, getLogger, DEBUG
from pprint import pprint

logger = getLogger(__name__)


def _tag_check(client, data, obj, module, fix=False):
    obj_data = {'display_name': data[obj]}
    cluster_tag = {'scope': 'ncp/cluster', 'tag': data['cluster_name']}
    if module.exist(client, obj_data):
        obj_data = module.get(client, obj_data)
        if has_tag(obj_data, cluster_tag):
            logger.info(obj + ' has tag')
        else:
            logger.warning(obj + ' does not have tag')
            if fix:
                obj_data = add_or_update_tag(obj_data, cluster_tag)
                module.update(client, obj_data)
    else:
        logger.error(obj + ' does not exist')


def delete(client, data):
    logger.info('delete nat rules on T0')
    obj_data = {'display_name': data['t0']}
    t0 = nsx_t0lr.get(client, obj_data)
    param = {'logical-router-id': t0['id']}
    request = client.__getattr__(
        'Logical Routing And Services').ListNatRules(**param)
    response, _ = request.result()
    nat_ids = [i['id'] for i in response['results']]
    for ruleid in nat_ids:
        param = {'logical-router-id': t0['id'], 'rule-id': ruleid}
        request = client.__getattr__(
            'Logical Routing And Services').DeleteNatRule(**param)
        response = request.result()

    logger.info('delete ip allocations on ip pool')
    obj_data = {'display_name': data['ippool']['name']}
    ippool = nsx_ippool.get(client, obj_data)
    param = {'pool-id': ippool['id']}
    request = client.__getattr__(
        'Pool Management').ListIpPoolAllocations(**param)
    poolallocations, _ = request.result()
    if poolallocations['results']:
        for allocation in poolallocations['results']:
            param = {'action': 'RELEASE', 'pool-id': ippool['id'], 'AllocationIpAddress': {
                'allocation_id': allocation['allocation_id']}}
            request = client.__getattr__(
                'Pool Management').AllocateOrReleaseFromIpPool(**param)
            response, _ = request.result()


def validate(client, data, fix=False):
    cluster_tag = {'scope': 'ncp/cluster', 'tag': data['cluster_name']}
    obj_data = {'display_name': data['k8s_transport_ls']}
    if nsx_logicalswitch.exist(client, obj_data):
        logger.info('K8s transport LS exists')
    else:
        logger.error('K8s transport LS does not exist')
        if fix:
            obj_data['transport_zone_id'] = data['tz']
            nsx_logicalswitch.create(client, obj_data)

    # Check VIF tag
    ls_lps = nsx_lp.get_list(client,
                             logical_switch_id=nsx_logicalswitch.get_id(client, obj_data))
    request = client.__getattr__('Fabric').ListVirtualMachines()
    vms = request.result()[0]['results']
    request = client.__getattr__('Fabric').ListVifs()
    vifs = request.result()[0]['results']
    for node in data['nodes']:
        vm_id = [vm['external_id'] for vm in vms if vm['display_name'] == node]
        if len(vm_id) == 1:
            vm_vifs = [vif for vif in vifs if vif['owner_vm_id'] == vm_id[0]]
            for vm_vif in vm_vifs:
                vm_lp = [lp for lp in ls_lps if lp['attachment']
                         ['id'] == vm_vif['lport_attachment_id']]
                if len(vm_lp) == 1:
                    obj_data = vm_lp[0]
                    node_tag = {'scope': 'ncp/node_name', 'tag': node}
                    if has_tag(obj_data, cluster_tag) and has_tag(obj_data, node_tag):
                        logger.info('LP attached to VIF has tag')
                    else:
                        logger.warning('LP attached to VIF does not have tag')
                        if fix:
                            obj_data = add_or_update_tag(obj_data, cluster_tag)
                            obj_data = add_or_update_tag(obj_data, node_tag)
                            nsx_lp.update(client, obj_data)
    pass


def run(client, action, data, config=None):
    if action == 'create':
        logger.error('Not implemented')
        return None
    elif action == 'update':
        if data.has_key('validate'):
            return validate(client, data['validate'], fix=data['validate']['fix'])
        else:
            logger.error('Not implemented')
            return None
    elif action == 'delete':
        return delete(client, data)
