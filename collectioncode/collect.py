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
    logging.debug('Retrieve all network elements..')
    incomplete = True
    jsonmerged = {}
    # uri = '/nsi/api/v6/networkConstructs?limit=50'
    uri = '/nsi/api/search/networkConstructs?include=expectations%2CphysicalLocation&limit=50&networkConstructType=networkElement%2Cmanual&offset=0'
    URL = baseURL + uri
    while incomplete:        
        jsonresponse = utils.rest_get_json(URL, cienauser, cienapassw, token)
        jsonaddition = json.loads(jsonresponse)
        try:
            next = ''
            if jsonaddition.get('links'):
                next = jsonaddition.get('links').get('next')
        except Exception:
            logging.info("No data found")
        if next:
            URL = next
            merge(jsonmerged,jsonaddition)
        else:
            incomplete = False
            merge(jsonmerged,jsonaddition)

    # Saving the data for future use
    with open('jsonfiles/all_nodes.json', 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        # f.write(data)

def merge(a, b):
    "merges b into a"
    for key in b:
        if key in a:  # if key is in both a and b
            if isinstance(a[key], dict) and isinstance(b[key], dict):  # if the key is dict Object
                merge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key] = a[key] + b[key]
        else:  # if the key is not in dict a , add it to dict a
            a.update({key: b[key]})
    return a

def get_ports(baseURL, cienauser, cienapassw, token):
    logging.debug('Retrieve TPE data for nodes..')
    allNodes= utils.open_file_load_data("jsonfiles/all_nodes.json")
    nodesData = allNodes['data']
    for node in nodesData:
        networkConstrId = node['id']
        incomplete = True
        jsonmerged = {}
        uri = '/nsi/api/search/tpes?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&content=detail&limit=2000&include=tpePlanned%2C%20tpeDiscovered%2C%20concrete%2C%20networkConstructs%2C%20srlgs&networkConstruct.id={}'.format(networkConstrId)

        # uri = '/nsi/api/search/tpes?fields=data.attributes&offset=0&limit=100&content=detail&resourceState=planned,discovered,plannedAndDiscovered&networkConstruct.id={}'.format(networkConstrId)
        URL = baseURL + uri
        while incomplete:
            portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
            jsonaddition = json.loads(portData)
            # logging.debug('The API response for URL {} is:\n{}'.format(URL))
            if jsonaddition:
                try:
                    next = ''
                    if jsonaddition.get('links'):
                        next = jsonaddition.get('links').get('next')
                except Exception:
                    logging.info("No data found")
                if next:
                    URL = next
                    merge(jsonmerged,jsonaddition)
                else:
                    incomplete = False
                    merge(jsonmerged,jsonaddition)

        # Inserting this line for testing since the response is too large to print it
        filename = "tpe_"+networkConstrId
        with open('jsongets/'+filename+'.json', 'wb') as f:
            f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
            f.close()
        logging.info('TPE data retrieved..')

def get_links(baseURL, cienauser, cienapassw, token):
    allNodes= utils.open_file_load_data("jsonfiles/all_nodes.json")
    nodesData = allNodes['data']
    logging.debug('Retrieve FRE data for nodes:')
    for node in nodesData:
        networkConstrId = node['id']
        logging.debug('networkConstrId:\n{}'.format(networkConstrId))
        incomplete = True
        jsonmerged = {}
        ## ONlY ETHERNET and IP
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=ETHERNET&serviceClass=IP&limit=1000&networkConstruct.id={}'.format(networkConstrId)
        ## ETHERNET and MPLS
        uri = '/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&layerRate=MPLS%2CETHERNET&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=IP%2CTunnel&sortBy=name&limit=1000&networkConstruct.id={}'.format(networkConstrId)
        # uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&sortBy=name&networkConstruct.id={}'.format(networkConstrId)
        # ########uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&limit=200&networkConstruct.id={}'.format(networkConstrId)
        URL = baseURL + uri
        logging.debug('URL:\n{}'.format(URL))
        while incomplete:
            portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
            jsonaddition = json.loads(portData)
            # logging.debug('The API response for URL {} is:\n{}'.format(URL))
            if jsonaddition:
                try:
                    next = ''
                    if jsonaddition.get('links'):
                        next = jsonaddition.get('links').get('next')
                except Exception:
                    logging.info("No data found")
                if next:
                    URL = next
                    merge(jsonmerged,jsonaddition)
                else:
                    incomplete = False
                    merge(jsonmerged,jsonaddition)

        # Write data for each network construct id
        filename = "fre_"+networkConstrId
        with open('jsongets/'+filename+'.json', 'wb') as f:
            f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
            f.close()
        logging.info('FRE data retrieved..')
        
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



def get_supporting_nodes(circuit_id, baseURL, cienauser, cienapassw, token):
    # Make the api call to get the supporting node info
    logging.info('Retrieve Supporting nodes..')
    uri = '/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&networkConstruct.id=&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportingFreId={}'.format(
        circuit_id)
    URL = baseURL + uri
    data = utils.rest_get_json(URL, cienauser, cienapassw, token)
    data = json.loads(data)
    ret = []

    if "included" in data:
        included = data['included']
        for i in range(len(included)):
            if included[i]['type'] == 'endPoints' and included[i]['id'][-1] != '2':
                if included[i].get('relationships') and included[i+1].get('relationships') and included[i].get('relationships').get('tpes') and included[i+1].get('relationships').get('tpes'):
                    temp = {}
                    temp['Name'] = included[i]['id'][:-2]
                    temp['NodeA'] = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                    temp['NodeB'] = included[i +
                                            1]['relationships']['tpes']['data'][0]['id'][:36]
                    ret.append(temp)
    # Return the network construct id's for the next hop nodes
    return ret
