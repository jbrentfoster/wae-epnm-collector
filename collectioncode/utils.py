import requests
import urllib3
import json
import errors
import xml.dom.minidom
import logging
import configparser
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)
config = configparser.ConfigParser(interpolation=None)
config.read('configs/config.ini')
timeout_limit = config['DEFAULT']['Timeout_limit']


def rest_get_json(baseURL, uri, user, password):
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/json'
    headers = {'content-type': appformat, 'accept': appformat}
    restURI = baseURL + uri
    try:
        r = requests.get(restURI, headers=headers, proxies=proxies, auth=(user, password), verify=False)
        logging.debug('The API response for URL {} is:\n{}'.format(restURI, json.dumps(r.json(), separators=(",",":"), indent=4)))
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2)
        else:
            raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
    except errors.InputError as err:
        logging.error('Exception raised: ' + str(type(err)) + '\nURL: {}\n{}'.format(err.expression, err.message))
        return

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

    def request(self, baseURL, uri, user, password):
        proxies = {
            "http": None,
            "https": None,
        }
        appformat = 'application/json'
        headers = {'content-type': appformat, 'accept': appformat}
        restURI = baseURL + uri
        self.get_state()
        if self.state == "closed" or self.state == "half-closed":
            while self.failed_tries < self.failure_threshold:
                try:
                    check_not_empty = True
                    r = requests.get(restURI, headers=headers, proxies=proxies, auth=(user, password), verify=False, timeout=self.timeout_limit)
                    logging.debug('The API response for URL {} is:\n{}'.format(restURI, json.dumps(r.json(), separators=(",",":"), indent=4)))
                    #Checking for empty responses
                    response_uni = json.dumps(r.json(), indent=2)
                    response = json.loads(response_uni)
                    length = len(response)
                    print(response, length)
                    if length == 0 or length == 1:
                        key = response.keys()[0]
                        print(len(response[key]))
                        if len(response[key]) > 0:
                            pass
                        else: check_not_empty = False
                        
                    if r.status_code == 200 and check_not_empty:
                        self.reset()
                        return response_uni
                    else:
                        raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
                except Exception as err:
                    logging.error('Exception raised: ' + str(type(err)) + '\nURL: {}\n{}'.format(err.args, err.message))
                    self.record_failure()
                    if self.failed_tries >= self.failure_threshold:
                        temp = []
                        return json.dumps(temp)

        else: 
            logging.error('Exception raised: Circuit is open')
            raise("Circuit is open")



def rest_get_xml(baseURL, uri, user, password):
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/xml'
    headers = {'content-type': appformat, 'accept': appformat}
    restURI = baseURL + uri
    try:
        r = requests.get(restURI, headers=headers, proxies=proxies, auth=(user, password), verify=False)
        # print "HTTP response code is: " + str(r.status_code)
        if r.status_code == 200:
            response_xml = xml.dom.minidom.parseString(r.content)
            return response_xml.toprettyxml()
        else:
            raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
    except errors.InputError as err:
        print "Exception raised: " + str(type(err))
        print err.expression
        print err.message
        return


def rest_post_xml(baseURL, uri, thexml, user, password):
    proxies = {
        "http": None,
        "https": None,
    }
    appformat = 'application/xml'
    headers = {'content-type': appformat, 'accept': appformat}
    restURI = baseURL + uri
    try:
        r = requests.post(restURI, data=thexml, headers=headers, proxies=proxies, auth=(user, password), verify=False)
        # print "HTTP response code is: " + str(r.status_code)
        if r.status_code == 200:
            response_xml = xml.dom.minidom.parseString(r.content)
            return response_xml.toprettyxml()
        else:
            raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
    except errors.InputError as err:
        print "Exception raised: " + str(type(err))
        print err.expression
        print err.message
        return

def rest_post_json(baseURL, uri, thejson, user, password):
        proxies = {
            "http": None,
            "https": None,
        }
        appformat = 'application/json'
        headers = {'content-type': appformat, 'accept': appformat}
        restURI = baseURL + uri
        try:
            r = requests.post(restURI, data=thejson, headers=headers, proxies=proxies, auth=(user, password),verify=False)
            logging.debug('The API response for URL {} is:\n{}'.format(restURI, json.dumps(r.json(), separators=(",",":"), indent=4)))
            if r.status_code == 200:
                return json.dumps(r.json(), indent=2)
            else:
                raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
        except errors.InputError as err:
            logging.error('Exception raised: ' + str(type(err)) + '\nURL: {}\n{}'.format(err.expression, err.message))
            return

# def cleanxml(thexml):
#     cleanedupXML = "".join([s for s in thexml.splitlines(True) if s.strip("\r\n\t")])
#     return cleanedupXML
