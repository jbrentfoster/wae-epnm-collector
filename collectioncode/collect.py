import time
import re
import json
import logging
import sys
import traceback
import configparser
import l1_collect
import l3_collect
import utils
import threading
from multiprocessing.dummy import Pool as ThreadPool

'''
Here i'm implementing the collection router function

The logic is In the 'collect.py' file, if it's phase type l1_circuits then you run the following -->

All_node_collect()
L1node_collect()
L1link_collect()
L1circuit_collect()

If l1_links then -->

All_node_collect()
L1node_collect()
L1link_collect()

Etc. 

And the same for l3_circuits...

'''

thread_data = threading.local()

def collection_router(collection_call):
    global timeout_limit
    config = configparser.ConfigParser(interpolation=None)
    config.read('resources/config.ini')
    timeout = config['DEFAULT']['Timeout_limit']
    timeout_limit = float(timeout) * 3 if timeout.isnumeric() else None

    try:
        if collection_call['type'] == "all_nodes":
            logging.info("Collecting all nodes...")
            #Getting the all nodes log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect all nodes')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])

        if collection_call['type'] == "l1nodes":
            logging.info("Collecting l1 nodes...")
            #Getting the l1 nodes log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l1 nodes')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l1_nodes()

        if collection_call['type'] == "l1links":
            logging.info("Collecting l1 links...")
            #Getting the l1 links log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l1 links')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l1_nodes()
            get_l1_links(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])

        if collection_call['type'] == "l1circuits":
            logging.info("Collecting l1 circuits...")
            #Getting the l1 circuits log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l1 circuits')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l1_nodes()
            get_l1_links(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l1_circuits(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])

        if collection_call['type'] == "l3nodes":
            logging.info("Collecting l3 nodes...")
            #Getting the l3 nodes log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l3 nodes')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l3_nodes()

        if collection_call['type'] == "l3links":
            logging.info("Collecting l3 links...")
            #Getting the l3 links log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l3 links')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l3_nodes()
            get_l3_links(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])

        if collection_call['type'] == "l3circuits":
            logging.info("Collecting l3 circuits...")
            #Getting the l3 circuits log object
            global thread_data
            thread_data.logger = logging.getLogger(collection_call['type'])
            thread_data.logger.info('Starting to collect l3 circuits')
            get_all_nodes(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l3_nodes()
            get_l3_links(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])
            get_l3_circuits(collection_call['baseURL'], collection_call['cienauser'], collection_call['cienapassw'], collection_call['token'])

    except Exception:
        thread_data.logger.propagate = True
        thread_data.logger.debug('Exception: Setting the build_plan_check variable to False')                                         
        with open('configs/config.ini', 'rb') as f:
            data = f.readlines()

        with open('configs/config.ini', 'wb') as f:
            for line in data:
                if line.startswith('Build_plan'):
                    line = 'Build_plan_check = {}\n'.format(False)
                f.write(line)    
        thread_data.logger.exception('**********\n\nCaught an exception on thread: {}\n\n'.format(collection_call['type']))   
        raise

def get_all_nodes(baseURL, cienauser, cienapassw, token):
    uri = '/nsi/api/v6/networkConstructs?limit=300'
    URL = baseURL + uri
    thread_data.logger.info('Starting to collect all nodes')
    circuit_breaker1 = utils.Circuit_breaker()
    data = circuit_breaker1.request(URL, cienauser, cienapassw, token)
    #Saving the data for future use
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
    #Make the api call to get the supporting node info

    #New API to get the supporting nodes
    uri = "/nsi/api/v2/search/fres?include=networkConstructs&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&supportingFreId={}".format(circuit_id)

    URL = baseURL + uri
    circuit_breaker1 = utils.Circuit_breaker()
    data = circuit_breaker1.request(URL, cienauser, cienapassw, token)
    data = json.loads(data)
    #Saving the data for future use
    logging.debug('Got the supporting node for {}:\n{}'.format(circuit_id, data))
    thread_data.logger.info('Got the supporting node for {}:\n{}'.format(circuit_id, data))
    ret = []
    try:
        included = data['included']
        #Only putting in supporting nodes informaton. Stops at the 2nd to last object so that 'NodeB' can be the last object
        for i in range(len(included) - 1):
            if included[i]['type'] == 'networkConstructs':
                temp = {}
                temp['Name'] = included[i]['attributes']['displayData']['displayName']
                temp['NodeA'] = included[i]['id']
                temp['NodeB'] = included[i+1]['id']
                ret.append(temp)
    except:
        pass
    #Return the network construct id's for the next hop nodes
    return ret


if __name__ == '__main__':
    # get_l1_circuits()
    pass