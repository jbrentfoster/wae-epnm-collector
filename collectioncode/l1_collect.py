import time
import re
import json
import logging
import sys
import csv
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
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'
node_key_val = {}

###### New method for l1 nodes based on l1 circuits ####################
def get_l1_nodes(baseURL, cienauser, cienapassw, token, state_or_states_list):
    logging.info('Retrieve L1 Nodes')
    data, node_list, l1data = '', [], {}
    nodesData = utils.getAllNodesForStates(state_or_states_list)
    for node in nodesData:
        l1fredata = get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list, node['id'])
        if 'data' in l1fredata:
            l1data = l1fredata['data']
        if l1data:
            if 'typeGroup' in node['attributes']:
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
        link_data = get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list, networkId)

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
            layer_key_val['{}'.format(links['id'])] = links['attributes']['layerRate']
        for i in range(len(included)):
            val = i+1
            linkName = ''
            if val < len(included):
                if included[i]['id'][:-2] in layer_key_val.keys():
                    layerRate = layer_key_val[included[i]['id'][:-2]]
                else:
                    layerRate = ''
                logging.debug('Layer Rate is :{}'.format(layerRate))
                logging.debug('Network id is :{}'.format(networkId))
                # Checking if type is endpoint and layer rate should be 'OMS' for L1 links
                if included[i]['type'] == 'endPoints':
                    logging.debug(
                        'OMS / OTS include id is :{}'.format(included[i]['id']))
                    if included[i]['id'][-1] == '1' and included[i].get('relationships').get('tpes'):
                        networkConstructA_id = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                        nodeAid = included[i]['relationships']['tpes']['data'][0]['id']
                    if included[i+1]['id'][-1] == '2' and included[i+1].get('relationships').get('tpes'):
                        networkConstructB_id = included[i+1]['relationships']['tpes']['data'][0]['id'][:36]
                        nodeBid = included[i+1]['relationships']['tpes']['data'][0]['id']
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
                    if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                        nodeA = node_key_val[networkConstructA_id]
                        nodeB = node_key_val[networkConstructB_id]
                    else:
                        continue
                    # Retrive port details for each node
                    portNodeA, portNodeB, circuitName = getPortDetails(baseURL, cienauser, cienapassw, token, networkConstructA_id, nodeAid, nodeA, networkConstructB_id, nodeBid, nodeB)
                    # Retrieve link name data
                    if portNodeA and portNodeB and nodeA and nodeB:
                        linkName = getLinkName(portNodeA.split('-',1)[1], portNodeB.split('-',1)[1], nodeA.split('-',1)[0], nodeB.split('-',1)[0])
                    logging.info("Link Name is########: {}".format(linkName))
                    if linkName and len(linkName.split('/')) > 2:
                        if linkName.split('/')[2] == nodeA.split('-')[0]:
                            new_obj['l1nodeA'] = nodeA
                            new_obj['l1nodeB'] = nodeB
                        elif linkName.split('/')[2] == nodeB.split('-')[0]:
                            new_obj['l1nodeA'] = nodeB
                            new_obj['l1nodeB'] = nodeA
                        else:
                            new_obj['l1nodeA'] = nodeA
                            new_obj['l1nodeB'] = nodeB
                        # Check if userlable field populated then populate circuit name otherwise populate with Dummy followed by linkid
                        circuitname = linkname_key_val[new_obj['linkid']]
                        if not circuitName:
                            new_obj['circuitName'] = 'Dummy_'+'_'+new_obj['linkid']
                        new_obj['description'] = new_obj['l1nodeA'] + '-' + new_obj['l1nodeB'] + '-' + str(i)
                        new_obj['portA'] = portNodeA.split('-',1)[1]
                        new_obj['portB'] = portNodeB.split('-',1)[1]
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

def get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list, networkConstrId):
    logging.info('Retrieving L1 links data from MCP..')
    logging.debug(
        'Retrieve L1 links data for nodes belongs to list of states:')
    logging.debug('networkConstrId:\n{}'.format(networkConstrId))
    incomplete, jsonmerged, jsonaddition = True, {}, {}
    # Priv retrieving data for OMS , OTS and OTU's  (ORIGINAL QUERY: COMMENT TEMPRARY)
    # uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=ROADM%20Line%2C%20Fiber%2COTU&limit=1000&networkConstruct.id='
    ########### Query to retrieve l1 links data
    uri = '/nsi/api/search/fres?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&layerRate=OMS%2COTS%2COTU4%2COTUCn&serviceClass=SNC%2CROADM%20Line%2CPhotonic%2CFiber%2COTU&limit=1000&networkConstruct.id='

    URL = baseURL + uri + networkConstrId
    logging.debug('URL:\n{}'.format(URL))
    while incomplete:
        portData = utils.rest_get_json(URL, cienauser, cienapassw, token)
        try:
            jsonaddition = json.loads(portData)
        except ValueError:
            if 'HTTP status code: 401' in portData:
                logging.debug("get L1 link API returned Unauthozied error: Retrying with new token for network construct id : {}".format(networkConstrId))
                tokenString = collect.getToken(baseURL, cienauser, cienapassw)
                portData = utils.rest_get_json(URL, cienauser, cienapassw, tokenString)
                try:
                    jsonaddition = json.loads(portData)
                except ValueError:
                    logging.debug("get L1 link API returned Unauthozied error with new token for network construct id : {}".format(networkConstrId))
            elif 'HTTP status code: 500' in portData:
                logging.debug("get L1 link API returned 500 Intrenal Server error for network construct id : {}".format(networkConstrId))
                incomplete = False
            else:
                logging.debug("get L1 link API didn't return the valid JSON response for network construct id : {}".format(networkConstrId))
                incomplete = False
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

    return jsonmerged


def get_l1_circuits(baseURL, cienauser, cienapassw, token, state_or_states_list):
    logging.info('Generating L1 Circuits...')
    l1_circuit_list, dupl_check, links_key_val= [], {}, {}
    # Setting up the links and l1 nodes data for use later on
    l1nodesAll = utils.open_file_load_data('jsonfiles/l1nodes.json')
    l1nodes_dict = {val: 1 for node in l1nodesAll for (
        key, val) in node.items() if key == 'id'}
    for node in l1nodesAll:
        node_key_val['{}'.format(
            node['id'])] = node['attributes']['displayData']['displayName']
    # Retrieve link names for link id
    l1linksAll = utils.open_file_load_data('jsonfiles/l1links.json')
    for links in l1linksAll:
        links_key_val['{}'.format(links['linkid'])] = links['linkname']
    for l1nodes in l1nodesAll:
        # linkname_key_val = {}
        networkId = l1nodes['id']
        all_links_dict = get_l1_links_data(baseURL, cienauser, cienapassw, token, state_or_states_list, networkId)
        if all_links_dict.get('data'):
            data = all_links_dict['data']
        else:
            logging.debug(
                'There is no FRE data for network construct id to build circuits:{}'.format(networkId))
            continue
        if all_links_dict.get('included'):
            included = all_links_dict['included']
        for obj in data:
            circuit_id = obj['id']
            logging.debug('Circuit id is :\n{}'.format(circuit_id))
            layerRate = obj['attributes']['layerRate']
            logging.debug('layerRate is :\n{}'.format(layerRate))

            if ('OTU' not in obj['attributes']['layerRate']):
                logging.debug('This layerRate should not process for L1 Circuits:\n{}'.format(layerRate)+' for circuit id :{}'.format(circuit_id))

            if ('OTU' not in obj['attributes']['layerRate']):
                continue

            for node in included:
                if node['type'] == 'endPoints' and node['id'][-1] == '1':
                    if node['id'][:-2] == circuit_id:
                        start_node = node['relationships']['tpes']['data'][0]['id'][:36]
                        startNodeId = node['relationships']['tpes']['data'][0]['id']
                if node['type'] == 'endPoints' and node['id'][-1] == '2':
                    if node['id'][:-2] == circuit_id:
                        end_node = node['relationships']['tpes']['data'][0]['id'][:36]
                        endNodeId = node['relationships']['tpes']['data'][0]['id']
                        break

            # check if starting node is not equal to ending node .
            l1_check = start_node in l1nodes_dict and end_node in l1nodes_dict and start_node != end_node
            if l1_check:
                logging.debug(
                    ' Retrieve supporting nodes for  circuit id: {}'.format(circuit_id))
                logging.debug('Token sending to Get Supporting Nodes ..'+token)
                link_list = collect.get_supporting_nodes(
                    circuit_id, baseURL, cienauser, cienapassw, token)
                # Check based on the returned nodes to see if they're valid l1 nodes
                supporting_link_check = True

                if supporting_link_check:
                    terminationNodeA, terminationNodeB, terminationList = {}, {}, []
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
                        "L1_Hops": [],
                        "termination-points":[]
                    }
                    start_node_name = node_key_val['{}'.format(
                        start_node)]
                    end_node_name = node_key_val['{}'.format(end_node)]
                    portStartNode, portEndNode, circuitName = getPortDetails(baseURL, cienauser, cienapassw, token, start_node, startNodeId, start_node_name, end_node, endNodeId, end_node_name)
                    if circuitName in dupl_check:
                        continue
                    if circuitName:
                        temp_obj['circuitName'] = circuitName
                    else:
                        circuitName = 'Dummy_' + circuit_id
                        temp_obj['circuitName'] = circuitName
                    temp_obj['circuitID'] = circuit_id
                    if '/' in circuitName:
                        if circuitName.split('/')[2] == start_node_name.split('-')[0]:
                            nodea = start_node_name
                            porta = portStartNode
                            nodeb = end_node_name
                            portb = portEndNode
                        elif circuitName.split('/')[2] == end_node_name.split('-')[0]:
                            nodea = end_node_name
                            porta = portEndNode
                            nodeb = start_node_name
                            portb = portStartNode
                    else:
                        nodea = start_node_name
                        porta = portStartNode
                        nodeb = end_node_name
                        portb = portEndNode
                    temp_obj['portStartNode'] = porta
                    temp_obj['portEndNode'] = portb
                    terminationNodeA['node'] = nodea
                    terminationNodeA['port'] = porta
                    terminationNodeB['node'] = nodeb
                    terminationNodeB['port'] = portb
                    if obj.get('attributes').get('displayData') and obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                        if 'wavelength' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['wavelength'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['wavelength']
                        if 'frequency' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['frequency'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['frequency']
                        if 'channel' in obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                            temp_obj['channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel']

                    temp_obj['status'] = obj['attributes']['operationState']
                    dupl_link_check = {}
                    if link_list:
                        i = 0
                        linkname = ''
                        for link in link_list:
                            nodea = node_key_val['{}'.format(link['nodeA'])]
                            nodeb = node_key_val['{}'.format(link['nodeB'])]
                            linkname = retrieveLinkName(nodea, nodeb)
                            logging.debug("Retrieved link name is : {}".format(linkname))
                            if not linkname:
                                linkname = nodea + '_' + nodeb + '-' + str(i)
                            if linkname in dupl_link_check:
                                continue
                            if '/' in linkname and len(linkname.split('/')) > 2:
                                if nodea.split('-')[0] == linkname.split('/')[2]:
                                    link['nodeA'] = nodea
                                    link['nodeB'] = nodeb
                                elif nodeb.split('-')[0] == linkname.split('/')[2]:
                                    link['nodeA'] = nodeb
                                    link['nodeB'] = nodea
                                else:
                                    link['nodeA'] = nodea
                                    link['nodeB'] = nodeb
                            else:
                                # logging.debug("This is dummy link name : {}".format(linkname))
                                link['nodeA'] = nodea
                                link['nodeB'] = nodeb
                            i += 1
                            link['linkname'] = linkname
                            dupl_link_check[link['linkname']] = linkname
                        l1hopslist = []
                        for link in link_list:
                            if 'linkname' in link:
                                l1hopslist.append(link)
                            else:
                                continue
                        terminationList.append(terminationNodeA)
                        terminationList.append(terminationNodeB)
                        temp_obj['termination-points'] = terminationList
                        temp_obj['L1_Hops'] = l1hopslist
                    if temp_obj['circuitName'] != 'THISISANULHLINEPORT':
                        l1_circuit_list.append(temp_obj)
                    dupl_check[temp_obj['circuitName']] = temp_obj['circuitName']
    # if l1_circuit_list:
    l1_circuit_list = json.dumps(
        l1_circuit_list, sort_keys=True, indent=4, separators=(',', ': '))
    with open('jsonfiles/l1circuits.json', 'wb') as f:
        f.write(l1_circuit_list)
        f.close()
    logging.info('L1 Circuits generated..')
    logging.info('Reordering L1 hops for l1 circuits')
    reorderl1hops_l1circuits()
    logging.info('L1 hops reordering completed')

def returnorderedlist(firstnode, l1hops):
    l1hopsordered = []
    # hopa = firstnode
    hopa = ""
    hopb = ""
    completed = False
    loopcount = 0
    while not completed:
        if len(l1hops) == 0: completed = True
        for hop in l1hops:
            if len(hop) != 2:
                logging.debug("Invalid L1 hop!  Could not process L1 hops!")
                return None
            elif hop[0].split('-')[0] == firstnode or hop[1].split('-')[0] == firstnode:
                l1hopsordered.insert(0, hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif (hopa == hop[0] or hopb == hop[1]) or (hopa == hop[1] or hopb == hop[0]):
                l1hopsordered.append(hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif loopcount > 200:
                logging.debug("Could not process L1 hops!")
                return None
            loopcount += 1
    return l1hopsordered

def reorderl1hops_l1circuits():
    with open("jsonfiles/l1circuits.json", 'rb') as f:
        l1circuits = json.load(f)
        f.close()

    for l1circuit in l1circuits:
        if 'L1_Hops' in l1circuit:
            l1hops = []
            circuitName = l1circuit['circuitName']
            for hops in l1circuit['L1_Hops']:
                nodelist = []
                nodelist.append(hops['nodeA'])
                nodelist.append(hops['nodeB'])
                l1hops.append(nodelist)
            if len(l1circuit.get('termination-points')) > 0:
                ref_node = l1circuit['termination-points'][0]['node']
                l1hopsordered = returnorderedlist(ref_node.split('-')[0], l1hops)
                if l1hopsordered == None:
                    logging.debug("Error generating ordered L1 hops for circuitName=" + circuitName)
                    logging.debug(
                        "Removing L1 hops from this link.  Check this circuitName and debug with if necessary.")
                    l1circuit.pop('L1_Hops')
                    continue
            
                tmphops = []
                for hop in l1hopsordered:
                    nodes = {}
                    nodes['nodeA'] = hop[0]
                    nodes['nodeB'] = hop[1]
                    for l1circuithop in l1circuit['L1_Hops']:
                        if l1circuithop['nodeA'] == nodes['nodeA'] and l1circuithop['nodeB'] == nodes['nodeB']:
                            nodes['linkname'] = l1circuithop['linkname'] 
                    tmphops.append(nodes)

                l1circuit['Ordered L1 Hops'] = tmphops
                l1circuit.pop('L1_Hops')
                logging.debug( "next L1 hop...")
            else:
                tmphops = []
                l1circuit['Ordered L1 Hops'] = tmphops
                l1circuit.pop('L1_Hops')
    with open("jsonfiles/l1circuitsfinal.json", "wb") as f:
        f.write(json.dumps(l1circuits, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def retrieveLinkName(nodea, nodeb):
    linkname = ''
    # Retrieve link names 
    logging.debug("Link name to retrieve for nodes : {}{}".format(nodea, nodeb))
    l1linksAll = utils.open_file_load_data('jsonfiles/l1links.json')
    linkdata = next((items for items in l1linksAll if (items['l1nodeA'] == nodea and items['l1nodeB'] == nodeb) or (items['l1nodeA'] == nodeb and items['l1nodeB'] == nodea)),None)
    if linkdata and linkname is not 'None':
        linkname = linkdata['linkname']
    return linkname

def getPortDetails(baseURL, cienauser, cienapassw, token, start_node, startNodeId, startNodeName, end_node, endNodeId, endNodeName):
    logging.info('Retrieve port info for L1 circuits')
    circuitName, portStartNode, portEndNode = '', '', ''
    dataStartNode, dataEndNode, includedDataA, includedDataB  = {}, {}, {}, {}
    portDataNodeA = collect.get_ports(baseURL, cienauser, cienapassw, token, start_node,startNodeId)
    if portDataNodeA:
        if portDataNodeA.get('included'):
            includedDataA = portDataNodeA['included']
        if portDataNodeA.get('data'):
            dataStartNode = portDataNodeA['data']
        dataNodeA = next(
            items for items in dataStartNode if items['id'] == startNodeId)
        portStartNode = dataNodeA['attributes']['nativeName']
        if 'locations' in dataNodeA.get('attributes'):
            if 'port' in dataNodeA['attributes']['locations'][0]:
                portA = dataNodeA['attributes']['locations'][0]['port']
            if 'shelf' in dataNodeA['attributes']['locations'][0]:
                shelfA = dataNodeA['attributes']['locations'][0]['shelf']
            if 'slot' in dataNodeA['attributes']['locations'][0]:
                slotA = dataNodeA['attributes']['locations'][0]['slot']
    else:
        logging.info('tpe data not found for starting node id :{}'.format(start_node))
    # Retrieve port data for end node
    portDataNodeB = collect.get_ports(baseURL, cienauser, cienapassw, token, end_node,endNodeId)
    if portDataNodeB:
        if portDataNodeB.get('included'):
            includedDataB = portDataNodeB['included']
        if portDataNodeB.get('data'):
            dataEndNode = portDataNodeB['data']
        dataNodeB = next(
            items for items in dataEndNode if items['id'] == endNodeId)
        portEndNode = dataNodeB['attributes']['nativeName']
        if 'locations' in dataNodeB.get('attributes'):
            if 'port' in dataNodeB['attributes']['locations'][0]:
                portB = dataNodeB['attributes']['locations'][0]['port']
            if 'shelf' in dataNodeB['attributes']['locations'][0]:
                shelfB = dataNodeB['attributes']['locations'][0]['shelf']
            if 'slot' in dataNodeB['attributes']['locations'][0]:
                slotB = dataNodeB['attributes']['locations'][0]['slot']
    else:
        logging.info('tpe data not fou for ending node id :{}'.format(end_node))
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

def getLinkName(portNameA, portNameB, startNode, endNode):
    linkName = ''
    linkNamesData = csv.DictReader(open('resources/l1linknames.csv'))
    for row in linkNamesData:
        if ((portNameA in row['A_PORT_AID']) and (startNode in row['TRAIL_NAME']) and (endNode in row['TRAIL_NAME'])):
            linkName = row['TRAIL_NAME']
            break
        else:
            if ((portNameB in row['A_PORT_AID']) and (startNode in row['TRAIL_NAME']) and (endNode in row['TRAIL_NAME'])):
                linkName = row['TRAIL_NAME']
                break
    return linkName
    
if __name__ == "__main__":
    ########################################

    reorderl1hops_l1circuits()

