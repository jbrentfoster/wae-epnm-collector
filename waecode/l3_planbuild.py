import com.cisco.wae.design
import logging

from com.cisco.wae.design.model.net import HopType
from com.cisco.wae.design.model.net import LSPType
# keys
from com.cisco.wae.design.model.net import NodeKey
from com.cisco.wae.design.model.net import InterfaceKey
from com.cisco.wae.design.model.net.layer1 import L1NodeKey
from com.cisco.wae.design.model.net.layer1 import L1PortKey
from com.cisco.wae.design.model.net.layer1 import L1LinkKey
from com.cisco.wae.design.model.net.layer1 import L1CircuitKey
from com.cisco.wae.design.model.net import DemandKey
from com.cisco.wae.design.model.net import DemandEndpointKey
from com.cisco.wae.design.model.net import ServiceClassKey
from com.cisco.wae.design.model.net import LSPKey
from com.cisco.wae.design.model.traffic import DemandTrafficKey
from com.cisco.wae.design.model.net import TrafficLevelKey
# records
from com.cisco.wae.design.model.net import NodeRecord
from com.cisco.wae.design.model.net import SiteRecord
from com.cisco.wae.design.model.net import SiteKey
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


def generateL3nodes(plan, l3nodeslist):
    for l3node in l3nodeslist:
        name = l3node['attributes']['name']
        # logging.debug('This is the node:\n{}'.format(l3node))
        if check_node_exists(plan, name):
            logging.warn("Node already exists in plan file, will not add duplicate: " + name)
            continue
        longitude = float(l3node['longitude'])
        latitude = float(l3node['latitude'])
        siteName = l3node['siteName']
        vendor = 'Ciena'
        model = l3node['attributes']['typeGroup']
        os = l3node['attributes']['softwareVersion']
        description = l3node['attributes']['deviceType']
        # logging.debug(' L3 node name is : {}'.format(name))
        if l3node.get('attributes').get('ipAddress'):
            ipAddress = l3node['attributes']['ipAddress']
        else:
            ipAddress = ''
        nodeRec = NodeRecord(name=name,
                             model=model,
                             vendor=vendor,
                             os=os,
                             description=description,
                             ipAddress=ipAddress,
                             longitude=longitude,
                             latitude=latitude,
                             site=SiteKey(siteName))
        newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec) 


def generateL3circuits(plan, l3linksdict):
    i = 0
    linkslist = []
    duplicatelink = False
    # circ_srlgs = {}
    circuit_name_list = []

    for k1, v1 in l3linksdict.items():
        # logging.info "**************Nodename is: " + k1
        # logging.debug('Node Name is : {}'.format(k1))
        # firstnode = k1
        for k2, v2 in v1.items():
            if isinstance(v2, dict):
                for k3, v3 in v2.items():
                    # logging.warn "***************Linkname is: " + k3
                    firstnode = v3['l3node']
                    lastnode = v3['l3NeighborNode']
                    # logging.debug('lastnode Name is : {}'.format(lastnode))
                    # discoveredname = v3['discoveredname']
                    try:
                        affinity = v3['local Affinity']
                    except Exception as err:
                        affinity = ""
                    firstnode_ip = [v3['local IP']]
                    firstnode_intf = v3['local Intf']
                    if 'neighbor IP' in v3:
                        lastnode_ip = [v3['neighbor IP']]
                    else:
                        continue
                    lastnode_intf = v3['neighbor Intf']
                    # te_metric = int(v3['TE Metric'])
                    te_metric = 0
                    try:
                        igp_metric = int(v3['local IGP Metrics'])
                    except Exception as err:
                        igp_metric = 0
                    phy_bw = float(v3['local Phy BW'])
                    rsvpbw = float(v3['local RSVP BW'])
                    # intfbw = getintfbw(phy_bw)
                    intfbw = phy_bw
                    try:
                        circuitName = v3['circuitName']
                    except Exception as err:
                        circuitName = ""
                    discoveredname = v3['circuitName']
                    # Fix start and End nodes based on returned circuit naame. API is returning the incorrect start and end node for several nodes.
                    if '/' in circuitName:
                        if circuitName.split('/')[2] == firstnode.split('-')[0]:
                            nodea = firstnode
                            nodeb = lastnode
                            nodea_ip = firstnode_ip
                            nodeb_ip = lastnode_ip
                            nodea_intf = firstnode_intf
                            nodeb_intf = lastnode_intf
                        elif circuitName.split('/')[2] == lastnode.split('-')[0]:
                            nodea = lastnode
                            nodeb = firstnode
                            nodea_ip = lastnode_ip
                            nodeb_ip = firstnode_ip
                            nodea_intf = lastnode_intf
                            nodeb_intf = firstnode_intf
                    else:
                            nodea = firstnode
                            nodeb = lastnode
                            nodea_ip = firstnode_ip
                            nodeb_ip = lastnode_ip
                            nodea_intf = firstnode_intf
                            nodeb_intf = lastnode_intf

                    for linkdiscoveredname in linkslist:
                        if discoveredname == linkdiscoveredname: duplicatelink = True
                    if not duplicatelink:
                        linkslist.append(discoveredname)

                        rsvpbw = float(v3['local RSVP BW'])
                        # l3circuit = generateL3circuit(plan, tp_description, firstnode, lastnode, affinity, firstnode_ip,lastnode_ip, firstnode_intf, lastnode_intf, igp_metric, te_metric,rsvpbw)
                        l3circuit = generateL3circuit(plan, circuitName, nodea, nodeb, affinity, nodea_ip, nodeb_ip, nodea_intf, nodeb_intf, igp_metric, te_metric,rsvpbw)
                        logging.debug('Circuit Created : {}'.format(l3circuit))
                        if l3circuit:
                            l1CircuitManager = plan.getNetwork().getL1Network().getL1CircuitManager()
                            l1circuits = l1CircuitManager.getAllL1Circuits()
                            l3circuit.setCapacity(phy_bw)
                            intfdict = l3circuit.getAllInterfaces()
                            for k6, v6 in intfdict.items():
                                v6.setResvBW(int(rsvpbw))
                            for attr, val in l1circuits.items():
                                l1circuit_name = val.getName()
                                if l1circuit_name:
                                    # logging.info("L1 circuit name is " + l1circuit_name)
                                    l1circuit = l1CircuitManager.getL1Circuit(val.getKey())
                                    l1NodeA= l1circuit.getRecord().l1PortAKey.l1Node.name.split("-")[0]
                                    l1NodeB= l1circuit.getRecord().l1PortBKey.l1Node.name.split("-")[0]
                                    l3NodeA = nodea.split("-")[0]
                                    l3NodeB = nodeb.split("-")[0]
                                    if l1NodeA == l3NodeA and l1NodeB == l3NodeB:
                                        l3circuit.setL1Circuit(l1circuit)
                                        logging.info("L1 - L3 circuit mapping added ")
                    duplicatelink = False



def generateL3circuit(plan, name, l3nodeA, l3nodeB, affinity, l3nodeA_ip, l3nodeB_ip, nodeAintfname, nodeBintfname,igp_metric, te_metric,rsvpbw):
    nodeAKey = NodeKey(l3nodeA)
    nodeBKey = NodeKey(l3nodeB)
    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    affinities = []
    try:
        affinitylist = list(bin(int(affinity, scale))[2:].zfill(num_of_bits))
        c = 0
        for afbit in reversed(affinitylist):
            if afbit == '1':
                affinities.append(c)
            c += 1
    except Exception as err:
        affinities = []
    intfArec = InterfaceRecord(sourceKey=nodeAKey, name=nodeAintfname, isisLevel=2, affinityGroup=affinities,ipAddresses=l3nodeA_ip, igpMetric=igp_metric,reservableBW=rsvpbw)
    intfBrec = InterfaceRecord(sourceKey=nodeBKey, name=nodeBintfname, isisLevel=2, affinityGroup=affinities,ipAddresses=l3nodeB_ip, igpMetric=igp_metric,)
    circRec = CircuitRecord(name=name)
    network = plan.getNetwork()
    # logging.debug('This is circuit data : {} '.format(intfArec) )
    # logging.debug('This is circuit data : {} '.format(intfBrec))
    # logging.debug('This is circuit data : {} '.format(circRec))
    try:
        circuit = network.newConnection(ifaceARec=intfArec, ifaceBRec=intfBrec, circuitRec=circRec)
        return circuit
    except Exception as err:
        logging.warn('Could not create circuit for: ' + name)
        # logging.warn(err)

def getintfbw(bw):
    intfbw = 0
    if bw > 0 and bw <= 1000000:
        intfbw = 1000
    elif bw > 1000000 and bw <= 10000000:
        intfbw = 10000
    elif bw > 10000000 and bw <= 40000000:
        intfbw = 40000
    elif bw > 40000000 and bw <= 100000000:
        intfbw = 100000
    else:
        logging.warn("Error determining interface bandwidth!!!")
    return intfbw

def check_node_exists(plan, node_name):
    node_manager = plan.getNetwork().getNodeManager()
    all_node_keys = node_manager.getAllNodeKeys()
    for node_key in all_node_keys:
        if node_key.name == node_name:
            # logging.info(" node already exists in plan, skipping this one...")
            return True
    return False

def generate_lsps(plan, lsps, l3nodeloopbacks):
    index = 0
    for lsp in lsps:
        if isinstance(lsp['signalledBW'], basestring):
            lspBW = int(int(lsp['signalledBW'])/1000)
        elif isinstance(lsp['signalledBW'],int):
            lspBW = lsp['signalledBW']/1000
        else:
            lspBW = 0
            logging.debug('LSP did not have valid BW')
        direction = lsp['direction']
        frr = False
        frrval = 'false'
        if lsp.get('FRR'):
            frrval = lsp['FRR']
        if frrval == 'true': frr = True
        index +=1
        if lsp['adminstate'] == 'up':
            tunnelId = lsp['Tunnel Id']
            lspName = lsp['Tunnel Name']+"_"+tunnelId
            lspSetupPriority = lsp['setup-priority']
            lspHoldPriority = lsp['hold-priority']
            if lsp.get('affinitybits'):
                affinity = lsp['affinitybits']
            else:
                affinity = "0x01"
            tunnelType = lsp['Tunnel Type']
            demandName = "Demand for "+lspName
            # src = getNodeName(lsp['Tunnel Source'],l3nodeloopbacks)
            # destination = getNodeName(lsp['Tunnel Destination'],l3nodeloopbacks)
            src = lsp['Tunnel Headend']
            destination = lsp['Tunnel Tailend']
            if src == None or destination == None:
                logging.debug('Could not get valid source or destination')
            else:
                try:
                    new_lsp(plan, src, destination, lspName, lspBW, tunnelType, frr, lspSetupPriority, lspHoldPriority, affinity)
                    new_demand_lsp(plan, src, destination, lspName, demandName, lspBW)
                except Exception as err:
                        logging.warn("Could not process Data LSP: " + lspName)
                        logging.warn(err)


def new_lsp(plan, src, destination, lspName, lspBW, tunnelType, frr, lspSetupPriority, lspHoldPriority, affinity):
    lspRec = LSPRecord(
        sourceKey = NodeKey(name=src),
        name=lspName,
        destinationKey=NodeKey(name=destination),
        setupPriority=int(lspSetupPriority),
        holdPriority=int(lspHoldPriority),
        isActive=True,
        isPrivate=True,
        setupBW=lspBW,
        FRREnabled=True,
        type=LSPType.RSVP,
        includeAffinities=getAffinities(affinity)
    )

    lspManager=plan.getNetwork().getLSPManager()
    lspManager.newLSP(lspRec)

def new_demand_lsp(plan, src, destination, lspName, demandName, lspBW):
    serviceClass = 'Default'
    serviceClassMgr = plan.getNetwork().getServiceClassManager()
    serviceClassExists = serviceClassMgr.hasServiceClass(
        ServiceClassKey(name=serviceClass))

    if not serviceClassExists:
        svcClassRec = ServiceClassRecord(name=serviceClass)
        serviceClassMgr.newServiceClass(svcClassRec)

    keyList = serviceClassMgr.getAllServiceClassKeys()
    demandRec = DemandRecord(
        name=demandName,
        source=DemandEndpointKey(key=src),
        destination=DemandEndpointKey(key=destination),
        serviceClass=ServiceClassKey(name='Default'),
        privateLSP=LSPKey(
            name=lspName,
            sourceKey=NodeKey(name=src)
        )
    )
    demandManager = plan.getNetwork().getDemandManager()
    demandManager.newDemand(demandRec)
    demandTraffKey = DemandTrafficKey(
        traffLvlKey=TrafficLevelKey(name='Default'),
        dmdKey=DemandKey(
            name=demandName,
            source=DemandEndpointKey(key=src),
            destination=DemandEndpointKey(key=destination),
            serviceClass=ServiceClassKey(name='Default'),
        )
    )
    demandTraffManager = plan.getTrafficManager().getDemandTrafficManager()
    demandTraffManager.setTraffic(demandTraffKey,lspBW)


def getNodeName(nodeAddress, nodelist):
    for node in nodelist:
        for k, v in node.items():
            if v == nodeAddress:
                return k

def getAffinities(affinity):
    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    # print bin(int(affinity, scale))[2:].zfill(num_of_bits)
    affinitylist = list(bin(int(affinity, scale))[2:].zfill(num_of_bits))

    affinities = []
    c = 0
    for afbit in reversed(affinitylist):
        if afbit == '1':
            affinities.append(c)
        c += 1
    return affinities