import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import xml.dom.minidom
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor as Threadpool
import configparser
import logging
from datetime import datetime
import time
import os
import distutils.dir_util
from distutils.dir_util import remove_tree
from distutils.dir_util import mkpath
import com.cisco.wae.design
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import SiteRecord
from collectioncode import collect
from waecode import planbuild, l1_planbuild, l3_planbuild
from pbkdf2 import PBKDF2
from Crypto.Cipher import AES
from Crypto import Random
import base64


urllib3.disable_warnings(InsecureRequestWarning)


def main():
    # Setting up the properties file
    config = configparser.ConfigParser(interpolation=None)
    config.read('resources/config.ini')

    # Getting inputs for the script from cli args
    parser = argparse.ArgumentParser(
        description='A WAE collection tool for Ciena')
    parser.add_argument('-a', '--archive_root', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Archive_root'],
                        help='Please provide the local path to your archive directory')
    parser.add_argument('-i', '--ciena_ipaddr', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_ipaddr'],
                        help="Please provide the Ciena Server address for API calls")
    parser.add_argument('-u', '--ciena_user', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_user'],
                        help="Please provide the user name for the Ciena Server")
    parser.add_argument('-p', '--ciena_pass', metavar='N', type=str, nargs='?', default=config['DEFAULT']['CIENA_pass'],
                        help="Please provide the password for the Ciena Server")
    # parser.add_argument('-ph', '--phases', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Phases'],
    #                     help="List of the collection phases to run(1-6), example '1356'")
    parser.add_argument('-l', '--logging', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Logging'],
                        help="Add this flag to set the logging level.")
    parser.add_argument('-b', '--build_plan', action='store_true',
                        help="Add this flag to build the plan file.")
    parser.add_argument('-d', '--delete_previous', action='store_true',
                        help="Add this flag to delete previous collection files.")
    args = parser.parse_args()

    cienaipaddr = args.ciena_ipaddr
    baseURL = 'https://' + cienaipaddr
    cienauser = args.ciena_user
    cienapassw = args.ciena_pass
    encryption_check = 'enCrYpted'
    # Decrypting the Ciena password for later use
    if cienapassw.startswith(encryption_check):
        encoded_pb_key = config['DEFAULT']['CIENA_key']
        pb_key = base64.b64decode(encoded_pb_key)
        decoded_str = base64.b64decode(cienapassw[len(encryption_check):])
        iv = decoded_str[:16]
        pb_key_check = decoded_str[-32:]
        if pb_key != pb_key_check:
            raise Exception('Incorrect password')
        cipher = AES.new(pb_key, AES.MODE_CFB, iv)
        password = cipher.decrypt(decoded_str[16:-32])
        cienapassw = password

    current_time = str(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    archive_root = args.archive_root + '/captures/' + current_time
    planfiles_root = args.archive_root + '/planfiles/'
    start_time = time.time()
    build_plan = args.build_plan
    delete_previous = args.delete_previous
    logging_level = args.logging.upper()

    # Setting up the main log file
    logFormatter = logging.Formatter('%(levelname)s:  %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.level = eval('logging.{}'.format(logging_level))

    log_file_name = 'collection-' + current_time + '.log'
    fileHandler = logging.FileHandler(filename=log_file_name)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    logging.info("Collection start time is " + current_time)
    logging.debug("Archive root is: {}".format(args.archive_root))
    logging.debug("Ciena ip address is: {}".format(args.ciena_ipaddr))
    logging.debug("Ciena user is: {}".format(args.ciena_user))
    # logging.debug("Phases is: {}".format(args.phases))
    # Delete all output files
    if delete_previous:
        logging.info("Cleaning files from last collection...")
        try:
            remove_tree('jsonfiles')
            remove_tree('jsongets')

        except Exception as err:
            logging.info("No files to cleanup...")
        # Recreate output directories
        mkpath('jsonfiles')
        mkpath('jsongets')
        mkpath(planfiles_root)
    else:
        # Create path for archive root and loggger
        mkpath(archive_root)
        mkpath(planfiles_root)
        mkpath('jsonfiles')
        mkpath('jsongets')
        logger = create_log('collection', logging_level, archive_root)

        logging.info(
            "Keeping collection files from previous collection, building plan file only...")

    # Create a service to be used by this script
    conn = com.cisco.wae.design.ServiceConnectionManager.newService()

    cwd = os.getcwd()
    fileName = os.path.join(cwd, 'planfiles/blank.pln')
    plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

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
            r = requests.post(resttokenURI, proxies=proxies,
                              headers=headers, json=data, verify=False)
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

    # Get all the nodes
    collect.get_all_nodes(baseURL, cienauser, cienapassw, token_string)

    # Get all the l1nodes
    collect.get_l1_nodes()

    # Get all the l1 links
    collect.get_l1_links(baseURL, cienauser, cienapassw, token_string)

    # Code to get the l1 circuits
    collect.get_l1_circuits(baseURL, cienauser, cienapassw, token_string)

    # Get all the l3nodes
    collect.get_l3_nodes()

    # Get all the l3 links
    collect.get_l3_links(baseURL, cienauser, cienapassw, token_string)

    # Code to get the l1 circuits
    collect.get_l3_circuits(baseURL, cienauser, cienapassw, token_string)

    if build_plan:
        # Add l1sites to plan
        logging.info("Adding sites")
        with open("jsonfiles/l1sites.json", 'rb') as f:
            sitelist = json.load(f)
        planbuild.generateSites(plan, sitelist)

        # Add L1 nodes to plan
        logging.info("Adding L1 nodes")
        with open("jsonfiles/l1nodes.json", 'rb') as f:
            l1nodeslist = json.load(f)
        l1_planbuild.generateL1nodes(plan, l1nodeslist)

        # Add L1 links to plan
        logging.info("Adding L1 links (ROADM degrees) ...")
        with open("jsonfiles/l1links.json", 'rb') as f:
            l1linkslist = json.load(f)
        l1_planbuild.generateL1links(plan, l1linkslist)

        # Add L1 circuits to plan
        logging.info("Adding L1 circuits to the plan...")
        with open("jsonfiles/l1circuits.json", 'rb') as f:
            l1circuitlist = json.load(f)
        l1_planbuild.generateL1circuits(plan, och_trails=l1circuitlist)

        # Add l3sites to plan
        logging.info("Adding sites")
        with open("jsonfiles/l3sites.json", 'rb') as f:
            sitelist = json.load(f)
        planbuild.generateSites(plan, sitelist)

        # Add l3 nodes to plan
        logging.info("Adding L3 nodes to plan file")
        with open("jsonfiles/l3nodes.json", 'rb') as f:
            l3nodeslist = json.load(f)
        l3_planbuild.generateL3nodes(plan, l3nodeslist)

        # Save the plan file
        plan.serializeToFileSystem('planfiles/latest.pln')
        plan.serializeToFileSystem(planfiles_root + current_time + '.pln')
        logging.info("Plan file created")

    end_time = str(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    logging.info("Script finish time is: {}".format(end_time))
    logging.info("Completed in {0:.2f} seconds".format(
        time.time() - start_time))

# Creating a new log object and the file to store the logs in the /archive/captures dir


def create_log(log_name, logging_level, archive_root):
    log_name = log_name
    logging_level = logging_level
    current_time = str(datetime.now().strftime('%Y-%m-%d__%H-%M-%S'))
    logFormatter = logging.Formatter(
        '%(asctime)s %(levelname)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    Logger = logging.getLogger(log_name)
    Logger.level = eval('logging.{}'.format(logging_level))

    milli = str(datetime.now().strftime('%Y-%m-%d-%H:%M:%S.%f'))[-6:-3]
    log_file_name = archive_root + \
        '/{}-'.format(log_name) + current_time + '-' + milli + '.log'
    fileHandler = logging.FileHandler(filename=log_file_name)
    fileHandler.setFormatter(logFormatter)
    Logger.addHandler(fileHandler)
    Logger.propagate = False
    return Logger


if __name__ == "__main__":
    main()
