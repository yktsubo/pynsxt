#!/usr/bin/env python

from logging import basicConfig, getLogger, DEBUG
from pynsxt_utils import connect_cli

logger = getLogger(__name__)


def get_thumbprint(config):
    thumbprint = ''
    logger.info('Get API Thumbprint')
    cli = connect_cli(config['nsxManager'])
    stdin, stdout, stderr = cli.exec_command('get certificate api thumbprint')
    for line in stdout:
        if len(line.strip()) == 0:
            continue
        else:
            thumbprint = line.strip()
            print("Thumbprint: %s" % thumbprint)
    return thumbprint
