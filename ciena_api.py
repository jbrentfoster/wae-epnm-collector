import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import json
import xml.dom.minidom
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor as ThreadPool
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
import shutil
from distutils.dir_util import copy_tree
from distutils.dir_util import remove_tree
from distutils.dir_util import mkpath


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
    parser.add_argument('-ph', '--phases', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Phases'],
                        help="List of the collection phases to run(1-6), example '1356'")
    parser.add_argument('-l', '--logging', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Logging'],
                        help="Add this flag to set the logging level.")
    parser.add_argument('-t', '--timeout', metavar='N', type=str, nargs='?', 
                        help="Add this flag to set the timeout value manually.") 
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

    #Taking the timeout cl argument and setting it for future use
    timeout = args.timeout
    if timeout:
        with open('configs/config.ini', 'rb') as f:
            data = f.readlines()

        with open('configs/config.ini', 'wb') as f:
            for line in data:
                if line.startswith('Timeout'):
                    line = 'Timeout_limit = {}\n'.format(timeout)
                f.write(line)

    current_time = str(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    archive_root = args.archive_root + '/captures/' + current_time
    planfiles_root = args.archive_root + '/planfiles/'
    start_time = time.time()
    build_plan = args.build_plan
    delete_previous = args.delete_previous
    logging_level = args.logging.upper()
    phases = args.phases

    #Setting up the main log file 
    logFormatter = logging.Formatter('%(asctime)s %(levelname)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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
    logging.debug("Phases is: {}".format(args.phases))

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
        logging.info("Keeping collection files from previous collection, building plan file only...")

    #Getting the API token
    #The tokens last 24 hours so explore saving the token in cache and refreshing every 24 hours after running a check on the cache
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

    '''
    So the logic here is minimize the amount of work the script has to do.
    It's taking the clarg phases, converting them into an int type and putting it in 
    the phase_list var.
    Then for each phase, it's taking the object that's in that corresponding phase and putting it into 
    the phases_to_run var.
    Here at this step, i want to change the logic. 
    So it essentially has 2 parts. Run the highest phase of 1234, and the highest phase of 1567. So if
    i enter 123456 as my clarg, then the script will run (all_nodes, l1nodes and l1links) and (all_nodes, l3nodes and l3links) because essentially it'll only run 3 and 6 and the script will take care of running the 3 functions for each group on the back end. 
    '''
    #Setting up the multi-threaded collection
    grp1, grp2, max_temp1, max_temp2 = [1,2,3,4], [5,6,7], 0, 0
    phase_list = []
    phases_to_run = []
    phase_objects_to_run = []

    for phase in phases:
        phase_list.append(int(phase))

    #Candidate for refactoring
    for index in range(len(phase_list)):
        phase = phase_list[index]
        if phase in grp1:
                if phase > max_temp1: max_temp1 = phase 
        if phase in grp2:
                if phase > max_temp2: max_temp2 = phase 
        
        if index == len(phase_list) - 1 and phase != 0: 
            if max_temp2 > 0: 
                phases_to_run.extend([max_temp1, max_temp2])
            else: 
                phases_to_run.append(max_temp1)
       

    # Run the collector...
    collection_calls = [
                        {'type': 'all_nodes', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw':
                        cienapassw, 'token': token_string},
                        {'type': 'l1nodes', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw':
                        cienapassw, 'token': token_string},
                        {'type': 'l1links', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw':       cienapassw, 'token': token_string},
                        {'type': 'l1circuits', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw': cienapassw, 'token': token_string},
                        {'type': 'l3nodes', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw':       cienapassw, 'token': token_string},
                        {'type': 'l3links', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw':       cienapassw, 'token': token_string},
                        {'type': 'l3circuits', 'baseURL': baseURL, 'cienauser': cienauser, 'cienapassw': cienapassw, 'token': token_string}
                        ]
    
    for phase in phases_to_run:
        phase_objects_to_run.append(collection_calls[phase - 1])

    #Creating the log for each thread
    mkpath(archive_root)
    for phase in phase_objects_to_run:
        phase_type = phase['type']
        logger = create_log(phase_type, logging_level, archive_root)
        logger.info('{} logger instantiated'.format(phase_type))
    
    pool = ThreadPool(7)
    pool.map(collect.collection_router, phase_objects_to_run)
    pool.shutdown(wait=True)

    # Create a service to be used by this script
    conn = com.cisco.wae.design.ServiceConnectionManager.newService()
    cwd = os.getcwd()
    fileName = os.path.join(cwd, 'planfiles/blank.pln')
    plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

    #Making sure the collection was successful before building the plan
    config = configparser.ConfigParser(interpolation=None)
    config.read('resources/config.ini')
    check = config['CHECK']['Build_plan_check']
    build_plan_check = True if check == 'True' else False
    
    if build_plan and build_plan_check:
        # Add sites to plan
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
        l1_planbuild.generateL1circuits(plan, l1circuitlist)

        # # Add L3 nodes to plan
        # logging.info("Adding L3 nodes")
        # with open("jsonfiles/l3nodes.json", 'rb') as f:
        #     l3nodeslist = json.load(f)
        # l3_planbuild.generateL3nodes(plan, l3nodeslist)

        # # Add L3 circuits to plan
        # logging.info("Adding L3 circuits to the plan...")
        # with open("jsonfiles/l3circuits.json", 'rb') as f:
        #     l3circuitlist = json.load(f)
        # l3_planbuild.generateL3circuits(plan, l3circuitlist)

        # Save the plan file
        plan.serializeToFileSystem('planfiles/latest.pln')
        plan.serializeToFileSystem(planfiles_root + current_time + '.pln')
        logging.info("Plan file created")

    # Backup current output files
    logging.info("Backing up files from collection...")
    try:
        copy_tree('jsonfiles', archive_root + '/jsonfiles')
        copy_tree('planfiles', archive_root + '/planfiles')
        copy_tree('jsongets', archive_root + '/jsongets')
    except Exception as err:
        logging.info("No output files to backup...")

    # Script completed
    if build_plan_check == False:
        with open('configs/config.ini', 'rb') as f:
            data = f.readlines()

        with open('configs/config.ini', 'wb') as f:
            for line in data:
                if line.startswith('Build_plan'):
                    line = 'Build_plan_check = {}\n'.format(True)
                f.write(line)
    end_time = str(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    logging.info("Script finish time is {}".format(end_time))
    logging.info("Completed in {0:.2f} seconds".format(time.time() - start_time))

    try:
        shutil.copy(log_file_name, archive_root + '/collection.log')
    except Exception as err:
        logging.info("No log file to copy...")
    time.sleep(2)

#Creating a new log object and the file to store the logs in the /archive/captures dir
def create_log(log_name, logging_level, archive_root):
    log_name = log_name
    logging_level = logging_level
    current_time = str(datetime.now().strftime('%Y-%m-%d__%H-%M-%S'))
    logFormatter = logging.Formatter('%(asctime)s %(levelname)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    Logger = logging.getLogger(log_name)
    Logger.level = eval('logging.{}'.format(logging_level))
    
    milli = str(datetime.now().strftime('%Y-%m-%d-%H:%M:%S.%f'))[-6:-3]
    log_file_name = archive_root + '/{}-'.format(log_name) + current_time + '-' + milli + '.log'
    fileHandler = logging.FileHandler(filename=log_file_name)
    fileHandler.setFormatter(logFormatter)
    Logger.addHandler(fileHandler)
    Logger.propagate = False
    return Logger

if __name__ == "__main__":
    main()
