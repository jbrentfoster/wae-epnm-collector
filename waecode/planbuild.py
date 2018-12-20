import com.cisco.wae.design
import logging
import flexlsp_creator
from com.cisco.wae.design.model.net import HopType
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1LinkKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathKey
from com.cisco.wae.design.model.net import DemandKey
from com.cisco.wae.design.model.net import DemandEndpointKey
from com.cisco.wae.design.model.net import ServiceClassKey
from com.cisco.wae.design.model.net import LSPKey
from com.cisco.wae.design.model.traffic import DemandTrafficKey
from com.cisco.wae.design.model.net import TrafficLevelKey
# records
from com.cisco.wae.design.model.net import NodeRecord
from com.cisco.wae.design.model.net.layer1 import L1NodeRecord
from com.cisco.wae.design.model.net.layer1 import L1LinkRecord
from com.cisco.wae.design.model.net.layer1 import L1PortRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathRecord
from com.cisco.wae.design.model.net.layer1 import L1CircuitPathHopRecord
from com.cisco.wae.design.model.net import InterfaceRecord
from com.cisco.wae.design.model.net import CircuitRecord
from com.cisco.wae.design.model.net import DemandRecord
from com.cisco.wae.design.model.net import ServiceClassRecord
from com.cisco.wae.design.model.net import LSPRecord
from com.cisco.wae.design.model.net import SRLGRecord


def generateL1nodes(plan, l1nodelist):
    l1NodeManager = plan.getNetwork().getL1Network().getL1NodeManager()
    for l1node in l1nodelist:
        l1nodeRec = L1NodeRecord(name=l1node['Name'], site=l1node['sitekey'])
        newl1node = l1NodeManager.newL1Node(l1nodeRec)


def generateL1links(plan, l1linksdict):
    l1LinkManager = plan.getNetwork().getL1Network().getL1LinkManager()
    i = 1

    for k, v in l1linksdict.items():
        nodeAname = v['Nodes'][0]
        nodeBname = v['Nodes'][1]
        l1nodeAKey = L1NodeKey(nodeAname)
        l1nodeBKey = L1NodeKey(nodeBname)
        fdn = v['fdn']
        l1linkname = nodeAname + "_" + nodeBname + "_" + str(i)
        logging.info("Processing L1 link: " + fdn)
        l1linkRec = L1LinkRecord(name=fdn, l1NodeAKey=l1nodeAKey, l1NodeBKey=l1nodeBKey, description=l1linkname)
        try:
            l1LinkManager.newL1Link(l1linkRec)
        except Exception as err:
            logging.warn("Could not add L1 link to the plan!")
            logging.warn(err)
        i += 1


def generateL1circuit(plan, name, l1nodeA, l1nodeB, l1hops, bw):
    l1portManager = plan.getNetwork().getL1Network().getL1PortManager()
    l1nodeAKey = L1NodeKey(l1nodeA)
    l1nodeBKey = L1NodeKey(l1nodeB)
    l1portAname = name + '_port_to_' + l1nodeB
    l1portBname = name + '_port_to_' + l1nodeA
    l1portRecA = L1PortRecord(name=l1portAname, l1Node=l1nodeAKey)
    l1portRecB = L1PortRecord(name=l1portBname, l1Node=l1nodeBKey)

    l1portManager.newL1Port(l1portRecA)
    l1portManager.newL1Port(l1portRecB)

    l1portAkey = L1PortKey(name=l1portAname, l1Node=l1nodeAKey)
    l1portBkey = L1PortKey(name=l1portBname, l1Node=l1nodeBKey)

    l1circuitrec = L1CircuitRecord(name=name, l1PortAKey=l1portAkey, l1PortBKey=l1portBkey, bandwidth=bw)

    l1circuitManager = plan.getNetwork().getL1Network().getL1CircuitManager()
    l1circuit = l1circuitManager.newL1Circuit(l1circuitrec)

    l1circKey = L1CircuitKey(l1PortAKey=l1portAkey, l1PortBKey=l1portBkey)
    l1circuitpathRec = L1CircuitPathRecord(l1CircKey=l1circKey, pathOption=1)
    l1circuitpathManager = plan.getNetwork().getL1Network().getL1CircuitPathManager()
    l1circuitpath = l1circuitpathManager.newL1CircuitPath(l1circuitpathRec)

    l1linkManager = plan.getNetwork().getL1Network().getL1LinkManager()

    hoptype = HopType('PathStrict', 1)
    l1hoprec = L1CircuitPathHopRecord(l1CircPathKey=l1circuitpath.getKey(), hopNode=L1NodeKey(l1nodeA), step=0,
                                      type=hoptype)
    l1circuitpath.addHop(l1hoprec)
    c = 1
    for l1hop in l1hops:
        l1_nodeA_key = L1NodeKey(l1hop[0][0])
        l1_nodeB_key = L1NodeKey(l1hop[0][1])
        l1_link_name = l1hop[1]
        l1_link_key = L1LinkKey(l1_link_name, l1_nodeA_key, l1_nodeB_key)
        l1_link = l1linkManager.getL1Link(l1_link_key)
        l1hoprec = L1CircuitPathHopRecord(l1CircPathKey=l1circuitpath.getKey(), hopNode=l1_nodeA_key,
                                          hopLink=l1_link.getKey(), step=c, type=hoptype)
        l1circuitpath.addHop(l1hoprec)
        hops = l1circuitpath.getHops()
        c += 1
    return l1circuit


def generateL3nodes(plan, l3nodelist):
    for l3node in l3nodelist:
        nodeRec = NodeRecord(name=l3node['Name'])
        newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec)
        # newl3node.setLatitude(int(l3node['Y']))
        # newl3node.setLongitude(int(l3node['X']))


def generateL3circuits(plan, l3linksdict):
    c = 0
    i = 0
    linkslist = []
    l1NodeManager = plan.getNetwork().getL1Network().getL1NodeManager()
    nodemanager = plan.getNetwork().getNodeManager()
    duplicatelink = False
    circ_srlgs = {}
    for k1, v1 in l3linksdict.items():
        # logging.info "**************Nodename is: " + k1
        firstnode = k1
        if firstnode == "LYBRNYLB-01153A08A":
            pass
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.warn "***************Linkname is: " + k3
                    lastnode = v3['Neighbor']
                    if lastnode == "NYCKNYAL-0223502A":
                        pass
                    discoveredname = v3['discoveredname']
                    affinity = v3['Affinity']
                    firstnode_ip = [v3['Local IP']]
                    firstnode_intf = v3['Local Intf']
                    lastnode_ip = [v3['Neighbor IP']]
                    lastnode_intf = v3['Neighbor Intf']
                    te_metric = int(v3['TE Metric'])
                    igp_metric = int(v3['IGP Metric'])
                    rsvpbw = float(v3['RSVP BW'].split(' ')[0])
                    intfbw = getintfbw(rsvpbw)

                    srlgs = []
                    if 'SRLGs' in v3:
                        srlgs = v3['SRLGs']
                    #     for k4, v4 in v3['SRLGs'].items():
                    #         srlgs.append(v4)
                    for linkdiscoveredname in linkslist:
                        if discoveredname == linkdiscoveredname: duplicatelink = True
                    if 'Ordered L1 Hops' in v3 and not duplicatelink:
                        if len(v3['Ordered L1 Hops']) > 0:
                            linkslist.append(discoveredname)
                            c += 1
                            i += 1
                            l1hops, firstl1node, lastl1node = getfirstlastl1node(v3['Ordered L1 Hops'], firstnode,
                                                                                 lastnode)
                            firstsite = l1NodeManager.getL1Node(L1NodeKey(firstl1node)).getSite()
                            # print "Node is " + k1 + "Site is " + str(firstsite.getKey())
                            nodemanager.getNode(NodeKey(firstnode)).setSite(firstsite)
                            try:
                                lastsite = l1NodeManager.getL1Node(L1NodeKey(lastl1node)).getSite()
                            except Exception as err:
                                logging.warn("")
                            nodemanager.getNode(NodeKey(lastnode)).setSite(lastsite)

                            name = "L1_circuit_" + str(c)
                            try:
                                l1circuit = generateL1circuit(plan, name, firstl1node, lastl1node, l1hops,
                                                              intfbw)
                            except Exception as err:
                                logging.critical(
                                    "Could not generate L1 circuit for L3 circuit " + firstnode + " to " + lastnode + " " + k3)
                            name = "L3_circuit_" + str(i)
                            l3circuit = generateL3circuit(plan, name, firstnode, lastnode, affinity, firstnode_ip,
                                                          lastnode_ip, firstnode_intf, lastnode_intf, igp_metric, te_metric)
                            l3circuit.setL1Circuit(l1circuit)
                            l3circuit.setCapacity(l1circuit.getBandwidth())
                            intfdict = l3circuit.getAllInterfaces()
                            for k6, v6 in intfdict.items():
                                v6.setResvBW(int(rsvpbw / 1000))
                            circ_name = l3circuit.getName()
                            circ_key = l3circuit.getKey()
                            circ_dict = {'SRLGs': srlgs, 'Circuit Key': circ_key, 'discoveredname': discoveredname}
                            circ_srlgs[circ_name] = circ_dict

                    elif not duplicatelink:
                        i += 1
                        name = "L3_circuit_" + str(i)
                        linkslist.append(discoveredname)
                        l3circuit = generateL3circuit(plan, name, firstnode, lastnode, affinity, firstnode_ip,
                                                      lastnode_ip, firstnode_intf, lastnode_intf, igp_metric, te_metric)
                        l3circuit.setCapacity(intfbw)
                        intfdict = l3circuit.getAllInterfaces()
                        for k6, v6 in intfdict.items():
                            v6.setResvBW(int(rsvpbw / 1000))
                        circ_name = l3circuit.getName()
                        circ_key = l3circuit.getKey()
                        circ_dict = {'SRLGs': srlgs, 'Circuit Key': circ_key, 'discoveredname': discoveredname}
                        circ_srlgs[circ_name] = circ_dict

                    duplicatelink = False

    logging.info("Processing SRLG's...")
    process_srlgs(plan, circ_srlgs)


def generateL3circuit(plan, name, l3nodeA, l3nodeB, affinity, l3nodeA_ip, l3nodeB_ip, nodeAintfname, nodeBintfname,
                      igp_metric, te_metric):
    nodeAKey = NodeKey(l3nodeA)
    nodeBKey = NodeKey(l3nodeB)
    # nodeAintfname = "L3_intf_" + name + "_to_" + l3nodeB
    # nodeBintfname = "L3_intf_" + name + "_to_" + l3nodeA

    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    # logging.warn bin(int(affinity, scale))[2:].zfill(num_of_bits)
    affinitylist = list(bin(int(affinity, scale))[2:].zfill(num_of_bits))

    affinities = []
    c = 0
    for afbit in reversed(affinitylist):
        if afbit == '1':
            affinities.append(c)
        c += 1
    intfArec = InterfaceRecord(sourceKey=nodeAKey, name=nodeAintfname, isisLevel=2, affinityGroup=affinities,
                               ipAddresses=l3nodeA_ip, igpMetric=igp_metric, teMetric=te_metric)
    intfBrec = InterfaceRecord(sourceKey=nodeBKey, name=nodeBintfname, isisLevel=2, affinityGroup=affinities,
                               ipAddresses=l3nodeB_ip, igpMetric=igp_metric, teMetric=te_metric)
    circRec = CircuitRecord(name=name)
    network = plan.getNetwork()
    circuit = network.newConnection(ifaceARec=intfArec, ifaceBRec=intfBrec, circuitRec=circRec)

    return circuit


def process_srlgs(plan, circ_srlgs):
    srlg_mgr = plan.getNetwork().getSRLGManager()
    circ_mgr = plan.getNetwork().getCircuitManager()
    circ_recs = circ_mgr.getAllCircuitRecords()

    srlg_list = []
    for circ, circ_dict in circ_srlgs.items():
        for srlg in circ_dict['SRLGs']:
            if not srlg in srlg_list:
                logging.debug("Processing SRLG: " + srlg)
                circ_list = []
                circ_keys_list = []
                srlg_list.append(srlg)
                for circ2, circ_dict2 in circ_srlgs.items():
                    for srlg2 in circ_dict2['SRLGs']:
                        if srlg2 == srlg:
                            circ_list.append(circ_dict2)
                            circ_keys_list.append(circ_dict2['Circuit Key'])
                            break
                srlg_rec = SRLGRecord(circuitKeys=circ_keys_list, name=hex(int(srlg)), description="Foo")
                srlg_mgr.newSRLG(srlg_rec)


def assignSites(plan):
    node_manager = plan.getNetwork().getNodeManager()
    site_manager = plan.getNetwork().getSiteManager()
    nodes = node_manager.getAllNodes()
    for node in nodes:
        node_name = node_manager.getNode(node).getName()
        node_site = node_manager.getNode(node).getSite()
        if node_site != None:
            node_site_name = node_site.getName()
            logging.info("Node: " + node_name + " Site: " + node_site_name)
        else:
            logging.info("Node " + node_name + " does not have a site.")
            intf_dict = node_manager.getNode(node).getAllInterfaces()
            if len(intf_dict) > 0:
                for k, v in intf_dict.items():
                    circuit = v.getCircuit()
                    for k1, v1 in circuit.getAllInterfaces().items():
                        if k != k1:
                            logging.info("Connected node name is " + v1.getSource().getName())
                            node_rec = v1.getSource().getRecord()
                            if v1.getSource().getSite() is not None:
                                logging.info(
                                    "Setting site to connected node site: " + v1.getSource().getSite().getName())
                                connected_site = v1.getSource().getSite()
                                node_manager.getNode(node).setSite(connected_site)
                            else:
                                logging.info("Could not get site for connected node...")
                                site_name = set_site_using_name(site_manager, node_manager, node)
                                if site_name is not None:
                                    logging.info("Setting site based on node name to " + site_name)
                                else:
                                    logging.info("Could not match a site name!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        elif k1 == k1:
                            logging.info("Local node name is " + v1.getSource().getName())
            else:
                logging.info("Node does not have interfaces...")
                site_name = set_site_using_name(site_manager, node_manager, node)
                if site_name is not None:
                    logging.info("Setting site based on node name to " + site_name)
                else:
                    logging.info("Could not match a site name!!!!!!!!!!!!!!!!!!!!!!!!!!!")


def set_site_using_name(site_manager, node_manager, node):
    sites = site_manager.getAllSites()
    node_name = node_manager.getNode(node).getName()
    for x in range(14, 10, -1):
        for site in sites:
            site_name = site_manager.getSite(site).getName()
            try:
                site_name_prefix = site_name[0:x]
                node_name_prefix = node_name[0:x]
            except Exception as err:
                logging.info("Site or node name is less than " + x + " characters.")
            if site_name_prefix == node_name_prefix:
                logging.info("Setting site to " + site_name)
                node_manager.getNode(node).setSite(site_manager.getSite(site))
                return site_name


def generate_lsps(plan, lsps, l3nodeloopbacks, options, conn):
    index = 0
    for lsp in lsps:
        if isinstance(lsp['signalled-bw'], basestring):
            lspBW = int(int(lsp['signalled-bw']) / 1000)
        elif isinstance(lsp['signalled-bw'], int):
            lspBW = lsp['signalled-bw'] / 1000
        else:
            lspBW = '0'
            logging.warn('LSP did not have valid BW, setting to zero.')
        direction = lsp['direction']
        frr = False
        frrval = lsp['FRR']
        if frrval == 'true': frr = True
        index += 1
        # if lspBW > 0:
        if lsp['admin-state'] == 'com:admin-state-up':
            tuID = lsp['Tunnel ID']
            # lspName = lsp['fdn'].split('!')[1].split('=')[1]
            lspName = lsp['tufdn'].split('!')[1].split('=')[1] + "-" + \
                      lsp['tufdn'].split('!')[2].split('=')[2].split(';')[0]
            logging.info(lspName)
            demandName = "Demand for " + lspName
            src = getnodename(lsp['Tunnel Source'], l3nodeloopbacks)
            dest = getnodename(lsp['Tunnel Destination'], l3nodeloopbacks)
            if src == None or dest == None:
                logging.warn("Could not get valid source or destination node from Tu IP address")
                logging.warn("Could not add LSP to plan file: " + lspName)
            else:
                if direction == "com:bi-direction":
                    logging.info("Processing FlexLSP: " + src + " to " + dest + " Tu" + str(tuID))
                    nodes = [src, dest]
                    try:
                        flexlsp_creator.createflexlsp(options, conn, plan, nodes, lspName, lspBW)
                        new_demand_for_LSP(plan, src, dest, lspName + "_forward", demandName + "_forward", lspBW)
                        new_demand_for_LSP(plan, dest, src, lspName + "_reverse", demandName + "_reverse", lspBW)
                    except Exception as err:
                        logging.warn(
                            "Could not add LSP to topology due to FlexLSP routing errors: " + src + " to " + dest + " Tu" + str(
                                tuID))
                elif lsp['auto-route-announce-enabled'] == True:
                    logging.info("Processing Data LSP: " + src + " to " + dest + " Tu" + str(tuID))
                    new_private_lsp(plan, src, dest, lspName, lspBW, frr)
                    new_demand_for_LSP(plan, src, dest, lspName, demandName, lspBW)


def new_demand_for_LSP(id, src, dest, lspName, demandName, val):
    serviceClass = 'Default'
    serviceClassMgr = id.getNetwork().getServiceClassManager()
    serviceClassExists = serviceClassMgr.hasServiceClass(
        ServiceClassKey(name=serviceClass))
    if not serviceClassExists:
        serviceClassRecord = ServiceClassRecord(name=serviceClass)
        serviceClassMgr.newServiceClass(serviceClassRecord)

    keylist = serviceClassMgr.getAllServiceClassKeys()
    dmdRec = DemandRecord(
        name=demandName,
        source=DemandEndpointKey(key=src),
        destination=DemandEndpointKey(key=dest),
        serviceClass=ServiceClassKey(name='Default'),
        privateLSP=LSPKey(
            name=lspName,
            sourceKey=NodeKey(name=src)
        )
    )
    dmdMgr = id.getNetwork().getDemandManager()
    dmdMgr.newDemand(dmdRec)

    dmdTraffKey = DemandTrafficKey(
        traffLvlKey=TrafficLevelKey(name='Default'),
        dmdKey=DemandKey(
            name=demandName,
            source=DemandEndpointKey(key=src),
            destination=DemandEndpointKey(key=dest),
            serviceClass=ServiceClassKey(name='Default'),
        )
    )
    dmdTrafficMgr = id.getTrafficManager().getDemandTrafficManager()
    dmdTrafficMgr.setTraffic(dmdTraffKey, val)


def new_private_lsp(id, src, dest, name, lspBW, frr):
    lspRec = LSPRecord(
        sourceKey=NodeKey(name=src),
        name=name,
        destinationKey=NodeKey(name=dest),
        isActive=True,
        isPrivate=True,
        setupBW=lspBW,
        FRREnabled=True,
        type=LSPType.RSVP
    )
    lspMgr = id.getNetwork().getLSPManager()
    lspMgr.newLSP(lspRec)


def getnodename(loopback, nodelist):
    for node in nodelist:
        for k, v in node.items():
            if v == loopback:
                return k


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
        logging.warn("Error determining interface bandwidth!!!")
    return intfbw


def getfirstlastl1node(orderedl1hops, firstnode, lastnode):
    l1hops = []
    firstl1node = ""
    lastl1node = ""
    for l1hop in orderedl1hops:
        nodelist = []
        fdn = l1hop['fdn']
        firstlasthop = False
        for k5, v5 in l1hop['Nodes'].items():
            if k5 == firstnode or k5 == lastnode: firstlasthop = True
            nodelist.append(k5)
        if not firstlasthop:
            l1hops.append((nodelist, fdn))
            # l1hops.append(nodelist)
        elif nodelist[0] == firstnode:
            firstl1node = nodelist[1]
        elif nodelist[1] == firstnode:
            firstl1node = nodelist[0]
        elif nodelist[0] == lastnode:
            lastl1node = nodelist[1]
        elif nodelist[1] == lastnode:
            lastl1node = nodelist[0]
    return l1hops, firstl1node, lastl1node
