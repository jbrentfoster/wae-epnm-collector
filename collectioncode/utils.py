import requests
import urllib3
import json
import xml.dom.minidom
import logging
import configparser
import threading
import collect
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)
config = configparser.ConfigParser(interpolation=None)
config.read('resources/config.ini')
timeout = config['DEFAULT']['Timeout_limit']
timeout_limit = float(timeout) if timeout.isnumeric() else None



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

################

#The circuit breaker pattern has been implemented
#Will need to add unit tests to the Ciena script to verify final funcitonality
#i.e. checking empty responses, timeouts, error responses etc. 

################
class Circuit_breaker:

    def __init__(self, failure_threshold = 3, timeout_limit = timeout_limit):
        self.failure_threshold = failure_threshold
        self.timeout_limit = timeout_limit
        self.reset_call = 20.2
        self.failed_tries = 0
        self.last_failure_time=0
        self.state="closed"

    def reset(self):
        self.failed_tries = 0
        self.last_failure_time = 0

    def get_state(self):
        if self.failed_tries >= self.failure_threshold and datetime.now() - self.last_failure_time > self.reset_call:
            self.state = "half-closed"
        elif self.failed_tries >= self.failure_threshold:
            self.state = "open"
        else: self.state = "closed"

    def record_failure(self):
        self.failed_tries += 1
        self.last_failure_time = datetime.now()

    def request(self, URL, cienauser, cienapassw, token):
        #Get the endpoint for the calls
        proxies = {
            "http": None,
            "https": None,
        }
        appformat = 'application/json'
        headers = {'content-type': appformat, 'accept': appformat, 'authorization': 'Bearer {}'.format(token)}
        data = {'username': cienauser, 'password': cienapassw}
        self.get_state()
        if self.state == "closed" or self.state == "half-closed":
            while self.failed_tries < self.failure_threshold:
                try:
                    check_not_empty = True
                    r = requests.get(URL, headers=headers, proxies=proxies, json=data, verify=False, timeout=self.timeout_limit, allow_redirects=True)
                    collect.thread_data.logger.debug('The API response for URL {} is:\n{}'.format(URL, json.dumps(r.json(), separators=(",",":"), indent=4)))
                    #Checking for empty responses
                    response_uni = json.dumps(r.json(), indent=2)
                    response = json.loads(response_uni)
                    length = len(response)
                    if length == 0 or length == 1:
                        key = response.keys()[0]
                        if len(response[key]) > 0:
                            pass
                        else: check_not_empty = False
                    if r.status_code == 200 and check_not_empty:
                        self.reset()
                        return response_uni
                    else:
                        raise ("HTTP status code: " + str(r.status_code))

                except Exception as err:
                    collect.thread_data.logger.error('Exception raised: ' + str(type(err)) + '\nURL: {}\n{}'.format(err.args, err.message))
                    self.record_failure()
                    if self.failed_tries >= self.failure_threshold:
                        temp = []
                        return json.dumps(temp)

        else: 
            collect.thread_data.logger.error('Exception raised: Circuit is open')
            raise("Circuit is open")

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
