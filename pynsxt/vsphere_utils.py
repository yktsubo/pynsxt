#!/usr/bin/env python

from logging import basicConfig, getLogger, DEBUG
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
import sys
import atexit
import pynsxt_utils

logger = getLogger(__name__)


def list_vm(args):
    config = pynsxt_utils.load_configfile(args)
    si = _connect_si(config)
    content = si.RetrieveContent()
    children = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True).view
    vms = [(child.name, child._moId, child.runtime.host.name, child.guest.guestState)
           for child in children]
    for vm in vms:
        print vm
    return children


def delete_vm(args):
    config = pynsxt_utils.load_configfile(args)
    si = _connect_si(config)
    content = si.RetrieveContent()
    children = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True).view
    targets = [child for child in children if child._moId == args.target_vm]
    if len(targets) != 1:
        logger.error("No target VM")
        sys.exit(2)
    else:
        target = targets[0]
        target_name = target.name
        logger.info("Deleting %s" % target_name)
        if target.guest.guestState == 'running':
            tasks = [target.PowerOff()]
            logger.info('Power off ' + target_name)
            _wait_for_task(tasks, si)
        tasks = [target.Destroy_Task()]
        logger.info('Destroy ' + target_name)
        _wait_for_task(tasks, si)
    logger.info("Successfully deleted %s" % target_name)
    pass


def _connect_si(config):
    vcenter_host = config['vcenter']['ip']
    vcenter_username = config['vcenter']['user']
    vcenter_password = config['vcenter']['password']
    if config['vcenter'].has_key('port'):
        vcenter_port = int(config['vcenter']['port'])
    else:
        vcenter_port = int(443)

    try:
        si = SmartConnectNoSSL(
            host=vcenter_host, user=vcenter_username, pwd=vcenter_password, port=vcenter_port)
        atexit.register(Disconnect, si)
    except IOError as e:
        pass
    if not si:
        raise SystemExit("Unable to connect to host with supplied info.")
    return si


def _wait_for_task(tasks, si):
    """
    Given the service instance si and tasks, it returns after all the
    tasks are complete
    """

    pc = si.content.propertyCollector

    taskList = [str(task) for task in tasks]

    # Create filter
    objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                for task in tasks]
    propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                          pathSet=[], all=True)
    filterSpec = vmodl.query.PropertyCollector.FilterSpec()
    filterSpec.objectSet = objSpecs
    filterSpec.propSet = [propSpec]
    filter = pc.CreateFilter(filterSpec, True)

    try:
        version, state = None, None

        # Loop looking for updates till the state moves to a completed state.
        while len(taskList):
            update = pc.WaitForUpdates(version)
            for filterSet in update.filterSet:
                for objSet in filterSet.objectSet:
                    task = objSet.obj
                    for change in objSet.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        if not str(task) in taskList:
                            continue

                        if state == vim.TaskInfo.State.success:
                            # Remove task from taskList
                            taskList.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # Move to next version
            version = update.version
    finally:
        if filter:
            filter.Destroy()


def construct_parser(subparsers):
    vsphere_parser = subparsers.add_parser('vsphere', description="Functions for vSphere API",
                                           help="Functions for vSphere API")
    vsphere_subparsers = vsphere_parser.add_subparsers()
    vsphere_listvm_parser = vsphere_subparsers.add_parser(
        'list_vm', help='List VM')
    vsphere_listvm_parser.set_defaults(func=list_vm)

    vsphere_deletevm_parser = vsphere_subparsers.add_parser(
        'delete_vm', help='Delete VM')
    vsphere_deletevm_parser.add_argument("-t",
                                         "--target_vm",
                                         help="Target VM moId")
    vsphere_deletevm_parser.set_defaults(func=delete_vm)
