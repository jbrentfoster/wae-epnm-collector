import json
import errors
import urllib3
import logging
import requests
import xml.dom.minidom
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def rest_get_json(URL, cienauser, cienapassw, token):
    # Get the endpoint for the calls
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/json'
    headers = {'content-type': appformat, 'accept': appformat,
               'authorization': 'Bearer {}'.format(token)}
    data = {'username': cienauser, 'password': cienapassw}

    try:
        # Use the request module to make the actual call
        r = requests.get(URL, headers=headers, proxies=proxies,
                         json=data, verify=False)
        # logging.debug('The API response for URL {} is:\n{}'.format(URL, json.dumps(r.json(), separators=(",",":"), indent=4)))
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2)
        else:
            raise errors.InputError(
                URL, "HTTP status code: " + str(r.status_code))
    except errors.InputError as err:
        logging.error('Exception raised: ' + str(type(err)) +
                      '\nURL: {}\nMessage: {}'.format(str(err), err.message))
        return

# Helper function to load json data
def open_file_load_data(file_name):
    with open(file_name, 'rb') as f:
        data = json.load(f)
        f.close()
    return data

# Helper function to get State Nodes data
def getStateNodes(state_or_states_list):
    allNodes = open_file_load_data("jsonfiles/all_nodes.json")
    allnodesData = allNodes['data']
    nodesData = {}
    for node in allnodesData:
        if len(state_or_states_list) > 0:
            if node['attributes']['name'][4:6] in state_or_states_list:
                nodesData['{}'.format(node['id'])] = node['attributes']['name']
        else:
            nodesData['{}'.format(node['id'])] = node['attributes']['name']
    return nodesData

# Helper function to get Nodes data
def getNodes():
    allNodes = open_file_load_data("jsonfiles/all_nodes.json")
    allnodesData = allNodes['data']
    nodesData = {}
    for node in allnodesData:
        nodesData['{}'.format(node['id'])] = node['attributes']['name']
    return nodesData


# Helper function to merge API returned JSON data
def merge(a, b):
    # function to merge Json's
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


def rest_get_tpe_fre_json(baseURL, cienauser, cienapassw, token):
    data, id_list = '', []
    # with  open('jsongets/new_6500.json', 'rb') as f:
    #     data = json.loads(f.read())
    data = open_file_load_data("jsongets/new_6500.json")

    for node in data['data']:
        if 'typeGroup' in node['attributes']:
            if node['attributes']['typeGroup'] == "Ciena6500":
                id_list.append(node['id'])

    proxies = {
        "http": None,
        "https": None,
    }
    tpe = '/nsi/api/tpes?networkConstruct.id='
    fre = '/nsi/api/fres?networkConstruct.id='
    appformat = 'application/json'
    headers = {'content-type': appformat, 'accept': appformat,
               'authorization': 'Bearer {}'.format(token)}
    data = {'username': cienauser, 'password': cienapassw}
    for id in id_list:
        restURI_tpe = baseURL + tpe + id
        restURI_fre = baseURL + fre + id

        r_tpe = requests.get(restURI_tpe, headers=headers,
                             proxies=proxies, json=data, verify=False)
        r_fre = requests.get(restURI_fre, headers=headers,
                             proxies=proxies, json=data, verify=False)

        if r_tpe.status_code == 200:
            with open('jsongets/{}.json'.format(id + '_tpe'), 'wb') as f:
                data = json.dumps(r_tpe.json(), indent=2)
                f.write(data)
        if r_fre.status_code == 200:
            with open('jsongets/{}.json'.format(id + '_fre'), 'wb') as f:
                data = json.dumps(r_fre.json(), indent=2)
                f.write(data)

# Helper function to sanitize strings
def normalize_sites(name):
    return name.strip().replace(' ', '')


# Helper function to retrieve Site names
def getSiteName(longi, lat):
    with open('jsonfiles/sites.json', 'rb') as f:
        thejson = json.load(f)
    data = next(
        (item for item in thejson if item['longitude'] == longi and item['latitude'] == lat), None)
    siteName = normalize_sites(
        '{}'.format(data['name']))
    logging.debug('site name is '+siteName)
    return siteName

# Helper function to get all l3 nodes
def getl3nodes():
    with open("jsonfiles/l3linksall.json", 'rb') as f:
        l3linksdict = json.load(f)
    l3nodes = []
    for k1, v1 in l3linksdict.items():
        tmpnode = {'Name': k1}
        l3nodes.append(tmpnode)
    return l3nodes, l3linksdict
