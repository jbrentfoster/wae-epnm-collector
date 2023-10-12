import os
import com.cisco.wae.design
import waecode.planbuild
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import SiteRecord
import json
import csv
from datetime import datetime
from distutils.dir_util import copy_tree
from distutils.dir_util import remove_tree
from distutils.dir_util import mkpath
import collectioncode.collect
import logging
import shutil
import argparse
import time
import re
from concurrent.futures import ThreadPoolExecutor as ThreadPool
import configparser
import getpass
from pbkdf2 import PBKDF2
from Crypto.Cipher import AES
from Crypto import Random
import base64

thread_count = 6


def get_l3_nodes(state):
    with open("jsonfiles/{state}_l3Links_final.json".format(state=state.replace(' ', '_')), 'rb') as f:
        l3linksdict = json.load(f)
        
    l3nodes = []
    for k1, v1 in l3linksdict.items():
        tmpnode = {'Name': k1}
        l3nodes.append(tmpnode)
    return l3nodes, l3linksdict

def get_l3_nodes_combined(state, instance):
    # with open("jsonfiles/{state}_l3Links_final.json".format(state=state.replace(' ', '_')), 'rb') as f:
    with open("jsonfiles/{}_l3Links_add_tl_{}.json".format(state.replace(' ', '_'), instance), 'rb') as f:
        l3linksdict = json.load(f)
        f.close()
    l3nodes = []
    for k1, v1 in l3linksdict.items():
        tmpnode = {'Name': k1}
        l3nodes.append(tmpnode)
    return l3nodes, l3linksdict


def main():
    #Code for the new properties file
    config = configparser.ConfigParser(interpolation=None)
    config.read('configs/config.ini')

    # Get path for collection files from command line arguments
    parser = argparse.ArgumentParser(description='A WAE collection tool for EPNM')
    parser.add_argument('-a', '--archive_root', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Archive_root'],
                        help='Please provide the local path to your archive directory')
    parser.add_argument('-s', '--state_or_states', metavar='N', type=str, nargs='?', default=config['DEFAULT']['State_or_states'],
                        help="Please provide a list of states for mplstopo discovery. 'New York, Florida'")
    parser.add_argument('-i', '--epnm_ipaddr', metavar='N', type=str, nargs='?', default=config['DEFAULT']['EPNM_ipaddr'],
                        help="Please provide the EPNM Server address for API calls")
    parser.add_argument('-u', '--epnm_user', metavar='N', type=str, nargs='?', default=config['DEFAULT']['EPNM_user'],
                        help="Please provide the EPNM User name for the EPNM Server")
    parser.add_argument('-p', '--epnm_pass', metavar='N', type=str, nargs='?', default=config['DEFAULT']['EPNM_pass'],
                        help="Please provide the EPNM password for the EPNM Server")
    parser.add_argument('-ph', '--phases', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Phases'],
                        help="List of the collection phases to run(1-6), example '1356'")
    parser.add_argument('-l', '--logging', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Logging'],
                        help="Add this flag to set the logging level.")
    parser.add_argument('-t', '--timeout', metavar='N', type=str, nargs='?', default=config['DEFAULT']['Timeout_limit'],
                        help="Add this flag to set the timeout value manually.")
    parser.add_argument('-b', '--build_plan', action='store_true',
                        help="Add this flag to build the plan file.")
    parser.add_argument('-d', '--delete_previous', action='store_true',
                        help="Add this flag to delete previous collection files.")
    parser.add_argument('-in', '--instance', action='store_true',
                        help="Add this flag to pass in the instance run value.")
    parser.add_argument('-sa', '--save', action='store_true',
                        help="Add this flag to save the states list and the instance to the instance.json file, and add the instance string to the names of all the data files.")
    parser.add_argument('-c', '--combine', action='store_true',
                        help="Add this flag in combination w/ the -b(build) and -sa(save) flags to combine the outputs from multiple collection runs into one plan file.")
    args = parser.parse_args()

    epnmipaddr = args.epnm_ipaddr
    baseURL = "https://" + epnmipaddr + "/restconf"
    epnmuser = args.epnm_user
    epnmpassword = args.epnm_pass
    encryption_check = 'enCrYpted'
    #Decrypting the EPNM password for later use
    if epnmpassword.startswith(encryption_check):
        encoded_pb_key = config['DEFAULT']['EPNM_key']
        pb_key = base64.b64decode(encoded_pb_key)
        decoded_str = base64.b64decode(epnmpassword[len(encryption_check):])
        iv = decoded_str[:16]
        pb_key_check = decoded_str[-32:]
        if pb_key != pb_key_check:
            raise Exception('Incorrect password')
        cipher = AES.new(pb_key, AES.MODE_CFB, iv)
        password = cipher.decrypt(decoded_str[16:-32])
        epnmpassword = password    

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

    current_time = str(datetime.now().strftime('%Y-%m-%d__%H-%M-%S'))
    start_time = time.time()
    archive_root = args.archive_root + "/captures/" + current_time
    planfiles_root = args.archive_root + "/planfiles/"
    phases = args.phases
    build_plan = args.build_plan
    delete_previous = args.delete_previous
    state_or_states_list = args.state_or_states.split(',')
    state_or_states_list = [state.strip(' ').title() for state in state_or_states_list]
    logging_level = args.logging.upper()
    instance = config['INSTANCE']['Instance']
    save = args.save
    combine = args.combine

    #Implementing a basic spellchecker for the states
    STATES = {

         'Alabama','Alaska','Arizona','Arkansas','California','Colorado',
         'Connecticut','Deleware','Florida','Georgia','Hawaii','Idaho', 
         'Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana',
         'Maine' 'Maryland','Massachusetts','Michigan','Minnesota',
         'Mississippi', 'Missouri','Montana','Nebraska','Nevada',
         'New Hampshire','New Jersey','New Mexico','New York',
         'North Carolina','North Dakota','Ohio',    
         'Oklahoma','Oregon','Pennsylvania','Rhode Island',
         'South  Carolina','South Dakota','Tennessee','Texas','Utah',
         'Vermont','Virginia','Washington','West Virginia',
         'Wisconsin','Wyoming'
    }
    def known(state):
        return set(w for w in state if w in STATES)
    def variation1(state):
        letters = 'abcdefghijklmnopqrstuvwxyz'
        splits = [(state[:i],state[i:])  for i in range(len(state) + 1)]
        deletes = [l + r[1:] for l, r in splits if r]
        transposes = [l + r[1] + r[0] + r[2:] for l, r in splits if len(r) > 1]
        replaces = [l + c + r[1:] for l, r in splits if r for c in letters]
        inserts = [l + c + r for l, r in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)
    state_or_states_list = [''.join(known(variation1(state))) for state in state_or_states_list]

    #Setting up the main log file 
    logFormatter = logging.Formatter('%(asctime)s %(levelname)s:  %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    rootLogger = logging.getLogger()
    rootLogger.level = eval('logging.{}'.format(logging_level))

    milli = str(datetime.now().strftime('%Y-%m-%d-%H:%M:%S.%f'))[-6:-3]
    log_file_name = 'collection-' + current_time + '-' + milli + '.log'
    fileHandler = logging.FileHandler(filename=log_file_name)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    logging.info("Collection start time is " + current_time)
    logging.info("State list is " + str(state_or_states_list))
    logging.debug("Archive_root is: {}".format(args.archive_root))
    logging.debug("Epnm_ipaddr is: {}".format(args.epnm_ipaddr))
    logging.debug("Epnm_user is: {}".format(args.epnm_user))
    logging.debug("State_or_states is: {}".format(args.state_or_states))
    logging.debug("Phases is: {}".format(args.phases))
    logging.debug("Timeout value is: {} seconds".format(timeout))

    # Delete all output files
    if delete_previous:
        logging.info("Cleaning files from last collection...")
        try:
            remove_tree('jsonfiles')
            remove_tree('jsongets')

            instance_json = {
                "instances": [],
                "states": []
            }
            with open('configs/instance.json', 'wb') as f:
                f.write(json.dumps(instance_json, sort_keys=True, indent=4, separators=(',', ': ')))

        except Exception as err:
            logging.info("No files to cleanup...")
        # Recreate output directories
        mkpath('jsonfiles')
        mkpath('jsongets')
        mkpath(planfiles_root)
    else:
        logging.info("Keeping collection files from previous collection, building plan file only...")

    phase_list = []
    for phase in phases:
        phase_list.append(int(phase))
    
    # Run the collector...
    collection_calls = [{'type': 'l1nodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        {'type': 'l1links', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        {'type': 'allnodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        {'type': '4knodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        {'type': 'lsps', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        {'type': 'mpls', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword, 'state_or_states': state_or_states_list},
                        {'type': 'optical', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword, 'state_or_states': state_or_states_list}
                        # {'type': 'optical_phase_b', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
                        # {'type': 'optical_phase_c', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword}
                        ]
    phases_to_run = []
    c = 1
    for call in collection_calls:
        for phase_num in phase_list:
            if phase_num == c:
                phases_to_run.append(call)
                break
        c +=1

    #Creating the log for each thread
    mkpath(archive_root)
    for phase in phases_to_run:
        phase_type = phase['type']
        logger = create_log(phase_type, logging_level, archive_root)
        logger.info('{} logger instantiated'.format(phase_type))
    
    pool = ThreadPool(7)
    pool.map(collectioncode.collect.collection_router, phases_to_run)
    pool.shutdown(wait=True)

    # collectioncode.collect.runcollector(baseURL, epnmuser, epnmpassword, state_or_states_list)

    # print "PYTHONPATH=" + os.getenv('PYTHONPATH')
    # print "PATH=" + os.getenv('PATH')
    # print "CARIDEN_HOME=" + os.getenv('CARIDEN_HOME')
    if save:
        #Add the states list and the instance to the instance.json file
        with open('configs/instance.json', 'rb') as f:
            instance_dict = json.load(f)

        instance_dict['states'].append(state_or_states_list)
        instance_dict['instances'].append(instance)
        instance_dict = json.dumps(instance_dict, sort_keys=True, indent=4, separators=(',', ': '))
        logging.info('***********\n{}'.format(instance_dict))

        with open('configs/instance.json', 'wb') as f:
            f.write(instance_dict)
        #Append the instance string to the name of all the data file in the jsongets and jsonfiles folders
        #directories to look in
        directories = ['jsonfiles', 'jsongets']
        for dir in directories:
            cwd = os.getcwd()
            folderName = os.path.join(cwd, dir)
            for path, subdir, files in os.walk(folderName):
                for file in files:
                    match_object = re.search('_instance[0-9]', file)
                    if match_object == None:
                        filePath = path + '\\{}'.format(file)
                        file = re.sub('.json', '_{}.json'.format(instance), file)
                        file = re.sub('.txt', '_{}.txt'.format(instance), file)
                        new_file_path = path + '\\{}'.format(file)
                        os.rename(filePath, new_file_path)


    config = configparser.ConfigParser(interpolation=None)
    config.read('configs/config.ini')
    check = config['CHECK']['Build_plan_check']
    build_plan_check = True if check == 'True' else False

    if build_plan and build_plan_check and combine == False:
        logging.info("Building plan file...")

        # Create a service to be used by this script
        conn = com.cisco.wae.design.ServiceConnectionManager.newService()

        cwd = os.getcwd()
        fileName = os.path.join(cwd, 'planfiles/blank.pln')
        plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

        #######################################
        #
        #  Experimental
        #
        #######################################
        # Read node coordinates file into a dict
        # nodecoordinates = []
        # with open('waecode/node_coordinates.csv', 'rb') as f:
        #     reader = csv.DictReader(f)
        #     for row in reader:
        #         nodecoordinates.append(row)
        #     f.close()

        #######################################
        #
        #  Experimental
        #
        #######################################
        # # Add MPLS nodes to plan
        # logging.info("Adding nodes to plan...")
        # with open("jsonfiles/mpls_nodes.json", 'rb') as f:
        #     mpls_nodes = json.load(f)
        #     f.close()
        # l3nodes = []
        # for mpls_node in mpls_nodes:
        #     tmpnode = {'Name': mpls_node}
        #     l3nodes.append(tmpnode)
        # waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)

        # Check 4k_nodes_db.json for duplicate entries
        # logging.info("Checking 4k-nodes_db.json for duplicate entries...")
        # with open("jsonfiles/4k-nodes_db.json", 'rb') as f:
        #     four_k_nodes = json.load(f)
        #     f.close()
        # for k, v in four_k_nodes.items():
        #     count = 0
        #     for k1, v1 in four_k_nodes.items():
        #         if v['Name'] == v1['Name']:
        #             count += 1
        #     if count > 1:
        #         logging.info("Found a dup, removing this node: " + v['Name'])
        #         four_k_nodes.pop(k)

        #######################################
        #
        #  Build Optical Plan Components
        #
        #######################################

        # Add L1 nodes to plan
        logging.info("Adding L1 nodes...")
        with open("jsonfiles/l1Nodes.json", 'rb') as f:
            l1nodesdict = json.load(f)
            f.close()
        l1nodes = []
        # sites = []
        # site_manager = plan.getNetwork().getSiteManager()
        # found = False
        dictlength =  len(l1nodesdict)
        logging.info("number of nodes "+str(dictlength))
        counter = 0
        for k1, v1 in l1nodesdict.items():
            if v1['Longitude'] is None and v1['Latitude'] is None:
                logging.info("Assigning STATIC values of Longitude and Latitude")
                tmpnode = {'Name': v1['Name'], 'X': 0.00, 'Y': 0.00}
            else:
                logging.info("Assigning ACTUAL values to Longitude and Latitude")
                tmpnode = {'Name': v1['Name'], 'X': v1['Longitude']['fdtn.double-amount'], 'Y': v1['Latitude']['fdtn.double-amount']}

            # site_rec = SiteRecord(name=tmpnode['Name'], latitude=float(tmpnode['Y']), longitude=float(tmpnode['X']))
            try:
                # tmpsite = site_manager.newSite(siteRec=site_rec)
                # tmpnode['sitekey'] = tmpsite.getKey()
                # sites.append(tmpsite)
                l1nodes.append(tmpnode)
                logging.info("successfully added node " + tmpnode['Name'])
            except Exception as err:
                logging.warn('Could not process node ' + tmpnode['Name'])
                logging.warn(err)
        waecode.planbuild.generateL1nodes(plan, l1nodelist=l1nodes)

        # Add L1 links to plan
        logging.info("Adding L1 links...")
        with open("jsonfiles/l1Links.json", 'rb') as f:
            l1linksdict = json.load(f)
            f.close()
        waecode.planbuild.generateL1links(plan, l1linksdict)

        # Add 4K nodes (pure OTN) to plan (if any are duplicated from MPLS nodes skip it)
        logging.info("Adding 4k nodes to plan...")
        with open("jsonfiles/4k-nodes_db.json", 'rb') as f:
            four_k_nodes = json.load(f)
            f.close()
        added_nodes = []
        l3nodes = []
        for k, v in four_k_nodes.items():
            exists = waecode.planbuild.check_node_exists(plan,v['Name'])
            if not exists:
                tmpnode = {'Name': v['Name']}
                if "cisco.com" in tmpnode['Name']:
                    new_name = tmpnode['Name'].split('.cisco.com')[0]
                    tmpnode['Name'] = new_name
                added_nodes.append(tmpnode)
                l3nodes.append({'Name': v['Name']})

        waecode.planbuild.generateL3nodes(plan, l3nodelist=added_nodes)

        # Set node coordinates
        logging.info("Setting node coordinates...")
        node_manager = plan.getNetwork().getNodeManager()
        with open("jsonfiles/all-nodes.json", 'rb') as f:
            nodesdict = json.load(f)
            f.close()
        for l3_node in l3nodes:
            tmp_name = l3_node['Name']
            tmp_node = next(
                (item for item in nodesdict if item["name"] == tmp_name or item['name'].split('.')[0] == tmp_name),
                None)
            node = node_manager.getNode(NodeKey(l3_node['Name']))
            if tmp_node:
                node.setLatitude(tmp_node['Latitude']['fdtn.double-amount'])
                node.setLongitude(tmp_node['Longitude']['fdtn.double-amount'])

        # Add OCH-Trails (wavelengths) to plan
        logging.info("Adding OCH Trails as L1 circuits to the plan...")
        with open("jsonfiles/och_trails.json", 'rb') as f:
            och_trails = json.load(f)
            f.close()
        waecode.planbuild.generateL1circuits(plan, och_trails=och_trails)

        # Add circuits based on OTU links to the plan
        logging.info("Adding OTU circuits to the plan...")
        with open("jsonfiles/otn_links.json", 'rb') as f:
            otn_links = json.load(f)
            f.close()
        waecode.planbuild.generate_OTN_circuits(plan, otn_links)


        # # Add OTN services to the plan
        # logging.info("Adding ODU services to the plan...")
        # with open("jsonfiles/odu_services.json", 'rb') as f:
        #     odu_services = json.load(f)
        #     f.close()
        # waecode.planbuild.generate_otn_lsps(plan, odu_services, conn)

        #######################################
        #
        #  Build MPLS Plan Components
        #
        #######################################
        #
        # l3nodeloopbacks = []
        # # Add L3 nodes to plan
        # for state in state_or_states_list:
        #     logging.info("Adding L3 nodes...")
        #     l3nodes, l3linksdict = get_l3_nodes(state)
        #     waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)
        #
        #     # Add L3 links to plan and stitch to L1 links where applicable
        #     logging.info("Adding L3 links...")
        #     waecode.planbuild.generateL3circuits(plan, l3linksdict)  # <--- Moved above OCH Trails
        #
        #     # read FlexLSP add-on options
        #     with open("waecode/options.json", 'rb') as f:
        #         options = json.load(f)
        #
        #     # Make/update list of nodenames and loopbacks
        #     for k1, v1 in l3linksdict.items():
        #         tmpnode = {k1: v1['Loopback Address']}
        #         l3nodeloopbacks.append(tmpnode)
        #
        #     # Set node coordinates
        #     logging.info("Setting node coordinates...")
        #     node_manager = plan.getNetwork().getNodeManager()
        #     with open("jsonfiles/all-nodes.json", 'rb') as f:
        #         nodesdict = json.load(f)
        #     for l3_node in l3nodes:
        #         tmp_name = l3_node['Name']
        #         try:
        #             tmp_node = next(
        #                 (item for item in nodesdict if item["name"] == tmp_name or item['name'].split('.')[0] == tmp_name),
        #                 None)
        #             node = node_manager.getNode(NodeKey(l3_node['Name']))
        #             node.setLatitude(tmp_node['Latitude']['fdtn.double-amount'])
        #             node.setLongitude(tmp_node['Longitude']['fdtn.double-amount'])
        #         except Exception as err:
        #             logging.warn("Unable to set node coordinates, node not in EPNM inventory: " + tmp_name)
        #
        #
        # # Add LSPs to plan
        # logging.info("Adding LSP's...")
        # with open("jsonfiles/lsps.json", 'rb') as f:
        #     lsps = json.load(f)
        #     f.close()
        # waecode.planbuild.generate_lsps(plan, lsps, l3nodeloopbacks, options, conn)

        # Create and assign nodes to Sites
        logging.info("Assigning nodes to sites...")
        waecode.planbuild.assignSites_l1nodes(plan)
        # waecode.planbuild.assignSites_l3nodes(plan)

        # Save the plan file
        plan.serializeToFileSystem('planfiles/latest.pln')
        plan.serializeToFileSystem(planfiles_root + current_time + '.pln')
        logging.info("Plan file created.")

    #The building 'combined' plan file section
    if build_plan and combine and build_plan_check:
        logging.info("Building combined plan file...")

        # Create a service to be used by this script
        conn = com.cisco.wae.design.ServiceConnectionManager.newService()

        cwd = os.getcwd()
        fileName = os.path.join(cwd, 'planfiles/blank.pln')
        plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

        #Get the information from the instance.json file
        with open('configs/instance.json', 'rb') as f:
            instance_dict = json.load(f)

        list_of_state_lists = instance_dict['states']
        epnm_instances = instance_dict['instances']

        #######################################
        #
        #  Experimental
        #
        #######################################
        # Read node coordinates file into a dict
        # nodecoordinates = []
        # with open('waecode/node_coordinates.csv', 'rb') as f:
        #     reader = csv.DictReader(f)
        #     for row in reader:
        #         nodecoordinates.append(row)
        #     f.close()

        #######################################
        #
        #  Experimental
        #
        #######################################
        # # Add MPLS nodes to plan
        # logging.info("Adding nodes to plan...")
        # with open("jsonfiles/mpls_nodes.json", 'rb') as f:
        #     mpls_nodes = json.load(f)
        #     f.close()
        # l3nodes = []
        # for mpls_node in mpls_nodes:
        #     tmpnode = {'Name': mpls_node}
        #     l3nodes.append(tmpnode)
        # waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)

        # Check 4k_nodes_db.json for duplicate entries
        logging.info("Checking 4k-nodes_db.json for duplicate entries...")
        for instance in epnm_instances:
            #Note that i manually added in the '_' before the string insertion
            with open("jsonfiles/4k-nodes_db_{}.json".format(instance), 'rb') as f:
                four_k_nodes = json.load(f)
            for k, v in four_k_nodes.items():
                count = 0
                for k1, v1 in four_k_nodes.items():
                    if v['Name'] == v1['Name']:
                        count += 1
                if count > 1:
                    logging.info("Found a dup, removing this node: " + v['Name'])
                    four_k_nodes.pop(k)



        #######################################
        #
        #  Build Optical Plan Components
        #
        #######################################

        # Add L1 nodes to plan
        # logging.info("Adding L1 nodes...")
        # with open("jsonfiles/l1Nodes.json", 'rb') as f:
        #     l1nodesdict = json.load(f)
        #     f.close()
        # l1nodes = []
        # sites = []
        # site_manager = plan.getNetwork().getSiteManager()
        # # found = False
        # for k1, v1 in l1nodesdict.items():
        #     tmpnode = {'Name': v1['Name'], 'X': v1['Longitude']['fdtn.double-amount'], 'Y': v1['Latitude']['fdtn.double-amount']}
        #     site_rec = SiteRecord(name=tmpnode['Name'], latitude=float(tmpnode['Y']), longitude=float(tmpnode['X']))
        #     try:
        #         tmpsite = site_manager.newSite(siteRec=site_rec)
        #         tmpnode['sitekey'] = tmpsite.getKey()
        #         sites.append(tmpsite)
        #         l1nodes.append(tmpnode)
        #         logging.info("successfully added node " + tmpnode['Name'])
        #     except Exception as err:
        #         logging.warn('Could not process node ' + tmpnode['Name'])
        #         logging.warn(err)
        # waecode.planbuild.generateL1nodes(plan, l1nodelist=l1nodes)

        # # Add L1 links to plan
        # logging.info("Adding L1 links...")
        # with open("jsonfiles/l1Links.json", 'rb') as f:
        #     l1linksdict = json.load(f)
        #     f.close()
        # waecode.planbuild.generateL1links(plan, l1linksdict)

        # Add 4K nodes (pure OTN) to plan (if any are duplicated from MPLS nodes skip it)
        logging.info("Adding 4k nodes to plan...")
        l3nodes = []
        for instance in epnm_instances:
            #Note that i manually added in the '_' before the string insertion
            with open("jsonfiles/4k-nodes_db_{}.json".format(instance), 'rb') as f:
                four_k_nodes = json.load(f)
            added_nodes = []
            for k, v in four_k_nodes.items():
                exists = waecode.planbuild.check_node_exists(plan,v['Name'])
                if not exists:
                    tmpnode = {'Name': v['Name']}
                    added_nodes.append(tmpnode)
                    l3nodes.append({'Name': v['Name']})

            waecode.planbuild.generateL3nodes_combined(plan, added_nodes, instance)

        # Set node coordinates
        logging.info("Setting node coordinates...")
        node_manager = plan.getNetwork().getNodeManager()
        for instance in epnm_instances:
            #Note that i manually added in the '_' before the string insertion
            with open("jsonfiles/all-nodes_{}.json".format(instance), 'rb') as f:
                nodesdict = json.load(f)
            for l3_node in l3nodes:
                tmp_name = l3_node['Name']
                tmp_node = next(
                    (item for item in nodesdict if item["name"] == tmp_name or item['name'].split('.')[0] == tmp_name),
                    None)
                node = node_manager.getNode(NodeKey(l3_node['Name']))
                node.setLatitude(tmp_node['Latitude']['fdtn.double-amount'])
                node.setLongitude(tmp_node['Longitude']['fdtn.double-amount'])

        # Add OCH-Trails (wavelengths) to plan
        # logging.info("Adding OCH Trails as L1 circuits to the plan...")
        # with open("jsonfiles/och_trails.json", 'rb') as f:
        #     och_trails = json.load(f)
        #     f.close()
        # waecode.planbuild.generateL1circuits(plan, och_trails=och_trails)


        # TODO see if assignSites is breaking something (seems to be)
        waecode.planbuild.assignSites(plan)


        # Add OTN services to the plan
        # logging.info("Adding ODU services to the plan...")
        # with open("jsonfiles/odu_services.json", 'rb') as f:
        #     odu_services = json.load(f)
        #     f.close()
        # waecode.planbuild.generate_otn_lsps(plan, odu_services, conn)

        #######################################
        #
        #  Build MPLS Plan Components
        #
        #######################################

        
        # Add L3 nodes to plan
        for state_or_states_list in list_of_state_lists:
            l3nodeloopbacks = []
            #Get the index value of state_or_states_list within the list_of_state_lists
            instance_index = list_of_state_lists.index(state_or_states_list)
            #Using the index of state_or_states_list to get the instance value since they're tied together when created using the '-sa or --save' flag
            instance = epnm_instances[instance_index]
            for state in state_or_states_list:
                logging.info("Adding L3 nodes...")
                l3nodes, l3linksdict = get_l3_nodes_combined(state, instance)
                waecode.planbuild.generateL3nodes_combined(plan, l3nodes, instance)

                # Add L3 links to plan and stitch to L1 links where applicable
                logging.info("Adding L3 links...")
                waecode.planbuild.generateL3circuits(plan, l3linksdict)  # <--- Moved above OCH Trails

                # Make/update list of nodenames and loopbacks
                for k1, v1 in l3linksdict.items():
                    tmpnode = {k1: v1['Loopback Address']}
                    l3nodeloopbacks.append(tmpnode)

                # Set node coordinates
                logging.info("Setting node coordinates...")
                node_manager = plan.getNetwork().getNodeManager()
                #Note that i manually added in the '_' before the string insertion
                with open("jsonfiles/all-nodes_{}.json".format(instance), 'rb') as f:
                    nodesdict = json.load(f)
                for l3_node in l3nodes:
                    tmp_name = l3_node['Name']
                    try:
                        tmp_node = next(
                            (item for item in nodesdict if item["name"] == tmp_name or item['name'].split('.')[0] == tmp_name),
                            None)
                        node = node_manager.getNode(NodeKey(l3_node['Name']))
                        node.setLatitude(tmp_node['Latitude']['fdtn.double-amount'])
                        node.setLongitude(tmp_node['Longitude']['fdtn.double-amount'])
                    except Exception as err:
                        logging.warn("Unable to set node coordinates, node not in EPNM inventory: " + tmp_name)

            # read FlexLSP add-on options
            with open("waecode/options.json", 'rb') as f:
                options = json.load(f)

            # Add LSPs to plan
            logging.info("Adding LSP's...")
            #Note that i manually added in the '_' before the string insertion
            with open("jsonfiles/lsps_{}.json".format(instance), 'rb') as f:
                lsps = json.load(f)
            waecode.planbuild.generate_lsps(plan, lsps, l3nodeloopbacks, options, conn)            

        # Create and assign nodes to Sites
        # logging.info("Assigning nodes to sites...")
        # waecode.planbuild.assignSites_l3nodes(plan)

        # Save the plan file
        plan.serializeToFileSystem('planfiles/latest.pln')
        plan.serializeToFileSystem(planfiles_root + current_time + '.pln')
        logging.info("Plan file created.")

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
    finish_time = str(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    logging.info("Collection finish time is " + finish_time)
    logging.info("Total script completion time is {0:.2f} seconds.".format(time.time() - start_time))

    logging.info("Copying log file...")
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


if __name__ == '__main__':
    main()