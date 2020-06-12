import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import argparse
from datetime import datetime
import configparser
import time
import os


urllib3.disable_warnings(InsecureRequestWarning)

def main():
    #Setting up the properties file
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini')

    # Get path for collection files from command line arguments
    parser = argparse.ArgumentParser(description='A WAE collection tool for Ciena')
    parser.add_argument('-i', '--ciena_ipaddr', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_ipaddr'],
                        help="Please provide the Ciena Server address for API calls")
    parser.add_argument('-u', '--ciena_user', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_user'],
                        help="Please provide the user name for the Ciena Server")
    parser.add_argument('-p', '--ciena_pass', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_pass'],
                        help="Please provide the password for the Ciena Server")
    args = parser.parse_args()

    cienaipaddr = args.ciena_ipaddr
    baseURL = 'https://' + cienaipaddr
    cienauser = args.ciena_user
    cienapassw = args.ciena_pass
    start_time = str(datetime.now().strftime('%Y-%m-%d__%H-%M-%S'))
    print('Start Time: {}'.format(start_time))
    

    tokenPath = '/tron/api/v1/tokens'
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/json'
    headers = {'Content-type': appformat, 'Accept': appformat}
    data = {'username': cienauser, 'password': cienapassw}
    resttokenURI = baseURL + tokenPath
    token = None

    if token == None:
        try:
            r = requests.post(resttokenURI, proxies=proxies, headers=headers, json=data, verify=False)
            if r.status_code == 201:
                token = json.dumps(r.json(), indent=2)
                print token
            else:
                r.raise_for_status()

        except requests.exceptions.RequestException as err:
            print "Exception raised: " + str(err)
            return 
    
    token = json.loads(token)
    token_string = token['token']

    #Get all the nodes
    get_all_nodes(baseURL, cienauser, cienapassw, token_string)

def get_all_nodes(baseURL, cienauser, cienapassw, token):
    # uri = '/nsi/api/v1/search/networkConstructs?resourceState=planned%2Cdiscovered%2CplannedAndDiscovered&limit=20'
    uri = '/nsi/api/v6/networkConstructs?limit=300'
    # uri = '/nsi/api/tpes?networkConstruct.id=310bae56-03fb-3d12-b9dc-e0a6f3ac4eeb'
    # uri = '/nsi/api/fres?layerRate=MPLS&type=link'
    # uri = '/nsi/api/v6/fres?group=infrastructure&networkConstruct.id=310bae56-03fb-3d12-b9dc-e0a6f3ac4eeb'
    # uri = "/nsi/api/v2/search/fres?include=planned&limit=0&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CintentLifeCyclePhaseString%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel%2ClqsData.status%2ClqsData.fiber.reconciled%2ClqsData.fiber.method&searchText=&serviceClass=Fiber%2COTU%2COSRP%20Line%2COSRP%20Link%2CROADM%20Line"
    # uri = '/nsi/api/v2/search/fres?include=expectations%2Ctpes%2CnetworkConstructs&limit=200&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CintentLifeCyclePhaseString%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel&networkConstruct.id=&offset=0&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportedByFreId=2415192029866680545&supportedByQualifier=all'
    # uri = '/nsi/api/v2/search/fres?limit=0&metaDataFields=serviceClass%2ClayerRate%2ClayerRateQualifier%2CintentLifeCyclePhaseString%2CdisplayOperationState%2CdisplayAdminState%2Cdirectionality%2CdomainTypes%2CresilienceLevel&serviceClass=EVC%2CEAccess%2CETransit%2CFiber%2CICL%2CIP%2CLAG%2CLLDP%2CTunnel%2COTU%2COSRP%20Line%2COSRP%20Link%2CPhotonic%2CROADM%20Line%2CSNC%2CSNCP%2CTDM%2CTransport%20Client%2CVLAN%2CRing&supportingFreId=2415192029866680545'
    # uri = '/nsi/api/v2/search/fres?id=3273775411947469989%2C-8370648649743722158%2C1338328350753312431%2C-5500017266127469792%2C7823756777504203244%2C9048522077166322071&limit=50'
    
    URL = baseURL + uri
    data = rest_get_json(URL, cienauser, cienapassw, token)
    #Saving the data for future use
    with open('jsongets/test_api.json', 'wb') as f:
        f.write(data)
    end_time = str(datetime.now().strftime('%Y-%m-%d__%H-%M-%S'))
    print('End Time: {}'.format(end_time))

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
        # print('The API response for URL {} is:\n{}'.format(URL, json.dumps(r.json(), separators=(",",":"), indent=4)))
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2)
        else:
            r.raise_for_status()
    except requests.exceptions.RequestException as err:
        print('Exception raised: ' + str(type(err)) + '\nURL: {}\nMessage: {}'.format(str(err), err.message))
        return

if __name__ == '__main__':
    main()