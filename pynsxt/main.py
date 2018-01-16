#!/usr/bin/env python

import argparse
from logging import basicConfig, getLogger, StreamHandler, DEBUG, INFO

import nsx_manager
import nsx_controller
import nsx_edge
import nsx_fabric
import nsx_transport
import nsx_poolmanagement
import pynsxt_utils
import vsphere_utils


logger = getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='PyNSXT')
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

    subparsers = parser.add_subparsers()
    nsx_manager.construct_parser(subparsers)
    nsx_controller.construct_parser(subparsers)
    nsx_edge.construct_parser(subparsers)
    nsx_fabric.construct_parser(subparsers)
    nsx_transport.construct_parser(subparsers)
    nsx_poolmanagement.construct_parser(subparsers)
    vsphere_utils.construct_parser(subparsers)
    return parser.parse_args()


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
