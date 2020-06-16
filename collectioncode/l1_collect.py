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

#Setting up the properties file
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
name = config['DEFAULT']['Site_name'].upper()
sitename_bucket = 'ExtraNodes'
node_key_val = {}

def get_all_nodes(baseURL, cienauser, cienapassw, token):
    uri = '/nsi/api/v6/networkConstructs?limit=300'
    URL = baseURL + uri
    data = utils.rest_get_json(URL, cienauser, cienapassw, token)
    #Saving the data for future use
    with open('jsonfiles/all_nodes.json', 'wb') as f:
        f.write(data)

def get_l1_nodes():
    data, node_list, site_list = '', [], []
    data = utils.open_file_load_data("jsonfiles/all_nodes.json")
    counter = 1

    for node in data['data']:
        if 'typeGroup' in node['attributes']:
            match_object = re.search('SHELF-([0-9]|1[0-9]|20)$', node['attributes']['accessIdentifier'])
            if node['attributes']['typeGroup'] == "Ciena6500" and match_object != None:
                node['longitude'] = 0
                node['latitude'] = 0
                if 'geoLocation' in node['attributes']:
                    node['longitude'] = node.get('attributes').get('geoLocation').get('longitude') or 0
                    node['latitude'] = node.get('attributes').get('geoLocation').get('latitude') or 0
                #Setting the site name, starting w/ the clli code check
                new_match_object = re.search(r"^\w{8}-", node['attributes']['name'])
                s_name = bool(node['attributes']['siteName'])

                if new_match_object != None:
                    node['wae_site_name'] = str(node['attributes']['name'])[:8]
                elif s_name and len(node['attributes']['siteName']) > 0:
                    node['wae_site_name'] = utils.normalize_sites('{}'.format(node['attributes']['siteName']))
                elif node['longitude'] != 0 and node['latitude'] != 0: 
                    node['wae_site_name'] = utils.normalize_sites('{}[{}]'.format(name, counter))
                    counter += 1
                else:
                    node['wae_site_name'] = utils.normalize_sites('{}'.format(sitename_bucket))
                node_list.append(node)

    node_list = json.dumps(node_list, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug('These are the L1 nodes:\n{}'.format(node_list))
    with open('jsonfiles/l1nodes.json', 'wb') as f:
        f.write(node_list)

    #Creating the sites.json file
    #for each node in node_list
    node_list = json.loads(node_list)
    dupl_check = {}
    for node in node_list:
        #Making sure no duplicates are in our sites file
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
        dupl_check[obj['name']] = 'Random_string'
        site_list.append(obj)

    site_list = json.dumps(site_list, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug('These are the sites:\n{}'.format(site_list))
    with open('jsonfiles/sites.json', 'wb') as f:
        f.write(site_list)

def get_l1_links(baseURL, cienauser, cienapassw, token):

    uri = "/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs%2Cplanned&limit=200&offset=0&searchFields=data.attributes.mgmtName%2Cdata.attributes.userLabel%2Cdata.attributes.nativeName%2Cdata.attributes.serviceClass%2Cdata.attributes.displayData.operationState%2Cdata.attributes.layerRate%2Cdata.attributes.layerRateQualifier%2Cdata.attributes.note%2Cdata.attributes.tpeLocations%2Cdata.attributes.neNames%2Cdata.attributes.displayData.adminState%2Cdata.attributes.displayData.intentLifeCyclePhaseString%2Cdata.attributes.displayData.intentDeploymentStateString%2Cdata.attributes.resilienceLevel%2Cdata.attributes.domainTypes%2Cdata.attributes.customerName%2Cdata.attributes.displayData.displayPhotonicSpectrumData.frequency%2Cdata.attributes.displayData.displayPhotonicSpectrumData.channel%2Cdata.attributes.displayData.displayPhotonicSpectrumData.wavelength%2Cdata.attributes.lqsData.fiber.measuredLoss%2Cdata.attributes.lqsData.fiber.modeledLoss%2Cdata.attributes.lqsData.fiber.modeledMargin%2Cdata.attributes.lqsData.fiber.method%2Cdata.attributes.lqsData.fiber.reconciled%2Cdata.attributes.description%2Cdata.attributes.tags&searchText=&serviceClass=Fiber%2COTU%2COSRP%20Line%2COSRP%20Link%2CROADM%20Line&sortBy=name"
    URL = baseURL + uri
    link_data = utils.rest_get_json(URL, cienauser, cienapassw, token)
    #Inserting this line for testing since the response is too large to print it
    with open('jsongets/all_links.json', 'wb') as f:
        f.write(link_data)
    link_data = json.loads(link_data)
    included = link_data['included']
    logging.debug('This is the API response for the [included] field:\n{}'.format(included))

    #Making a dictionary w/ the l1node's id and wae_site_name as the key/value pairs for later use
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
            new_obj['name'] = included[i]['id'][:-2]
            if new_obj['name'] in dupl_check or len(included[i]['relationships']) == 0 or len(included[i+1]['relationships']) == 0:
                continue
            #Duplicate but okay for readability
            networkConstructA_id = id1
            networkConstructB_id = id2
            if networkConstructA_id in node_key_val and networkConstructB_id in node_key_val:
                new_obj['l1nodeA'] = node_key_val[networkConstructA_id]
                new_obj['l1nodeB'] = node_key_val[networkConstructB_id]
            else: continue
            new_obj['description'] = new_obj['l1nodeA'] + '-' + new_obj['l1nodeB'] + '-' + str(i)
            dupl_check[new_obj['name']] = i
            l1links_list.append(new_obj)

    l1links_list = json.dumps(l1links_list, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug('These are the l1 links:\n{}'.format(l1links_list))
    with open('jsonfiles/l1links.json', 'wb') as f:
        f.write(l1links_list)

'''
#Generate the l1 circuits
#So i like this amendment to break the circuit generation into 2 parts, get_l1_circuit() and get_l1_circuits() coz otherwise the function would be too big

Example l1 circuit object from EPNM/NAUTILUS

{
    "CircuitID": "I1001/OTUC2/ALPRGAXV/NRCSGAHX",
    "StartL1Node": "ALPRGAXV-0110212A",
    "EndL1Node": "NRCSGAHX-0110800A",
    "Channel": "I1001/OTUC2/ALPRGAXV/NRCSGAHX",
    "BW": "200000",
    "status": "IN EFFECT",
    "Ordered_Hops": [
      {
        "Name": "I1001/OM96/ALPRGAXV/NRCSGAHX",
        "NodeA": "ALPRGAXV-0110212A",
        "NodeB": "NRCSGAHX-0110800A"
      }
    ]
}

Make the temp object w/ the l1 circuit info
Get the starting and ending nodes and verify that they're l1 nodes
If so then put them into the temp object
Get the supporting nodes from the get_l1_circuit() and put them into the temp object
I know that i'm changing up the logic, getting the info mainly from the get_l1_circuits() instead but it works better this way
'''

def get_l1_circuits(baseURL, cienauser, cienapassw, token):
    l1_circuit_list = []
    #Setting up the links and l1 nodes data for use later on
    l1nodes_dict = utils.open_file_load_data('jsonfiles/l1nodes.json')
    l1nodes_dict = {val: 1 for node in l1nodes_dict for (key, val) in node.items() if key == 'id'}
    all_links_dict = utils.open_file_load_data('jsongets/all_links.json')
    data = all_links_dict['data']
    included = all_links_dict['included']
   
    for obj in data:
        circuit_check = True if obj['attributes']['layerRate'] != 'OMS' and obj['attributes']['layerRate'] != 'OTS' else False
        #Implemented the starting and ending l1 node check. Go into included and grab the network construct id and check if it's in the l1nodes_dict
        circuit_id = obj['id']
        #This block of code is faulty. It'll keep going and won't stop, expensive operation.  
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
            #and if so then make the call to get_l1_circuit() to get the supporting nodes
            link_list = collect.get_supporting_nodes(circuit_id, baseURL, cienauser, cienapassw, token)
            #Check based on the returned nodes to see if they're valid l1 nodes
            supporting_link_check = False
            for link_obj in link_list:
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
                #Checking for the node_key_val to be populated, and if not setting the l1node's id and name as the key/value pairs for later use
                if len(node_key_val) == 0:
                    node_data = utils.open_file_load_data("jsonfiles/l1nodes.json")
                    for node in node_data:
                        node_key_val['{}'.format(node['id'])] = node['attributes']['name']
                starting_node_name = node_key_val['{}'.format(starting_node)]
                ending_node_name = node_key_val['{}'.format(ending_node)]        
                temp_obj['Name'] = obj['attributes']['userLabel']
                temp_obj['CircuitID'] = circuit_id
                temp_obj['StartL1Node'] = starting_node_name
                temp_obj['EndL1Node'] = ending_node_name
                #Setting the channel value. Unsure of what exactly the channel is in this situation so either setting it to the channel value that exists in the api data or the name value for now. 
                try:
                    temp_obj['Channel'] = obj['attributes']['displayData']['displayPhotonicSpectrumData'][0]['channel'] 
                except: 
                    temp_obj['Channel'] = obj['attributes']['userLabel']
                #Hmm how do i get the BW?? Perhaps i'll need to create some kind of chart and the BW is determined by the layer rate?
                temp_obj['status'] = obj['attributes']['operationState']
                for link in link_list:
                    link['NodeA'] = node_key_val['{}'.format(link['NodeA'])]
                    link['NodeB'] = node_key_val['{}'.format(link['NodeB'])]
                link_list.insert(0, {'Name': 'Starting Link', 'NodeA': '{}'.format(starting_node_name), 'NodeB': '{}'.format(link_list[0]['NodeA'])})
                link_list.append({'Name': 'Ending Link', 'NodeA': '{}'.format(link_list[1]['NodeB']), 'NodeB': '{}'.format(ending_node_name)})
                temp_obj['Ordered_Hops'] = link_list
                l1_circuit_list.append(temp_obj)
                
    l1_circuit_list = json.dumps(l1_circuit_list, sort_keys=True, indent=4, separators=(',', ': '))
    logging.debug('These are the l1 circuits:\n{}'.format(l1_circuit_list))
    with open('jsonfiles/l1circuits.json', 'wb') as f:
        f.write(l1_circuit_list)