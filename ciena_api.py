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
import collectioncode.utils as utils


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
    parser.add_argument('-s', '--state_or_states', metavar='N', type=str, nargs='?', default=config['DEFAULT']['State_or_states'],
                        help="Please provide a list of states for mplstopo discovery. 'NY, MD'")
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
    state_or_states_list = args.state_or_states.split(',')
    state_or_states_list = [x.strip(' ') for x in state_or_states_list]
    logging_level = args.logging.upper()

    # Setting up the main log file
    logFormatter = logging.Formatter(
        '%(asctime)s %(levelname)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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
    logging.info("State list is: {} ".format(state_or_states_list))
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
        isdirExists = os.path.isdir('jsongets')
        #isfiledirExists = os.path.isdir('jsonfiles')
        if not isdirExists:
            logging.info(
                "This is first time run. Creating jsongets and jsonfiles")
            mkpath('jsonfiles')
            mkpath('jsongets')
        else:
            logging.info(
                "Keeping collection files from previous collection, building plan file only...")
        logger = create_log('collection', logging_level, archive_root)

    # Create a service to be used by this script
    conn = com.cisco.wae.design.ServiceConnectionManager.newService()

    cwd = os.getcwd()
    fileName = os.path.join(cwd, 'planfiles/blank.pln')
    plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

    token = None

    if delete_previous or not isdirExists:
        tokenPath = '/tron/api/v1/tokens'
        proxies = {
            "http": None,
            "https": None,
        }
        appformat = 'application/json'
        headers = {'Content-type': appformat, 'Accept': appformat}
        data = {'username': cienauser, 'password': cienapassw}
        resttokenURI = baseURL + tokenPath
        try:
            r = requests.post(resttokenURI, proxies=proxies,
                              headers=headers, json=data, verify=False)
            if r.status_code == 201:
                token = json.dumps(r.json(), indent=2)
                # print token
            else:
                r.raise_for_status()

        except requests.exceptions.RequestException as err:
            print "Exception raised: " + str(err)
            return

        token = json.loads(token)
        token_string = token['token']

        # Get all the nodes
        logging.debug("Retrieve all nodes..")
        collect.get_all_nodes(baseURL, cienauser, cienapassw, token_string)
        logging.debug("All nodes retrieved")

        # Populate Site information
        logging.debug("Populate Sites..")
        collect.get_Sites(baseURL, cienauser, cienapassw, token_string)
        logging.debug("Sites data populated..")

        # Retrieve all  ports / TPE data for states
        logging.debug("Retrieve all ports data..")
        collect.get_ports(baseURL, cienauser, cienapassw,
                          token_string, state_or_states_list)
        logging.debug("All ports retrieved..")

        # Retrieve all the links and cicruits
        logging.debug("Retrieve all Links data..")
        collect.get_links(baseURL, cienauser, cienapassw,
                          token_string, state_or_states_list)
        logging.debug("All links retrieved..")

        # Retrieve l1 links data for all l1 nodes
        collect.get_l1_links_data(baseURL, cienauser, cienapassw,
                          token_string, state_or_states_list)
        logging.debug("L1 links retrieved..")

        # Get all the l1nodes
        logging.debug("Retrieve L1 nodes..")
        collect.get_l1_nodes(state_or_states_list)
        logging.debug("L1 nodes generated..")

        # Get all the l1 links
        logging.debug("Retrieve L1 links..")
        collect.get_l1_links(baseURL, cienauser, cienapassw,
                             token_string, state_or_states_list)
        logging.debug("L1 links retrieved..")

        # Code to get the l1 circuits
        logging.debug("Retrieve L1 Circuits..")
        collect.get_l1_circuits(baseURL, cienauser, cienapassw, token_string)
        logging.debug("L1 Circuits retrieved..")

        # Get all the l3nodes
        logging.debug("Retrieve L3 nodes..")
        collect.get_l3_nodes(state_or_states_list)
        logging.debug("L3 nodes generated..")

        # Get all the l3 links
        logging.debug("Retrieve L3 links and Circuits..")
        collect.get_l3_links(baseURL, cienauser, cienapassw, token_string)
        logging.debug("L3 links and circuit generated..")

    #######################################
    #
    #  Build MPLS Plan Components
    #
    #######################################

    if build_plan:
        # Add l1sites to plan
        logging.info("Adding sites")
        sitelist = utils.open_file_load_data('jsonfiles/sites.json')
        planbuild.generateSites(plan, sitelist)

        # Add L1 nodes to plan
        logging.info("Adding L1 nodes")
        l1nodeslist = utils.open_file_load_data('jsonfiles/l1nodes.json')
        l1_planbuild.generateL1nodes(plan, l1nodeslist)

        # Add L1 links to plan
        logging.info("Adding L1 links ...")
        l1linkslist = utils.open_file_load_data('jsonfiles/l1links.json')
        l1_planbuild.generateL1links(plan, l1linkslist)

        # Add L1 circuits to plan (temp commenting out)
        logging.info("Adding L1 circuits to the plan...")
        l1circuitlist = utils.open_file_load_data('jsonfiles/l1circuits.json')
        l1_planbuild.generateL1circuits(plan, l1_data=l1circuitlist)

        # Add l3 nodes to plan
        logging.info("Adding L3 nodes to plan file")
        l3nodeslist = utils.open_file_load_data('jsonfiles/l3nodes.json')
        l3_planbuild.generateL3nodes(plan, l3nodeslist)
        # Set node coordinates
        logging.info("Setting node coordinates...")
        node_manager = plan.getNetwork().getNodeManager()
        for l3_node in l3nodeslist:
            tmp_name = l3_node['attributes']['name']
            tmp_node = next(
                (item for item in l3nodeslist if item['attributes']
                 ['name'] == tmp_name), None)
            node = node_manager.getNode(NodeKey(l3_node['attributes']['name']))
            if tmp_node:
                node.setLatitude(float(tmp_node['latitude']))
                node.setLongitude(float(tmp_node['longitude']))
        l3nodeloopbacks = []
        # Add L3 links to plan and link with l1 links where applicable
        logging.info("Adding L3 links and circuits...")
        l3nodes, l3linksdict = utils.getl3nodes()
        l3_planbuild.generateL3circuits(plan, l3linksdict)

        for k1, v1 in l3linksdict.items():
            tempnode = {k1: v1['loopback address']}
            l3nodeloopbacks.append(tempnode)

        # Adding LSPs to plan file
        logging.info("Adding LSP's to plan file...")
        lsps = utils.open_file_load_data('jsonfiles/lsps.json')
        if lsps:
            l3_planbuild.generate_lsps(plan, lsps, l3nodeloopbacks)

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
