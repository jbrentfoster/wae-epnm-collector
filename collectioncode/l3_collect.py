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

# Setting up the properties file
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'
node_key_val = {}


def get_l3_nodes():
    data, node_list, site_list = '', [], []
    data = utils.open_file_load_data("jsonfiles/all_nodes.json")
    counter = 1
    for node in data['data']:
        if 'typeGroup' in node['attributes']:
            match_object = re.search(
                'SHELF-([0-9]{3,}|2[1-9]|[3-9][0-9])$', node['attributes']['accessIdentifier'])
            if node['attributes']['typeGroup'] == "Ciena6500" and (match_object != None or node['attributes']['accessIdentifier'] == 'SHELF-1'):
            # if node['attributes']['typeGroup'] == "Ciena6500" and match_object != None:
                node['longitude'] = 0
                node['latitude'] = 0
                if 'geoLocation' in node['attributes']:
                    node['longitude'] = node.get('attributes').get(
                        'geoLocation').get('longitude') or 0
                    node['latitude'] = node.get('attributes').get(
                        'geoLocation').get('latitude') or 0
                # Setting the site name, starting w/ the clli code check
                new_match_object = re.search(
                    r"^\w{8}-", node['attributes']['name'])
                s_name = bool(node['attributes']['siteName'])

                if new_match_object != None:
                    node['wae_site_name'] = str(node['attributes']['name'])[:8]
                elif s_name and len(node['attributes']['siteName']) > 0:
                    node['wae_site_name'] = utils.normalize_sites(
                        '{}'.format(node['attributes']['siteName']))
                elif node['longitude'] != 0 and node['latitude'] != 0:
                    node['wae_site_name'] = utils.normalize_sites(
                        '{}[{}]'.format(name, counter))
                    counter += 1
                else:
                    node['wae_site_name'] = utils.normalize_sites(
                        '{}'.format(sitename_bucket))
                node_list.append(node)

    node_list = json.dumps(node_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    logging.debug('These are the L3 nodes:\n{}'.format(node_list))
    with open('jsonfiles/l3nodes.json', 'wb') as f:
        f.write(node_list)

    # Creating the sites.json file for each node in node_list
    node_list = json.loads(node_list)
    dupl_check = {}
    for node in node_list:
        # Making sure no duplicates are in our sites file
        if node['wae_site_name'] in dupl_check:
            continue
        obj = {
            "name": "",
            "latitude": 0,
            "longitude": 0,
            "id": "",
            "description": ""
        }
        obj['name'] = node['wae_site_name']
        obj['longitude'] = node['longitude']
        obj['latitude'] = node['latitude']
        if 'siteId' in node['attributes']:
            obj['id'] = node['attributes']['siteId']
        obj['description'] = node['relationships']['managementSession']['data']['id']
        # Making the duplicate check valid
        dupl_check[obj['name']] = 'Random_string'
        site_list.append(obj)

    site_list = json.dumps(site_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    logging.debug('These are the l3 sites:\n{}'.format(site_list))
    with open('jsonfiles/l3sites.json', 'wb') as f:
        f.write(site_list)


def get_l3_links(baseURL, cienauser, cienapassw, token):
    nodes = {}
    l3nodesAll = utils.open_file_load_data('jsonfiles/l3nodes.json')
    allnodes = utils.open_file_load_data('jsonfiles/all_nodes.json')
    dataAllNodes = allnodes['data']
    for node in dataAllNodes:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
    l3links_list = []
    for l3nodes in l3nodesAll:
        dupl_check = {}
        fre_node_key_val = {}
        circuit_name_key_val = {}
        networkId = l3nodes['id']
        logging.debug(' Network iconstruct d is :{}'.format(networkId))
        node = l3nodes['attributes']['name']
        if l3nodes.get('attributes').get('l2Data') and l3nodes.get('attributes').get('l2Data')[0].get('loopbackAddresses'):
            loopbackAddress = l3nodes['attributes']['l2Data'][0]['loopbackAddresses'][0]
        else:
            loopbackAddress = ''
        nodes[node] = {'loopback address': loopbackAddress}
        fileName = 'fre_'+networkId
        logging.debug('Filename :\n{}'.format(fileName))
        nodes[node]['Links'] = dict()
        with open('jsongets/{}.json'.format(fileName), 'rb') as f:
            thejson = f.read()
            f.close()    
        link_data = json.loads(thejson)
        if link_data.get('data'):
            freData = link_data['data']
        for frenode in freData:
            if frenode.get('attributes').get('mgmtName'):
                fre_node_key_val['{}'.format(frenode['id'])] = frenode['attributes']['mgmtName']
        if link_data.get('included'):
            included = link_data['included']
        logging.debug(
            'This is the value of len(included):\n{}'.format(len(included)))
        counter = 0
        for i in range(len(included)):
            val = i+1
            logging.debug('Length of i+1 :{}'.format(val))
            if val < len(included):
                if included[i]['type'] == 'endPoints':
                    if included[i]['id'][-1] == '1' and included[i].get('relationships').get('tpes'):
                        id1 = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                        linkId1 = included[i]['relationships']['tpes']['data'][0]['id']
                    if included[i+1]['id'][-1] == '2' and included[i+1].get('relationships').get('tpes'):
                        id2 = included[i+1]['relationships']['tpes']['data'][0]['id'][:36]
                        linkId2 = included[i+1]['relationships']['tpes']['data'][0]['id']
                    # logging.debug('This is the value of ID1:\n{}'.format(id1))
                    # logging.debug('This is the value of ID2:\n{}'.format(id2))
                else:
                    break
                if 'network1' in id1:
                    break

                new_obj = {}
                if id1 and id2:
                    networkConstructA_id = id1
                    networkConstructB_id = id2
                    if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val and networkConstructA_id != networkConstructB_id:
                        # Duplicate then continue
                        if included[i]['id'][:-2] in dupl_check :
                            continue
                        new_obj = get_link_data(id1,linkId1,id2,linkId2)
                        if new_obj:
                            counter += 1
                            linkid = "Link" + str(counter)
                            nodes[node]['Links'][linkid] = dict()
                            new_obj['l3node'] = node_key_val[networkConstructA_id]
                            new_obj['l3NeighborNode'] = node_key_val[networkConstructB_id]
                            new_obj['description'] = node_key_val[networkConstructA_id] + '_' + node_key_val[networkConstructB_id] + '-' + str(counter)
                            new_obj['name'] = included[i]['id'][:-2]
                            if(fre_node_key_val).get(included[i]['id'][:-2]):
                                new_obj['circuitName'] = fre_node_key_val[included[i]['id'][:-2]]+ '-' + included[i]['id'][:-2]
                            else:
                                new_obj['circuitName'] = 'Dummy_'+included[i]['id'][:-2]

                            if(fre_node_key_val).get(included[i]['id'][:-2]):
                                new_obj['linkName'] = fre_node_key_val[included[i]['id'][:-2]]
                            else:
                                new_obj['linkName'] = 'Dummy_'+included[i]['id'][:-2]

                            nodes[node]['Links'][linkid] = new_obj
                            dupl_check[new_obj['name']] = i
                        else:
                            continue
                    else:
                        continue
    with open('jsonfiles/l3linksall.json', 'wb') as f:
        f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))


def get_link_data(link1,linkId1,link2,linkId2):
    new_obj = {}
    filenameId1 = 'tpe_'+link1
    filenameId2 = 'tpe_'+link2
    tpeData1 = utils.open_file_load_data('jsongets/{}.json'.format(filenameId1))
    tpeData2 = utils.open_file_load_data('jsongets/{}.json'.format(filenameId2))
    if tpeData1.get('data'):
        lnkData1 = tpeData1['data']
    if tpeData2.get('data'):
        lnkData2 = tpeData2['data']
    # temp_obj = {}

    # for data in lnkData1:
    #     if linkId1 == data['id']:
    data = next((item for item in lnkData1 if item['id'] == linkId1),None)
    if data:
        logging.debug('link data id1 is : {}'.format(linkId1))
        if data.get('attributes').get('layerTerminations')[0]:
            if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceIp'):
                new_obj['local IP'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceIp']
            if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceName'):
                new_obj['local Intf'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceName']
            if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('linkCost'):
                new_obj['local IGP Metrics'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['linkCost']
            if data.get('attributes').get('layerTerminations')[0].get('mplsPackage'):
                new_obj['local Phy BW'] = int(data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maximum'])/1000
                new_obj['local RSVP BW'] = int(data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maxReservable'])/1000
                if data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('colorGroup'):
                    new_obj['local Affinity'] = data['attributes']['layerTerminations'][0]['mplsPackage']['colorGroup']['bitmask']
    if new_obj.get('local IP'):
        # for data in lnkData2:
        #     if linkId2 == data['id']:
        data = next((item for item in lnkData2 if item['id'] == linkId2),None)
        if data:
            logging.debug('link data id2 is : {}'.format(linkId2))
            if data.get('attributes').get('layerTerminations')[0]:
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceIp'):
                    new_obj['neighbor IP'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceIp']
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('interfaceName'):
                    new_obj['neighbor Intf'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['interfaceName']
                if data.get('attributes').get('layerTerminations')[0].get('additionalAttributes').get('linkCost'):
                    new_obj['neighbor IGP Metrics'] = data['attributes']['layerTerminations'][0]['additionalAttributes']['linkCost']
                if data.get('attributes').get('layerTerminations')[0].get('mplsPackage'):
                    new_obj['neighbor Phy BW'] = int(data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maximum'])/1000
                    new_obj['neighbor RSVP BW'] = int(data['attributes']['layerTerminations'][0]['mplsPackage']['bw']['maxReservable'])/1000
                    if data.get('attributes').get('layerTerminations')[0].get('mplsPackage').get('colorGroup'):
                        new_obj['Neighbor Affinity'] = data['attributes']['layerTerminations'][0]['mplsPackage']['colorGroup']['bitmask']
    return new_obj


