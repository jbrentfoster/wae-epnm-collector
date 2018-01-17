import xmlcode.utils
import xml.dom.minidom
import xml.parsers.expat
import time
import re
import json


def runcollector(baseURL, epnmuser, epnmpassword):
    print "Collecting L1 nodes..."
    collectL1Nodes(baseURL, epnmuser, epnmpassword)
    print "Collecting L1 links..."
    collectL1links(baseURL, epnmuser, epnmpassword)
    print "Collecting ISIS database..."
    collectISIS(baseURL, epnmuser, epnmpassword)
    print "Processing ISIS database..."
    processISIS()
    print "Collecting MPLS topological links..."
    collectMPLSinterfaces(baseURL, epnmuser, epnmpassword)
    print "Collecting virtual connections..."
    collectvirtualconnections(baseURL, epnmuser, epnmpassword)
    print "Collecting L1 paths..."
    addL1hopstol3links(baseURL, epnmuser, epnmpassword)
    print "Re-ordering L1 hops..."
    reorderl1hops()
    print "Network collection completed!"
    collectlsps(baseURL, epnmuser, epnmpassword)


def collectL1Nodes(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-resource-physical:node"
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/l1-nodes-xml", 'wb') as f:
        f.write(xmlresponse)
        f.close()
    with open("xmlgets/l1-nodes-xml", 'rb') as f:
        xmlresponse = f.read()
        f.close()

    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message is not XML."
        return
    l1nodes = {}
    i = 1
    with open("jsonfiles/l1Nodes.json", 'wb') as f:
        for item in thexml.getElementsByTagName("ns31:node"):
            if item.getElementsByTagName("ns31:product-series")[
                0].firstChild.nodeValue == "Cisco Network Convergence System 2000 Series":
                nodeName = item.getElementsByTagName("ns31:name")[0].firstChild.nodeValue
                latitude = item.getElementsByTagName("ns31:latitude")[0].getElementsByTagName("ns32:double-amount")[
                    0].firstChild.nodeValue
                longitude = item.getElementsByTagName("ns31:longitude")[0].getElementsByTagName("ns32:double-amount")[
                    0].firstChild.nodeValue
                l1nodes['Node' + str(i)] = dict([('Name', nodeName), ('Latitude', latitude), ('Longitude', longitude)])
                i += 1
        f.write(json.dumps(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectL1links(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer"
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/l1-links-xml", 'wb') as f:
        f.write(xmlresponse)
        f.close()
    with open("xmlgets/l1-links-xml", 'rb') as f:
        xmlresponse = f.read()
        f.close()

    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error."
        return
    l1links = {}
    i = 1
    with open("jsonfiles/l1Links.json", 'wb') as f:
        for item in thexml.getElementsByTagName("ns17:topological-link"):
            fdn = item.getElementsByTagName("ns17:fdn")[0].firstChild.nodeValue
            l1links['Link' + str(i)] = dict([('fdn', fdn)])
            l1links['Link' + str(i)]['Nodes'] = []
            for subitem in item.getElementsByTagName("ns17:endpoint-list"):
                if subitem.childNodes.length > 3:
                    for subsubitem in subitem.getElementsByTagName("ns17:endpoint"):
                        endpoint = subsubitem.getElementsByTagName("ns17:endpoint-ref")[0].firstChild.nodeValue
                        node = endpoint.split('!')[1].split('=')[1]
                        l1links['Link' + str(i)].get('Nodes').append(node)
            i += 1
        f.write(json.dumps(l1links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectISIS(baseURL, epnmuser, epnmpassword):
    with open("xmlcode/post-cli-template", 'r') as f:
        xmlbody = f.read()
        f.close()

    uri = "/operations/v1/cisco-resource-activation:run-cli-configuration"
    xmlresponse = xmlcode.utils.rest_post_xml(baseURL, uri, xmlbody, epnmuser, epnmpassword)

    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message from websocket is not XML."
        return

    jobname = thexml.getElementsByTagName("ns13:job-name")[0].firstChild.nodeValue

    print "Successfully submitted the API call to retrieve the ISIS database."
    print "jobname is: " + jobname

    notDone = True
    print "Checking job status..."
    results = ""
    while notDone:
        time.sleep(5)
        uri = "/operations/v1/cisco-resource-activation:get-cli-configuration-run-status/" + jobname
        xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)
        try:
            thexml = xml.dom.minidom.parseString(xmlresponse)
        except xml.parsers.expat.ExpatError as err:
            print "XML parsing error."
            return
        try:
            print "Job status: " + thexml.getElementsByTagName("ns13:status")[0].firstChild.nodeValue
            if thexml.getElementsByTagName("ns13:status")[0].firstChild.nodeValue == "SUCCESS":
                print "Completed running the script..."
                results = thexml.getElementsByTagName("ns13:transcript")[0].firstChild.nodeValue
                notDone = False
        except IndexError:
            print "Run status: " + thexml.getElementsByTagName("ns13:run-status")[0].firstChild.nodeValue
            if thexml.getElementsByTagName("ns13:run-status")[0].firstChild.nodeValue == "COMPLETED":
                print "Completed running the script..."
                results = thexml.getElementsByTagName("ns13:transcript")[0].firstChild.nodeValue
                notDone = False

    print "Database received."
    with open("jsonfiles/isisdb", 'wb') as f:
        f.write(results)
        f.close()


def processISIS():
    nodes = {}
    with open("jsonfiles/isisdb", 'rb') as f:
        lines = f.read().splitlines()
        ilines = iter(lines)
        for line in ilines:
            if "00-00 " in line:
                node = line.split('.')[0]
                i = 0
            elif "Router ID" in line:
                routerid = line.split(':')[1].strip()
                nodes[node] = dict([('Loopback Address', routerid)])
                nodes[node]['Links'] = dict()
            elif "Metric" in line and "IS-Extended" in line:
                try:
                    neighbor = re.search('.*%s (.*).00' % ('IS-Extended'), line).group(1)
                    i += 1
                    linkid = "Link" + str(i)
                    nodes[node]['Links'][linkid] = dict([('Neighbor', neighbor)])
                except:
                    print "There was a problem parsing the neighbor!"
                try:
                    metric = re.search('Metric: (.*).*IS-Extended.*', line).group(1).strip()
                    nodes[node]['Links'][linkid]['Metric'] = metric
                except:
                    print "There was a problem parsing the metric!"
            elif "Affinity" in line:
                affinity = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Affinity'] = affinity
            elif "Interface IP Address" in line:
                localIP = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Local IP'] = localIP
            elif "Neighbor IP Address" in line:
                neighIP = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Neighbor IP'] = neighIP
            elif "Reservable Global pool BW" in line:
                rsvpBW = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['RSVP BW'] = rsvpBW
            elif "SRLGs" in line:
                nodes[node]['Links'][linkid]['SRLGs'] = dict()
                srlgs = next(ilines).strip().split(',')
                for srlg in srlgs:
                    nodes[node]['Links'][linkid]['SRLGs'][srlg.split(':')[0].strip()] = srlg.split(":")[1].strip()
        f.close()

    with open("jsonfiles/l3Links.json", "wb") as f:
        f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectMPLSinterfaces(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=mpls-link-layer"
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/tl-mpls-link-layer-xml", 'wb') as f:
        f.write(xmlresponse)
        f.close()
    with open("xmlgets/tl-mpls-link-layer-xml", 'rb') as f:
        xmlresponse = f.read()
        f.close()
    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message is not XML."
        return
    with open("jsonfiles/l3Links.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    names = []
    for k1, v1 in l3links.items():
        # print "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # print "***************Linkname is: " + k3
                    n1IP = v3.get('Local IP')
                    n2IP = v3.get('Neighbor IP')
                    name1 = n1IP + '-' + n2IP
                    name2 = n2IP + '-' + n1IP
                    matchedlink = False
                    for item in thexml.getElementsByTagName("ns17:topological-link"):
                        fdn = item.getElementsByTagName("ns17:fdn")[0].firstChild.nodeValue
                        # TODO fix this issue where discovered name is not getting set with Guy's testbed
                        discoveredname = item.getElementsByTagName("ns17:discovered-name")[0].firstChild.nodeValue
                        if (name1 == discoveredname or name2 == discoveredname):
                            matchedlink = True
                            names.append(discoveredname)
                            v3['discoveredname'] = discoveredname
                            node1 = \
                                item.getElementsByTagName("ns17:endpoint-ref")[0].firstChild.nodeValue.split('!')[
                                    1].split('=')[1]
                            node1intf = \
                                item.getElementsByTagName("ns17:endpoint-ref")[0].firstChild.nodeValue.split('!')[
                                    2].split('=')[2]
                            node1intfparsed = node1intf.split('-')[0]

                            node2 = \
                                item.getElementsByTagName("ns17:endpoint-ref")[1].firstChild.nodeValue.split('!')[
                                    1].split('=')[1]

                            node2intf = \
                                item.getElementsByTagName("ns17:endpoint-ref")[1].firstChild.nodeValue.split('!')[
                                    2].split('=')[2]
                            node2intfparsed = node2intf.split('-')[0]

                            if node2 == v3.get('Neighbor'):
                                v3['Neighbor Intf'] = node2intfparsed
                                v3['Local Intf'] = node1intfparsed
                            elif node1 == v3.get('Neighbor'):
                                v3['Neighbor Intf'] = node1intfparsed
                                v3['Local Intf'] = node2intfparsed
                            else:
                                print "Could not match node names for interface assignment!!!!!!"
                    if not matchedlink:
                        print "Could not match discovered name for node " + k1 + " link " + k3 + ": " + name1 + " or " + name2
    with open("jsonfiles/l3Links_add_tl.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectvirtualconnections(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-service-network:virtual-connection?type=optical"
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/vc-optical", 'wb') as f:
        f.write(xmlresponse)
        f.close()

    with open("jsonfiles/l3Links_add_tl.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    with open("xmlgets/vc-optical", 'rb') as f:
        xmlresponse = f.read()
        f.close()
    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message is not XML."
        return
    for item in thexml.getElementsByTagName("ns9:virtual-connection"):
        fdn = item.getElementsByTagName("ns9:fdn")[0].firstChild.nodeValue
        subtype = item.getElementsByTagName("ns9:subtype")[0].firstChild.nodeValue
        if subtype == "ns41:och-trail-uni":
            vcdict = {}
            for subitem in item.getElementsByTagName("ns9:termination-point-list"):
                for subsubitem in subitem.getElementsByTagName("ns9:termination-point"):
                    tmpfdn = subsubitem.getElementsByTagName("ns9:fdn")[0].firstChild.nodeValue
                    tmpnode = tmpfdn.split('!')[1].split('=')[1]
                    vcdict[tmpnode] = tmpfdn.split('!')[2].split('=')[2].split(';')[0]
            for k1, v1 in l3links.items():
                # print "**************Nodename is: " + k1
                for k2, v2 in v1.items():
                    if isinstance(v2, dict):
                        for k3, v3 in v2.items():
                            # print "***************Linkname is: " + k3
                            for node, intf in vcdict.items():
                                if node == k1:
                                    if parseintfnum(intf) == parseintfnum(v3.get('Local Intf')):
                                        v3['vc-fdn'] = fdn
    print "completed collecting virtual connections..."
    with open("jsonfiles/l3Links_add_vc.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def addL1hopstol3links(baseURL, epnmuser, epnmpassword):
    with open("jsonfiles/l3Links_add_vc.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    for k1, v1 in l3links.items():
        # print "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # print "***************Linkname is: " + k3
                    vcfdn = v3.get('vc-fdn')
                    if vcfdn != None:
                        l1hops = collectmultilayerroute(baseURL, epnmuser, epnmpassword, vcfdn)
                        v3['L1 Hops'] = l1hops
                        if len(l1hops) > 0:
                            print "Completed L3 link " + k1 + " " + k3
                        else:
                            print "Could not get L1 hops for " + k1 + " " + k3
                            print "vcFDN is " + vcfdn
                    else:
                        print "Node " + k1 + ":  " + k3 + " has no vcFDN.  Assuming it is a non-optical L3 link."

    print "completed collecting L1 paths..."
    with open("jsonfiles/l3Links_add_l1hops.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectmultilayerroute(baseURL, epnmuser, epnmpassword, vcfdn):
    uri = "/data/v1/cisco-resource-network:virtual-connection-multi-layer-route?vcFdn=" + vcfdn
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/multilayerroute", 'wb') as f:
        f.write(xmlresponse)
        f.close()

    with open("xmlgets/multilayerroute", 'rb') as f:
        xmlresponse = f.read()
        f.close()
    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message is not XML."
        return
    l1hops = {}
    l1hopsops = parsemultilayerroute(thexml, "ns17:ops-link-layer", "Optics")
    l1hopsots = parsemultilayerroute(thexml, "ns17:ots-link-layer", "LINE")
    i = 1
    for k, v in l1hopsops.items():
        l1hops['L1 Hop' + str(i)] = v
        i += 1
    for k, v in l1hopsots.items():
        l1hops['L1 Hop' + str(i)] = v
        i += 1
    return l1hops


def parsemultilayerroute(thexml, topologylayer, intftype):
    l1hops = {}
    tmpl1hops = {}
    tmpl1hops['Nodes'] = dict()
    firsthop = False
    i = 1
    for item in thexml.getElementsByTagName("ns17:virtual-connection-multi-layer-route"):
        subtype = item.getElementsByTagName("ns17:topology-layer")[0].firstChild.nodeValue
        if subtype == topologylayer:
            for subitem in item.getElementsByTagName("ns17:tl-list"):
                tmpfdn = subitem.getElementsByTagName("ns17:fdn")[0].firstChild.nodeValue
                for subsubitem in subitem.getElementsByTagName("ns17:endpoint-list"):
                    for subsubsubitem in subsubitem.getElementsByTagName("ns17:endpoint"):
                        tmpep = subsubsubitem.getElementsByTagName("ns17:endpoint-ref")[0].firstChild.nodeValue
                        tmpnode = tmpep.split('!')[1].split('=')[1]
                        tmpport = tmpep.split('!')[2].split('=')[2].split(';')[0]
                        tmpl1hops['Nodes'][tmpnode] = dict([('Port', tmpport)])
                    for key, val in tmpl1hops.get('Nodes').items():
                        porttype = val.get('Port')
                        if intftype in porttype: firsthop = True
                    if firsthop:
                        l1hops['L1 Hop' + str(i)] = tmpl1hops
                        l1hops['L1 Hop' + str(i)]['fdn'] = tmpfdn
                        i += 1
                    tmpl1hops = {}
                    tmpl1hops['Nodes'] = dict()
                    firsthop = False
                i = 1
    return l1hops


def reorderl1hops():
    with open("jsonfiles/l3Links_add_l1hops.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    for k1, v1 in l3links.items():
        # print "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # print "***************Linkname is: " + k3
                    if 'L1 Hops' in v3:
                        print "Node " + k1 + " " + k3 + " has L1 hops.  Processing..."
                        l1hops = []
                        for k4, v4 in v3.get('L1 Hops').items():
                            nodelist = []
                            for k5, v5 in v4.get('Nodes').items():
                                nodelist.append(k5)
                            l1hops.append(nodelist)
                        l1hopsordered = returnorderedlist(k1, l1hops)
                        if len(l1hopsordered) == 0:
                            print "error generating ordered L1 hops"
                        tmphops = []
                        completed = False
                        while not completed:
                            if len(l1hopsordered) == 0: completed = True
                            for hop in l1hopsordered:
                                for k4, v4 in v3.get('L1 Hops').items():
                                    tmpnodes = []
                                    for k5, v5 in v4.get('Nodes').items():
                                        tmpnodes.append(k5)
                                    if (hop[0] == tmpnodes[0] and hop[1] == tmpnodes[1]) or \
                                            (hop[0] == tmpnodes[1] and hop[1] == tmpnodes[0]):
                                        tmphops.append(v4)
                                        l1hopsordered.remove(hop)
                                        break
                                break
                        v3['Ordered L1 Hops'] = tmphops
                        v3.pop('L1 Hops')
                        # print "next L1 hop..."
    with open("jsonfiles/l3Links_final.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def returnorderedlist(firstnode, l1hops):
    l1hopsordered = []
    hopa = firstnode
    hopb = ""
    completed = False
    while not completed:
        if len(l1hops) == 0: completed = True
        for hop in l1hops:
            if hop[0] == firstnode or hop[1] == firstnode:
                l1hopsordered.insert(0, hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif (hopa == hop[0] or hopb == hop[1]) or (hopa == hop[1] or hopb == hop[0]):
                l1hopsordered.append(hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
    return l1hopsordered


def collectlsps(baseURL, epnmuser, epnmpassword):
    uri = "/data/v1/cisco-service-network:virtual-connection?type=mpls-te-tunnel"
    xmlresponse = xmlcode.utils.rest_get_xml(baseURL, uri, epnmuser, epnmpassword)

    with open("xmlgets/vc-mpls-te-tunnel-xml", 'wb') as f:
        f.write(xmlresponse)
        f.close()
    with open("xmlgets/vc-mpls-te-tunnel-xml", 'rb') as f:
        xmlresponse = f.read()
        f.close()

    try:
        thexml = xml.dom.minidom.parseString(xmlresponse)
    except xml.parsers.expat.ExpatError as err:
        print "XML parsing error.  The received message is not XML."
        return
    lsplist = []
    vcdict = {}
    i = 1
    for item in thexml.getElementsByTagName("ns9:virtual-connection"):
        adminstate = item.getElementsByTagName("ns9:admin-state")[0].firstChild.nodeValue
        fdn = item.getElementsByTagName("ns9:fdn")[0].firstChild.nodeValue
        if not adminstate == "ns4:admin-state-unavailable":
            direction = item.getElementsByTagName("ns9:direction")[0].firstChild.nodeValue
            vcdict['fdn'] = fdn
            vcdict['direction'] = direction
            for subsubitem in item.getElementsByTagName("ns9:termination-point-list"):
                tmpfdn = subsubitem.getElementsByTagName("ns9:fdn")[0].firstChild.nodeValue
                for subsubsubitem in subsubitem.getElementsByTagName("ns9:mpls-te-tunnel-tp"):
                    affinitybits = subsubsubitem.getElementsByTagName("ns9:affinity-bits")[0].firstChild.nodeValue
                    signalledBW = subsubsubitem.getElementsByTagName("ns9:signalled-bw")[0].firstChild.nodeValue
                    destinationIP = subsubsubitem.getElementsByTagName("ns9:destination-address")[
                        0].firstChild.nodeValue
                    for subsubsubsubitem in subsubitem.getElementsByTagName("ns9:fast-reroute"):
                        fastreroute = subsubsubsubitem.getElementsByTagName("ns9:is-enabled")[0].firstChild.nodeValue
            for subitem in item.getElementsByTagName("ns9:te-tunnel"):
                tunnelID = subitem.getElementsByTagName("ns9:tunnel-id")[0].firstChild.nodeValue
                tunnelsource = subitem.getElementsByTagName("ns9:tunnel-source")[0].firstChild.nodeValue
                tunneldestination = subitem.getElementsByTagName("ns9:tunnel-destination")[0].firstChild.nodeValue
                corouted = subitem.getElementsByTagName("ns9:co-routed-enabled")[0].firstChild.nodeValue
            vcdict['tufdn'] = tmpfdn
            vcdict['affinitybits'] = affinitybits
            vcdict['Destination IP'] = destinationIP
            vcdict['Tunnel ID'] = tunnelID
            vcdict['Tunnel Source'] = tunnelsource
            vcdict['Tunnel Destination'] = tunneldestination
            vcdict['co-routed'] = corouted
            vcdict['signalled-bw'] = signalledBW
            vcdict['FRR'] = fastreroute
            lsplist.append(vcdict)
            vcdict = {}
            i += 1
        else:
            print "Tunnel unavailable: " + fdn
    print "done"
    with open("jsonfiles/lsps.json", "wb") as f:
        f.write(json.dumps(lsplist, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def parseintfnum(nodeintf):
    nodeintfnum = ""
    intflist = ['HundredGigE', 'TenGigE', 'FortyGigE', 'Optics']
    returnstring = ""
    for i in intflist:
        try:  # this block is for Ethernet interfaces
            nodeintfnum = re.search('.*%s(.*)\..*' % (i), nodeintf).group(1)
            break
        except:
            pass
        try:  # this block is for "Optics" interfaces
            nodeintfnum = re.search('.*%s(.*).*' % (i), nodeintf).group(1)
            break
        except:
            pass
    try:
        re.search('%s(.*).*' % ('BDI'), nodeintf).group(1)
        nodeintfnum = nodeintf
        return nodeintfnum
    except:
        pass
    if nodeintfnum == "":
        print "Could not parse interface number!!!!!!!!!"
    else:
        if len(nodeintfnum.split('/')) == 5:
            shortnodeintfnum = nodeintfnum.split('/')[:-1]
        else:
            shortnodeintfnum = nodeintfnum.split('/')
        for num in shortnodeintfnum:
            returnstring += num + "/"

    return returnstring[:-1]