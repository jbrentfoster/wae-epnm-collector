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

###### New method for l1 nodes based on l1 circuits ####################
def get_l1_nodes(state_or_states_list):
    logging.info('Retrieve L1 Nodes')
    data, node_list, l1data = '', [], {}
    data = utils.open_file_load_data('jsonfiles/all_nodes.json')
    for node in data['data']:
        fileName = 'l1_fre_'+node['id']+'.json'
        logging.debug('l1 filename is {}'.format(fileName))
        l1fredata = utils.open_file_load_data('jsongets/{}'.format(fileName))
        if 'data' in l1fredata:
            l1data = l1fredata['data']
        if l1data:
            if 'typeGroup' in node['attributes']:
                # match_object = re.search(
                #     'SHELF-([0-9]|1[0-9]|20)$', node['attributes']['accessIdentifier'])
                # if node['attributes']['typeGroup'] == "Ciena6500" and (node['attributes']['name'][4:6] in state_or_states_list) and ((node['attributes']['accessIdentifier'] == 'SHELF-21' and (node['attributes']['deviceVersion'] == "6500-T24 PACKET-OPTICAL") or (node['attributes']['deviceVersion'] == "6500-T12 PACKET-OPTICAL")) or match_object != None):
                # if node['attributes']['typeGroup'] == "Ciena6500" and (node['attributes']['name'][4:6] in state_or_states_list) and 'l2Data' not in node['attributes']:
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

    node_list = json.dumps(node_list, sort_keys=True,
                           indent=4, separators=(',', ': '))
    with open('jsonfiles/l1nodes.json', 'wb') as f:
        f.write(node_list)
        f.close()
    logging.debug('L1 nodes completed..')


def get_l1_links(baseURL, cienauser, cienapassw, token, state_or_states_list):
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
        link_data = utils.open_file_load_data('jsongets/{}'.format(fileName))
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
                if included[i]['id'][:-2] in layer_key_val.keys():
                    layerRate = layer_key_val[included[i]['id'][:-2]]
                else:
                    layerRate = ''
                logging.debug('Layer Rate is :{}'.format(layerRate))
                # if layerRate != 'OMS' or layerRate == '':
                #     continue
                # if 'OM' not in layerRate:
                #     logging.debug('This layer rate should not link :{}'.format(layerRate))
                #     continue
                logging.debug('Network id is :{}'.format(networkId))
                # Checking if type is endpoint and layer rate should be 'OMS' for L1 links
                if included[i]['type'] == 'endPoints':
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
                    # Check for duplicate link id
                    if new_obj['linkid'] in dupl_check:
                        continue
                    # Check if userlable field populated then populate circuit name otherwise populate with Dummy followed by linkid
                    circuitname = linkname_key_val[new_obj['linkid']]
                    if circuitname == '':
                        new_obj['circuitName'] = 'Dummy_'+'_'+new_obj['linkid']
                    else:
                        new_obj['circuitName'] = circuitname +'_'+new_obj['linkid']

                    if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                        new_obj['l1nodeA'] = node_key_val[networkConstructA_id]
                        new_obj['l1nodeB'] = node_key_val[networkConstructB_id]
                    else:
                        continue
                    new_obj['description'] = new_obj['l1nodeA'] + \
                        '-' + new_obj['l1nodeB'] + '-' + str(i)

                    linkName = getLinkName(networkConstructA_id, new_obj['l1nodeA'], new_obj['l1nodeB'])
                    if linkName == '':
                        new_obj['linkname'] = 'Dummy_'+'_'+new_obj['linkid']
                    else:
                        new_obj['linkname'] = linkName

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
    nodesData = utils.getStateNodes(state_or_states_list)
    # nodesData = utils.getNodes()
    logging.debug(
        'Retrieve L1 links data for nodes belongs to list of states:')
    for k in nodesData.keys():
        networkConstrId = k
        logging.debug('networkConstrId:\n{}'.format(networkConstrId))
        incomplete, jsonmerged = True, {}
        # Priv retrieving data for OMS , OTS and OTU's  (ORIGINAL QUERY: COMMENT TEMPRARY)
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id='
        ########### Query to retrieve l1 links data
        uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=SNC%2CROADM%20Line%2CPhotonic%2CFiber%2COTU&limit=1000&networkConstruct.id='

        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=ETHERNET&serviceClass=IP&limit=1000&networkConstruct.id={}'.format(networkConstrId)
        # uri = '/nsi/api/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CdisplayDeploymentState%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2CdisplayRecoveryCharacteristicsOnHome&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CEmbedded%20Ethernet%20Link%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing%2CL3VPN&sortBy=name&networkConstruct.id={}'.format(networkConstrId)
        # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id={}'.format(networkConstrId)
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
    l1_circuit_list, dupl_check, links_key_val= [], {}, {}
    # Setting up the links and l1 nodes data for use later on
    l1nodesAll = utils.open_file_load_data('jsonfiles/l1nodes.json')
    l1nodes_dict = {val: 1 for node in l1nodesAll for (
        key, val) in node.items() if key == 'id'}
    for node in l1nodesAll:
        node_key_val['{}'.format(
            node['id'])] = node['attributes']['name']
    # Retrieve link names for link id
    l1linksAll = utils.open_file_load_data('jsonfiles/l1links.json')
    for links in l1linksAll:
        links_key_val['{}'.format(links['linkid'])] = links['linkname']
    for l1nodes in l1nodesAll:
        # linkname_key_val = {}
        networkId = l1nodes['id']
        filename = 'l1_fre_'+networkId+'.json'
        logging.debug('filename to retrieve L1 circuits:\n{}'.format(filename))
        all_links_dict = utils.open_file_load_data('jsongets/{}'.format(filename))
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
            # if circuit_id in dupl_check:
            #     continue
            logging.debug('Circuit id is :\n{}'.format(circuit_id))
            layerRate = obj['attributes']['layerRate']
            logging.debug('layerRate is :\n{}'.format(layerRate))
            # if (obj['attributes']['layerRate'] != 'OTS') and (obj['attributes']['layerRate'] !='OTU4') and (obj['attributes']['layerRate'] !='OTSi'):
            #     logging.debug('This layerRate should not process :\n{}'.format(layerRate)+' for circuit id :{}'.format(circuit_id))

            # if layer rate is not OTS then continue
            # if (obj['attributes']['layerRate'] != 'OTS') and (obj['attributes']['layerRate'] !='OTU4') and (obj['attributes']['layerRate'] !='OTSi'):
            #     continue

            if (obj['attributes']['layerRate'] != 'OTS') and (obj['attributes']['layerRate'] != 'OMS') and ('OTU' not in obj['attributes']['layerRate']):
                logging.debug('This layerRate should not process for L1 Circuits:\n{}'.format(layerRate)+' for circuit id :{}'.format(circuit_id))

            # if (obj['attributes']['layerRate'] != 'OTS') and (obj['attributes']['layerRate'] != 'OMS') and ('OTU' not in obj['attributes']['layerRate']):
            #     continue
            # if (obj['attributes']['layerRate'] != 'OTS') and ('OTU' not in obj['attributes']['layerRate']):
            #     continue
            if ('OTU' not in obj['attributes']['layerRate']):
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
                    circuit_id, filename, links_key_val, baseURL, cienauser, cienapassw, token)
                # Check based on the returned nodes to see if they're valid l1 nodes
                supporting_link_check = True
                # supporting_link_check = False
                # if link_list:
                #     for link_obj in link_list:
                #         if link_obj['NodeA'] in l1nodes_dict and link_obj['NodeB'] in l1nodes_dict:
                #             supporting_link_check = True
                #         else:
                #             supporting_link_check = False

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
                    starting_node_name = node_key_val['{}'.format(
                        starting_node)]
                    ending_node_name = node_key_val['{}'.format(ending_node)]
                    portStartNode, portEndNode, circuitName = getPortDetails(
                        starting_node, startingNodeId, starting_node_name, ending_node, endingNodeId, ending_node_name)
                    if circuitName in dupl_check:
                        continue
                    if circuitName:
                        temp_obj['circuitName'] = circuitName
                    else:
                        circuitName = 'Dummy_' + circuit_id
                        temp_obj['circuitName'] = circuitName

                    # temp_obj['portStartNode'] = circuitName
                    # temp_obj['portEndNode'] = circuitName
                    temp_obj['portStartNode'] = portStartNode
                    temp_obj['portEndNode'] = portEndNode

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

                    temp_obj['status'] = obj['attributes']['operationState']
                    if link_list:
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
                    # dupl_check[temp_obj['circuitID']] = temp_obj['circuitID']
                    dupl_check[temp_obj['circuitName']] = temp_obj['circuitName']
    # if l1_circuit_list:
    l1_circuit_list = json.dumps(
        l1_circuit_list, sort_keys=True, indent=4, separators=(',', ': '))
    with open('jsonfiles/l1circuits.json', 'wb') as f:
        f.write(l1_circuit_list)
        f.close()
    logging.info('L1 Circuits generated..')


def getPortDetails(starting_node, startingNodeId, startNodeName, ending_node, endingNodeId, endNodeName):
    logging.info('Retrieve port info for L1 circuits')
    circuitName, portStartNode, portEndNode = '', '', ''
    dataStartNode, dataEndNode, includedDataA, includedDataB  = {}, {}, {}, {}
    fileNameA = 'tpe_'+starting_node
    fileNameB = 'tpe_'+ending_node
    portDataStartNode = utils.open_file_load_data('jsongets/{}.json'.format(fileNameA))
    if portDataStartNode:
        if portDataStartNode.get('included'):
            includedDataA = portDataStartNode['included']
        if portDataStartNode.get('data'):
            dataStartNode = portDataStartNode['data']
        dataNodeA = next(
            items for items in dataStartNode if items['id'] == startingNodeId)
        portStartNode = dataNodeA['attributes']['nativeName']
        if 'locations' in dataNodeA.get('attributes'):
            if 'port' in dataNodeA['attributes']['locations'][0]:
                portA = dataNodeA['attributes']['locations'][0]['port']
            if 'shelf' in dataNodeA['attributes']['locations'][0]:
                shelfA = dataNodeA['attributes']['locations'][0]['shelf']
            if 'slot' in dataNodeA['attributes']['locations'][0]:
                slotA = dataNodeA['attributes']['locations'][0]['slot']
    else:
         logging.info('tpe data not found for starting node id :{}'.format(starting_node))
    
    portDataEndNode = utils.open_file_load_data('jsongets/{}.json'.format(fileNameB))
    if portDataEndNode:
        if portDataEndNode.get('included'):
            includedDataB = portDataEndNode['included']
        if portDataEndNode.get('data'):
            dataEndNode = portDataEndNode['data']
        dataNodeB = next(
            items for items in dataEndNode if items['id'] == endingNodeId)
        portEndNode = dataNodeB['attributes']['nativeName']
        if 'locations' in dataNodeB.get('attributes'):
            if 'port' in dataNodeB['attributes']['locations'][0]:
                portB = dataNodeB['attributes']['locations'][0]['port']
            if 'shelf' in dataNodeB['attributes']['locations'][0]:
                shelfB = dataNodeB['attributes']['locations'][0]['shelf']
            if 'slot' in dataNodeB['attributes']['locations'][0]:
                slotB = dataNodeB['attributes']['locations'][0]['slot']
    else:
        logging.info('tpe data not found for ending node id :{}'.format(ending_node))
    if includedDataA:
        circuitName = getCircuitName(includedDataA, portA, shelfA, slotA, startNodeName, endNodeName)
        logging.debug("Circuit name retrieved with Start node port data: {}".format(circuitName))
    if not circuitName and includedDataB:
        circuitName = getCircuitName(includedDataB,portB, shelfB, slotB, startNodeName, endNodeName)
        logging.debug("Circuit name retrieved with End node port data: {}".format(circuitName))

    logging.info('L1 port info retrieved..')
    return portStartNode, portEndNode, circuitName

def getCircuitName(nodeData, port, shelf, slot, startNodeName, endNodeName):
    startNode = startNodeName.split("-")[0]
    endNode = endNodeName.split("-")[0]
    circuitName =''
    for item in nodeData:
        cirName = ''
        if circuitName:
            break
        if 'locations' in item['attributes'] and 'port' in item['attributes']['locations'][0] and 'shelf' in item['attributes']['locations'][0] and 'slot' in item['attributes']['locations'][0]:
            if item['attributes']['locations'][0]['port'] == port and item['attributes']['locations'][0]['shelf'] == shelf and item['attributes']['locations'][0]['slot'] == slot:
                if 'layerTerminations' in item['attributes']:
                    layerData = item['attributes']['layerTerminations']
                    for layers in layerData:
                        if layers.get('additionalAttributes'):
                            if 'userLabel' in layers['additionalAttributes']:
                                cirName = layers['additionalAttributes']['userLabel']
                                if (startNode in cirName) and (endNode in cirName) and ('OTU4' in cirName):
                                    circuitName = cirName
                                break
            else:
                continue
    return circuitName


def getLinkName(starting_node,startNodeName, endNodeName):
    nodeData = {}
    startNode = startNodeName.split("-")[0]
    endNode = endNodeName.split("-")[0]
    fileName = 'tpe_'+starting_node
    portDataStartNode = utils.open_file_load_data('jsongets/{}.json'.format(fileName))
    if portDataStartNode:
        if portDataStartNode.get('included'):
            nodeData = portDataStartNode['included']
    linkName =''
    for item in nodeData:
        linkNm = ''
        if linkName:
            break
        if 'userLabel' in item['attributes']:
            linkNm = item['attributes']['userLabel']
            if (startNode in linkNm) and (endNode in linkNm):
                # import pdb
                # pdb.set_trace()
                if 'OTU4' in linkNm:
                    linkName = linkNm.replace('OTU4','OM96')
                if 'GE100' in linkNm:
                    linkName = linkNm.replace('GE100','OM96')
                break
            else:
                continue
    if not linkName:
        linkName = 'I1001/OM96/'+startNode+'/'+endNode
    return linkName
