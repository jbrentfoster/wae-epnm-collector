# ===================================================
# ===================================================


# Stub in for the l3 code


# ===================================================
# ===================================================


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
            if node['attributes']['typeGroup'] == "Ciena6500" and match_object != None:
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
    l3nodesAll = utils.open_file_load_data('jsonfiles/l3nodes.json')
    for node in l3nodesAll:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
    l3links_list = []
    dupl_check = {}
    for l3nodes in l3nodesAll:
        networkId = l3nodes['id']
        fileName = 'fre_'+networkId+'.json'
        logging.debug('Filename :\n{}'.format(fileName))
        # import pdb
        # pdb.set_trace()
        with open('jsongets/'+fileName, 'rb') as f:
            thejson = f.read()
            f.close()    
        link_data = json.loads(thejson)
        if link_data.get('included'):
            included = link_data['included']
        # logging.debug(
        #     'This is the API response for the [included] field:\n{}'.format(included))

        # all_links_dict = utils.open_file_load_data('jsongets/all_links.json')
        # data = all_links_dict['data']
        # included = all_links_dict['included']

        # Making a dictionary w/ the l1node's id and wae_site_name as the key/value pairs for later use
        # # node_data = utils.open_file_load_data("jsonfiles/l3nodes.json")
        # # for node in node_data:
        # node_key_val['{}'.format(l3nodes['id'])] = l3nodes['attributes']['name']

        logging.debug(
            'This is the vaallue of len(included):\n{}'.format(len(included)))
        for i in range(len(included)):
            if included[i]['type'] == 'endPoints':
                if included[i]['id'][-1] == '1' and included[i].get('relationships').get('tpes'):
                    id1 = included[i]['relationships']['tpes']['data'][0]['id'][:36]
                if included[i+1]['id'][-1] == '2' and included[i+1].get('relationships').get('tpes'):
                    id2 = included[i+1]['relationships']['tpes']['data'][0]['id'][:36]
                # logging.debug('This is the value of ID1:\n{}'.format(id1))
                # logging.debug('This is the value of ID2:\n{}'.format(id2))
            else:
                break
            if 'network1' in id1:
                break
            new_obj = {}
            if id1 and id2:
                new_obj['name'] = included[i]['id'][:-2]
                if new_obj['name'] in dupl_check :
                    continue
                # Duplicate but okay for readability
                networkConstructA_id = id1
                networkConstructB_id = id2
                if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                    new_obj['l3nodeA'] = node_key_val[networkConstructA_id]
                    new_obj['l3nodeB'] = node_key_val[networkConstructB_id]
                else:
                    continue
                new_obj['description'] = new_obj['l3nodeA'] + \
                    '-' + new_obj['l3nodeB'] + '-' + str(i)
                dupl_check[new_obj['name']] = i
                l3links_list.append(new_obj)
    l3links_list = json.dumps(
        l3links_list, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug('These are the l3 links:\n{}'.format(l3links_list))
    with open('jsonfiles/l3links.json', 'wb') as f:
        f.write(l3links_list)

def get_l3_circuits(baseURL, cienauser, cienapassw, token):
    l3_circuit_list = []
    dupl_check = {}
    # Setting up the links and l3 nodes data for use later on
    l3nodesAll = utils.open_file_load_data('jsonfiles/l3nodes.json')
    l3nodes_dict = {val: 1 for node in l3nodesAll for (key, val) in node.items() if key == 'id'}
    for l3nodes in l3nodesAll:
        networkId = l3nodes['id']
        filename = 'fre_'+networkId+'.json'
        # filename = 'fre_0d5dfa44-202e-3b38-b78e-7ac8e463ae76.json'
        logging.debug('filename to retrieve circuit:\n{}'.format(filename))
        # all_links_dict = utils.open_file_load_data('jsongets/fre_c9386224-d384-3b6d-b8fc-9f286626d272.json')
        all_links_dict = utils.open_file_load_data('jsongets/'+filename)
        if all_links_dict.get('data'):
            data = all_links_dict['data']
        else:
            continue
        if all_links_dict.get('included'):
            included = all_links_dict['included']
        for obj in data:
            circuit_check = False
            # if obj.get('attributes').get('layerRate'):
            # circuit_check = True if obj['attributes']['layerRate'] != 'OMS' and obj['attributes']['layerRate'] != 'OTS' else False
            # Implemented the starting and ending l1 node check. Go into included and grab the network construct id and check if it's in the l3nodes_dict
            circuit_id = obj['id']
            # This block of code is faulty. It'll keep going and won't stop, expensive operation.
            for node in included:
                if node['type'] == 'endPoints' and node['id'][-1] == '1':
                    if node['id'][:-2] == circuit_id:
                        starting_node = node['relationships']['tpes']['data'][0]['id'][:36]
                if node['type'] == 'endPoints' and node['id'][-1] == '2':
                    if node['id'][:-2] == circuit_id:
                        ending_node = node['relationships']['tpes']['data'][0]['id'][:36]
                        break
            # l1_check = starting_node in l3nodes_dict and ending_node in l3nodes_dict

            # Adding temp check if starting node is not equal to ending node . NEED TO CHECK BACK
            l3_check = starting_node in l3nodes_dict and ending_node in l3nodes_dict and starting_node != ending_node

            # nodeid = l3nodes_dict.get('id')
            # if circuit_check and l3_check:
            if l3_check:
                # import pdb
                # pdb.set_trace()
                # and if so then make the call to get_l3_circuit() to get the supporting nodes
                link_list = collect.get_supporting_nodes(
                    circuit_id, baseURL, cienauser, cienapassw, token)
                # Check based on the returned nodes to see if they're valid l3 nodes
                supporting_link_check = False
                # import pdb
                # pdb.set_trace() 
                if link_list:
                    logging.debug(
                        'These are the link_list response:\n{}'.format(link_list))
                    for link_obj in link_list:
                        if link_obj['NodeA'] in l3nodes_dict and link_obj['NodeB'] in l3nodes_dict:
                            supporting_link_check = True
                        else:
                            supporting_link_check = False

                if supporting_link_check:
                    temp_obj = {
                        "Name": "",
                        "CircuitID": "",
                        "CircuitName": "",
                        "StartL3Node": "",
                        "EndL3Node": "",
                        "Channel": "",
                        "BW": 0,
                        "RsvpBW": 0,
                        "Status": "",
                        "Type": "",
                        "LayerRate": "",
                        "InterfaceName": "",
                        "Frequency": 0,
                        "Wavelength": 0,
                        "Ordered_Hops": []
                    }
                    # Checking for the node_key_val to be populated, and if not setting the l3node's id and name as the key/value pairs for later use
                    # Adding tto check id in all nodes as couple of id's are present in l3 nodes
                    if len(node_key_val) == 0:
                        node_data = utils.open_file_load_data(
                            "jsonfiles/all_nodes.json")
                        allNodesData = node_data['data']
                        for node in allNodesData:
                            node_key_val['{}'.format(
                                node['id'])] = node['attributes']['name']
                    # if len(node_key_val) == 0:
                    #     node_data = utils.open_file_load_data(
                    #         "jsonfiles/l3nodes.json")
                    #     for node in node_data:
                    #         node_key_val['{}'.format(
                    #             node['id'])] = node['attributes']['name']
                    starting_node_name = node_key_val['{}'.format(starting_node)]
                    ending_node_name = node_key_val['{}'.format(ending_node)]
                    temp_obj['Name'] = obj['attributes']['userLabel']
                    temp_obj['CircuitID'] = circuit_id
                    temp_obj['StartL3Node'] = starting_node_name
                    temp_obj['EndL3Node'] = ending_node_name
                    temp_obj['Type'] = obj['attributes']['serviceClass']
                    temp_obj['LayerRate'] = obj['attributes']['layerRate']
                    if obj.get('attributes').get('locations'):
                        temp_obj['InterfaceName'] = obj['attributes']['locations'][0]['interfaceName']
                    else:
                        temp_obj['InterfaceName'] = ''
                    if obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                        temp_obj['Frequency'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['frequency']
                    else:
                        temp_obj['Frequency'] = 0
                    if obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                        temp_obj['Wavelength'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['wavelength']
                    else:
                        temp_obj['Wavelength'] = 0
                    if obj.get('attributes').get('bandwidthTriggers') and obj.get('attributes').get('bandwidthTriggers').get('maxBW'):
                        temp_obj['BW'] = obj['attributes']['bandwidthTriggers']['maxBW']
                    else:
                        temp_obj['BW'] = 0
                    if obj.get('attributes').get('maxReservableBandwidth'):
                        temp_obj['RsvpBW'] = obj['attributes']['maxReservableBandwidth'][0]['capacitySize']['size']
                    else:
                        temp_obj['RsvpBW'] = 0
                    if obj.get('attributes').get('displayData').get('displayPhotonicSpectrumData'):
                        temp_obj['Channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel']
                    else:
                        temp_obj['Channel'] = ''
                    try:
                        # temp_obj['Channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel']
                        if obj.get('attributes').get('userLabel') == '':
                            if obj.get('attributes').get('linkLabel') == '':
                                temp_obj['CircuitName'] = 'Dummy_'+ circuit_id
                            else:
                                temp_obj['CircuitName'] = obj['attributes']['linkLabel']
                        else:
                            temp_obj['CircuitName'] = obj['attributes']['userLabel']
                    except:
                            temp_obj['CircuitName'] = 'Dummy_'+ circuit_id
                    if temp_obj['CircuitName'] in dupl_check:
                        continue
                    # Still not able to retrieve the affinity. As discussed colorGroups should cconsider as Affinity but I dont find any tpe / fre returned the param colorGroup. Need to check.
                    if obj.get('attributes').get('operationState'):
                        temp_obj['Status'] = obj['attributes']['operationState']
                    for link in link_list:
                        link['NodeA'] = node_key_val['{}'.format(link['NodeA'])]
                        link['NodeB'] = node_key_val['{}'.format(link['NodeB'])]
                    link_list.insert(0, {'Name': 'Starting Link', 'NodeA': '{}'.format(
                        starting_node_name), 'NodeB': '{}'.format(link_list[0]['NodeA'])})
                    link_list.append({'Name': 'Ending Link', 'NodeA': '{}'.format(
                        link_list[1]['NodeB']), 'NodeB': '{}'.format(ending_node_name)})
                    temp_obj['Ordered_Hops'] = link_list
                    #Temporary commenting to avoid duplicate error
                    if temp_obj['Name'] != 'THISISANULHLINEPORT':
                        l3_circuit_list.append(temp_obj)
                    dupl_check[temp_obj['Channel']] = temp_obj['Channel']
    # logging.debug(
    #     'These are the l3_circuit_list values**********:\n{}'.format(l3_circuit_list))
    if l3_circuit_list:
        # logging.debug(
        #     'These are the l3_circuit_list values:\n{}'.format(l3_circuit_list))
        l3_circuit_list = json.dumps(
            l3_circuit_list, sort_keys=True, indent=4, separators=(',', ': '))
        # logging.debug('These are the l3 circuits:\n{}'.format(l3_circuit_list))
        with open('jsonfiles/l3circuits.json', 'wb') as f:
            f.write(l3_circuit_list)
    # else:
    #     logging.debug(
    #         'These are the l3_circuit_list values EMPTY:\n{}'.format(l3_circuit_list))

