import collectioncode.utils
import time
import re
import json
import logging
import sys


def runcollector(baseURL, epnmuser, epnmpassword, seednode_id):
    logging.info("Collecting L1 nodes...")
    collectL1Nodes_json(baseURL, epnmuser, epnmpassword)
    logging.info("Collecting L1 links...")
    collectL1links_json(baseURL, epnmuser, epnmpassword)
    # logging.info("Collecting ISIS database...")
    # collectISIS_json(baseURL, epnmuser, epnmpassword, seednode_id)
    # logging.info("Processing ISIS database...")
    # processISIS()
    # logging.info("Collecting MPLS topological links...")
    # try:
    #     collectMPLSinterfaces_json(baseURL, epnmuser, epnmpassword)
    # except Exception as err:
    #     logging.critical("MPLS topological links are not valid.  Halting execution.")
    #     sys.exit("Collection error.  Halting execution.")
    #
    # logging.info("Collecting virtual connections...")
    # collectvirtualconnections_json(baseURL, epnmuser, epnmpassword)
    # logging.info("Collecting L1 paths...")
    # addL1hopstol3links(baseURL, epnmuser, epnmpassword)
    # logging.info("Re-ordering L1 hops...")
    # reorderl1hops()
    # logging.info("Network collection completed!")
    # logging.info("Collecting LSPs...")
    # collectlsps_json(baseURL, epnmuser, epnmpassword)


def collectL1Nodes_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-physical:node?product-series=Cisco Network Convergence System 2000 Series&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
        else:
            incomplete = False
        merge(jsonmerged,jsonaddition)

    with open("jsongets/l1-nodes.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/l1-nodes.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    l1nodes = {}
    i = 1
    with open("jsonfiles/l1Nodes.json", 'wb') as f:
        for node in thejson['com.response-message']['com.data']['nd.node']:
            if node['nd.product-series'] == "Cisco Network Convergence System 2000 Series":
                nodeName = node['nd.name']
                logging.info("Processing node " + nodeName)
                try:
                    latitude = node['nd.latitude']
                    longitude = node['nd.longitude']
                except KeyError:
                    logging.error("Could not get longitude or latitidude for node " + nodeName + ".  Setting to 0.0 and 0.0")
                    latitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
                    longitude = {'fdtn.double-amount': 0.0, 'fdtn.units': 'DEGREES_DECIMAL'}
                l1nodes['Node' + str(i)] = dict([('Name', nodeName), ('Latitude', latitude), ('Longitude', longitude)])
                i += 1
        f.write(json.dumps(l1nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

def collectL1links_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
        else:
            incomplete = False
        merge(jsonmerged,jsonaddition)

    with open("jsongets/l1-links.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/l1-links.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    l1links = {}
    i = 1
    with open("jsonfiles/l1Links.json", 'wb') as f:
        for link in thejson['com.response-message']['com.data']['topo.topological-link']:
            fdn = link['topo.fdn']
            nodes = []
            endpointlist = link['topo.endpoint-list']['topo.endpoint']

            if len(endpointlist) > 1:
                for ep in endpointlist:
                    endpoint = ep['topo.endpoint-ref']
                    node = endpoint.split('!')[1].split('=')[1]
                    nodes.append(node)
                if len(nodes) > 1:
                    duplicates = False
                    if not duplicates:
                        l1links['Link' + str(i)] = dict([('fdn', fdn)])
                        l1links['Link' + str(i)]['Nodes'] = nodes
                    i += 1
        f.write(json.dumps(l1links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectISIS_json(baseURL, epnmuser, epnmpassword, seednode_id):
    with open("collectioncode/post-cli-template.json", 'r') as f:
        jsonbody = f.read()
        f.close()
    jsonbody_js = json.loads(jsonbody)

    seednode = jsonbody_js['ra.run-cli-configuration']['ra.target-list']['ra.target']['ra.node-ref']
    nodeid = seednode.split('=')[2]
    new_nodeid = seednode_id
    seednode = seednode.replace(nodeid, new_nodeid)

    jsonbody_js['ra.run-cli-configuration']['ra.target-list']['ra.target']['ra.node-ref'] = seednode
    jsonbody = json.dumps(jsonbody_js)

    uri = "/operations/v1/cisco-resource-activation:run-cli-configuration"
    jsonresponse = collectioncode.utils.rest_post_json(baseURL, uri, jsonbody, epnmuser, epnmpassword)

    thejson = json.loads(jsonresponse)

    jobname = thejson['ra.config-response']['ra.job-status']['ra.job-name']

    logging.info("Successfully submitted the API call to retrieve the ISIS database.")
    logging.info("jobname is: " + jobname)

    notDone = True
    logging.info("Checking job status...")
    results = ""
    while notDone:
        time.sleep(5)
        uri = "/operations/v1/cisco-resource-activation:get-cli-configuration-run-status/" + jobname
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        thejson = json.loads(jsonresponse)
        try:
            status = thejson['ra.config-response']['ra.job-status']['ra.status']
            logging.info("Job status: " + status)
            if status == "SUCCESS":
                logging.info("Completed running the script...")
                results = thejson['ra.config-response']['ra.deploy-result-list']['ra.deploy-result']['ra.transcript']
                notDone = False
            elif status == "FAILURE":
                logging.critical("Could not get ISIS database!!!!!!")
                sys.exit("Collection error.  Ending execution.")
        except KeyError:
            status = thejson['ra.config-response']['ra.job-status']['ra.run-status']
            logging.info("Run status: " + status)
            if status == "COMPLETED":
                logging.info("Completed running the script...")
                results = thejson['ra.deploy-result']['ra.transcript']
                notDone = False
            elif status == "FAILURE":
                logging.critical("Could not get ISIS database!!!!!!")
                sys.exit("Collection error.  Ending execution.")

    logging.info("Database received.")
    with open("jsonfiles/isisdb", 'wb') as f:
        f.write(results)
        f.close()


def processISIS():
    nodes = {}
    with open("jsonfiles/isisdb", 'rb') as f:
        lines = f.read().splitlines()
        ilines = lines
        c = 0
        for line in ilines:
            if "00-00 " in line or "00-00*" in line:
                node = line.split('.')[0]
                i = 0
                ignoreIntfIPs = False
                foundfirstlink = False
            elif "Router ID" in line:
                routerid = line.split(':')[1].strip()
                nodes[node] = dict([('Loopback Address', routerid)])
                nodes[node]['Links'] = dict()
            elif "Metric" in line and "IS-Extended" in line:
                ignoreIntfIPs = False
                foundfirstlink = True
                try:
                    neighbor = re.search('.*%s (.*).00' % ('IS-Extended'), line).group(1)
                    i += 1
                    linkid = "Link" + str(i)
                    nodes[node]['Links'][linkid] = dict([('Neighbor', neighbor)])
                except Exception as err:
                    logging.warn("There was a problem parsing the neighbor!")
                    logging.exception(err)
                    logging.critical("Critical error!")
                    sys.exit("ISIS database is not complete for node " + node + "!!! Halting execution!")
                try:
                    metric = re.search('Metric: (.*).*IS-Extended.*', line).group(1).strip()
                    nodes[node]['Links'][linkid]['Metric'] = metric
                except Exception as err:
                    logging.warn("There was a problem parsing the metric!")
                    logging.exception(err)
                    logging.critical("Critical error!")
                    sys.exit("ISIS database is not complete for node " + node + "!!! Halting execution!")
            elif "Affinity" in line:
                affinity = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Affinity'] = affinity
            elif "MPLS SRLG" in line:
                ignoreIntfIPs = True
            elif "Interface IP Address" in line and not ignoreIntfIPs:
                localIP = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Local IP'] = localIP
            elif "Neighbor IP Address" in line and not ignoreIntfIPs:
                neighIP = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['Neighbor IP'] = neighIP
            elif "Reservable Global pool BW" in line:
                rsvpBW = line.split(':')[1].strip()
                nodes[node]['Links'][linkid]['RSVP BW'] = rsvpBW
            elif "SRLGs" in line and foundfirstlink:
                nodes[node]['Links'][linkid]['SRLGs'] = dict()
                d = 1
                srlgs = []
                while True:
                    tline = ilines[c + d]
                    if "[" in tline:
                        srlgs = srlgs + tline.strip().split(',')
                        d += 1
                    else:
                        break
                for srlg in srlgs:
                    if ":" in srlg:
                        nodes[node]['Links'][linkid]['SRLGs'][srlg.split(':')[0].strip()] = srlg.split(":")[1].strip()
                    else:
                        logging.info("Errored SRLG list found while processing isis db line " + str(c))
            c += 1
        f.close()

    # go through links and remove any invalid links
    for k1, v1 in nodes.items():
        # logging.info "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.info "***************Linkname is: " + k3
                    if not 'Affinity' in v3:
                        v2.pop(k3)
                        logging.info("Removing invalid link with neighbor " + v3['Neighbor'])

    with open("jsonfiles/l3Links.json", "wb") as f:
        f.write(json.dumps(nodes, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectMPLSinterfaces_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=mpls-link-layer&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
        else:
            incomplete = False
        merge(jsonmerged,jsonaddition)

    with open("jsongets/tl-mpls-link-layer.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/tl-mpls-link-layer.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    with open("jsonfiles/l3Links.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    names = []
    for k1, v1 in l3links.items():
        # logging.info "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.info "***************Linkname is: " + k3
                    n1IP = v3.get('Local IP')
                    n2IP = v3.get('Neighbor IP')
                    name1 = n1IP + '-' + n2IP
                    name2 = n2IP + '-' + n1IP
                    matchedlink = False
                    for item in thejson['com.response-message']['com.data']['topo.topological-link']:

                        # for item in thexml.getElementsByTagName("ns17:topological-link"):
                        fdn = item['topo.fdn']
                        discoveredname = item['topo.discovered-name']
                        if (name1 == discoveredname or name2 == discoveredname):
                            matchedlink = True
                            names.append(discoveredname)
                            v3['discoveredname'] = discoveredname
                            try:
                                parse1 = item['topo.endpoint-list']['topo.endpoint'][0]['topo.endpoint-ref']
                                node1 = parse1.split('!')[1].split('=')[1]
                                node1intf = parse1.split('!')[2].split('=')[2]
                                node1intfparsed = node1intf.split('-')[0]

                                parse2 = item['topo.endpoint-list']['topo.endpoint'][1]['topo.endpoint-ref']
                                node2 = parse2.split('!')[1].split('=')[1]
                                node2intf = parse2.split('!')[2].split('=')[2]
                                node2intfparsed = node2intf.split('-')[0]

                                if node2 == v3['Neighbor']:
                                    v3['Neighbor Intf'] = node2intfparsed
                                    v3['Local Intf'] = node1intfparsed
                                elif node1 == v3['Neighbor']:
                                    v3['Neighbor Intf'] = node1intfparsed
                                    v3['Local Intf'] = node2intfparsed
                                else:
                                    logging.warn(
                                        "Could not match node names for interface assignment for node " + k1 + " link " + k3)
                                    logging.warn("Removing link from topology...")
                                    v2.pop(k3)
                            except Exception as err:
                                logging.critical("Missing endpoint-ref for " + k1 + " " + k3 + " " + discoveredname)
                                # sys.exit("Collection error.  Halting execution.")
                                logging.warn("Removing link from topology...")
                                v2.pop(k3)
                    if not matchedlink:
                        logging.warn(
                            "Could not match discovered name for node " + k1 + " link " + k3 + ": " + name1 + " or " + name2)
                        logging.warn("Removing link from topology...")
                        v2.pop(k3)
    with open("jsonfiles/l3Links_add_tl.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectvirtualconnections_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-service-network:virtual-connection?type=optical&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
        else:
            incomplete = False
        merge(jsonmerged,jsonaddition)

    with open("jsongets/vc-optical.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()

    with open("jsonfiles/l3Links_add_tl.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    with open("jsongets/vc-optical.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    for item in thejson['com.response-message']['com.data']['vc.virtual-connection']:
        matched_fdn = False
        fdn = item['vc.fdn']
        subtype = item['vc.subtype']
        if subtype == "oc:och-trail-uni":
            vcdict = {}
            logging.info("Processing virtual connection: " + fdn)
            try:
                for subitem in item['vc.termination-point-list']['vc.termination-point']:
                    tmpfdn = subitem['vc.fdn']
                    tmpnode = tmpfdn.split('!')[1].split('=')[1]
                    tmpoptics = tmpfdn.split('!')[2].split('=')[2].split(';')[0]
                    vcdict[tmpnode] = tmpoptics
                for k1, v1 in l3links.items():
                    # logging.info "**************Nodename is: " + k1
                    for k2, v2 in v1.items():
                        if isinstance(v2, dict):
                            for k3, v3 in v2.items():
                                # logging.info "***************Linkname is: " + k3
                                for node, intf in vcdict.items():
                                    if node == k1:
                                        if parseintfnum(intf) == parseintfnum(v3.get('Local Intf')):
                                            v3['vc-fdn'] = fdn
                                            matched_fdn = True
                                            # if not matched_fdn:
                                            #     logging.info "Could not match vc-fdn " + fdn
            except KeyError:
                logging.error("Could not get virtual connection for " + fdn)
            except TypeError:
                logging.error("Type error encountered for " + fdn)
    logging.info("Completed collecting virtual connections...")
    with open("jsonfiles/l3Links_add_vc.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def addL1hopstol3links(baseURL, epnmuser, epnmpassword):
    with open("jsonfiles/l3Links_add_vc.json", 'rb') as f:
        l3links = json.load(f)
        f.close()

    for k1, v1 in l3links.items():
        # logging.info "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.info "***************Linkname is: " + k3
                    if 'vc-fdn' in v3:
                        vcfdn = v3['vc-fdn']
                        l1hops = collectmultilayerroute_json(baseURL, epnmuser, epnmpassword, vcfdn)
                        v3['L1 Hops'] = l1hops
                        if len(l1hops) > 0:
                            logging.info("Completed L3 link " + k1 + " " + k3)
                        else:
                            logging.info("Could not get L1 hops for " + k1 + " " + k3)
                            logging.info("vcFDN is " + vcfdn)
                    else:
                        logging.info(
                            "Node " + k1 + ":  " + k3 + " has no vcFDN.  Assuming it is a non-optical L3 link.")
                        try:
                            logging.info("    Neighbor: " + v3['Neighbor'])
                            logging.info("    Local Intf: " + v3['Local Intf'])
                            logging.info("    Neighbor Intf: " + v3['Neighbor Intf'])
                        except Exception as err:
                            logging.warn("    Serious error encountered.  EPNM is likely in partial state!!!")

    logging.info("completed collecting L1 paths...")
    with open("jsonfiles/l3Links_add_l1hops.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def collectmultilayerroute_json(baseURL, epnmuser, epnmpassword, vcfdn):
    uri = "/data/v1/cisco-resource-network:virtual-connection-multi-layer-route?vcFdn=" + vcfdn
    jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)

    with open("jsongets/multilayer_route.json", 'wb') as f:
        f.write(jsonresponse)
        f.close()

    with open("jsongets/multilayer_route.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    l1hops = {}
    l1hopsops = parsemultilayerroute_json(thejson, "topo:ops-link-layer", "Optics")
    l1hopsots = parsemultilayerroute_json(thejson, "topo:ots-link-layer", "LINE")
    i = 1
    for k, v in l1hopsops.items():
        l1hops['L1 Hop' + str(i)] = v
        i += 1
    for k, v in l1hopsots.items():
        l1hops['L1 Hop' + str(i)] = v
        i += 1
    return l1hops


def parsemultilayerroute_json(jsonresponse, topologylayer, intftype):
    l1hops = {}
    tmpl1hops = {}
    tmpl1hops['Nodes'] = dict()
    firsthop = False
    i = 1
    for item in jsonresponse['com.response-message']['com.data']['topo.virtual-connection-multi-layer-route-list'][
        'topo.virtual-connection-multi-layer-route']:
        subtype = item['topo.topology-layer']
        if subtype == topologylayer:
            topo_links = item['topo.tl-list']['topo.topological-link']
            if isinstance(topo_links, list):
                for subitem in topo_links:
                    tmpfdn = subitem['topo.fdn']
                    for subsubitem in subitem['topo.endpoint-list']['topo.endpoint']:
                        tmpep = subsubitem['topo.endpoint-ref']
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
            else:
                tmpfdn = topo_links['topo.fdn']
                for subitem in topo_links['topo.endpoint-list']['topo.endpoint']:
                    tmpep = subitem['topo.endpoint-ref']
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
        # logging.info "**************Nodename is: " + k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.info "***************Linkname is: " + k3
                    if 'L1 Hops' in v3:
                        logging.info("Node " + k1 + " " + k3 + " has L1 hops.  Processing...")
                        l1hops = []
                        for k4, v4 in v3.get('L1 Hops').items():
                            nodelist = []
                            for k5, v5 in v4.get('Nodes').items():
                                nodelist.append(k5)
                            l1hops.append(nodelist)
                        l1hopsordered = returnorderedlist(k1, l1hops)
                        if len(l1hopsordered) == 0:
                            logging.info("error generating ordered L1 hops")
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
                        # logging.info "next L1 hop..."
    with open("jsonfiles/l3Links_final.json", "wb") as f:
        f.write(json.dumps(l3links, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()


def returnorderedlist(firstnode, l1hops):
    l1hopsordered = []
    hopa = firstnode
    hopb = ""
    completed = False
    loopcount = 0
    while not completed:
        if len(l1hops) == 0: completed = True
        for hop in l1hops:
            if len(hop) != 2:
                logging.warn("Invalid L1 hop!  Could not process L1 hops for " + firstnode + " !!!!")
                return l1hopsordered
            elif hop[0] == firstnode or hop[1] == firstnode:
                l1hopsordered.insert(0, hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif (hopa == hop[0] or hopb == hop[1]) or (hopa == hop[1] or hopb == hop[0]):
                l1hopsordered.append(hop)
                l1hops.remove(hop)
                hopa = hop[0]
                hopb = hop[1]
            elif loopcount > 50:
                logging.warn("Could not process L1 hops for " + firstnode + " !!!!")
                return l1hopsordered
            loopcount += 1
    return l1hopsordered


def collectlsps_json(baseURL, epnmuser, epnmpassword):
    incomplete = True
    startindex = 0
    jsonmerged = {}
    while incomplete:
        uri = "/data/v1/cisco-service-network:virtual-connection?type=mpls-te-tunnel&.startIndex=" + str(startindex)
        jsonresponse = collectioncode.utils.rest_get_json(baseURL, uri, epnmuser, epnmpassword)
        jsonaddition = json.loads(jsonresponse)
        firstindex = jsonaddition['com.response-message']['com.header']['com.firstIndex']
        lastindex = jsonaddition['com.response-message']['com.header']['com.lastIndex']
        if (lastindex - firstindex) == 99 and lastindex != -1:
            startindex += 100
        else:
            incomplete = False
        merge(jsonmerged,jsonaddition)

    with open("jsongets/vc-mpls-te-tunnel.json", 'wb') as f:
        f.write(json.dumps(jsonmerged, f, sort_keys=True, indent=4, separators=(',', ': ')))
        f.close()
    with open("jsongets/vc-mpls-te-tunnel.json", 'rb') as f:
        jsonresponse = f.read()
        f.close()

    thejson = json.loads(jsonresponse)

    lsplist = []
    vcdict = {}



    for item in thejson['com.response-message']['com.data']['vc.virtual-connection']:
        tmpfdn = None
        adminstate = None
        affinitybits = None
        affinitymask = None
        destinationIP = None
        tunnelID = None
        tunnelsource = None
        tunneldestination = None
        corouted = None
        signalledBW = None
        fastreroute = None
        adminstate = None
        fdn = None
        erroredlsp = False
        autoroute = None
        adminstate = item['vc.admin-state']
        fdn = item['vc.fdn']
        if adminstate == "com:admin-state-up":
            direction = item['vc.direction']
            vcdict['fdn'] = fdn
            vcdict['direction'] = direction
            term_point = item['vc.termination-point-list']['vc.termination-point']
            if isinstance(term_point, dict):
                tmpfdn = item['vc.termination-point-list']['vc.termination-point']['vc.fdn']
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point']['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                signalledBW = subsubsubitem['vc.signalled-bw']
                destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True
            else:
                logging.info("List format term_point " + fdn)
                tmpfdn = item['vc.termination-point-list']['vc.termination-point'][0]['vc.fdn']
                subsubsubitem = item['vc.termination-point-list']['vc.termination-point'][0]['vc.mpls-te-tunnel-tp']
                try:
                    affinitybits = subsubsubitem['vc.affinity-bits']
                    affinitymask = subsubsubitem['vc.affinity-mask']
                except Exception as err2:
                    logging.warn("LSP has no affinity bits: " + fdn)
                signalledBW = subsubsubitem['vc.signalled-bw']
                destinationIP = subsubsubitem['vc.destination-address']
                autoroute = subsubsubitem['vc.auto-route-announce-enabled']
                fastreroute = subsubsubitem['vc.fast-reroute']['vc.is-enabled']
                try:
                    subitem = item['vc.te-tunnel']
                    tunnelID = subitem['vc.tunnel-id']
                    tunnelsource = subitem['vc.tunnel-source']
                    tunneldestination = subitem['vc.tunnel-destination']
                    corouted = subitem['vc.co-routed-enabled']
                except Exception as err:
                    logging.warn("Exception: could not get LSP te-tunnel attributes for " + fdn)
                    logging.warn(err)
                    erroredlsp = True

            if not erroredlsp:
                vcdict['admin-state'] = adminstate
                vcdict['tufdn'] = tmpfdn
                vcdict['affinitybits'] = affinitybits
                vcdict['affinitymask'] = affinitymask
                vcdict['Destination IP'] = destinationIP
                vcdict['Tunnel ID'] = tunnelID
                vcdict['Tunnel Source'] = tunnelsource
                vcdict['Tunnel Destination'] = tunneldestination
                vcdict['co-routed'] = corouted
                vcdict['signalled-bw'] = signalledBW
                vcdict['FRR'] = fastreroute
                vcdict['auto-route-announce-enabled'] = autoroute
                lsplist.append(vcdict)
                logging.info(
                    "Collected tunnel " + str(
                        tunnelID) + " Source: " + tunnelsource + " Destination " + tunneldestination)
            else:
                logging.warn("Could not retrieve necessary attributes.  LSP will be left out of plan: " + fdn)
            vcdict = {}
        else:
            logging.warning("Tunnel unavailable: " + fdn)
    logging.info("Completed collecting LSPs...")
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
        logging.info("Could not parse interface number!!!!!!!!!")
    else:
        if len(nodeintfnum.split('/')) == 5:
            shortnodeintfnum = nodeintfnum.split('/')[:-1]
        else:
            shortnodeintfnum = nodeintfnum.split('/')
        for num in shortnodeintfnum:
            returnstring += num + "/"

    return returnstring[:-1]

def merge(a, b):
    "merges b into a"
    for key in b:
        if key in a:# if key is in both a and b
            if isinstance(a[key], dict) and isinstance(b[key], dict): # if the key is dict Object
                merge(a[key], b[key])
            else:
              a[key] =a[key]+ b[key]
        else: # if the key is not in dict a , add it to dict a
            a.update({key:b[key]})
    return a