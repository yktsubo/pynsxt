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
import base64
import urllib2
import uuid
from pprint import pprint
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
from requests.packages.urllib3.exceptions import InsecureRequestWarning


def load_configfile(args):
    with open(args.config_file, 'r') as f:
        config = yaml.load(f)
    return config


def connect_cli(config):
    if config.has_key('cli'):
        return config['cli']
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(config['ip'], username=config['username'],
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


def get_api_client(config, validation=False):
    if config.has_key('client'):
        return config['client']
    requests.packages.urllib3.disable_warnings(
        InsecureRequestWarning)  # Disable SSL warnings
    url = "https://%s/api/v1/spec/openapi/nsx_api.json" % config['nsxManager']['ip']
    base64string = base64.encodestring(('%s:%s' % (
        config['nsxManager']['username'], config['nsxManager']['password'])).encode("utf-8"))[:-1]
    headers = {
        "Authorization": "Basic %s" % base64string.decode("utf-8")
    }
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    req = urllib2.Request(url=url, headers=headers)
    response = urllib2.urlopen(req, context=context)
    raw_spec = json.loads(response.read())
    raw_spec['host'] = config['nsxManager']['ip']
    http_client = RequestsClient()
    http_client.session.verify = False
    http_client.set_basic_auth(
        config['nsxManager']['ip'], config['nsxManager']['username'], config['nsxManager']['password'])
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


def is_uuid(uuid):
    try:
        uuid.UUID(uuid)
    except:
        return False
    return True


def has_tag(obj, tag):
    if obj['tags']:
        matched_tag = [t for t in obj['tags'] if t['scope'] == tag['scope']]
        if len(matched_tag) == 1 and matched_tag[0]['tag'] == tag['tag']:
            return True
    return False


def add_or_update_tag(obj, tag):
    if not obj['tags']:
        obj['tags'] = []
    matched_tag = [t for t in obj['tags'] if t['scope'] == tag['scope']]
    if len(matched_tag) == 0:
        obj['tags'].append(tag)
    else:
        for t in obj['tags']:
            if t['scope'] == tag['scope']:
                t['tag'] = tag['tag']
    return obj
