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
        # site = l3node['wae_site_name']
        vendor = 'Ciena'
        # model = 'Ciena6500'
        model = l3node['attributes']['resourceType']
        os = l3node['attributes']['softwareVersion']
        description = l3node['attributes']['deviceType']
        logging.debug(' L3 node name is : {}'.format(name))
        if l3node.get('attributes').get('ipAddress'):
            ipManage = l3node['attributes']['ipAddress']
        else:
            ipManage = ''
        nodeRec = NodeRecord(name=name,
                             model=model,
                             vendor=vendor,
                             os=os,
                             description=description,
                             ipManage=ipManage,
                             longitude=longitude,
                             latitude=latitude)
        newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec) 
        # nodeRec = NodeRecord(name=name, vendor=vendor, model=model, site=SiteKey(
        #     site))
        # newl3node = plan.getNetwork().getNodeManager().newNode(nodeRec)

def generateL3circuits(plan, l3linksdict):
    i = 0
    linkslist = []
    duplicatelink = False
    circ_srlgs = {}
    circuit_name_list = []

    for k1, v1 in l3linksdict.items():
        # logging.info "**************Nodename is: " + k1
        logging.debug('Node Name is : {}'.format(k1))
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
                        affinity = v3['Local Affinity']
                    except Exception as err:
                        affinity = ""
                    firstnode_ip = [v3['local IP']]
                    firstnode_intf = v3['local Intf']
                    lastnode_ip = [v3['neighbor IP']]
                    lastnode_intf = v3['neighbor Intf']
                    # te_metric = int(v3['TE Metric'])
                    te_metric = 0
                    try:
                        igp_metric = int(v3['local IGP Metrics'])
                    except Exception as err:
                        igp_metric = 0
                    phy_bw = float(v3['local Phy BW'])
                    rsvpbw = float(v3['local RSVP BW'])
                    intfbw = getintfbw(phy_bw)
                    try:
                        tp_description = v3['circuitName']
                    except Exception as err:
                        tp_description = ""
                    discoveredname = v3['circuitName']
                    srlgs = []
                    if 'SRLGs' in v3:
                        srlgs = v3['SRLGs']
                    for linkdiscoveredname in linkslist:
                        if discoveredname == linkdiscoveredname: duplicatelink = True
                    if not duplicatelink:
                        linkslist.append(discoveredname)
                        name = ""
                        if tp_description == "":
                            for elem in circuit_name_list:
                                node_check = elem['1'] == firstnode and elem['3'] == lastnode
                                interface_check = elem['2'] == firstnode_intf and elem['4'] == lastnode_intf
                                if node_check and interface_check:
                                    name = elem['0']
                                    break
                                elif elem['1'] == firstnode and elem['2'].startswith('BDI'):
                                    name = elem['0']
                                    break
                            if name == "":
                                i += 1
                                name = 'l3_circuit_{}/{}/{}'.format(int(i), firstnode, lastnode)
                        else:
                            if 'CktId: ' in tp_description:
                                name = tp_description.split('CktId: ')[1]
                            elif 'CID:' in tp_description:
                                name = tp_description.split('CID:')[1]
                            else:
                                name = tp_description
  
                        rsvpbw = float(v3['local RSVP BW'])
                        l3circuit = generateL3circuit(plan, tp_description, firstnode, lastnode, affinity, firstnode_ip,lastnode_ip, firstnode_intf, lastnode_intf, igp_metric, te_metric,rsvpbw)
                        logging.debug('Circuit Created : {}'.format(l3circuit))
                        # if l3circuit:
                        #     if 'vc-fdn' in v3:
                        #         l1CircuitManager = plan.getNetwork().getL1Network().getL1CircuitManager()
                        #         l1circuits = l1CircuitManager.getAllL1Circuits()
                        #         for attr, val in l1circuits.items():
                        #             l1circuit_name = val.getName()
                        #             # logging.info("L1 circuit name is " + l1circuit_name)
                        #             if v3['vc-fdn'] == val.getName():
                        #                 # logging.info("Name matched!")
                        #                 l1circuit = l1CircuitManager.getL1Circuit(val.getKey())
                        #                 l3circuit.setL1Circuit(l1circuit)
                        #                 # TODO recode setting the L3 node site based on connected L1 node site
                        #     l3circuit.setCapacity(intfbw)
                        #     intfdict = l3circuit.getAllInterfacess()
                        #     for k6, v6 in intfdict.items():
                        #         v6.setResvBW(int(rsvpbw / 1000))
                        #     circ_name = l3circuit.getName()
                        #     circ_key = l3circuit.getKey()
                        #     circ_dict = {'SRLGs': srlgs, 'Circuit Key': circ_key, 'discoveredname': discoveredname}
                        #     circ_srlgs[circ_name] = circ_dict
                    duplicatelink = False

    # logging.info("Processing SRLG's...")
    # process_srlgs(plan, circ_srlgs)

def generateL3circuit(plan, name, l3nodeA, l3nodeB, affinity, l3nodeA_ip, l3nodeB_ip, nodeAintfname, nodeBintfname,igp_metric, te_metric,rsvpbw):
    nodeAKey = NodeKey(l3nodeA)
    nodeBKey = NodeKey(l3nodeB)

    scale = 16  ## equals to hexadecimal
    num_of_bits = 32
    # logging.warn bin(int(affinity, scale))[2:].zfill(num_of_bits)
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
            # logging.info("4k node already exists in plan, skipping this one...")
            return True
    return False

