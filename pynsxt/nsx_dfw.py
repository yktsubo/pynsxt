from logging import basicConfig, getLogger, DEBUG
from pprint import pprint

logger = getLogger(__name__)

OBJECT = 'DFW'
MODULE = 'Services'


def get_list(client, sectionId=None):
    """
    """
    if not sectionId:
        request = client.__getattr__(MODULE).ListSections()
        response, _ = request.result()
        sections = response['results']
        for section in sections:
            if section['applied_tos'] and section['applied_tos'][0]['target_type'] == 'LogicalRouter':
                continue
            param = {'section-id': section['id']}
            request = client.__getattr__(MODULE).GetRules(**param)
            response, _ = request.result()
            rules = response['results']
            pprint(section['display_name'])
            for rule in rules:
                pprint(rule['action'])
                pprint(rule['direction'])
                pprint(rule['sources'])
                pprint(rule['destinations'])


def _get_id(client, data):
    if data.has_key('id'):
        return param['id']
    elif data.has_key('display_name'):
        objects = get_list(client)
        for obj in objects:
            if obj['display_name'] == data['display_name']:
                return obj['id']
    return None


def _create_ipblock(client, data):
    """
    """
    param = {'IpBlock': data}
    request = client.__getattr__(MODULE).CreateIpBlock(**param)
    try:
        response, _ = request.result()
    except:
        logger.error("Could not create " + OBJECT)
        return []
    return response


def _delete_ipblock(client, data):
    """
    """
    param = {'block-id': _get_id(client, data)}
    request = client.__getattr__(MODULE).DeleteIpBlock(**param)
    try:
        response = request.result()
    except:
        logger.error("Could not delete " + OBJECT)
        return []
    return response


def run(client, action, data, config=None):
    get_list(client)
    logger.info(OBJECT + ' ' + action)
    if action == 'create':
        return _create_ipblock(client, data)
    elif action == 'delete':
        return _delete_ipblock(client, data)
