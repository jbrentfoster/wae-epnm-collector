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
import requests
from collectioncode import utils
import os
from os import path

# Setting up the properties file
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'


def get_all_nodes(baseURL, cienauser, cienapassw, token):
    logging.debug('Retrieve all network elements..')
    incomplete = True
    jsonmerged = {}
    # uri = '/nsi/api/v6/networkConstructs?limit=50'
    uri = '/nsi/api/search/networkConstructs?include=expectations%2CphysicalLocation&limit=50&networkConstructType=networkElement%2Cmanual&offset=0&resourcePartitionInfo=&resourceType=6500&searchText=&sortBy=data.attributes.displayData.displayName'
    # uri = '/nsi/api/search/networkConstructs?include=expectations%2CphysicalLocation&limit=50&networkConstructType=networkElement%2Cmanual&offset=0'
    URL = baseURL + uri
    while incomplete:
        jsonresponse = utils.rest_get_json(URL, cienauser, cienapassw, token)
        try:
            jsonaddition = json.loads(jsonresponse)
        except ValueError:
            if 'HTTP status code: 401' in jsonresponse:
                logging.debug("get all nodes API returned Unauthozied error: Retrying with new token")
                tokenString = getToken(baseURL, cienauser, cienapassw)
                jsonresponse = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
                try:
                    jsonaddition = json.loads(jsonresponse)
                except ValueError:
                    logging.debug("get all nodes API returned Unauthozied error with new token")
            elif 'HTTP status code: 500' in jsonresponse:
                logging.debug("get all nodes  API returned 500 Internal server server error")
                incomplete = False
            else:
                logging.debug("get all nodes API didn't return the valid JSON response")
                incomplete = False

        try:
            next = ''
            if jsonaddition.get('links'):
                next = jsonaddition.get('links').get('next')
        except Exception:
            logging.info("No data found")
        if next:
            URL = next
            utils.merge(jsonmerged, jsonaddition)
        else:
            incomplete = False
            utils.merge(jsonmerged, jsonaddition)

    # Saving the all nodes data
    with open('jsonfiles/all_nodes.json', 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True,
                           indent=4, separators=(',', ': ')))
        f.close()


def get_Sites(baseURL, cienauser, cienapassw, token_string):
    logging.debug('Retrieve Sites data for all nodes..')
    allNodes = utils.open_file_load_data('jsonfiles/all_nodes.json')
    nodesData = allNodes['data']
    site_list, dupl_check, counter = [], {}, 1

    for node in nodesData:
        # Making sure no duplicates are in sites file
        if node['attributes']['name'] in dupl_check:
            continue
        obj = {
            "name": "",
            "latitude": 0,
            "longitude": 0,
            "id": ""
        }
        if 'geoLocation' in node['attributes']:
            obj['longitude'] = node.get('attributes').get(
                'geoLocation').get('longitude') or 0
            obj['latitude'] = node.get('attributes').get(
                'geoLocation').get('latitude') or 0
        if 'siteId' in node['attributes']:
            obj['id'] = node['attributes']['siteId']

        if 'siteName' in node['attributes'] and node['attributes']['siteName'] != '':
            obj['name'] = utils.normalize_sites(
                '{}'.format(node['attributes']['siteName']))
        elif obj['longitude'] != 0 and obj['longitude'] != 0:
            obj['name'] = utils.normalize_sites(
                '{}[{}]'.format(name, counter))
            counter += 1
        else:
            obj['name'] = utils.normalize_sites(
                '{}'.format(sitename_bucket))

        # Making the duplicate check valid
        dupl_check[node['attributes']['name']] = 'Random_string'
        site_list.append(obj)

    site_list = json.dumps(site_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    with open('jsonfiles/sites.json', 'wb') as f:
        f.write(site_list)
        f.close()
    logging.debug('Sites population completed..')


def get_ports(baseURL, cienauser, cienapassw, token, state_or_states_list):
    logging.debug('Retrieve ports/TPE data for nodes for states..')
    nodesData = utils.getStateNodes(state_or_states_list)
    # nodesData = utils.getNodes()
    for k in nodesData.keys():
        networkConstrId = k
        incomplete = True
        jsonmerged, jsonaddition = {}, {}
        # uri = '/nsi/api/search/tpes?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&content=detail&limit=2000&include=tpePlanned%2C%20tpeDiscovered%2C%20concrete%2C%20networkConstructs%2C%20srlgs&networkConstruct.id={}'.format(networkConstrId)
        uri = '/nsi/api/search/tpes?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&content=detail&limit=2000&include=tpePlanned%2C%20tpeDiscovered%2C%20concrete%2C%20networkConstructs%2C%20srlgs&networkConstruct.id='
        # uri = '/nsi/api/search/tpes?fields=data.attributes&offset=0&limit=100&content=detail&resourceState=planned,discovered,plannedAndDiscovered&networkConstruct.id={}'.format(networkConstrId)
        URL = baseURL + uri + networkConstrId
        while incomplete:
            portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
            try:
                jsonaddition = json.loads(portData)
            except ValueError:
                if 'HTTP status code: 401' in portData:
                    logging.debug("get TPE's API returned Unauthozied error: Retrying with new token for network construct id : {}".format(networkConstrId))
                    tokenString = getToken(baseURL, cienauser, cienapassw)
                    portData = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
                    try:
                        jsonaddition = json.loads(portData)
                    except ValueError:
                        logging.debug("get TPE's API returned Unauthozied error with new token for network construct id : {}".format(networkConstrId))
                elif 'HTTP status code: 500' in portData:
                    logging.debug("get TPE's API returned 500 Internal Server Error for network construct id : {}".format(networkConstrId))
                    incomplete = False
                else:
                    logging.debug("get TPE's API didn't return the valid JSON response for network construct id : {}".format(networkConstrId))
                    incomplete = False

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
                    utils.merge(jsonmerged, jsonaddition)
                else:
                    incomplete = False
                    utils.merge(jsonmerged, jsonaddition)

        # Saving ports / tpe data to json file for all network id's
        if jsonmerged:
            filename = "tpe_"+networkConstrId+'.json'
            with open('jsongets/'+filename, 'wb') as f:
                f.write(json.dumps(jsonmerged, f, sort_keys=True,
                                indent=4, separators=(',', ': ')))
                f.close()
            logging.info('TPE data retrieved..')

################### Original Code ############################
# def get_links(baseURL, cienauser, cienapassw, token, state_or_states_list):
#     nodesData = utils.getStateNodes(state_or_states_list)
#     # nodesData = utils.getNodes()
#     for k in nodesData.keys():
#         networkConstrId = k
#         logging.debug('networkConstrId:\n{}'.format(networkConstrId))
#         incomplete = True
#         jsonmerged, jsonaddition = {}, {}
#         # ONlY ETHERNET and IP
#         # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=ETHERNET&serviceClass=IP&limit=1000&networkConstruct.id={}'.format(networkConstrId)
#         # Retrive data for ETHERNET and MPLS
#         uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&layerRate=MPLS%2CETHERNET&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=IP%2CTunnel&sortBy=name&limit=1000&networkConstruct.id={}'.format(
#             networkConstrId)
#         # uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&sortBy=name&networkConstruct.id={}'.format(networkConstrId)
#         # ########uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&limit=200&networkConstruct.id={}'.format(networkConstrId)
#         URL = baseURL + uri
#         logging.debug('URL:\n{}'.format(URL))
#         while incomplete:
#             portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
#             try:
#                 jsonaddition = json.loads(portData)
#             except ValueError:
#                 if 'HTTP status code: 401' in portData:
#                     logging.debug("get FRE's API returned Unauthozied error: Retrying with new token for network construct id : {}".format(networkConstrId))
#                     tokenString = getToken(baseURL, cienauser, cienapassw)
#                     portData = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
#                     try:
#                         jsonaddition = json.loads(portData)
#                     except ValueError:
#                         logging.debug("get FRE's API returned Unauthozied error with new token for network construct id : {}".format(networkConstrId))
#                 elif 'HTTP status code: 500' in portData:
#                     logging.debug("get FRE's API returned 500 Intrenal Server error for network construct id : {}".format(networkConstrId))
#                     incomplete = False
#                 else:
#                     logging.debug("get FRE's API didn't return the valid JSON response for network construct id : {}".format(networkConstrId))
#                     incomplete = False

#             # logging.debug('The API response for URL {} is:\n{}'.format(URL))
#             if jsonaddition:
#                 try:
#                     next = ''
#                     if jsonaddition.get('links'):
#                         next = jsonaddition.get('links').get('next')
#                 except Exception:
#                     logging.info("No data found")
#                 if next:
#                     URL = next
#                     utils.merge(jsonmerged, jsonaddition)
#                 else:
#                     incomplete = False
#                     utils.merge(jsonmerged, jsonaddition)

#         # saving fre data for each network construct id for L3
#         if jsonmerged:
#             filename = "fre_"+networkConstrId
#             with open('jsongets/'+filename+'.json', 'wb') as f:
#                 f.write(json.dumps(jsonmerged, f, sort_keys=True,
#                                 indent=4, separators=(',', ': ')))
#                 f.close()
#             logging.info('FRE data retrieved..')

def get_links(baseURL, cienauser, cienapassw, token, state_or_states_list):
    nodesData = utils.getStateNodes(state_or_states_list)
    # nodesData = utils.getNodes()
    for k in nodesData.keys():
        networkConstrId = k
        logging.debug('networkConstrId:\n{}'.format(networkConstrId))
        incomplete = True
        jsonmerged, jsonaddition = {}, {}
        # ONlY ETHERNET and IP
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=ETHERNET&serviceClass=IP&limit=1000&networkConstruct.id={}'.format(networkConstrId)
        # Retrive data for ETHERNET and MPLS
        uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&layerRate=MPLS%2CETHERNET&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=IP%2CTunnel&sortBy=name&limit=1000&networkConstruct.id={}'.format(
            networkConstrId)
        # uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&sortBy=name&networkConstruct.id={}'.format(networkConstrId)
        # ########uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&limit=200&networkConstruct.id={}'.format(networkConstrId)
        URL = baseURL + uri
        logging.debug('URL:\n{}'.format(URL))
        while incomplete:
            portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
            try:
                jsonaddition = json.loads(portData)
            except ValueError:
                if 'HTTP status code: 401' in portData:
                    logging.debug("get FRE's API returned Unauthozied error: Retrying with new token for network construct id : {}".format(networkConstrId))
                    tokenString = getToken(baseURL, cienauser, cienapassw)
                    portData = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
                    try:
                        jsonaddition = json.loads(portData)
                    except ValueError:
                        logging.debug("get FRE's API returned Unauthozied error with new token for network construct id : {}".format(networkConstrId))
                elif 'HTTP status code: 500' in portData:
                    logging.debug("get FRE's API returned 500 Intrenal Server error for network construct id : {}".format(networkConstrId))
                    incomplete = False
                else:
                    logging.debug("get FRE's API didn't return the valid JSON response for network construct id : {}".format(networkConstrId))
                    incomplete = False

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
                    utils.merge(jsonmerged, jsonaddition)
                else:
                    incomplete = False
                    utils.merge(jsonmerged, jsonaddition)

        # # saving fre data for each network construct id for L3
        # if jsonmerged:
        #     filename = "fre_"+networkConstrId
        #     with open('jsongets/'+filename+'.json', 'wb') as f:
        #         f.write(json.dumps(jsonmerged, f, sort_keys=True,
        #                         indent=4, separators=(',', ': ')))
        #         f.close()
        #     logging.info('FRE data retrieved..')

        #### return response
        return jsonmerged


def get_supporting_nodes(circuit_id, filename, baseURL, cienauser, cienapassw, token):
    # Make the api call to get the supporting node info
    # logging.info('Retrieve Supporting nodes..')
    data, incomplete, jsonmerged, jsonaddition= {}, True, {}, {}
    fileName = 'jsongets/l1_circuit_'+circuit_id+'.json'
    logging.debug('File name is ..'+fileName)
    # uri = '/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&networkConstruct.id=&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportingFreId={}'.format(
    #     circuit_id)
    logging.debug('Token received at Supporting nodes API ..'+token)
    if token:
        #Update query to get data from non versioned API
        uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=500&networkConstruct.id=&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportingFreId={}'.format(
            circuit_id.strip())
        URL = baseURL + uri
        logging.debug('Token sending to supporting nodes..'+token)
        while incomplete:
            ###### Original code
            jsondata = utils.rest_get_json(URL, cienauser, cienapassw, token)
            # jsonaddition = json.loads(jsondata)
            try:
                jsonaddition = json.loads(jsondata)
            except ValueError:
                if 'HTTP status code: 401' in jsondata:
                    logging.debug("Supporting nodes API returned Unauthozied error: Retrying with new token for circuit id {}".format(circuit_id))
                    tokenString = getToken(baseURL, cienauser, cienapassw)
                    jsondata = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
                    try:
                        jsonaddition = json.loads(jsondata)
                    except ValueError:
                        logging.debug("Supporting nodes API returned error for circuit id {} http error {}".format(circuit_id,jsondata))
                elif 'HTTP status code: 500' in jsondata:
                    logging.debug("Supporting nodes API returned 500 Internal server server error for circuit id {}".format(circuit_id))
                    incomplete = False
                else:
                    logging.debug("Supporting nodes API didn't return the valid JSON response for network construct id : {}".format(networkConstrId))
                    incomplete = False
  
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
                    utils.merge(jsonmerged, jsonaddition)
                else:
                    incomplete = False
                    utils.merge(jsonmerged, jsonaddition)

        # save data for each circuit id 
        with open(fileName, 'wb') as f:
            f.write(json.dumps(jsonmerged, f, sort_keys=True,
                                indent=4, separators=(',', ': ')))
            f.close()
        logging.info('L1 Circuits hops data retrieved and saved..')
    hopdata = []
    included = {}    
    if path.exists(fileName):
        data = utils.open_file_load_data(fileName)
        if data:
            if 'included' in data:
                included = data['included']
            if included:
                for i in range(len(included)):
                    if included[i]['type'] == 'endPoints' and included[i]['id'][-1] != '2':
                        if included[i].get('relationships') and included[i+1].get('relationships') and included[i].get('relationships').get('tpes') and included[i+1].get('relationships').get('tpes'):
                            temp = {}
                            temp['nodeA'] = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                            temp['nodeB'] = included[i +
                                                    1]['relationships']['tpes']['data'][0]['id'][:36]
                            hopdata.append(temp)
                    logging.info('Supporting Nodes data retrieved ..')
            else:
                logging.debug(" No INCLUDED Data returned for L1 supporting nodes for circuit id:{} ".format(circuit_id))
        else:
            logging.debug(" No Data returned for L1 supporting nodes for circuit id:{} ".format(circuit_id))
    # Return the hop nodes for each L1 circuits
    return hopdata

def getToken(baseURL, cienauser, cienapassw):
    token = None
    tokenPath = '/tron/api/v1/tokens'
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/json'
    headers = {'Content-type': appformat, 'Accept': appformat}
    data = {'username': cienauser, 'password': cienapassw}
    resttokenURI = baseURL + tokenPath
    try:
        r = requests.post(resttokenURI, proxies=proxies,
                            headers=headers, json=data, verify=False)
        if r.status_code == 201:
            token = json.dumps(r.json(), indent=2)
            # print token
        else:
            r.raise_for_status()

    except requests.exceptions.RequestException as err:
        print "Exception raised: " + str(err)
        return
    token = json.loads(token)
    token_string = token['token']
    return token_string

def get_l1_nodes(state_or_states_list):
    l1_collect.get_l1_nodes(state_or_states_list)


def get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list):
    l1_collect.get_l1_links_data(baseURL, cienauser, cienapassw,
                            token, state_or_states_list)

def get_l1_links(baseURL, cienauser, cienapassw, token, state_or_states_list):
    l1_collect.get_l1_links(baseURL, cienauser, cienapassw,
                            token, state_or_states_list)


def get_l1_circuits(baseURL, cienauser, cienapassw, token):
    l1_collect.get_l1_circuits(baseURL, cienauser, cienapassw, token)


def get_l3_nodes(state_or_states_list):
    l3_collect.get_l3_nodes(state_or_states_list)


def get_l3_links(baseURL, cienauser, cienapassw, token):
    l3_collect.get_l3_links(baseURL, cienauser, cienapassw, token)
