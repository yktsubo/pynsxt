#!/usr/bin/env python

import argparse
import time
import nsx_manager
import nsx_controller
import nsx_edge
import nsx_tz
import nsx_t0lr
import nsx_t1lr
import nsx_ippool
import nsx_ipblock
import nsx_dfw_section
import nsx_logicalswitch
import pynsxt_utils
from pprint import pprint
from logging import basicConfig, getLogger, StreamHandler, DEBUG, INFO

# For lab


logger = getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='NSX-T Swagger wrapper')
    parser.add_argument('-c',
                        '--config-file',
                        required=True,
                        help='nsxt configuration file')

    parser.add_argument('--spec-validation',
                        default=False,
                        action='store_true',
                        help='Enable spec validation')

    parser.add_argument('-d',
                        '--debug',
                        default=False,
                        action='store_true',
                        help='print low level debug of http transactions')
    parser.set_defaults(func=_run)
    return parser.parse_args()


def _run(args):
    module_selector = {
        'Manager': nsx_manager,
        'Controller': nsx_controller,
        'Edge': nsx_edge,
        'TransportZone': nsx_tz,
        'T0': nsx_t0lr,
        'T1': nsx_t1lr,
        'IPPool': nsx_ippool,
        'IPBlock': nsx_ipblock,
        'DFWSection': nsx_dfw_section,
        'LogicalSwitch': nsx_logicalswitch
    }

    config = pynsxt_utils.load_configfile(args)
    client = pynsxt_utils.get_api_client(
        config['env'], validation=args.spec_validation)

    for t in config['tasks']:
        if not ('module' in t.keys() and 'action' in t.keys()):
            logger.error('This task is ignored.')
            continue

        if 'data' in t.keys():
            data = t['data']
        else:
            data = {}
        logger.info("%s:%s action:%s" %
                    (t['module'], t['data']['display_name'], t['action']))
        response = module_selector[t['module']].run(client, t['action'], data)
        time.sleep(1)


def main():
    args = get_args()
    if args.debug:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)
    handler = StreamHandler()
    logger.addHandler(handler)
    args.func(args)


if __name__ == '__main__':
    main()
