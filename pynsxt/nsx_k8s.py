import nsx_logicalswitch
import nsx_lp
import nsx_tz
import nsx_t0lr
import nsx_t1lr
import nsx_lrp
import nsx_ippool
import nsx_ipblock
import nsx_dfw_section
import nsx_nsgroup
import nsx_ipset
import nsx_loadbalancer
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


def _cleanup_t0_snat(client, data, allocated_ips):
    t0 = {'display_name': data['t0']}
    t0_nat_list = nsx_t0lr.get_nat_list(client, t0)
    snat_list = [nat for nat in t0_nat_list
                 if nat['action'] == 'SNAT' and nat['translated_network'] in allocated_ips]
    logger.info("Number of SNAT to be deleted: %s" % len(snat_list))
    for nat in t0_nat_list:
        nsx_t0lr.delete_nat(client, t0, nat)
        logger.info("T0 SNAT: %s is deleted" % nat['display_name'])


def _cleanup_dfw_sections(client, data):
    dfw_sections = get_ncp_objects(
        nsx_dfw_section.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of Firewall Sections to be deleted: %s" %
                len(dfw_sections))
    if data['dry_run']:
        return
    for dfw in dfw_sections:
        nsx_dfw_section.delete(client, dfw)
        logger.info("Firewall Section: %s is deleted" % dfw['display_name'])


def _cleanup_ns_groups(client, data):
    nsgroups = get_ncp_objects(
        nsx_nsgroup.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of NSGroup to be deleted: %s" %
                len(nsgroups))
    if data['dry_run']:
        return
    for nsgroup in nsgroups:
        nsx_nsgroup.delete(client, nsgroup)
        logger.info("NSGroup: %s is deleted" % nsgroup['display_name'])


def _cleanup_ip_sets(client, data):
    ipsets = get_ncp_objects(
        nsx_ipset.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of IPset to be deleted: %s" %
                len(ipsets))
    if data['dry_run']:
        return
    for ipset in ipsets:
        nsx_ipset.delete(client, ipset)
        logger.info("IPset: %s is deleted" % ipset['display_name'])


def _cleanup_dfw_sections(client, data):
    dfw_sections = get_ncp_objects(
        nsx_dfw_section.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of Firewall Sections to be deleted: %s" %
                len(dfw_sections))
    if data['dry_run']:
        return
    for dfw in dfw_sections:
        nsx_dfw_section.delete(client, dfw)
        logger.info("Firewall Section: %s is deleted" % dfw['display_name'])


def _cleanup_lb_services(client, data):
    lb_services = get_ncp_objects(
        nsx_loadbalancer.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of LB to be deleted: %s" %
                len(lb_services))
    if data['dry_run']:
        return
    for lb_service in lb_services:
        nsx_loadbalancer.delete(client, lb_service)
        logger.info("LB: %s is deleted" % lb_service['display_name'])


def _cleanup_lb_virtual_servers(client, data):
    lb_vss = get_ncp_objects(
        nsx_loadbalancer.get_virtualserver_list(client), cluster=data['cluster_name'])
    logger.info("Number of LB virtual server to be deleted: %s" %
                len(lb_vss))
    if data['dry_run']:
        return
    for lb_vs in lb_vss:
        nsx_loadbalancer.delete_virtualserver(client, lb_vs)
        logger.info("LB virtual server: %s is deleted" %
                    lb_vs['display_name'])


def _cleanup_lb_rules(client, data):
    lb_rules = get_ncp_objects(
        nsx_loadbalancer.get_rule_list(client), cluster=data['cluster_name'])
    logger.info("Number of LB rule to be deleted: %s" %
                len(lb_rules))
    if data['dry_run']:
        return
    for lb_rule in lb_rules:
        nsx_loadbalancer.delete_rule(client, lb_rule)
        logger.info("LB rule: %s is deleted" %
                    lb_rule['display_name'])


def _cleanup_lb_pools(client, data):
    lb_pools = get_ncp_objects(
        nsx_loadbalancer.get_pool_list(client), cluster=data['cluster_name'])
    logger.info("Number of LB pool to be deleted: %s" %
                len(lb_pools))
    if data['dry_run']:
        return
    for lb_pool in lb_pools:
        nsx_loadbalancer.delete_pool(client, lb_pool)
        logger.info("LB pool: %s is deleted" %
                    lb_pool['display_name'])


def _cleanup_lrp(client, data):

    lrps = get_ncp_objects(
        nsx_lrp.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of Logical Router port to be deleted: %s" %
                len(lrps))
    if data['dry_run']:
        return
    for lrp in lrps:
        nsx_lrp.delete(client, lrp, force=True)
        logger.info("Logical Router port: %s is deleted" %
                    lrp['display_name'])


def _cleanup_lp(client, data):

    lps = get_ncp_objects(
        nsx_lp.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of Logical port to be deleted: %s" %
                len(lps))
    if data['dry_run']:
        return
    for lp in lps:
        nsx_lp.delete(client, lp, force=True)
        logger.info("Logical port: %s is deleted" %
                    lp['display_name'])


def _cleanup_t1lr(client, data):
    t1_routers = get_ncp_objects(
        nsx_t1lr.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of T1 Router to be deleted: %s" %
                len(t1_routers))
    if data['dry_run']:
        return
    for t1 in t1_routers:
        lrps = nsx_lrp.get_list(client, logical_router_id=t1['id'])
        for lrp in lrps:
            nsx_lrp.delete(client, lrp, force=True)
            logger.info("Logical Router port: %s is deleted" %
                        lrp['display_name'])

        nsx_t1lr.delete(client, t1)
        logger.info("T1 Router: %s is deleted" %
                    t1['display_name'])


def _cleanup_logicalswitch(client, data):
    logical_switches = get_ncp_objects(
        nsx_logicalswitch.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of Logical Switch to be deleted: %s" %
                len(logical_switches))
    if data['dry_run']:
        return
    for ls in logical_switches:
        nsx_logicalswitch.delete(client, ls, force=True)
        logger.info("Logical Switch: %s is deleted" %
                    ls['display_name'])


def _cleanup_ippool(client, data):
    ippools = get_ncp_objects(
        nsx_ippool.get_list(client), cluster=data['cluster_name'])
    logger.info("Number of IP pool to be deleted: %s" %
                len(ippools))
    if data['dry_run']:
        return
    for ippool in ippools:
        nsx_ippool.delete(client, ippool, force=True)
        logger.info("IP pool: %s is deleted" %
                    ippool['display_name'])


def _cleanup_ipblock_allocation(client, data):
    ipblock = nsx_ipblock.get(
        client, {'display_name': data['ipblock']['name']})
    ipblock_subnets = nsx_ipblock.get_subnet_list(client, ipblock)

    logger.info("Number of IP block subnets to be deleted: %s" %
                len(ipblock_subnets))
    if data['dry_run']:
        return
    for subnet in ipblock_subnets:
        nsx_ipblock.delete_subnet(client, subnet)
        logger.info("IP block subnet: %s is deleted" %
                    subnet['display_name'])


def _cleanup_ippool_allocation(client, data):
    ippool = nsx_ippool.get(
        client, {'display_name': data['ippool']['name']})
    if ippool is None:
        return
    ippool_allocations = nsx_ippool.get_allocations(client, ippool)
    logger.info("Number of IP pool allocations to be deleted: %s" %
                len(ippool_allocations))
    allocated_ips = [allocation['allocation_id']
                     for allocation in ippool_allocations]
    if data['dry_run']:
        return
    for allocation in ippool_allocations:
        # nsx_ippool.delete_allocation(
        #     client, ippool, allocation['allocation_id'])
        logger.info("IP pool allocation: %s is deleted" %
                    allocation['allocation_id'])
    return allocated_ips


def get_ncp_objects(object_list, cluster=None):
    ncp_objects = [obj for obj in object_list
                   if has_tag(obj, {'scope': 'ncp/cluster', 'tag': cluster})]
    return ncp_objects


def cleanup(client, data):
    _cleanup_dfw_sections(client, data)
    _cleanup_ns_groups(client, data)
    _cleanup_ip_sets(client, data)
    _cleanup_lb_services(client, data)
    _cleanup_lb_virtual_servers(client, data)
    _cleanup_lb_rules(client, data)
    _cleanup_lb_pools(client, data)
    _cleanup_lrp(client, data)
    _cleanup_lp(client, data)
    _cleanup_t1lr(client, data)
    _cleanup_logicalswitch(client, data)
    _cleanup_ippool(client, data)
    _cleanup_ipblock_allocation(client, data)
    allocated_ips = _cleanup_ippool_allocation(client, data)
    _cleanup_t0_snat(client, data, allocated_ips)


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
    elif action == 'cleanup':
        return cleanup(client, data)
