#!/usr/bin/env python

import argparse
import subprocess
import requests
import time
import paramiko
import pynsxt_utils

from logging import basicConfig, getLogger, DEBUG

logger = getLogger(__name__)


def deploy_manager(args):
    logger.info('Deploy NSX manager')
    config = pynsxt_utils.load_configfile(args)
    # Create deploy command
    cmd = ["ovftool"]
    cmd.append("--name=%s" % config['nsxManager']['name'])
    cmd.append("--X:injectOvfEnv")
    cmd.append("--allowExtraConfig")
    cmd.append("--datastore=\"%s\"" % config['nsxManager']['datastore'])
    cmd.append("--network=\"%s\"" % config['nsxManager']['network'])
    cmd.append("--acceptAllEulas")
    cmd.append("--noSSLVerify")
    cmd.append("--diskMode=thin")
    cmd.append("--powerOn")
    cmd.append("--prop:nsx_role=nsx-manager")
    cmd.append("--prop:nsx_ip_0=%s" % config['nsxManager']['ip'])
    cmd.append("--prop:nsx_netmask_0=%s" % config['nsxManager']['netmask'])
    cmd.append("--prop:nsx_gateway_0=%s" % config['nsxManager']['gw'])
    cmd.append("--prop:nsx_dns1_0=%s" % config['dns'])
    cmd.append("--prop:nsx_domain_0=%s" % config['domain'])
    cmd.append("--prop:nsx_ntp_0=%s" % config['ntp'])
    cmd.append("--prop:nsx_isSSHEnabled=True")
    cmd.append("--prop:nsx_allowSSHRootLogin=True")
    cmd.append("--prop:nsx_passwd_0=%s" % config['nsxManager']['password'])
    cmd.append("--prop:nsx_cli_passwd_0=%s" % config['nsxManager']['password'])
    cmd.append("--prop:nsx_hostname=%s" % config['nsxManager']['name'])
    cmd.append(config['nsxManager']['ova'])
    cmd.append("vi://%s:%s@%s/%s/host/%s" % (config['vcenter']['user'], config['vcenter']
                                         ['password'], config['vcenter']['ip'], config['nsxManager']['datacenter'], config['nsxManager']['cluster']))

    logger.debug('Executing command: ' + " ".join(cmd))
    ret = subprocess.check_call(" ".join(cmd), shell=True)
    if ret != 0:
        logger.error('Failed to deploy')
        return

    logger.info('Deployed successfully and try to check Manager status')
    for i in range(0, 10):
        try:
            r = requests.get("https://%s" %
                             config['nsxManager']['ip'], verify=False)
            if r.status_code == 200:
                logger.info('Successfully booted')
                return
        except:
            logger.debug(
                'Wait that NSX manager is booted. Retry in 60 seconds')
            time.sleep(60)
    logger.error(
        'Checked NSX manager status 10 times but could not get good status')
    pass


def get_thumbprint(args):
    config = pynsxt_utils.load_configfile(args)
    _connect_manager_cli(config)
    thumbprint = ''
    logger.info('Get API Thumbprint')
    cli = _connect_manager_cli(config)
    stdin, stdout, stderr = cli.exec_command('get certificate api thumbprint')
    for line in stdout:
        if len(line.strip()) == 0:
            continue
        else:
            thumbprint = line.strip()
            print("Thumbprint: %s" % thumbprint)
    return thumbprint


def _connect_manager_cli(config):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(config['nsxManager']['ip'], username=config['nsxManager']['user'],
                password=config['nsxManager']['password'], port=22, timeout=15.0, look_for_keys=False)
    return ssh


def construct_parser(subparsers):
    manager_parser = subparsers.add_parser('manager', description="Functions for NSX manager",
                                           help="Functions for NSX manager")
    manager_subparsers = manager_parser.add_subparsers()
    manager_deploy_parser = manager_subparsers.add_parser(
        'deploy', help='Deploy NSX-T Manager')
    manager_deploy_parser.set_defaults(func=deploy_manager)

    manager_get_thumbprint_parser = manager_subparsers.add_parser(
        'get_thumbprint', help='Get thumbprint')
    manager_get_thumbprint_parser.set_defaults(func=get_thumbprint)
