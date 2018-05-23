import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import errors
import xml.dom.minidom

urllib3.disable_warnings(InsecureRequestWarning)


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
        # print "HTTP response code is: " + str(r.status_code)
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2)
        else:
            raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
    except errors.InputError as err:
        print "Exception raised: " + str(type(err))
        print err.expression
        print err.message
        return


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
            r = requests.post(restURI, data=thejson, headers=headers, proxies=proxies, auth=(user, password),
                              verify=False)
            # print "HTTP response code is: " + str(r.status_code)
            if r.status_code == 200:
                return json.dumps(r.json(), indent=2)
            else:
                raise errors.InputError(restURI, "HTTP status code: " + str(r.status_code))
        except errors.InputError as err:
            print "Exception raised: " + str(type(err))
            print err.expression
            print err.message
            return

# def cleanxml(thexml):
#     cleanedupXML = "".join([s for s in thexml.splitlines(True) if s.strip("\r\n\t")])
#     return cleanedupXML
