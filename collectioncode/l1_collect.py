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


def get_l1_nodes(state_or_states_list):
    logging.info('Retrieve L1 Nodes')
    data, node_list = '', []
    data = utils.open_file_load_data("jsonfiles/all_nodes.json")
    for node in data['data']:
        if 'typeGroup' in node['attributes']:
            match_object = re.search(
                'SHELF-([0-9]|1[0-9]|20)$', node['attributes']['accessIdentifier'])
            if node['attributes']['typeGroup'] == "Ciena6500" and (node['attributes']['name'][4:6] in state_or_states_list) and ((node['attributes']['accessIdentifier'] == 'SHELF-21' and (node['attributes']['deviceVersion'] == "6500-T24 PACKET-OPTICAL") or (node['attributes']['deviceVersion'] == "6500-T12 PACKET-OPTICAL")) or match_object != None):
                # if node['attributes']['typeGroup'] == "Ciena6500" and (node['attributes']['name'][4:6] in state_or_states_list) and 'l2Data' not in node['attributes']:
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

    node_list = json.dumps(node_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    with open('jsonfiles/l1nodes.json', 'wb') as f:
        f.write(node_list)
        f.close()
    logging.debug('L1 nodes completed..')


def get_l1_links(baseURL, cienauser, cienapassw, token, state_or_states_list):
    # Retrieve l1 links data for all nodes
    get_l1_links_data(baseURL, cienauser, cienapassw,
                      token, state_or_states_list)
    logging.info('Generate L1 links...')
    l1nodesAll = utils.open_file_load_data('jsonfiles/l1nodes.json')
    for node in l1nodesAll:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
    l1links_list, dupl_check = [], {}
    for l1nodes in l1nodesAll:
        networkId = l1nodes['id']
        linkname_key_val, included, linkData, layer_key_val = {}, {}, {}, {}
        # Retrieve link info for each l1 node
        fileName = 'l1_fre_'+networkId+'.json'
        logging.debug('Filename :\n{}'.format(fileName))
        with open('jsongets/{}'.format(fileName), 'rb') as f:
            thejson = f.read()
            f.close()
        link_data = json.loads(thejson)
        if link_data.get('data'):
            linkData = link_data['data']
        else:
            logging.debug(
                'There is no FRE data returned for network construct id:{}'.format(networkId))
        if link_data.get('included'):
            included = link_data['included']
        else:
            continue
        # Retrieve link name and layer rate for each link id
        for links in linkData:
            linkname_key_val['{}'.format(
                links['id'])] = links['attributes']['userLabel']
            layer_key_val['{}'.format(links['id'])
                          ] = links['attributes']['layerRate']
        for i in range(len(included)):
            val = i+1
            if val < len(included):
                layerRate = layer_key_val[included[i]['id'][:-2]]
                logging.debug('Network id is :{}'.format(networkId))
                # Checking if type is endpoint and layer rate should be 'OMS' or 'OTS' for L1 links
                if included[i]['type'] == 'endPoints' and (layerRate == 'OMS' or layerRate == 'OTS'):
                    # if included[i]['type'] == 'endPoints':
                    logging.debug(
                        'OMS / OTS include id is :{}'.format(included[i]['id']))
                    if included[i]['id'][-1] == '1' and included[i].get('relationships').get('tpes'):
                        networkConstructA_id = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                    if included[i+1]['id'][-1] == '2' and included[i+1].get('relationships').get('tpes'):
                        networkConstructB_id = included[i +
                                                        1]['relationships']['tpes']['data'][0]['id'][:36]
                    # logging.info('This is the value of ID1:\n{}'.format(networkConstructA_id))
                    # logging.info('This is the value of ID2:\n{}'.format(networkConstructB_id))
                else:
                    continue
                if 'network1' in networkConstructA_id:
                    continue
                new_obj = {}
                if networkConstructA_id and networkConstructB_id:
                    new_obj['linkid'] = included[i]['id'][:-2]
                    # Check if userlable field populated then populate circuit name otherwise populate with Dummy followed by linkid
                    circuitname = linkname_key_val[new_obj['linkid']]
                    if circuitname == '':
                        new_obj['circuitName'] = 'Dummy_'+'_'+new_obj['linkid']
                    else:
                        new_obj['circuitName'] = circuitname + \
                            '_'+new_obj['linkid']
                    # Check for duplicate link id
                    if new_obj['linkid'] in dupl_check:
                        continue
                    if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                        new_obj['l1nodeA'] = node_key_val[networkConstructA_id]
                        new_obj['l1nodeB'] = node_key_val[networkConstructB_id]
                    else:
                        continue
                    new_obj['description'] = new_obj['l1nodeA'] + \
                        '-' + new_obj['l1nodeB'] + '-' + str(i)
                    # Add link id for duplicate check
                    dupl_check[new_obj['linkid']] = i
                    l1links_list.append(new_obj)
    # Write data in json file
    l1links_list = json.dumps(
        l1links_list, sort_keys=True, indent=4, separators=(',', ': '))
    with open('jsonfiles/l1links.json', 'wb') as f:
        f.write(l1links_list)
        f.close()
    logging.info('Complete L1 links...')


def get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list):
    logging.info('Retrieving L1 links data from MCP..')
    # nodesData = utils.getStateNodes(state_or_states_list)
    nodesData = utils.getNodes()
    logging.debug(
        'Retrieve L1 links data for nodes belongs to list of states:')
    for k in nodesData.keys():
        networkConstrId = k
        logging.debug('networkConstrId:\n{}'.format(networkConstrId))
        incomplete, jsonmerged = True, {}
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=ETHERNET&serviceClass=IP&limit=1000&networkConstruct.id={}'.format(networkConstrId)

        # uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&sortBy=name&networkConstruct.id={}'.format(networkConstrId)
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id={}'.format(networkConstrId)
        # Priv retrieving data for OMS , OTS and OTU's
        uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id='
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTU2%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id='
        URL = baseURL + uri + networkConstrId
        logging.debug('URL:\n{}'.format(URL))
        while incomplete:
            portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
            jsonaddition = json.loads(portData)
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

        # save data for each network construct id
        filename = "l1_fre_"+networkConstrId+'.json'
        with open('jsongets/{}'.format(filename), 'wb') as f:
            f.write(json.dumps(jsonmerged, f, sort_keys=True,
                               indent=4, separators=(',', ': ')))
            f.close()
        logging.info('Retrieved L1 links data...')


def get_l1_circuits(baseURL, cienauser, cienapassw, token):
    logging.info('Generating L1 Circuits...')
    l1_circuit_list, dupl_check = [], {}
    # Setting up the links and l1 nodes data for use later on
    l1nodesAll = utils.open_file_load_data('jsonfiles/l1nodes.json')
    l1nodes_dict = {val: 1 for node in l1nodesAll for (
        key, val) in node.items() if key == 'id'}
    for node in l1nodesAll:
        node_key_val['{}'.format(
            node['id'])] = node['attributes']['name']
    for l1nodes in l1nodesAll:
        # linkname_key_val = {}
        networkId = l1nodes['id']
        filename = 'l1_fre_'+networkId+'.json'
        logging.debug('filename to retrieve L1 circuits:\n{}'.format(filename))
        with open('jsongets/{}'.format(filename), 'rb') as f:
            thejson = f.read()
            f.close()
        all_links_dict = json.loads(thejson)
        if all_links_dict.get('data'):
            data = all_links_dict['data']
        else:
            logging.debug(
                'There is no FRE data for network construct id to build circuits:{}'.format(networkId))
            continue
        if all_links_dict.get('included'):
            included = all_links_dict['included']
        for obj in data:
            # circuit_check = False
            circuit_id = obj['id']
            if circuit_id in dupl_check:
                continue
            # if layer rate is not OTU4 then continue
            if obj['attributes']['layerRate'] != 'OTU4':
                continue
            for node in included:
                if node['type'] == 'endPoints' and node['id'][-1] == '1':
                    if node['id'][:-2] == circuit_id:
                        starting_node = node['relationships']['tpes']['data'][0]['id'][:36]
                        startingNodeId = node['relationships']['tpes']['data'][0]['id']
                if node['type'] == 'endPoints' and node['id'][-1] == '2':
                    if node['id'][:-2] == circuit_id:
                        ending_node = node['relationships']['tpes']['data'][0]['id'][:36]
                        endingNodeId = node['relationships']['tpes']['data'][0]['id']
                        break
            # l1_check = starting_node in l1nodes_dict and ending_node in l1nodes_dict

            # check if starting node is not equal to ending node .
            l1_check = starting_node in l1nodes_dict and ending_node in l1nodes_dict and starting_node != ending_node
            if l1_check:
                logging.debug(
                    ' Retrieve supporting nodes for  circuit id: {}'.format(circuit_id))
                link_list = collect.get_supporting_nodes(
                    circuit_id, baseURL, cienauser, cienapassw, token)
                # Check based on the returned nodes to see if they're valid l1 nodes
                supporting_link_check = False
                if link_list:
                    for link_obj in link_list:
                        if link_obj['NodeA'] in l1nodes_dict and link_obj['NodeB'] in l1nodes_dict:
                            supporting_link_check = True
                        else:
                            supporting_link_check = False

                if supporting_link_check:
                    temp_obj = {
                        "circuitName": "",
                        "circuitID": "",
                        "startL1Node": "",
                        "endL1Node": "",
                        "portStartNode": "",
                        "portEndNode": "",
                        "linkLabel": "",
                        "wavelength": 0.0,
                        "channel": "",
                        "frequency": 0.0,
                        "status": "",
                        "ordered_Hops": []
                    }
                    portStartNode, portEndNode = getPortDetails(
                        starting_node, startingNodeId, ending_node, endingNodeId)
                    temp_obj['portStartNode'] = portStartNode
                    temp_obj['portEndNode'] = portEndNode

                    starting_node_name = node_key_val['{}'.format(
                        starting_node)]
                    ending_node_name = node_key_val['{}'.format(ending_node)]
                    temp_obj['circuitID'] = circuit_id
                    temp_obj['startL1Node'] = starting_node_name
                    temp_obj['endL1Node'] = ending_node_name

                    if obj.get('attributes').get('displayData') and obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                        if 'wavelength' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['wavelength'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['wavelength']
                        if 'frequency' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['frequency'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['frequency']
                        if 'channel' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel']
                    try:
                        if obj.get('attributes').get('userLabel') == '':
                            temp_obj['circuitName'] = 'Dummy_' + circuit_id
                        else:
                            temp_obj['circuitName'] = obj['attributes']['userLabel'] + \
                                '_' + circuit_id
                    except Exception as err:
                        logging.warn('Circuit name returning blank for circuit id :{}'.format(
                            temp_obj['circuitID']))
                        temp_obj['circuitName'] = 'Dummy_' + circuit_id

                    temp_obj['status'] = obj['attributes']['operationState']
                    for link in link_list:
                        link['NodeA'] = node_key_val['{}'.format(
                            link['NodeA'])]
                        link['NodeB'] = node_key_val['{}'.format(
                            link['NodeB'])]
                    link_list.insert(0, {'Name': 'Starting Link', 'NodeA': '{}'.format(
                        starting_node_name), 'NodeB': '{}'.format(link_list[0]['NodeA'])})
                    link_list.append({'Name': 'Ending Link', 'NodeA': '{}'.format(
                        link_list[len(link_list)-1]['NodeB']), 'NodeB': '{}'.format(ending_node_name)})
                    temp_obj['ordered_Hops'] = link_list
                    if temp_obj['circuitName'] != 'THISISANULHLINEPORT':
                        l1_circuit_list.append(temp_obj)
                    dupl_check[temp_obj['circuitID']] = temp_obj['circuitID']
    # if l1_circuit_list:
    l1_circuit_list = json.dumps(
        l1_circuit_list, sort_keys=True, indent=4, separators=(',', ': '))
    with open('jsonfiles/l1circuits.json', 'wb') as f:
        f.write(l1_circuit_list)
        f.close()
    logging.info('L1 Circuits generated..')


def getPortDetails(starting_node, startingNodeId, ending_node, endingNodeId):
    logging.info('Retrieve port info for L1 circuits')
    fileNameA = 'tpe_'+starting_node
    fileNameB = 'tpe_'+ending_node
    with open('jsongets/{}.json'.format(fileNameA), 'rb') as f:
        thejson = f.read()
        f.close()
    portDataStartNode = json.loads(thejson)
    if portDataStartNode.get('data'):
        dataStartNode = portDataStartNode['data']
    dataNodeA = next(
        items for items in dataStartNode if items['id'] == startingNodeId)
    portStartNode = dataNodeA['attributes']['nativeName']

    with open('jsongets/{}.json'.format(fileNameB), 'rb') as f:
        thejson = f.read()
        f.close()
    portDataEndNode = json.loads(thejson)
    if portDataEndNode.get('data'):
        dataEndNode = portDataEndNode['data']
    dataNodeB = next(
        items for items in dataEndNode if items['id'] == endingNodeId)
    portEndNode = dataNodeB['attributes']['nativeName']
    logging.info('L1 port info retrieved..')
    return portStartNode, portEndNode
