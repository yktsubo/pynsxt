#!/usr/bin/env python

from logging import getLogger, StreamHandler, DEBUG, INFO, Formatter
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
import sys
import atexit

NAME = 'Yuki Tsuboi'
VERSION = '0.1'

# Set up for logging
logger = getLogger(__name__)

def connect_si(config):
    if not config.has_key('vcenter'):
        logger.error('No vcenter information in the config file')
        sys.exit(1)
    vcenter_host = config['vcenter']['ip']
    vcenter_username = config['vcenter']['user']
    vcenter_password = config['vcenter']['password']
    if config['vcenter'].has_key('port'):
        vcenter_port = int(config['vcenter']['port'])
    else:
        vcenter_port = int(443)

    try:
        si = SmartConnectNoSSL(host=vcenter_host, user=vcenter_username,pwd=vcenter_password,port=vcenter_port)
        atexit.register(Disconnect, si) 
    except IOError as e:
        pass
    if not si:
        raise SystemExit("Unable to connect to host with supplied info.")
    return si
 
def WaitForTasks(tasks, si):
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

