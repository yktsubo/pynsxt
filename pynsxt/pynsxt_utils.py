import yaml
import json
import paramiko
import requests
import ssl
import socket
import hashlib
import os
import pickle
import time
from pprint import pprint
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient

PYNSXTOBJFILE = '.pynsxt'
SPEC_PATH = "/tmp/nsx_api.json"


def load_configfile(args):
    with open(args.config_file, 'r') as f:
        config = yaml.load(f)
    return config


def connect_cli(config):
    if config.has_key('cli'):
        return config['cli']
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(config['ip'], username=config['user'],
                password=config['password'], port=22, timeout=15.0, look_for_keys=False)
    config['cli'] = ssh
    return ssh


def exec_command(cli, cmd, display=False):
    output = ""
    if display:
        print("# %s" % cmd)
    stdin, stdout, stderr = cli.exec_command(cmd)
    for line in stdout:
        output += line
    if display:
        print(output)
    return output


def load_spec(manager):
    raw_spec = requests.get("https://%s/api/v1/spec/openapi/nsx_api.json" %
                            manager['ip'], auth=(manager['user'], manager['password']), verify=False).json()


def api_request(args, method, uri, data=""):
    config = load_configfile(args)
    uri = "https://%s/" % config['nsxManager']['ip'] + uri
    # headers = {'Content-Type': 'application/json'}
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json'}
    auth = (config['nsxManager']['user'], config['nsxManager']['password'])
    if method == 'get':
        res = requests.get(uri, auth=auth, headers=headers, verify=False)
    elif method == 'post':
        res = requests.post(uri, auth=auth, headers=headers,
                            data=data, verify=False)
    elif method == 'delete':
        res = requests.delete(uri, auth=auth, headers=headers,
                              data=data, verify=False)
    return (res.status_code, res.json())


def get_api_client(config, validation=False):
    if config.has_key('client'):
        return config['client']
    raw_spec = json.load(open(SPEC_PATH))
    raw_spec['host'] = config['nsxManager']['ip']
    http_client = RequestsClient()
    http_client.session.verify = False
    http_client.set_basic_auth(
        config['nsxManager']['ip'], config['nsxManager']['user'], config['nsxManager']['password'])
    config = {
        'also_return_response': True,
        'validate_swagger_spec': validation,
        'validate_responses': False,
        'validate_requests': False,
        'use_models': False
    }
    client = SwaggerClient.from_spec(
        raw_spec, http_client=http_client, config=config)
    config['client'] = client
    return client


def get_thumbprint(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    wrappedSocket = ssl.wrap_socket(sock)

    try:
        wrappedSocket.connect((ip, 443))
    except:
        response = False
    else:
        der_cert_bin = wrappedSocket.getpeercert(True)
        pem_cert = ssl.DER_cert_to_PEM_cert(wrappedSocket.getpeercert(True))
        # Thumbprint
        thumb_sha256 = hashlib.sha256(der_cert_bin).hexdigest()
        wrappedSocket.close()
        return ':'.join(map(''.join, zip(*[iter(thumb_sha256)] * 2)))


def convert_to_dict(model):
    try:
        model = model.__dict__['_Model__dict']
        for k, v in model.items():
            model[k] = convert_to_dict(v)
    except AttributeError:
        if isinstance(model, dict):
            for k, v in model.items():
                model[k] = convert_to_dict(v)
        if isinstance(model, list):
            for i, v in enumerate(model):
                model[i] = convert_to_dict(v)
    return model


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
