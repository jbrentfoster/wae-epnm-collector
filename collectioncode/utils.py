import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import xml.dom.minidom
import logging

urllib3.disable_warnings(InsecureRequestWarning)



def rest_get_json(URL, cienauser, cienapassw, token):
    #Get the endpoint for the calls
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/json'
    headers = {'content-type': appformat, 'accept': appformat, 'authorization': 'Bearer {}'.format(token)}
    data = {'username': cienauser, 'password': cienapassw}

    try:
        #Use the request module to make the actual call
        r = requests.get(URL, headers=headers, proxies=proxies, json=data, verify=False)
        logging.debug('The API response for URL {} is:\n{}'.format(URL, json.dumps(r.json(), separators=(",",":"), indent=4)))
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2)
        else:
            r.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.error('Exception raised: ' + str(type(err)) + '\nURL: {}\nMessage: {}'.format(str(err), err.message))
        return

def open_file_load_data(file_name):
    with open(file_name, 'rb') as f:
        data = json.load(f)
    return data

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
    headers = {'content-type': appformat, 'accept': appformat, 'authorization': 'Bearer {}'.format(token)}
    data = {'username': cienauser, 'password': cienapassw}
    for id in id_list:
        restURI_tpe = baseURL + tpe + id
        restURI_fre = baseURL + fre + id
        
        r_tpe = requests.get(restURI_tpe, headers=headers, proxies=proxies, json=data, verify=False)
        r_fre = requests.get(restURI_fre, headers=headers, proxies=proxies, json=data, verify=False)

        if r_tpe.status_code == 200:
            with open('jsongets/{}.json'.format(id + '_tpe'), 'wb') as f:
                data = json.dumps(r_tpe.json(), indent=2)
                f.write(data)
        if r_fre.status_code == 200:
            with open('jsongets/{}.json'.format(id + '_fre'), 'wb') as f:
                data = json.dumps(r_fre.json(), indent=2)
                f.write(data)

#Helper function to sanitize strings
def normalize_sites(name):
    return name.strip().replace(' ', '')
