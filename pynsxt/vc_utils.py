#!/usr/bin/env python

"""
Usage:
    ./DeleteVm.py -c <config-file> <vmname>
    ./DeleteVm.py -h | --help
    ./DeleteVm.py -v | --version

options:
    <vmname>              Target VM name
    -c <config-file>      Config file
    -h, --help            show this help message and exit
    -v, --version         show version
"""

from docopt import docopt
from logging import getLogger, StreamHandler, DEBUG
from pyVmomi import vim
import pyVmomiUtils
import yaml
import sys


NAME = 'Yuki Tsuboi'
VERSION = '0.1'

logger = getLogger(__name__)

def main(args):
    with open(args['-c'], 'r') as f:
        data = yaml.load(f)

    si = pyVmomiUtils.connect_si(data)
    content = si.RetrieveContent()
    children = content.viewManager.CreateContainerView(content.rootFolder,[vim.VirtualMachine],True).view
    targets = [child for child in children if child.name == args['<vmname>']]
    if len(targets) != 1:
        logger.error("No target VM or more than 1 VM are selected")
        sys.exit(2)
    else:
        target = targets[0]
        logger.debug("Target VM state is " + target.guest.guestState)
        if target.guest.guestState == 'running':
            tasks = [target.PowerOff()]
            logger.info('Power off ' + target.name)
            pyVmomiUtils.WaitForTasks(tasks, si)
        tasks = [target.Destroy_Task()]
        logger.info('Destroy ' + target.name)
        pyVmomiUtils.WaitForTasks(tasks, si)
    pass

if __name__ == "__main__":
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
    args = docopt(__doc__, version="{0} {1}".format(NAME, VERSION))
    main(args)
