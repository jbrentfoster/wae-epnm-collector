import time
import re
import json
import logging
import sys
from multiprocessing.dummy import Pool as ThreadPool
import traceback
import utils
import configparser
import collect
import os
from os import path

# Setting up the properties file
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
jsongets_folder = config['DEFAULT']['jsongets_folder']
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'
node_key_val = {}

def get_l3_nodes(state_or_states_list):
    logging.info('Generate L3 nodes')
    data, node_list, l3data = '', [], {}
    data = utils.open_file_load_data('jsonfiles/all_nodes.json')
    for node in data['data']:
        #fileName = 'jsongets/{}'.format('fre_' + node['id'] + '.json')
        fileName = jsongets_folder + '/{}'.format('fre_'+node['id']+'.json')
        logging.debug('l3 filename is {}'.format(fileName))
        if path.exists(fileName):
            fredata = utils.open_file_load_data(fileName)
            if 'data' in fredata:
                l3data = fredata['data']
            if l3data:
                if 'typeGroup' in node['attributes']:
                    # match_object = re.search(
                    #     'SHELF-([0-9]{3,}|2[1-9]|[3-9][0-9])$', node['attributes']['accessIdentifier'])
                    # if node['attributes']['typeGroup'] == "Ciena6500" and (match_object != None or node['attributes']['accessIdentifier'] == 'SHELF-1'):
                    # if node['attributes']['typeGroup'] == "Ciena6500" and match_object != None:
                    # if node['attributes']['typeGroup'] == "Ciena6500" and (node['attributes']['name'][4:6] in state_or_states_list) and ('l2Data' in node['attributes'] and node['attributes']['l2Data'][0]['l2NodeRoutingCapabilities']['isMPLSEnabled'] == True):
                    if node['attributes']['typeGroup'] == "Ciena6500":
                        node['longitude'] = 0
                        node['latitude'] = 0
                        if 'geoLocation' in node['attributes']:
                            node['longitude'] = node.get('attributes').get(
                                'geoLocation').get('longitude') or 0
                            node['latitude'] = node.get('attributes').get(
                                'geoLocation').get('latitude') or 0
                        if 'siteName' in node['attributes'] and node['attributes']['siteName'] != '':
                            node['siteName'] = utils.normalize_sites(
                                '{}'.format(node.get('attributes').get('siteName')))
                        else:
                            node['siteName'] = utils.getSiteName(
                                node['longitude'], node['latitude'])
                        node_list.append(node)
        else:
            logging.debug(" FRE file does not exist to retrieve the L3 node : {}".format(fileName))

    node_list = json.dumps(node_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    with open('jsonfiles/l3nodes.json', 'wb') as f:
        f.write(node_list)
        f.close()
    logging.info('L3 nodes completed...')


def get_l3_links(baseURL, cienauser, cienapassw, token):
    logging.info('Generate L3 links...')
    nodes = {}
    lsplist = []
    l3nodesAll = utils.open_file_load_data('jsonfiles/l3nodes.json')
    allnodes = utils.open_file_load_data('jsonfiles/all_nodes.json')
    dataAllNodes = allnodes['data']
    for node in dataAllNodes:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
    for l3nodes in l3nodesAll:
        dupl_check = {}
        fre_node_key_val = {}
        included = {}
        freData = {}
        networkId = l3nodes['id']
        logging.debug(' Network iconstruct d is :{}'.format(networkId))
        node = l3nodes['attributes']['name']
        if l3nodes.get('attributes').get('l2Data') and l3nodes.get('attributes').get('l2Data')[0].get('loopbackAddresses'):
            loopbackAddress = l3nodes['attributes']['l2Data'][0]['loopbackAddresses'][0]
        else:
            loopbackAddress = ''
        nodes[node] = {'loopback address': loopbackAddress}
        #fileName = 'jsongets/{}.json'.format('fre_' + networkId)
        fileName = jsongets_folder + '/{}.json'.format('fre_'+networkId)
        logging.debug('Filename :\n{}'.format(fileName))
        if path.exists(fileName):
            nodes[node]['Links'] = dict()
            link_data = utils.open_file_load_data(fileName)
            if link_data.get('data'):
                freData = link_data['data']
            for frenode in freData:
                if frenode.get('attributes').get('mgmtName'):
                    fre_node_key_val['{}'.format(
                        frenode['id'])] = frenode['attributes']['mgmtName']
            if link_data.get('included'):
                included = link_data['included']
            logging.debug(
                'Value of len(included):\n{}'.format(len(included)))
            counter = 0
            for i in range(len(included)):
                val = i+1
                id1, tId1, id2, tId2 = '', '', '', ''
                includeDatset = {}
                # logging.debug('Length of i+1 :{}'.format(val))
                if val < len(included):
                    if included[i]['type'] == 'endPoints':
                        if ((included[i]['id'][-3:] == 'EP0' and included[i].get('relationships').get('tpes')) and (included[i+1]['id'][-3:] == 'EP1' and included[i+1].get('relationships').get('tpes'))):
                            tId1 = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                            tunnelId1 = included[i]['relationships']['tpes']['data'][0]['id']
                            tId2 = included[i +
                                            1]['relationships']['tpes']['data'][0]['id'][:36]
                            tunnelId2 = included[i +
                                                1]['relationships']['tpes']['data'][0]['id']
                        elif ((included[i]['id'][-1] == '1' and included[i].get('relationships').get('tpes')) and (included[i+1]['id'][-1] == '2' and included[i+1].get('relationships').get('tpes'))):
                            id1 = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                            linkId1 = included[i]['relationships']['tpes']['data'][0]['id']
                            id2 = included[i +
                                        1]['relationships']['tpes']['data'][0]['id'][:36]
                            linkId2 = included[i +
                                            1]['relationships']['tpes']['data'][0]['id']
                            # logging.debug('This is the value of ID1:\n{}'.format(id1))
                            # logging.debug('This is the value of ID2:\n{}'.format(id2))
                            if id1 and 'network1' in id1:
                                continue
                    else:
                        continue
                    new_obj = {}
                    if tId1 and tId2:
                        if tId1 in node_key_val and tId2 in node_key_val:
                            if tId1 == tId2:
                                logging.debug(
                                    'Tunnel head end and tail end are same')
                            else:
                                populateLspData(tId1, tunnelId1, tId2,
                                                tunnelId2, node_key_val, lsplist)
                    if id1 and id2:
                        networkConstructA_id = id1
                        networkConstructB_id = id2
                        if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val and networkConstructA_id != networkConstructB_id:
                            # Duplicate then continue
                            if included[i]['id'][:-2] in dupl_check:
                                continue
                            new_obj = get_link_data(id1, linkId1, id2, linkId2)
                            if new_obj:
                                counter += 1
                                linkid = "Link" + str(counter)
                                nodes[node]['Links'][linkid] = dict()
                                new_obj['l3node'] = node_key_val[networkConstructA_id]
                                new_obj['l3NeighborNode'] = node_key_val[networkConstructB_id]
                                new_obj['description'] = node_key_val[networkConstructA_id] + \
                                    '-' + \
                                    node_key_val[networkConstructB_id] + \
                                    '-' + str(counter)
                                new_obj['name'] = included[i]['id'][:-2]
                                if(fre_node_key_val).get(included[i]['id'][: -2]):
                                    new_obj['linkName'] = fre_node_key_val[included[i]['id'][:-2]]
                                else:
                                    new_obj['linkName'] = 'Dummy_' + \
                                        included[i]['id'][: -2]

                                nodes[node]['Links'][linkid] = new_obj
                                dupl_check[new_obj['name']] = i
                            else:
                                continue
                        else:
                            continue
        else:
            logging.debug("FRE file does not exist to retrieve links data for : {}".format(fileName))
            continue
    if nodes:
        with open('jsonfiles/l3linksall.json', 'wb') as f:
            f.write(json.dumps(nodes, f, sort_keys=True,
                               indent=4, separators=(',', ': ')))
        logging.info('L3 links generated..')
    if lsplist:
        with open('jsonfiles/lsps.json', 'wb') as f:
            f.write(json.dumps(lsplist, f, sort_keys=True,
                               indent=4, separators=(',', ': ')))
        logging.info('Lsp data generated..')


def populateLspData(tId1, tunnelId1, tId2, tunnelId2, node_key_val, lsplist):
    lspdict = {}
    logging.debug('mpls tunnel endpoint are : '+tunnelId1 + ' and '+tunnelId2)
    #fileNameEnd1 = 'jsongets/{}.json'.format('tpe_' + tId1)
    fileNameEnd1 = jsongets_folder + '/{}.json'.format('tpe_'+tId1)
    logging.debug('Filename :\n{}'.format(fileNameEnd1))
    #fileNameEnd2 = 'jsongets/{}.json'.format('tpe_' + tId2)
    fileNameEnd2 = jsongets_folder + '/{}.json'.format('tpe_'+tId2)
    logging.debug('Filename :\n{}'.format(fileNameEnd2))
    if path.exists(fileNameEnd1):
        tunnelEnd1 = utils.open_file_load_data(fileNameEnd1)
        if tunnelEnd1:
            if tunnelEnd1.get('data'):
                tunnelEnd1Data = tunnelEnd1['data']
                end1Data = next(
                    (item for item in tunnelEnd1Data if item['id'] == tunnelId1), None)
            if end1Data:
                if 'layerTerminations' in end1Data['attributes'] and end1Data['attributes']['layerTerminations'][0]['mplsPackage']['tunnelRole'] == 'headEnd':
                    # logging.debug('Tunnel head end id is:'.format(tunnelId1))
                    lspdict['Tunnel Headend'] = node_key_val[tId1]
                    lspdict['Tunnel Tailend'] = node_key_val[tId2]
                    getTunnelData(end1Data, lspdict, lsplist)
                else:
                    if path.exists(fileNameEnd2):
                        tunnelEnd2 = utils.open_file_load_data(fileNameEnd2)
                        if tunnelEnd2:
                            if tunnelEnd2.get('data'):
                                tunnelEnd2Data = tunnelEnd2['data']
                                end2Data = next(
                                    (item for item in tunnelEnd2Data if item['id'] == tunnelId2), None)
                            if end2Data:
                                if end2Data['attributes']['layerTerminations'][0]['mplsPackage']['tunnelRole'] == 'headEnd':
                                    # logging.debug('Tunnel head end id is:'.format(tunnelId2))
                                    lspdict['Tunnel Headend'] = node_key_val[tId2]
                                    lspdict['Tunnel Tailend'] = node_key_val[tId1]
                                    getTunnelData(end2Data, lspdict, lsplist)


def getTunnelData(lspData, lspdict, lsplist):
    adminstate = lspData['attributes']['layerTerminations'][0]['adminState']
    if adminstate == 'up':
        lspdict['adminstate'] = adminstate
        if lspData.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('includeAll'):
            lspdict['affinitybits'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['includeAll']['bitmask']
            lspdict['affinitymask'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['includeAll']['bitmask']
        else:
            logging.debug('LSP has no affinity bits: ')
            # lspdict['affinitybits'] = 0
            # lspdict['affinitymask'] = 0
        lspdict['direction'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['direction']
        signalledBW = lspData['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maximum']
        if isinstance(signalledBW, basestring):
            lspdict['signalledBW'] = int(int(signalledBW)/1000)
        elif isinstance(signalledBW, int):
            lspdict['signalledBW'] = signalledBW/1000
        else:
            lspdict['signalledBW'] = signalledBW
        lspdict['Tunnel Id'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['lspId']
        lspdict['Tunnel Name'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['lspName']
        lspdict['Tunnel Source'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['srcIp']
        lspdict['Tunnel Destination'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['destIp']
        lspdict['co-routed'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['coRouted']
        if lspData.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('fb'):
            lspdict['FRR'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['fb']['frrAutoCreated']
        lspdict['hold-priority'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['holdPriority']
        lspdict['setup-priority'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['setupPriority']
        lspdict['Tunnel Role'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['tunnelRole']
        lspdict['Tunnel Type'] = lspData['attributes']['layerTerminations'][0]['mplsPackage']['tunnelType']
        lsplist.append(lspdict)
    else:
        logging.debug('Tunnel admin state is not up: {}'.format(adminstate))


def get_link_data(link1, linkId1, link2, linkId2):
    logging.debug('Retrieve L3 links info...{}'.format(linkId2))
    new_obj = {
        'local IP': '',
        'local Intf': '',
        'local IGP Metrics': '',
        'local Phy BW': 0.0,
        'local RSVP BW': 0.0,
        'local Affinity': ''
    }
    port, shelf, slot = '', '', ''
    tpeData1, tpeData2 = {}, {}
    #filenameId1 = 'jsongets/{}.json'.format('tpe_'+link1)
    #filenameId2 = 'jsongets/{}.json'.format('tpe_'+link2)
    filenameId1 = jsongets_folder + '/{}.json'.format('tpe_'+link1)
    filenameId2 = jsongets_folder + '/{}.json'.format('tpe_'+link2)
    if path.exists(filenameId1):
        tpeData1 = utils.open_file_load_data(filenameId1)
    if path.exists(filenameId2):
        tpeData2 = utils.open_file_load_data(filenameId2)
    if tpeData1 and tpeData2:    
        if tpeData1.get('data'):
            lnkData1 = tpeData1['data']
        if tpeData2.get('data'):
            lnkData2 = tpeData2['data']
        data = next((item for item in lnkData1 if item['id'] == linkId1), None)
        if data:
            # logging.debug('link data id1 is : {}'.format(linkId1))
            if data.get('attributes').get('layerTerminations')[0]:
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceIp'):
                    new_obj['local IP'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceIp']
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceName'):
                    new_obj['local Intf'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceName']
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('linkCost'):
                    new_obj['local IGP Metrics'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['linkCost']
                if 'locations' in data.get('attributes'):
                    if 'port' in data['attributes']['locations'][0]:
                        port = data['attributes']['locations'][0]['port']
                    if 'shelf' in data['attributes']['locations'][0]:
                        shelf = data['attributes']['locations'][0]['shelf']
                    if 'slot' in data['attributes']['locations'][0]:
                        slot = data['attributes']['locations'][0]['slot']
                    new_obj['circuitName'] = getCircuitName(port, shelf, slot, linkId1, lnkData1)
                if data.get('attributes').get('layerTerminations')[0].get('mplsPackage') and data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('bw'):
                    new_obj['local Phy BW'] = int(
                        data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maximum'])/1000
                    new_obj['local RSVP BW'] = int(
                        data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maxReservable'])/1000
                    if data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('colorGroup'):
                        new_obj['local Affinity'] = data['attributes']['layerTerminations'][0]['mplsPackage']['colorGroup']['bitmask']
        if new_obj.get('local IP'):
            data = next((item for item in lnkData2 if item['id'] == linkId2), None)
            if data:
                # logging.debug('link data id2 is : {}'.format(linkId2))
                if data.get('attributes').get('layerTerminations')[0]:
                    if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceIp'):
                        new_obj['neighbor IP'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceIp']
                    if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceName'):
                        new_obj['neighbor Intf'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceName']
                    if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('linkCost'):
                        new_obj['neighbor IGP Metrics'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['linkCost']
                    if data.get('attributes').get('layerTerminations')[0].get('mplsPackage') and data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('bw'):
                        new_obj['neighbor Phy BW'] = int(
                            data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maximum'])/1000
                        new_obj['neighbor RSVP BW'] = int(
                            data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maxReservable'])/1000
                        if data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('colorGroup'):
                            new_obj['Neighbor Affinity'] = data['attributes']['layerTerminations'][0]['mplsPackage']['colorGroup']['bitmask']
    return new_obj

def getCircuitName(port, shelf, slot, linkId1, lnkData1):
    circuitName =''
    logging.debug('Link id is : {}'.format(linkId1))
    for item in lnkData1:
        if 'locations' in item['attributes'] and 'port' in item['attributes']['locations'][0]:
            if item['attributes']['locations'][0]['port'] == port and item['attributes']['locations'][0]['shelf'] == shelf and item['attributes']['locations'][0]['slot'] == slot:
                if item['id'] != linkId1 and 'userLabel' in item['attributes']:
                    circuitName = item['attributes']['userLabel']
                    break
            else:
                continue
    if circuitName == '':
        circuitName = 'Dummy_'+linkId1
    return circuitName
