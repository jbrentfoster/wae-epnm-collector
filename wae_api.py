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
from multiprocessing.dummy import Pool as ThreadPool


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
    logging.info("Collection start time is " + current_time)

    # Delete all output files
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

    # # Run the collector...
    # collection_calls = [{'type': 'l1nodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
    #                     {'type': 'l1links', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
    #                     {'type': 'allnodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
    #                     {'type': '4knodes', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
    #                     {'type': 'lsps', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword},
    #                     {'type': 'mpls', 'baseURL': baseURL, 'epnmuser': epnmuser, 'epnmpassword': epnmpassword, 'seednodeid': args.seednode_id}
    #                     ]
    # pool = ThreadPool(4)
    # pool.map(collectioncode.collect.collection_router, collection_calls)
    # pool.close()
    # pool.join()

    collectioncode.collect.runcollector(baseURL, epnmuser, epnmpassword, args.seednode_id)

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
    # nodecoordinates = []
    # with open('waecode/node_coordinates.csv', 'rb') as f:
    #     reader = csv.DictReader(f)
    #     for row in reader:
    #         nodecoordinates.append(row)
    #     f.close()

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
        try:
            tmpsite = site_manager.newSite(siteRec=site_rec)
            tmpnode['sitekey'] = tmpsite.getKey()
            sites.append(tmpsite)
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



    # Add nodes to plan
    logging.info("Adding nodes to plan...")
    with open("jsonfiles/mpls_nodes.json", 'rb') as f:
        mpls_nodes = json.load(f)
        f.close()
    l3nodes = []
    for mpls_node in mpls_nodes:
        tmpnode = {'Name': mpls_node}
        l3nodes.append(tmpnode)
    waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)


    # Add OCH-Trails (wavelengths) to plan
    logging.info("Adding OCH Trails as L1 circuits to the plan...")
    with open("jsonfiles/och_trails.json", 'rb') as f:
        och_trails = json.load(f)
        f.close()
    waecode.planbuild.generateL1circuits(plan, och_trails=och_trails)

    # # Add L3 nodes to plan
    # logging.info("Adding L3 nodes...")
    # with open("jsonfiles/l3Links_final.json", 'rb') as f:
    #     l3linksdict = json.load(f)
    #     f.close()
    # l3nodes = []
    # # found = False
    # for k1, v1 in l3linksdict.items():
    #     tmpnode = {'Name': k1}
    #     l3nodes.append(tmpnode)
    #     # found = False
    # waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)
    #
    # # Add L3 links to plan and stitch to L1 links where applicable
    # logging.info("Adding L3 links...")
    # waecode.planbuild.generateL3circuits(plan, l3linksdict)
    #
    # waecode.planbuild.assignSites(plan)
    #
    # # read FlexLSP add-on options
    # with open("waecode/options.json", 'rb') as f:
    #     options = json.load(f)
    #     f.close()
    #
    # # Add LSPs to plan
    # logging.info("Adding LSP's...")
    # l3nodeloopbacks = []
    # for k1, v1 in l3linksdict.items():
    #     tmpnode = {k1: v1['Loopback Address']}
    #     l3nodeloopbacks.append(tmpnode)
    #
    # with open("jsonfiles/lsps.json", 'rb') as f:
    #     lsps = json.load(f)
    #     f.close()
    # waecode.planbuild.generate_lsps(plan, lsps, l3nodeloopbacks, options, conn)

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
    finish_time = str(datetime.now().strftime('%Y-%m-%d-%H%M-%S'))
    logging.info("Collection finish time is " + finish_time)
    time.sleep(2)


if __name__ == '__main__':
    main()
