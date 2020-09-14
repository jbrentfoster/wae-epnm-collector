import time
import re
import json
import logging
import sys
import traceback
import utils
import configparser
import collect 
from multiprocessing.dummy import Pool as ThreadPool

# Setting up the properties file
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'
node_key_val = {}

def get_l1_nodes():
    data, node_list, site_list = '', [], []
    data = utils.open_file_load_data("jsonfiles/all_nodes.json")
    counter = 1

    for node in data['data']:
        if 'typeGroup' in node['attributes']:
            match_object = re.search(
                'SHELF-([0-9]|1[0-9]|20)$', node['attributes']['accessIdentifier'])
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

    node_list = json.dumps(node_list, sort_keys=True, indent=4, separators=(',', ': '))
    collect.thread_data.logger.debug('These are the L1 nodes:\n\n{}'.format(node_list))
    with open('jsonfiles/l1nodes.json', 'wb') as f:
        f.write(node_list)

    # Creating the sites.json file
    # for each node in node_list
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
        #Making the duplicate check valid
        dupl_check[obj['name']] = 'xxxxx'
        site_list.append(obj)

    site_list = json.dumps(site_list, sort_keys=True, indent=4, separators=(',', ': '))
    collect.thread_data.logger.debug('These are the L1 sites:\n\n{}'.format(site_list))
    with open('jsonfiles/l1_sites.json', 'wb') as f:
        f.write(site_list)


def get_l1_links(baseURL, cienauser, cienapassw, token):

    uri = "/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs%2Cplanned&limit=200&offset=0&searchFields=data.attributes.mgmtName%2Cdata.attributes.userLabel%2Cdata.attributes.nativeName%2Cdata.attributes.serviceClass%2Cdata.attributes.displayData.operationState%2Cdata.attributes.layerRate%2Cdata.attributes.layerRateQualifier%2Cdata.attributes.note%2Cdata.attributes.tpeLocations%2Cdata.attributes.neNames%2Cdata.attributes.displayData.adminState%2Cdata.attributes.displayData.intentLifeCyclePhaseString%2Cdata.attributes.displayData.intentDeploymentStateString%2Cdata.attributes.resilienceLevel%2Cdata.attributes.domainTypes%2Cdata.attributes.customerName%2Cdata.attributes.displayData.displayPhotonicSpectrumData.frequency%2Cdata.attributes.displayData.displayPhotonicSpectrumData.channel%2Cdata.attributes.displayData.displayPhotonicSpectrumData.wavelength%2Cdata.attributes.lqsData.fiber.measuredLoss%2Cdata.attributes.lqsData.fiber.modeledLoss%2Cdata.attributes.lqsData.fiber.modeledMargin%2Cdata.attributes.lqsData.fiber.method%2Cdata.attributes.lqsData.fiber.reconciled%2Cdata.attributes.description%2Cdata.attributes.tags&searchText=&serviceClass=Fiber%2COTU%2COSRP%20Line%2COSRP%20Link%2CROADM%20Line&sortBy=name"
    URL = baseURL + uri
    circuit_breaker1 = utils.Circuit_breaker()
    link_data = circuit_breaker1.request(URL, cienauser, cienapassw, token)
    #Inserting this line for testing since the response is too large to print it
    with open('jsongets/all_links.json', 'wb') as f:
        f.write(link_data)
    link_data = json.loads(link_data)
    included = link_data['included']
    collect.thread_data.logger.debug('This is the API response for the [included] field:\n{}'.format(included))

    # Making a dictionary w/ the l1node's id and wae_site_name as the key/value pairs for later use
    node_data = utils.open_file_load_data("jsonfiles/l1nodes.json")
    for node in node_data:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']

    l1links_list = []
    dupl_check = {}

    for i in range(len(included)):
        id1 = included[i]['relationships']['tpes']['data'][0]['id'][:36]
        id2 = included[i+1]['relationships']['tpes']['data'][0]['id'][:36]
        if 'network1' in id1:
            break
        new_obj = {}
        if included[i]['type'] == 'endPoints':
            if included[i]['id'][:-2] in dupl_check or len(included[i]['relationships']) == 0 or len(included[i+1]['relationships']) == 0:
                continue
            new_obj['name'] = included[i]['id'][:-2]
            #Duplicate but okay for readability
            networkConstructA_id = id1
            networkConstructB_id = id2
            if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                new_obj['l1nodeA'] = node_key_val[networkConstructA_id]
                new_obj['l1nodeB'] = node_key_val[networkConstructB_id]
            else:
                continue
            new_obj['description'] = new_obj['l1nodeA'] + \
                '-' + new_obj['l1nodeB'] + '-' + str(i)
            dupl_check[new_obj['name']] = i
            l1links_list.append(new_obj)

    l1links_list = json.dumps(l1links_list, sort_keys=True, indent=4, separators=(',', ': '))
    collect.thread_data.logger.debug('These are the l1 links:\n{}'.format(l1links_list))
    with open('jsonfiles/l1links.json', 'wb') as f:
        f.write(l1links_list)

def get_l1_circuits(baseURL, cienauser, cienapassw, token):
    l1_circuit_list = []
    # Setting up the links and l1 nodes data for use later on
    l1nodes_dict = utils.open_file_load_data('jsonfiles/l1nodes.json')
    l1nodes_dict = {val: 1 for node in l1nodes_dict for (
        key, val) in node.items() if key == 'id'}
    all_links_dict = utils.open_file_load_data('jsongets/all_links.json')
    data = all_links_dict['data']
    included = all_links_dict['included']
    #Making a dictionary w/ the l1node's id and wae_site_name as the key/value pairs for later use
    node_data = utils.open_file_load_data("jsonfiles/l1nodes.json")
    for node in node_data:
        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
   
    for obj in data:
        circuit_check = True if obj['attributes']['layerRate'] != 'OMS' and obj['attributes']['layerRate'] != 'OTS' else False
        # Implemented the starting and ending l1 node check. Go into included and grab the network construct id and check if it's in the l1nodes_dict
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
        l1_check = starting_node in l1nodes_dict and ending_node in l1nodes_dict
        if circuit_check and  l1_check:
            #and if so then make the call to get the supporting nodes
            link_list = collect.get_supporting_nodes(circuit_id, baseURL, cienauser, cienapassw, token)
            #Check based on the returned nodes to see if they're valid l1 nodes
            supporting_link_check = False
            for link_obj in link_list:
                #This check should work if link_list is an empty list as well
                if link_obj['NodeA'] in l1nodes_dict and link_obj['NodeB'] in l1nodes_dict:
                    supporting_link_check = True
                else: supporting_link_check = False
            if supporting_link_check: 
                temp_obj = {
                    "Name": "",
                    "CircuitID": "",
                    "StartL1Node": "",
                    "EndL1Node": "",
                    "Channel": "",
                    "BW": "0",
                    "status": "",
                    "Ordered_Hops": []
                }
                starting_node_name = node_key_val['{}'.format(starting_node)]
                ending_node_name = node_key_val['{}'.format(ending_node)]
                temp_obj['Name'] = obj['attributes']['userLabel']
                temp_obj['CircuitID'] = circuit_id
                temp_obj['StartL1Node'] = starting_node_name
                temp_obj['EndL1Node'] = ending_node_name
                # Setting the channel value. Unsure of what exactly the channel is in this situation so either setting it to the channel value that exists in the api data or the name value for now.
                try:
                    temp_obj['Channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel']
                except:
                    temp_obj['Channel'] = obj['attributes']['userLabel']
                #Code to get the BW if necessary here. Perhaps need to create some kind of chart and the BW is determined by the layer rate?
                temp_obj['status'] = obj['attributes']['operationState']
                for link in link_list:
                    link['NodeA'] = node_key_val['{}'.format(link['NodeA'])]
                    link['NodeB'] = node_key_val['{}'.format(link['NodeB'])]
                link_list.insert(0, {'Name': 'Starting Link', 'NodeA': '{}'.format(starting_node_name), 'NodeB': '{}'.format(link_list[0]['Name'])})
                link_list.append({'Name': 'Ending Link', 'NodeA': '{}'.format(link_list[-1]['Name']), 'NodeB': '{}'.format(ending_node_name)})
                temp_obj['Ordered_Hops'] = link_list
                l1_circuit_list.append(temp_obj)
                
    l1_circuit_list = json.dumps(l1_circuit_list, indent=4, separators=(',', ': '))
    collect.thread_data.logger.debug('These are the l1 circuits:\n{}'.format(l1_circuit_list))
    with open('jsonfiles/l1circuits.json', 'wb') as f:
        f.write(l1_circuit_list)

if __name__ == "__main__":
    baseURL, cienauser, cienapassw, token = 'https://165.122.92.244', 'ciscowae', 'Verizon123!', '<Change me to new api token>'
    get_l1_circuits(baseURL, cienauser, cienapassw, token)
