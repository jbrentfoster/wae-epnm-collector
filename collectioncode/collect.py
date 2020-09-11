import time
import re
import json
import logging
import sys
from multiprocessing.dummy import Pool as ThreadPool
import traceback
import configparser
import l1_collect
import l3_collect
from collectioncode import utils


def get_all_nodes(baseURL, cienauser, cienapassw, token):
    uri = '/nsi/api/v6/networkConstructs?limit=300'
    URL = baseURL + uri
    data = utils.rest_get_json(URL, cienauser, cienapassw, token)
    # Saving the data for future use
    with open('jsonfiles/all_nodes.json', 'wb') as f:
        f.write(data)


def get_l1_nodes():
    l1_collect.get_l1_nodes()


def get_l1_links(baseURL, cienauser, cienapassw, token):
    l1_collect.get_l1_links(baseURL, cienauser, cienapassw, token)


def get_l1_circuits(baseURL, cienauser, cienapassw, token):
    l1_collect.get_l1_circuits(baseURL, cienauser, cienapassw, token)


def get_l3_nodes():
    l3_collect.get_l3_nodes()


def get_l3_links(baseURL, cienauser, cienapassw, token):
    l3_collect.get_l3_links(baseURL, cienauser, cienapassw, token)


def get_l3_circuits(baseURL, cienauser, cienapassw, token):
    l3_collect.get_l3_circuits(baseURL, cienauser, cienapassw, token)


def get_supporting_nodes(circuit_id, baseURL, cienauser, cienapassw, token):
    # Make the api call to get the supporting node info
    uri = '/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&networkConstruct.id=&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportingFreId={}'.format(
        circuit_id)
    URL = baseURL + uri
    data = utils.rest_get_json(URL, cienauser, cienapassw, token)
    data = json.loads(data)
    # Saving the data for future use
    logging.debug(
        'Got the supporting node for {}:\n{}'.format(circuit_id, data))
    ret = []

    if "included" in data:
        included = data['included']
        for i in range(len(included)):
            if included[i]['type'] == 'endPoints' and included[i]['id'][-1] != '2':
                temp = {}
                temp['Name'] = included[i]['id'][:-2]
                temp['NodeA'] = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                temp['NodeB'] = included[i +
                                         1]['relationships']['tpes']['data'][0]['id'][:36]
                ret.append(temp)
    # Return the network construct id's for the next hop nodes
    return ret
