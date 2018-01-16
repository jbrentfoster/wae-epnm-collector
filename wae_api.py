import os
import com.cisco.wae.design
import waecode.planbuild
import json
import csv
import xmlcode.collect


def main():
    # EPNM server details for data collection...
    epnmipaddr = "10.135.7.222"
    baseURL = "https://" + epnmipaddr + "/restconf"
    epnmuser = "root"
    epnmpassword = "Epnm1234"

    # Run the collector...
    # xmlcode.collect.runcollector(baseURL, epnmuser, epnmpassword)

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
    with open("jsonfiles/l1Links.json", 'rb') as f:
        l1linksdict = json.load(f)
        f.close()
    l1links = []
    for k1, v1 in l1linksdict.items():
        l1links.append(v1['Nodes'])
    waecode.planbuild.generateL1links(plan, l1linklist=l1links)

    # Add L3 nodes to plan
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
    c = 0
    i = 0
    linkslist = []
    duplicatelink = False
    for k1, v1 in l3linksdict.items():
        firstnode = k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # print "***************Linkname is: " + k3
                    lastnode = v3['Neighbor']
                    discoveredname = v3['discoveredname']
                    rsvpbw = float(v3['RSVP BW'].split(' ')[0])
                    intfbw = getintfbw(rsvpbw)
                    for linkdiscoveredname in linkslist:
                        if discoveredname == linkdiscoveredname: duplicatelink = True
                    if 'Ordered L1 Hops' in v3 and not duplicatelink:
                        if len(v3['Ordered L1 Hops']) > 0:
                            linkslist.append(discoveredname)
                            c += 1
                            i += 1
                            l1hops, firstl1node, lastl1node = getfirstlastl1node(v3['Ordered L1 Hops'], firstnode,
                                                                                 lastnode)

                            name = "L1_circuit_" + str(c)
                            l1circuit = waecode.planbuild.generateL1circuit(plan, name, firstl1node, lastl1node, l1hops,
                                                                            intfbw)
                            name = "L3_circuit_" + str(i)
                            l3circuit = waecode.planbuild.generateL3circuit(plan, name, firstnode, lastnode)
                            l3circuit.setL1Circuit(l1circuit)
                            l3circuit.setCapacity(l1circuit.getBandwidth())
                            intfdict = l3circuit.getAllInterfaces()
                            for k6, v6 in intfdict.items():
                                v6.setResvBW(int(rsvpbw / 1000))

                    elif not duplicatelink:
                        i += 1
                        name = "L3_circuit_" + str(i)
                        linkslist.append(discoveredname)
                        l3circuit = waecode.planbuild.generateL3circuit(plan, name, firstnode, lastnode)
                        l3circuit.setCapacity(intfbw)
                        intfdict = l3circuit.getAllInterfaces()
                        for k6, v6 in intfdict.items():
                            v6.setResvBW(int(rsvpbw / 1000))

                    duplicatelink = False

    # read FlexLSP add-on options
    with open("waecode/options.json", 'rb') as f:
        options = json.load(f)
        f.close()

    # Add LSPs to plan
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


def getfirstlastl1node(orderedl1hops, firstnode, lastnode):
    l1hops = []
    firstl1node = ""
    lastl1node = ""
    for l1hop in orderedl1hops:
        nodelist = []
        firstlasthop = False
        for k5, v5 in l1hop['Nodes'].items():
            if k5 == firstnode or k5 == lastnode: firstlasthop = True
            nodelist.append(k5)
        if not firstlasthop:
            l1hops.append(nodelist)
        elif nodelist[0] == firstnode:
            firstl1node = nodelist[1]
        elif nodelist[1] == firstnode:
            firstl1node = nodelist[0]
        elif nodelist[0] == lastnode:
            lastl1node = nodelist[1]
        elif nodelist[1] == lastnode:
            lastl1node = nodelist[0]
    return l1hops, firstl1node, lastl1node


def getintfbw(rsvpbw):
    intfbw = 0
    if rsvpbw > 0 and rsvpbw <= 1000000:
        intfbw = 1000
    elif rsvpbw > 1000000 and rsvpbw <= 10000000:
        intfbw = 10000
    elif rsvpbw > 10000000 and rsvpbw <= 40000000:
        intfbw = 40000
    elif rsvpbw > 40000000 and rsvpbw <= 100000000:
        intfbw = 100000
    else:
        print "Error determining interface bandwidth!!!"
    return intfbw


if __name__ == '__main__':
    main()
