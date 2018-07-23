import os
import com.cisco.wae.design
import waecode.planbuild
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


def main():
    # Get path for collection files from command line arguments
    parser = argparse.ArgumentParser(description='A WAE collection tool for EPNM')
    parser.add_argument('archive_root', metavar='N', type=str,
                        help='the local path for storing collections')
    parser.add_argument('seednode_id', metavar='N', type=str,
                        help="Host ID of the seed node (must be XR!) for network discovery")
    parser.add_argument('epnm_ipaddr', metavar='N', type=str,
                        help="Host ID of the seed node (must be XR!) for network discovery")
    parser.add_argument('epnm_user', metavar='N', type=str,
                        help="Host ID of the seed node (must be XR!) for network discovery")
    parser.add_argument('epnm_pass', metavar='N', type=str,
                        help="Host ID of the seed node (must be XR!) for network discovery")
    args = parser.parse_args()

    epnmipaddr = args.epnm_ipaddr
    baseURL = "https://" + epnmipaddr + "/restconf"
    epnmuser = args.epnm_user
    epnmpassword = args.epnm_pass
    current_time = str(datetime.now().strftime('%Y-%m-%d-%H%M-%S'))
    archive_root = args.archive_root + "/captures/" + current_time
    planfiles_root = args.archive_root + "/planfiles/"

    # Set up logging
    try:
        os.remove('collection.log')
    except Exception as err:
        print("No log file to delete...")

    logFormatter = logging.Formatter('%(levelname)s:  %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.level = logging.INFO

    fileHandler = logging.FileHandler(filename='collection.log')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    # Delete all output files
    # logging.info("Cleaning files from last collection...")
    # try:
    #     remove_tree('jsonfiles')
    #     remove_tree('jsongets')
    # except Exception as err:
    #     logging.info("No files to cleanup...")
    #
    # # Recreate output directories
    # mkpath('jsonfiles')
    # mkpath('jsongets')
    # mkpath(planfiles_root)
    #
    # # Run the collector...
    # collectioncode.collect.runcollector(baseURL, epnmuser, epnmpassword, args.seednode_id)

    # print "PYTHONPATH=" + os.getenv('PYTHONPATH')
    # print "PATH=" + os.getenv('PATH')
    # print "CARIDEN_HOME=" + os.getenv('CARIDEN_HOME')

    logging.info("Building plan file...")

    # Create a service to be used by this script
    conn = com.cisco.wae.design.ServiceConnectionManager.newService()

    cwd = os.getcwd()
    fileName = os.path.join(cwd, 'planfiles/blank.pln')
    plan = conn.getPlanManager().newPlanFromFileSystem(fileName)

    # Read node coordinates file into a dict
    nodecoordinates = []
    with open('waecode/node_coordinates.csv', 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodecoordinates.append(row)
        f.close()

    # Add L1 nodes to plan
    logging.info("Adding L1 nodes...")
    with open("jsonfiles/l1Nodes.json", 'rb') as f:
        l1nodesdict = json.load(f)
        f.close()
    l1nodes = []
    sites = []
    site_manager = plan.getNetwork().getSiteManager()
    # found = False
    for k1, v1 in l1nodesdict.items():
        tmpnode = {'Name': v1['Name'], 'X': v1['Longitude']['fdtn.double-amount'], 'Y': v1['Latitude']['fdtn.double-amount']}
        site_rec = SiteRecord(name=tmpnode['Name'], latitude=float(tmpnode['Y']), longitude=float(tmpnode['X']))
        tmpsite = site_manager.newSite(siteRec=site_rec)
        tmpnode['sitekey'] = tmpsite.getKey()
        sites.append(tmpsite)
        l1nodes.append(tmpnode)
    #     for node in nodecoordinates:
    #         if node['Node'] == v1['Name']:
    #             tmpnode = {'Name': v1['Name'], 'X': node['X'], 'Y': node['Y']}
    #             l1nodes.append(tmpnode)
    #             found = True
    #             break
    #     # If node not found in coordinates list just initialize with default 0,0 coordinates
    #     if not found:
    #         tmpnode = {'Name': v1['Name'], 'X': 0, 'Y': 0}
    #         l1nodes.append(tmpnode)
    waecode.planbuild.generateL1nodes(plan, l1nodelist=l1nodes)

    # Add L1 links to plan
    logging.info("Adding L1 links...")
    with open("jsonfiles/l1Links.json", 'rb') as f:
        l1linksdict = json.load(f)
        f.close()
    waecode.planbuild.generateL1links(plan, l1linksdict)

    # Add L3 nodes to plan
    logging.info("Adding L3 nodes...")
    with open("jsonfiles/l3Links_final.json", 'rb') as f:
        l3linksdict = json.load(f)
        f.close()
    l3nodes = []
    # found = False
    for k1, v1 in l3linksdict.items():
        tmpnode = {'Name': k1}
        # for node in nodecoordinates:
        #     if node['Node'] == k1:
        #         tmpnode = {'Name': k1, 'X': node['X'], 'Y': node['Y']}
        #         found = True
        #         break
        # # If node not found in coordinates list just initialize with default 0,0 coordinates
        # if not found:
        #     tmpnode = {'Name': k1, 'X': 0, 'Y': 0}
        l3nodes.append(tmpnode)
        # found = False
    waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)

    # Add L3 links to plan and stitch to L1 links where applicable
    logging.info("Adding L3 links...")
    waecode.planbuild.generateL3circuits(plan, l3linksdict)

    # read FlexLSP add-on options
    with open("waecode/options.json", 'rb') as f:
        options = json.load(f)
        f.close()

    # Add LSPs to plan
    logging.info("Adding LSP's...")
    l3nodeloopbacks = []
    for k1, v1 in l3linksdict.items():
        tmpnode = {k1: v1['Loopback Address']}
        l3nodeloopbacks.append(tmpnode)

    with open("jsonfiles/lsps.json", 'rb') as f:
        lsps = json.load(f)
        f.close()
    waecode.planbuild.generate_lsps(plan, lsps, l3nodeloopbacks, options, conn)

    # Save the plan file
    plan.serializeToFileSystem('planfiles/latest.pln')
    plan.serializeToFileSystem(planfiles_root + current_time + '.pln')

    # Backup current output files
    logging.info("Backing up files from collection...")
    try:
        copy_tree('jsonfiles', archive_root + '/jsonfiles')
        copy_tree('planfiles', archive_root + '/planfiles')
        copy_tree('jsongets', archive_root + '/jsongets')
    except Exception as err:
        logging.info("No output files to backup...")

    logging.info("Copying log file...")
    try:
        mkpath(archive_root)
        shutil.copy('collection.log', archive_root + '/collection.log')
    except Exception as err:
        logging.info("No log file to copy...")

    # Script completed
    logging.info("Plan file created.")
    time.sleep(2)


if __name__ == '__main__':
    main()
