import os
import com.cisco.wae.design
import waecode.planbuild
import json
import csv
import shutil
from datetime import datetime
from distutils.dir_util import copy_tree
import xmlcode.collect


def main():
    # EPNM server details for data collection...
    epnmipaddr = "10.135.7.222"
    baseURL = "https://" + epnmipaddr + "/restconf"
    epnmuser = "root"
    epnmpassword = "Epnm1234"

    # Backup current output files
    current_time = str(datetime.now().strftime('%Y-%m-%d%H%M%S'))
    archive_root = "C:\Users\\brfoster\Temp\\" + current_time
    copy_tree('jsonfiles',archive_root+'\jsonfiles')
    copy_tree('planfiles', archive_root + '\planfiles')
    copy_tree('xmlgets', archive_root + '\\xmlgets')


    # Run the collector...
    xmlcode.collect.runcollector(baseURL, epnmuser, epnmpassword)

    # print "PYTHONPATH=" + os.getenv('PYTHONPATH')
    # print "PATH=" + os.getenv('PATH')
    # print "CARIDEN_HOME=" + os.getenv('CARIDEN_HOME')

    print "Building plan file..."

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
    print "Adding L1 nodes..."
    with open("jsonfiles/l1Nodes.json", 'rb') as f:
        l1nodesdict = json.load(f)
        f.close()
    l1nodes = []
    for k1, v1 in l1nodesdict.items():
        for node in nodecoordinates:
            if node['Node'] == v1['Name']:
                tmpnode = {'Name': v1['Name'], 'X': node['X'], 'Y': node['Y']}
                # TODO Add code to catch case where node name is not in the file with the coordinates (set to 0,0)
        l1nodes.append(tmpnode)
    waecode.planbuild.generateL1nodes(plan, l1nodelist=l1nodes)

    # Add L1 links to plan
    print "Adding L1 links..."
    with open("jsonfiles/l1Links.json", 'rb') as f:
        l1linksdict = json.load(f)
        f.close()
    l1links = []
    for k1, v1 in l1linksdict.items():
        l1links.append(v1['Nodes'])
    waecode.planbuild.generateL1links(plan, l1linklist=l1links)

    # Add L3 nodes to plan
    print "Adding L3 nodes..."
    with open("jsonfiles/l3Links_final.json", 'rb') as f:
        l3linksdict = json.load(f)
        f.close()
    l3nodes = []
    for k1, v1 in l3linksdict.items():
        for node in nodecoordinates:
            if node['Node'] == k1:
                tmpnode = {'Name': k1, 'X': node['X'], 'Y': node['Y']}
        l3nodes.append(tmpnode)
    waecode.planbuild.generateL3nodes(plan, l3nodelist=l3nodes)

    # Add L3 links to plan and stitch to L1 links where applicable
    print "Adding L3 links..."
    waecode.planbuild.generateL3circuits(plan, l3linksdict)

    # read FlexLSP add-on options
    with open("waecode/options.json", 'rb') as f:
        options = json.load(f)
        f.close()

    # Add LSPs to plan
    print "Adding LSP's..."
    l3nodeloopbacks = []
    for k1, v1 in l3linksdict.items():
        tmpnode = {k1: v1['Loopback Address']}
        l3nodeloopbacks.append(tmpnode)

    with open("jsonfiles/lsps.json", 'rb') as f:
        lsps = json.load(f)
        f.close()
    waecode.planbuild.generate_lsps(plan, lsps, l3nodeloopbacks, options, conn)

    # Save the plan file
    plan.serializeToFileSystem('planfiles/test.pln')

    # Script completed
    print "Plan file created.  See planfiles/test.pln"


if __name__ == '__main__':
    main()
